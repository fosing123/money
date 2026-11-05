import json
from decimal import Decimal, InvalidOperation

from asgiref.sync import sync_to_async
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .ai import ExpenseAIUnavailable, generate_money_insights
from .models import ExpenseAnalysis
from .scoring import analyze_planned_purchase
from .workspace import build_workspace_context


@login_required
@require_GET
def analyzer_view(request):
    """Read-only overview for analyzing activity, budgets, goals and expenses."""
    period = request.GET.get("period", "week").strip().lower()
    if period not in {"week", "month", "year"}:
        period = "week"
    focus = request.GET.get("scope", "activity").strip().lower()
    if focus not in {"activity", "transaction", "budget", "goal"}:
        focus = "activity"
    object_id = (
        request.GET.get("transaction_id") if focus == "transaction" else
        request.GET.get("budget_id") if focus == "budget" else
        request.GET.get("goal_id") if focus == "goal" else None
    )
    context = build_workspace_context(request.user, period=period, focus=focus, object_id=object_id)
    context["period_options"] = [
        {"value": "week", "label": "Week"},
        {"value": "month", "label": "Month"},
        {"value": "year", "label": "Year"},
    ]
    return render(request, "expense_analyzer/workspace.html", context)


def _build_transaction_preview(user, payload):
    if (payload.get("kind") or "expense") != "expense":
        raise ValueError("TIANA can preview spending impact for expenses. Income is not a spending decision.")
    try:
        amount = Decimal(str(payload.get("amount", "")).replace(",", "").strip())
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Enter a valid amount before analyzing this expense.") from exc
    if amount <= 0:
        raise ValueError("Enter an amount greater than zero.")

    report = analyze_planned_purchase(
        user,
        amount=amount,
        category=(payload.get("category") or "General").strip(),
        description=(payload.get("description") or "").strip(),
        is_essential=str(payload.get("is_essential", "")).lower() in {"1", "true", "yes", "on"},
        persist=False,
    )
    verdict = dict(ExpenseAnalysis.VERDICTS).get(report["verdict"], "Review")
    return {
        "score": report["score"],
        "verdict": verdict,
        "amount": str(report["amount"]),
        "currency": report["currency"],
        "summary": report["summary"],
        "recommendations": report["recommendations"],
        "alternatives": report["alternatives"],
        "score_breakdown": report["score_breakdown"],
        "confidence": report["confidence"],
    }


@login_required
async def analyzer_transaction_preview_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Use POST to analyze an expense preview."}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        if not isinstance(payload, dict):
            raise ValueError("The expense details are not valid.")
        preview = await sync_to_async(_build_transaction_preview, thread_sensitive=True)(
            request.user, payload
        )
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, ValidationError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    ai_payload = {
        "analysis_type": "planned_expense_preview",
        "currency": preview["currency"],
        "amount": preview["amount"],
        "category": (payload.get("category") or "General")[:50],
        "description": (payload.get("description") or "")[:255],
        "score": preview["score"],
        "verdict": preview["verdict"],
        "deterministic_summary": preview["summary"],
        "recommendations": preview["recommendations"],
        "score_breakdown": preview["score_breakdown"],
    }
    try:
        preview["ai_insights"] = await generate_money_insights(ai_payload)
        preview["ai_enhanced"] = True
    except ExpenseAIUnavailable as exc:
        preview["ai_error"] = str(exc)
        preview["ai_enhanced"] = False
    return JsonResponse(preview)


@login_required
async def analyzer_insight_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Use POST to request an AI explanation."}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        if not isinstance(payload, dict):
            raise ValueError("The analysis request is not valid.")
        period = (payload.get("period") or "week").strip().lower()
        if period not in {"week", "month", "year"}:
            period = "week"
        focus = (payload.get("scope") or "activity").strip().lower()
        if focus not in {"activity", "transaction", "budget", "goal"}:
            focus = "activity"
        object_id = payload.get("object_id")
        context = await sync_to_async(build_workspace_context, thread_sensitive=True)(
            request.user, period=period, focus=focus, object_id=object_id
        )
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, ValidationError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    try:
        insights = await generate_money_insights(context["ai_payload"])
    except ExpenseAIUnavailable as exc:
        return JsonResponse({"error": str(exc), "ai_enhanced": False}, status=503)
    return JsonResponse({"insights": insights, "ai_enhanced": True})
