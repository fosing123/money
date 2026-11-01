"""Authenticated device registration and account backup APIs."""
import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from budgets.models import Budget
from finance.models import Account, Transaction
from goals.models import Goal, GoalContribution
from .models import PushDevice


def _json_body(request):
    try:
        value = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return value if isinstance(value, dict) else None


@login_required
@require_POST
def register_push_device_view(request):
    payload = _json_body(request)
    if payload is None:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)
    token = payload.get("token")
    platform = payload.get("platform", "web")
    device_id = payload.get("device_id", "")
    if not isinstance(token, str) or not 20 <= len(token) <= 4096:
        return JsonResponse({"error": "A valid FCM registration token is required."}, status=400)
    if platform not in {"web", "android", "ios"}:
        return JsonResponse({"error": "Unsupported platform."}, status=400)
    device, _ = PushDevice.objects.update_or_create(
        token=token,
        defaults={
            "user": request.user,
            "platform": platform,
            "device_id": str(device_id)[:128],
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:512],
            "is_active": True,
            "last_seen_at": timezone.now(),
        },
    )
    return JsonResponse({"ok": True, "device_id": device.pk})


@login_required
@require_POST
def unregister_push_device_view(request):
    payload = _json_body(request)
    token = payload.get("token") if payload else None
    if not isinstance(token, str) or not token:
        return JsonResponse({"error": "A registration token is required."}, status=400)
    changed = PushDevice.objects.filter(user=request.user, token=token).update(is_active=False)
    return JsonResponse({"ok": True, "revoked": bool(changed)})


