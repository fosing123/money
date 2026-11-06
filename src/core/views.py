from decimal import Decimal, InvalidOperation
from datetime import date
import html
import json
import logging
import re
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
                cursor.execute("SELECT 1")
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
    return render(request, "core/money_school.html", {
        "adsense_enabled": settings.ADSENSE_ENABLED,
        "adsense_client_id": settings.ADSENSE_CLIENT_ID,
        "adsense_slot_id": settings.ADSENSE_SLOT_ID,
        "guides": list(MONEY_SCHOOL_GUIDES.values()),
    })

MONEY_SCHOOL_GUIDES = {
    "weekly-budget": {
        "slug": "weekly-budget",
        "title": "Build a weekly student budget that works in real life",
        "description": "A practical FCFA budgeting method for students: plan around reliable income, protect essentials, make room for savings and adjust when a week changes.",
        "intro": "A useful budget is not a punishment and it is not a promise that every week will go perfectly. It is a simple plan for the money you can reasonably expect, with enough flexibility to handle real life. For students managing allowances, Mobile Money, cash and school costs, a weekly review can make the next decision easier.",
        "reading_time": "5 minute guide",
        "sections": [
            {
                "heading": "Start with money you can count on",
                "paragraphs": [
                    "Write down the amount you can usually rely on for the coming week. Use money that is already available or that has a dependable arrival date. Do not build the entire plan around a possible gift, a business sale that has not happened or a payment someone has only promised.",
                    "When income changes from week to week, begin with a conservative amount. You can make a second plan for extra money when it actually arrives."
                ],
                "bullets": ["Record the amount and expected date.", "Separate regular income from occasional money.", "Keep a note of any amount that is already committed to a bill or debt."]
            },
            {
                "heading": "Give essentials a place before optional spending",
                "paragraphs": [
                    "List the costs that keep your week running: food, transport, school materials, phone data, accommodation or family responsibilities where these apply. The exact categories are personal. The important part is to name them before the small purchases begin.",
                    "Look at recent transactions to estimate realistic amounts. A budget based on what you actually spend is more useful than one based on what you wish you spent."
                ],
                "bullets": ["Use recent records rather than guesses where possible.", "Add a small buffer for costs that are difficult to predict.", "Avoid counting the same franc in two categories."]
            },
            {
                "heading": "Choose a savings amount you can repeat",
                "paragraphs": [
                    "Savings work best when the amount is achievable after essentials. Start small if necessary. A contribution you can repeat is usually more useful than an ambitious target that leaves you short before the week ends.",
                    "Give savings a purpose, such as education costs, equipment, an emergency reserve or a future business. A named goal makes it easier to decide whether to spend or keep the money."
                ],
                "bullets": ["Choose a weekly amount that fits your real income.", "Keep goal money distinct in your plan.", "Review the target when your income or costs change."]
            },
            {
                "heading": "Use a simple weekly check-in",
                "paragraphs": [
                    "At the end of the week, compare the plan with your recorded transactions. Look for patterns, not reasons to blame yourself. One unexpected journey or school expense does not mean the whole plan has failed.",
                    "Move money between categories only after checking what still needs to be paid. If a category is repeatedly short, adjust the plan rather than pretending the same limit will work next week."
                ],
                "bullets": ["What cost more than expected?", "Which expense was essential?", "What can change next week?", "Did the savings amount remain comfortable?"]
            }
        ],
        "takeaway": "The goal is not a perfect spreadsheet. It is a realistic plan you can understand, follow and improve."
    },
    "savings-goals": {
        "slug": "savings-goals",
        "title": "Turn a savings goal into a plan you can follow",
        "description": "Learn how to choose a savings target, set a realistic contribution, estimate a timeline and adjust without sacrificing essential needs.",
        "intro": "A goal gives your savings a destination. It could be a laptop for school, a professional course, a small business tool, a rent deposit or an emergency reserve. The best starting point is a clear target and a contribution that fits around the rest of your life.",
        "reading_time": "4 minute guide",
        "sections": [
            {
                "heading": "Make the goal specific",
                "paragraphs": [
                    "Give the goal a name and write down what you are saving for. Decide how much you need and, where useful, when you hope to reach it. A specific goal is easier to review than a general intention to save more.",
                    "Check the target amount before you begin. For a purchase, use current prices from reliable sellers and remember that delivery or supporting costs may also matter. Do not treat an estimate as a guaranteed final price."
                ],
                "bullets": ["Name the goal.", "Set a target amount and currency.", "Choose a date only if it is realistic."]
            },
            {
                "heading": "Work backwards from the amount remaining",
                "paragraphs": [
                    "Subtract the amount already saved from your target. Then divide what remains by the number of weeks or months available. This gives you a rough contribution to aim for; it is not a requirement to put that exact amount aside if doing so would affect essentials.",
                    "A large target with a short deadline may need more time or a different plan. Extending the date is often a better choice than borrowing to keep an unrealistic schedule."
                ],
                "bullets": ["Check the amount still needed.", "Estimate a weekly or monthly contribution.", "Extend the date or reduce the target if the amount is too difficult."]
            },
            {
                "heading": "Protect your day-to-day needs",
                "paragraphs": [
                    "Do not save so aggressively that you cannot afford food, transport, school costs or other important commitments. If your income is uncertain, build the plan around the money you can rely on and contribute extra only when it is actually available.",
                    "An emergency reserve can help prevent one surprise expense from forcing you to abandon another goal. Start with an amount that is manageable for your situation."
                ],
                "bullets": ["Cover essentials before optional contributions.", "Keep a little room for unexpected needs.", "Avoid borrowing just to keep a savings target on schedule."]
            },
            {
                "heading": "Review progress and adjust calmly",
                "paragraphs": [
                    "Check your saved amount regularly and make sure each contribution is recorded once. If income changes, update the plan. If you miss a contribution, recalculate the remaining amount instead of assuming you have failed.",
                    "When you reach the target, decide what comes next: complete the purchase, keep building a reserve or create a new milestone. A goal is a guide for your choices, not a source of pressure."
                ],
                "bullets": ["Review progress once a week or month.", "Update the timeline when circumstances change.", "Celebrate milestones without spending the money twice."]
            }
        ],
        "takeaway": "A steady, affordable contribution gives a goal momentum. Your plan should support your life, not compete with your essentials."
    },
    "mobile-money-safety": {
        "slug": "mobile-money-safety",
        "title": "Protect your Mobile Money and digital accounts",
        "description": "Practical account-safety habits for students using Mobile Money, banking apps, email and digital services in Cameroon.",
        "intro": "A phone can hold access to money, school communication, email and personal accounts. A few careful habits make it harder for someone else to misuse that access. This guide is general safety education; always follow the current security instructions from your own provider.",
        "reading_time": "5 minute guide",
        "sections": [
            {
                "heading": "Keep authentication details private",
                "paragraphs": [
                    "Never share your Mobile Money PIN, banking password, one-time password, recovery code or phone unlock code with someone who contacts you unexpectedly. A genuine support agent should not need you to reveal your secret PIN or one-time code in a chat or call.",
                    "Be careful with people who create urgency. Messages claiming that an account will be blocked immediately, that a prize is waiting or that a transfer must be reversed can be used to pressure you into revealing information."
                ],
                "bullets": ["Do not read one-time codes to callers.", "Use a different password for your email and financial accounts.", "Turn on device locking and available account security features."]
            },
            {
                "heading": "Check the recipient before confirming",
                "paragraphs": [
                    "Before confirming a transfer, pause and check the recipient name, number and amount on the confirmation screen. A familiar name in a message is not proof that a number belongs to the right person.",
                    "If a request comes from a friend or family member asking for urgent money, verify it through a separate trusted channel. An account may be impersonated or a phone may be in someone else's hands."
                ],
                "bullets": ["Read every confirmation screen.", "Verify unexpected requests directly.", "Keep the transaction reference after a successful payment."]
            },
            {
                "heading": "Be careful with links, apps and public devices",
                "paragraphs": [
                    "Do not install an application from an unknown link simply because a message says it is needed to receive money or fix an account. Use the official app store or the provider's official website, and check the publisher before installing.",
                    "Avoid signing in to money accounts on shared phones or public computers. If you must use a shared device, sign out completely and never save your password in the browser."
                ],
                "bullets": ["Check website spelling before entering credentials.", "Do not grant unnecessary app permissions.", "Keep your phone and apps updated when possible."]
            },
            {
                "heading": "Know what to do when something looks wrong",
                "paragraphs": [
                    "If your phone is lost, your SIM stops working unexpectedly or you notice a transaction you did not make, contact your provider through its official support channel as soon as possible. Use the provider's current process to secure the account and keep relevant transaction references.",
                    "Do not send more money to someone promising to recover a lost transfer for a fee. Keep screenshots and messages that may help the provider investigate, but do not post private account details publicly."
                ],
                "bullets": ["Contact the provider using verified contact details.", "Secure your email and other accounts connected to the phone.", "Keep PINs, passwords and recovery codes out of screenshots and support posts."]
            }
        ],
        "takeaway": "Pause before you share a code or confirm a transfer. A short verification step can protect a lot of time and money."
    },
    "variable-income": {
        "slug": "variable-income",
        "title": "Plan when your student income changes from week to week",
        "description": "A practical approach to budgeting with irregular allowances, part-time work, small business income or occasional support.",
        "intro": "Not everyone receives the same amount on the same day. Allowances can be delayed, part-time work can vary and small business sales can change. A useful plan separates money you can rely on from money that may arrive, so one uncertain payment does not create a chain of missed commitments.",
        "reading_time": "4 minute guide",
        "sections": [
            {
                "heading": "Build your basic plan around dependable income",
                "paragraphs": [
                    "Look at the money that usually arrives and how often it arrives. If the amount changes, use a conservative estimate based on your recent experience rather than the best week you have had.",
                    "List essential costs and due dates alongside the expected income dates. This helps you see whether money will arrive before it is needed, not only whether the monthly total looks large enough."
                ],
                "bullets": ["Separate reliable income from uncertain income.", "Write down when important costs are due.", "Keep a small buffer if your timing is unpredictable."]
            },
            {
                "heading": "Give extra income a job after it arrives",
                "paragraphs": [
                    "When extra money comes in, pause before treating it as free spending money. Check essential costs due soon, any shortfall from the current week and the goals you have already chosen.",
                    "You can divide an extra amount between catching up on a priority, strengthening a buffer, contributing to a goal and personal spending. The right balance depends on your needs; there is no universal percentage that fits every student."
                ],
                "bullets": ["Cover an essential cost that is due soon.", "Repair a shortfall or add to an emergency reserve.", "Move a manageable amount towards one goal.", "Keep a record of what remains."]
            },
            {
                "heading": "Keep business and personal money understandable",
                "paragraphs": [
                    "If you earn money from a small business, track sales separately from the money you can safely use personally. Sales revenue is not the same as profit: stock, transport, mobile data and other operating costs may still need to be paid.",
                    "Write down the money received and the costs connected with earning it. This makes it easier to see what the activity actually contributes to your personal budget."
                ],
                "bullets": ["Record each sale and business expense.", "Set aside money needed to restock or operate.", "Only count the amount you can reasonably take for personal use."]
            },
            {
                "heading": "Review the plan when a payment is late",
                "paragraphs": [
                    "If money arrives late, protect the most important commitments first. Contact the person or organisation responsible for the payment using a normal, trusted channel; do not borrow at a high cost just to preserve a budget that was based on an uncertain date.",
                    "Update your expected income and adjust optional spending. Once the payment arrives, decide how to catch up without committing the same amount twice."
                ],
                "bullets": ["Recheck the next few days, not only the month total.", "Delay optional purchases before risking essentials.", "Update your plan when the actual amount arrives."]
            }
        ],
        "takeaway": "A flexible plan is stronger than a budget built on money that has not arrived yet."
    }
}


