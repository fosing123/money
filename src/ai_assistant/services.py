"""Server-side Gemini integration for the TIANA money coach.

Only derived finance summaries are sent; never send passwords, API keys,
bank credentials, full account identifiers, or contact details to the model.
Cloudflare Workers outbound HTTP must use the runtime Fetch API, not sockets.
"""
import hashlib
import json
import logging
from datetime import timedelta

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.utils import timezone

from budgets.models import Budget
from budgets.services import attach_budget_spending
from finance.models import Transaction
from goals.models import Goal
from .models import AIResponseCache, AIUsage

logger = logging.getLogger(__name__)


class AIConfigurationError(Exception):
    pass


class AIServiceError(Exception):
    pass


class AIUsageLimitError(AIServiceError):
    pass


def _user_snapshot(user):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    month = Transaction.objects.filter(owner=user, transaction_date__gte=month_start, transaction_date__lte=today)
    income = month.filter(kind__in=["income", "refund", "transfer_in"]).aggregate(total=Sum("amount"))["total"] or 0
    expenses = month.filter(kind__in=["expense", "transfer_out"]).aggregate(total=Sum("amount"))["total"] or 0
    budget_rows = list(Budget.objects.filter(owner=user)[:6])
    attach_budget_spending(budget_rows, owner=user)
    budgets = [{
        "category_or_name": budget.category or budget.name,
        "limit_fcfa": str(budget.amount),
        "spent_fcfa": str(budget.spent_amount),
        "period": budget.get_period_display(),
    } for budget in budget_rows]
    goals = [{
        "name": goal.name,
        "target_fcfa": str(goal.target_amount),
        "saved_fcfa": str(goal.saved_amount),
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
        "weekly_budget_allocations_fcfa": user.weekly_budget_allocations or {},
        "current_month_income_fcfa": str(income),
        "current_month_outflow_fcfa": str(expenses),
        "budgets": budgets,
        "goals": goals,
        "recent_transactions": recent,
    }


def _reserve_ai_request(user):
    daily_limit = 20 if user.has_active_premium else 3
    today = timezone.localdate()
    with db_transaction.atomic():
        usage, _ = AIUsage.objects.get_or_create(user=user, usage_date=today)
        usage = AIUsage.objects.select_for_update().get(pk=usage.pk)
        if usage.request_count >= daily_limit:
            if user.has_active_premium:
                message = "You've reached today's 20 AI coach requests. Your allowance resets tomorrow."
            else:
                message = "You've used today's 3 free AI coach requests. Upgrade to TIANA Premium for a higher daily allowance."
            raise AIUsageLimitError(message)
        usage.request_count += 1
        usage.save(update_fields=["request_count", "updated_at"])
    return usage.pk


def _release_ai_request(usage_id):
    with db_transaction.atomic():
        usage = AIUsage.objects.select_for_update().filter(pk=usage_id).first()
        if usage and usage.request_count > 0:
            usage.request_count -= 1
            usage.save(update_fields=["request_count", "updated_at"])


def _prepare_ai_request(user, prompt):
    api_key = getattr(settings, "GEMINI_API_KEY", "") or getattr(settings, "AI_API_KEY", "")
    provider = getattr(settings, "AI_PROVIDER", "gemini").lower()
    model = getattr(settings, "GEMINI_MODEL", "") or getattr(settings, "AI_MODEL", "gemini-3.8-flash")

    if provider != "gemini" or not api_key:
        raise AIConfigurationError("Gemini is not configured on the server yet.")

    snapshot = _user_snapshot(user)
    snapshot_json = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
    normalized_prompt = " ".join(str(prompt).split()).casefold()
    fingerprint = hashlib.sha256((normalized_prompt + "\\n" + snapshot_json).encode("utf-8")).hexdigest()

    cached = AIResponseCache.objects.filter(
        user=user,
        fingerprint=fingerprint,
        created_at__gte=timezone.now() - timedelta(hours=24),
    ).first()
    if cached:
        return {"cached_response": cached.response}

    usage_id = _reserve_ai_request(user)
    system_prompt = (
        "You are TIANA, a warm, respectful personal money companion for students and young people "
        "in Cameroon. Use FCFA/XAF unless the user has another currency. Speak naturally, briefly, "
        "and without judgement. Be practical and kind; prefer one or two realistic next steps over "
        "a lecture. Never shame someone for spending, imply their data is perfect, invent missing "
        "facts, claim to move money, or promise investment returns. Do not give high-risk investment "
        "instructions. Make it clear when you are estimating. Financial education only, not a "
        "licensed financial adviser. Never request passwords, PINs, API keys or full account numbers. "
        "Your role is personalized guidance: help the user make progress toward their stated goals, "
        "compare priorities, plan an affordable purchase, and choose realistic next steps using their "
        "weekly plan and recent activity. The app's deterministic budget engine handles threshold "
        "warnings and notifications separately. Do not imitate system alerts, announce that a budget "
        "has crossed a threshold as if you triggered it, or replace a system warning with an AI message. "
        "When the user asks for advice, explain trade-offs and suggest a practical option without "
        "shaming or issuing commands."
    )
    contents = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{
            "role": "user",
            "parts": [{
                "text": "Here is a limited summary of my finance app data (numbers are FCFA where noted):\\n"
                        + snapshot_json
                        + "\\n\\nMy question:\\n" + prompt
            }],
        }],
        "generationConfig": {"maxOutputTokens": 380},
    }
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    return {
        "endpoint": endpoint,
        "api_key": api_key,
        "body": json.dumps(contents, ensure_ascii=False),
        "usage_id": usage_id,
        "user": user,
        "fingerprint": fingerprint,
        "model": model,
    }


