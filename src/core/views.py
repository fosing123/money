from decimal import Decimal, InvalidOperation
from datetime import date
import json
import logging
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction as db_transaction
from django.db.models import Q, Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.models import User
from budgets.models import Budget
from budgets.services import attach_budget_spending
from finance.models import Account, Transaction
from goals.models import Goal
from notifications.services import evaluate_spending_alerts
from core.money_intelligence import build_money_snapshot


logger = logging.getLogger(__name__)


def home_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard" if request.user.onboarding_completed else "onboarding_setup")
    return render(request, "core/landing.html")


@login_required
def dashboard_view(request):
    user = request.user
    if not user.onboarding_completed:
        return redirect("onboarding_setup")

    all_budgets = list(Budget.objects.filter(owner=user))
    evaluate_spending_alerts(user, budgets=all_budgets)
    snapshot = build_money_snapshot(user)
    return render(request, "core/dashboard.html", snapshot)


@require_GET
def health_check_view(request):
    """Check both Django startup and a real PostgreSQL round trip."""
    try:
        with db_transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT %s", [1])
                database_ok = cursor.fetchone() == (1,)
            if not database_ok:
                raise RuntimeError("Database health probe returned an unexpected result.")

            # Verify the two JSONField columns TIANA actually uses. Roll back
            # the probe row so this public health endpoint never leaves data.
            probe_name = f"__health_{uuid.uuid4().hex}"
            expected_priorities = ["cloudflare", "pg8000"]
            expected_allocations = {"health_probe": 1}
            probe_user = User.objects.create(
                username=probe_name,
                email=f"{probe_name}@invalid.test",
                financial_priorities=expected_priorities,
                weekly_budget_allocations=expected_allocations,
            )
            saved_user = User.objects.get(pk=probe_user.pk)
            if (
                saved_user.financial_priorities != expected_priorities
                or saved_user.weekly_budget_allocations != expected_allocations
            ):
                raise RuntimeError("PostgreSQL JSONField round-trip failed.")
            db_transaction.set_rollback(True)
    except Exception:
        logger.exception("TIANA database health check failed")
        return JsonResponse(
            {"status": "degraded", "service": "tiana", "database": "unavailable"},
            status=503,
        )
    return JsonResponse(
        {"status": "ok", "service": "tiana", "database": "ok", "json_fields": "ok"}
    )


@login_required
def investments_coming_soon_view(request):
    return render(request, "core/investments_coming_soon.html")



@require_GET
def service_worker_view(request):
    """Serve the dedicated Django PWA worker at the site root.

    This worker never caches authenticated HTML, financial JSON, POST requests,
    or uploaded media. The legacy prototype worker is intentionally not reused.
    """
    worker_path = settings.BASE_DIR / "tiana-service-worker.js"
    try:
        source = worker_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise Http404("TIANA service worker is unavailable.") from exc
    response = HttpResponse(source, content_type="application/javascript; charset=utf-8")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


@login_required
@require_GET
def offline_bootstrap_view(request):
    """Return the signed-in user's minimum offline snapshot; never cache this response."""
    user = request.user
    accounts = list(Account.objects.filter(owner=user, is_active=True).values(
        "id", "name", "account_type", "currency", "balance"
    ))
    budgets = list(Budget.objects.filter(owner=user).order_by("period", "name")[:20])
    attach_budget_spending(budgets, owner=user)
    budget_payload = []
    for budget in budgets:
        budget_payload.append({
            "id": budget.pk,
            "name": budget.name,
            "category": budget.category,
            "amount": str(budget.amount),
            "spent": str(budget.spent_amount),
            "currency": budget.currency,
            "period": budget.period,
        })
    goals = []
    for goal in Goal.objects.filter(owner=user).prefetch_related("contributions__transaction").order_by("status", "target_date")[:20]:
        goals.append({
            "id": goal.pk,
            "name": goal.name,
            "target": str(goal.target_amount),
            "saved": str(goal.saved_amount),
            "remaining": str(goal.remaining_amount),
            "progress": goal.progress_percentage,
            "currency": goal.currency,
            "status": goal.status,
        })
    recent = []
    for item in Transaction.objects.filter(owner=user).select_related("account")[:30]:
        recent.append({
            "id": item.pk,
            "kind": item.kind,
            "amount": str(item.amount),
            "currency": item.currency,
            "category": item.category,
            "description": item.description,
            "merchant": item.merchant,
            "account": item.account.name,
            "transaction_date": item.transaction_date.isoformat(),
        })
    response = JsonResponse({
        "currency": user.currency,
        "accounts": accounts,
        "budgets": budget_payload,
        "goals": goals,
        "recent_transactions": recent,
        "server_date": timezone.localdate().isoformat(),
    })
    response["Cache-Control"] = "private, no-store, max-age=0"
    response["Vary"] = "Cookie"
    return response