@require_GET
def money_school_guide_view(request, slug):
    guide = MONEY_SCHOOL_GUIDES.get(slug)
    if guide is None:
        raise Http404("This Money School guide could not be found.")
    related_guides = [item for item in MONEY_SCHOOL_GUIDES.values() if item["slug"] != slug]
    return render(request, "core/money_school_guide.html", {
        "guide": guide,
        "related_guides": related_guides,
    })





@require_GET
def about_view(request):
    return render(request, "core/about.html")


@require_GET
def privacy_view(request):
    return render(request, "core/privacy.html")


@require_GET
def terms_view(request):
    return render(request, "core/terms.html")


@require_GET
def ads_txt_view(request):
    """Serve the publisher record at the exact root path AdSense crawls."""
    client_id = (getattr(settings, "ADSENSE_CLIENT_ID", "") or "").strip()
    match = re.fullmatch(r"ca-pub-(\d{16})", client_id)
    if not match:
        return HttpResponse("", status=404, content_type="text/plain; charset=utf-8")
    publisher_id = match.group(1)
    response = HttpResponse(
        f"google.com, pub-{publisher_id}, DIRECT, f08c47fec0942fa0\n",
        content_type="text/plain; charset=utf-8",
    )
    response["Cache-Control"] = "public, max-age=3600"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_GET