async def _fetch_gemini_response(endpoint, api_key, body):
    """Call Gemini using Cloudflare's asynchronous Fetch runtime API."""
    from workers import fetch

    response = await fetch(
        endpoint,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        body=body,
    )
    return response.status, await response.text()


def _store_ai_response(user, fingerprint, answer):
    now = timezone.now()
    AIResponseCache.objects.filter(
        user=user,
        created_at__lt=now - timedelta(days=30),
    ).delete()
    AIResponseCache.objects.update_or_create(
        user=user,
        fingerprint=fingerprint,
        defaults={"response": answer, "created_at": now},
    )


async def generate_money_guidance(user, prompt):
    """Build a private finance snapshot, call Gemini over Workers fetch, and cache the answer."""
    prepared = await sync_to_async(_prepare_ai_request, thread_sensitive=True)(user, prompt)
    if "cached_response" in prepared:
        return prepared["cached_response"]

    usage_id = prepared["usage_id"]
    try:
        status, raw_body = await _fetch_gemini_response(
            prepared["endpoint"],
            prepared["api_key"],
            prepared["body"],
        )
    except Exception as exc:
        await sync_to_async(_release_ai_request, thread_sensitive=True)(usage_id)
        logger.exception("Gemini request failed before an HTTP response was received.")
        raise AIServiceError(
            "I couldn't connect to the AI service just now. Please try again shortly."
        ) from exc

    try:
        payload = json.loads(raw_body)
    except (TypeError, json.JSONDecodeError) as exc:
        await sync_to_async(_release_ai_request, thread_sensitive=True)(usage_id)
        logger.warning("Gemini returned a non-JSON response (HTTP %s).", status)
        raise AIServiceError(
            "The AI service returned an unexpected response. Please try again shortly."
        ) from exc

    if status < 200 or status >= 300:
        await sync_to_async(_release_ai_request, thread_sensitive=True)(usage_id)
        detail = str(payload.get("error", {}).get("message", ""))[:240]
        logger.warning("Gemini returned HTTP %s: %s", status, detail or "No error detail provided.")
        if status in (401, 403):
            raise AIServiceError(
                "Gemini rejected the configured server key or its API permissions. Check the Gemini API key and project access."
            )
        if status == 429:
            raise AIServiceError(
                "The AI coach has reached a temporary Gemini rate limit. Please try again in a moment."
            )
        if status == 404:
            raise AIServiceError(
                f"The configured Gemini model is unavailable ({prepared['model']}). Check the model ID and API access."
            )
        raise AIServiceError(
            f"Gemini could not complete the request (HTTP {status}). Please try again shortly."
        )

    try:
        candidates = payload.get("candidates", [])
        parts = candidates[0]["content"]["parts"]
        answer = "\\n".join(part.get("text", "") for part in parts if part.get("text")).strip()
    except (IndexError, KeyError, TypeError):
        answer = ""

    if not answer:
        await sync_to_async(_release_ai_request, thread_sensitive=True)(usage_id)
        feedback = payload.get("promptFeedback", {}).get("blockReason", "")
        if feedback:
            logger.info("Gemini blocked a prompt (reason: %s).", str(feedback)[:80])
            raise AIServiceError(
                "I couldn't answer that exact wording. Try rephrasing your question."
            )
        logger.warning("Gemini returned HTTP 200 without a text candidate.")
        raise AIServiceError(
            "I didn't get a usable answer back. Try asking in a different way."
        )

    answer = answer[:7000]
    await sync_to_async(_store_ai_response, thread_sensitive=True)(
        prepared["user"], prepared["fingerprint"], answer
    )
    return answer