@login_required
@require_POST
def offline_sync_view(request):
    """Idempotently accept only basic income/expense entries created offline."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "Send valid JSON."}, status=400)
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return JsonResponse({"error": "An items array is required."}, status=400)
    if len(items) > 25:
        return JsonResponse({"error": "Sync up to 25 entries at a time."}, status=413)

    results = []
    has_expense = False
    for raw in items:
        if not isinstance(raw, dict):
            results.append({"id": "", "status": "rejected", "message": "Invalid entry format."})
            continue
        client_id = str(raw.get("id", ""))
        try:
            offline_id = uuid.UUID(client_id)
        except (ValueError, TypeError, AttributeError):
            results.append({"id": client_id, "status": "rejected", "message": "This entry has an invalid sync ID."})
            continue

        existing = Transaction.objects.filter(offline_id=offline_id).first()
        if existing:
            if existing.owner_id == request.user.pk:
                results.append({"id": client_id, "status": "synced", "transaction_id": existing.pk, "duplicate": True})
            else:
                results.append({"id": client_id, "status": "rejected", "message": "This sync ID is already in use."})
            continue

        kind = str(raw.get("kind", "")).strip().lower()
        if kind not in {"income", "expense"}:
            results.append({"id": client_id, "status": "rejected", "message": "Offline sync accepts income and expense entries only."})
            continue
        try:
            amount = Decimal(str(raw.get("amount", "")))
            account_id = int(raw.get("account_id"))
            transaction_date = date.fromisoformat(str(raw.get("transaction_date", "")))
        except (InvalidOperation, ValueError, TypeError):
            results.append({"id": client_id, "status": "rejected", "message": "Check the amount, account and date."})
            continue
        if not amount.is_finite() or amount <= 0 or amount > Decimal("999999999999.99") or amount.as_tuple().exponent < -2:
            results.append({"id": client_id, "status": "rejected", "message": "Enter a valid positive amount with no more than two decimal places."})
            continue

        account = Account.objects.filter(pk=account_id, owner=request.user, is_active=True).first()
        if account is None:
            results.append({"id": client_id, "status": "rejected", "message": "That account is no longer available. Review the entry online."})
            continue
        currency = str(raw.get("currency") or account.currency).strip().upper()
        if currency != account.currency.upper():
            results.append({"id": client_id, "status": "rejected", "message": "The entry currency does not match the selected account."})
            continue

        item = Transaction(
            owner=request.user,
            account=account,
            offline_id=offline_id,
            amount=amount,
            currency=currency,
            kind=kind,
            category=str(raw.get("category") or "Other").strip()[:50] or "Other",
            description=str(raw.get("description") or "").strip()[:255],
            merchant=str(raw.get("merchant") or "").strip()[:120],
            transaction_date=transaction_date,
        )
        try:
            with db_transaction.atomic():
                item.save()
            has_expense = has_expense or kind == "expense"
            results.append({"id": client_id, "status": "synced", "transaction_id": item.pk})
        except (ValidationError, IntegrityError):
            existing = Transaction.objects.filter(offline_id=offline_id, owner=request.user).first()
            if existing:
                results.append({"id": client_id, "status": "synced", "transaction_id": existing.pk, "duplicate": True})
            else:
                results.append({"id": client_id, "status": "rejected", "message": "The entry could not be saved. Review it online."})

    if has_expense:
        evaluate_spending_alerts(request.user)
    response = JsonResponse({"results": results, "server_date": timezone.localdate().isoformat()})
    response["Cache-Control"] = "private, no-store, max-age=0"
    response["Vary"] = "Cookie"
    return response


@login_required
def premium_view(request):
    return render(request, "core/premium.html", {
        "premium_active": request.user.has_active_premium,
        "free_ai_daily_limit": 3,
        "premium_ai_daily_limit": 20,
    })


@require_GET
def money_school_view(request):
    """Keep third-party ad scripts on the public education page, never finance screens."""
    is_premium_member = (
        request.user.is_authenticated and request.user.has_active_premium
    )
    adsterra_enabled = settings.ADSTERRA_ENABLED and not is_premium_member
    adsense_enabled = (
        settings.ADSENSE_ENABLED and not is_premium_member and not adsterra_enabled
    )
    return render(request, "core/money_school.html", {
        "adsense_enabled": adsense_enabled,
        "adsense_client_id": settings.ADSENSE_CLIENT_ID,
        "adsense_slot_id": settings.ADSENSE_SLOT_ID,
        "adsterra_enabled": adsterra_enabled,
        "adsterra_website_id": settings.ADSTERRA_WEBSITE_ID,
        # Only trusted deployment secrets are rendered, and only on this
        # public education page after the explicit enablement checks above.
        "adsterra_banner_320x50_code": (
            settings.ADSTERRA_BANNER_320X50_CODE if adsterra_enabled else ""
        ),
        "adsterra_banner_300x250_code": (
            settings.ADSTERRA_BANNER_300X250_CODE if adsterra_enabled else ""
        ),
    })
