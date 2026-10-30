"""Server-side Gemini integration for the TIANA money coach.

Only derived finance summaries are sent; never send passwords, API keys,
bank credentials, full account identifiers, or contact details to the model.
"""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from budgets.models import Budget
from finance.models import Transaction
from goals.models import Goal


class AIConfigurationError(Exception):
    pass


class AIServiceError(Exception):
    pass


def _user_snapshot(user):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    month = Transaction.objects.filter(owner=user, transaction_date__gte=month_start, transaction_date__lte=today)
    income = month.filter(kind__in=["income", "refund", "transfer_in"]).aggregate(total=Sum("amount"))["total"] or 0
    expenses = month.filter(kind__in=["expense", "transfer_out"]).aggregate(total=Sum("amount"))["total"] or 0
    budgets = [{
        "category_or_name": budget.category or budget.name,
        "limit_fcfa": str(budget.amount),
        "spent_fcfa": str(budget.spent_amount),
        "period": budget.get_period_display(),
    } for budget in Budget.objects.filter(owner=user)[:6]]
    goals = [{
        "name": goal.name,
        "target_fcfa": str(goal.target_amount),
        "saved_fcfa": str(goal.current_amount),
        "progress_percent": goal.progress_percentage,
    } for goal in Goal.objects.filter(owner=user, status="active")[:6]]
    recent = [{
        "type": tx.get_kind_display(),
        "category": tx.category,
        "amount_fcfa": str(tx.amount),
        "date": tx.transaction_date.isoformat(),
    } for tx in Transaction.objects.filter(owner=user).order_by("-transaction_date", "-created_at")[:8]]
    return {
        "currency": user.currency,
        "weekly_income_estimate_fcfa": str(user.weekly_income),
        "weekly_savings_target_fcfa": str(user.weekly_savings_target),
        "current_month_income_fcfa": str(income),
        "current_month_outflow_fcfa": str(expenses),
        "budgets": budgets,
        "goals": goals,
        "recent_transactions": recent,
    }


def generate_money_guidance(user, prompt):
    api_key = getattr(settings, "GEMINI_API_KEY", "") or getattr(settings, "AI_API_KEY", "")
    provider = getattr(settings, "AI_PROVIDER", "gemini").lower()
    model = getattr(settings, "GEMINI_MODEL", "") or getattr(settings, "AI_MODEL", "gemini-3.8-flash")
    if provider != "gemini" or not api_key:
        raise AIConfigurationError("Gemini is not configured on the server yet.")

    system_prompt = (
        "You are TIANA, a warm, respectful personal money companion for students and young people "
        "in Cameroon. Use FCFA/XAF unless the user has another currency. Speak naturally, briefly, "
        "and without judgement. Be practical and kind; prefer one or two realistic next steps over "
        "a lecture. Never shame someone for spending, imply their data is perfect, invent missing "
        "facts, claim to move money, or promise investment returns. Do not give high-risk investment "
        "instructions. Make it clear when you are estimating. Financial education only, not a "
        "licensed financial adviser. Never request passwords, PINs, API keys or full account numbers."
    )
    contents = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{
            "role": "user",
            "parts": [{"text": "Here is a limited summary of my finance app data (numbers are FCFA where noted):\n"
                              + json.dumps(_user_snapshot(user), ensure_ascii=False)
                              + "\n\nMy question:\n" + prompt}],
        }],
        # Keep configuration portable across current Gemini Flash model generations.
        "generationConfig": {"maxOutputTokens": 520},
    }
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    request = Request(
        endpoint,
        data=json.dumps(contents).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urlopen(request, timeout=18) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code in (401, 403):
            raise AIServiceError("Gemini did not accept the configured server key. Check GEMINI_API_KEY.") from exc
        if exc.code == 429:
            raise AIServiceError("The AI coach is taking a short breather. Please try again in a moment.") from exc
        raise AIServiceError("The AI coach could not complete that request right now.") from exc
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise AIServiceError("I couldn't reach the AI coach just now. Please try again shortly.") from exc

    try:
        candidates = payload.get("candidates", [])
        parts = candidates[0]["content"]["parts"]
        answer = "\n".join(part.get("text", "") for part in parts if part.get("text")).strip()
    except (IndexError, KeyError, TypeError):
        answer = ""
    if not answer:
        raise AIServiceError("I didn't get a usable answer back. Try asking in a different way.")
    return answer[:7000]