@login_required
@require_GET
def backup_export_view(request):
    """Export only the current user's data in a versioned, portable JSON format."""
    user = request.user
    accounts = list(Account.objects.filter(owner=user).order_by("pk"))
    account_ids = [a.pk for a in accounts]
    transactions = list(Transaction.objects.filter(owner=user, account_id__in=account_ids).order_by("pk"))
    goals = list(Goal.objects.filter(owner=user).order_by("pk"))
    goal_ids = [g.pk for g in goals]
    contributions = list(GoalContribution.objects.filter(owner=user, goal_id__in=goal_ids).select_related("transaction").order_by("pk"))
    budgets = list(Budget.objects.filter(owner=user).order_by("pk"))

    payload = {
        "format": "tiana.account-backup",
        "version": 1,
        "exported_at": timezone.now().isoformat(),
        "profile": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "currency": user.currency,
            "timezone": user.timezone,
            "weekly_income": str(user.weekly_income),
            "weekly_savings_target": str(user.weekly_savings_target),
            "payday_weekday": user.payday_weekday,
            "financial_priorities": user.financial_priorities,
            "weekly_budget_allocations": user.weekly_budget_allocations,
            "theme": user.theme,
        },
        "accounts": [{
            "backup_id": a.pk, "name": a.name, "account_type": a.account_type,
            "currency": a.currency, "opening_balance": str(a.opening_balance),
            "is_active": a.is_active,
        } for a in accounts],
        "transactions": [{
            "backup_id": t.pk, "account_backup_id": t.account_id, "amount": str(t.amount),
            "currency": t.currency, "kind": t.kind, "category": t.category,
            "description": t.description, "merchant": t.merchant,
            "transaction_date": t.transaction_date.isoformat(),
        } for t in transactions],
        "budgets": [{
            "name": b.name, "amount": str(b.amount), "currency": b.currency,
            "period": b.period, "category": b.category, "start_date": b.start_date.isoformat(),
            "end_date": b.end_date.isoformat() if b.end_date else None,
        } for b in budgets],
        "goals": [{
            "backup_id": g.pk, "name": g.name, "description": g.description,
            "target_amount": str(g.target_amount), "current_amount": str(g.current_amount),
            "currency": g.currency, "target_date": g.target_date.isoformat() if g.target_date else None,
            "status": g.status,
        } for g in goals],
        "goal_contributions": [{
            "goal_backup_id": c.goal_id, "transaction_backup_id": c.transaction_id, "note": c.note,
        } for c in contributions],
    }
    response = HttpResponse(
        json.dumps(payload, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="tiana-backup-{timezone.localdate():%Y%m%d}.json"'
    response["Cache-Control"] = "private, no-store, max-age=0"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
@require_POST
def backup_restore_view(request):
    """Restore a versioned backup as additive data; never overwrite existing records."""
    if request.content_type != "application/json":
        return JsonResponse({"error": "Send the backup as application/json."}, status=415)
    if len(request.body) > 5 * 1024 * 1024:
        return JsonResponse({"error": "Backup exceeds the 5 MB limit."}, status=413)
    payload = _json_body(request)
    if not payload or payload.get("format") != "tiana.account-backup" or payload.get("version") != 1:
        return JsonResponse({"error": "Unsupported or invalid TIANA backup."}, status=400)
    for key in ("accounts", "transactions", "budgets", "goals", "goal_contributions"):
        if not isinstance(payload.get(key), list) or len(payload[key]) > 10000:
            return JsonResponse({"error": f"Invalid {key} collection."}, status=400)

    def money(value):
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount > Decimal("999999999999.99"):
            raise ValueError("Invalid monetary amount.")
        return amount

    try:
        with transaction.atomic():
            account_map = {}
            for item in payload["accounts"]:
                if not isinstance(item, dict) or not item.get("name"):
                    raise ValueError("Invalid account entry.")
                account = Account.objects.create(
                    owner=request.user, name=str(item["name"])[:100],
                    account_type=item.get("account_type", "cash"),
                    currency=str(item.get("currency", request.user.currency))[:10],
                    opening_balance=money(item.get("opening_balance", 0)),
                    is_active=bool(item.get("is_active", True)),
                )
                account_map[str(item.get("backup_id"))] = account

            transaction_map = {}
            for item in payload["transactions"]:
                if not isinstance(item, dict):
                    raise ValueError("Invalid transaction entry.")
                account = account_map.get(str(item.get("account_backup_id")))
                kind = item.get("kind")
                if account is None or kind not in dict(Transaction.KIND_CHOICES):
                    raise ValueError("Transaction references an unknown account or type.")
                entry = Transaction.objects.create(
                    owner=request.user, account=account, amount=money(item.get("amount")),
                    currency=str(item.get("currency", account.currency))[:10], kind=kind,
                    category=str(item.get("category", "General"))[:50],
                    description=str(item.get("description", ""))[:255],
                    merchant=str(item.get("merchant", ""))[:120],
                    transaction_date=date.fromisoformat(item["transaction_date"]),
                )
                transaction_map[str(item.get("backup_id"))] = entry

            for item in payload["budgets"]:
                Budget.objects.create(
                    owner=request.user, name=str(item.get("name", "Restored budget"))[:120],
                    amount=money(item.get("amount", 0)), currency=str(item.get("currency", request.user.currency))[:10],
                    period=item.get("period", "monthly"), category=str(item.get("category", ""))[:50],
                    start_date=date.fromisoformat(item["start_date"]),
                    end_date=date.fromisoformat(item["end_date"]) if item.get("end_date") else None,
                )

            goal_map = {}
            for item in payload["goals"]:
                goal = Goal.objects.create(
                    owner=request.user, name=str(item.get("name", "Restored goal"))[:120],
                    description=str(item.get("description", ""))[:5000],
                    target_amount=money(item.get("target_amount", 0)),
                    current_amount=money(item.get("current_amount", 0)),
                    currency=str(item.get("currency", request.user.currency))[:10],
                    target_date=date.fromisoformat(item["target_date"]) if item.get("target_date") else None,
                    status=item.get("status", "active"),
                )
                goal_map[str(item.get("backup_id"))] = goal

            for item in payload["goal_contributions"]:
                goal = goal_map.get(str(item.get("goal_backup_id")))
                entry = transaction_map.get(str(item.get("transaction_backup_id")))
                if goal is None or entry is None or entry.kind != "transfer_out":
                    raise ValueError("Goal contribution references invalid backup records.")
                GoalContribution.objects.create(
                    owner=request.user, goal=goal, transaction=entry, note=str(item.get("note", ""))[:160],
                )

        return JsonResponse({
            "ok": True, "accounts": len(account_map), "transactions": len(transaction_map),
            "budgets": len(payload["budgets"]), "goals": len(goal_map),
        }, status=201)
    except (ValueError, TypeError, KeyError, InvalidOperation) as exc:
        return JsonResponse({"error": str(exc) or "Backup validation failed."}, status=400)