def robots_txt_view(request):
    site_root = (getattr(settings, "PUBLIC_SITE_URL", "https://tiana.lol") or "https://tiana.lol").rstrip("/")
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Allow: /ads.txt\n"
        "Disallow: /admin/\n"
        "Disallow: /dashboard/\n"
        "Disallow: /transactions/\n"
        "Disallow: /budgets/\n"
        "Disallow: /goals/\n"
        "Disallow: /accounts/\n"
        "Disallow: /profile/\n"
        "Disallow: /analyzer/\n"
        "Disallow: /api/\n"
        f"Sitemap: {site_root}/sitemap.xml\n"
    )
    response = HttpResponse(body, content_type="text/plain; charset=utf-8")
    response["Cache-Control"] = "public, max-age=3600"
    return response


@require_GET
def sitemap_xml_view(request):
    site_root = (getattr(settings, "PUBLIC_SITE_URL", "https://tiana.lol") or "https://tiana.lol").rstrip("/")
    public_paths = (
        "", "money-school/", "money-school/weekly-budget/",
        "money-school/savings-goals/", "money-school/mobile-money-safety/",
        "money-school/variable-income/", "about/", "privacy/", "terms/",
    )
    entries = "".join(
        f"<url><loc>{html.escape(site_root + '/' + path, quote=True)}</loc></url>"
        for path in public_paths
    )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{entries}</urlset>"
    )
    response = HttpResponse(body, content_type="application/xml; charset=utf-8")
    response["Cache-Control"] = "public, max-age=3600"
    return response
