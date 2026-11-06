import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from asgiref.sync import sync_to_async
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.db import transaction as db_transaction

from finance.models import Transaction
from .ai import ExpenseAIUnavailable, generate_money_insights
from .models import AIPersonalization, ExpenseAnalysis
from .scoring import analyze_planned_purchase
from .workspace import build_workspace_context


VOICE_STYLES = dict(AIPersonalization.VOICE_STYLES)
AMBITIONS = dict(AIPersonalization.AMBITIONS)
STAGES = dict(AIPersonalization.STAGES)


def _profile_for(user):
    return AIPersonalization.objects.filter(user=user, setup_completed=True).first()


def _persona_payload(profile):
    if profile is None:
        return {}
    return {
        "voice_style": profile.voice_style,
        "ambition": profile.ambition,
        "current_stage": profile.current_stage,
        "ambition_label": profile.get_ambition_display() if profile.ambition else "",
        "current_stage_label": profile.get_current_stage_display() if profile.current_stage else "",
        "future_vision": profile.future_vision,
        "desired_career": profile.desired_career,
        "why_it_matters": profile.why_it_matters,
    }


def _save_personalization(user, payload):
    if not isinstance(payload, dict):
        raise ValueError("Please complete the personalisation form.")

    voice_style = str(payload.get("voice_style") or "friendly").strip()
    ambition = str(payload.get("ambition") or "").strip()
    current_stage = str(payload.get("current_stage") or "").strip()
    if voice_style not in VOICE_STYLES:
        raise ValueError("Choose how you would like TIANA to speak with you.")
    if ambition and ambition not in AMBITIONS:
        raise ValueError("Choose a valid future ambition.")
    if current_stage and current_stage not in STAGES:
        raise ValueError("Choose a valid current stage.")

    values = {
        "voice_style": voice_style,
        "ambition": ambition,
        "current_stage": current_stage,
        "future_vision": str(payload.get("future_vision") or "").strip()[:240],
        "desired_career": str(payload.get("desired_career") or "").strip()[:120],
        "why_it_matters": str(payload.get("why_it_matters") or "").strip()[:180],
        "setup_completed": True,
    }
    profile, _ = AIPersonalization.objects.update_or_create(user=user, defaults=values)
    return _persona_payload(profile)


def _metric(label, value, hint="", tone="neutral"):
    return {"label": label, "value": str(value), "hint": hint, "tone": tone}


def _modal_result(context):
    focus = context["focus"]
    activity = context["activity"]
    budgets = context["budgets"]
    goals = context["goals"]
    currency = activity["currency"]
    result = {
        "scope": focus,
        "currency": currency,
        "period": activity["period"],
        "period_label": activity["period_label"],
        "metrics": [],
        "categories": [],
        "rows": [],
        "breakdown": [],
        "notes": [],
        "score": None,
        "verdict": "",
        "confidence": "",
    }

    if focus in {"activity", "transaction"}:
        result["title"] = (
            context["transaction_analysis"]["description"]
            if focus == "transaction" else f"{activity['period_label']} money review"
        )
        result["subtitle"] = (
            f"One recorded expense · {activity['period_label'].lower()}"
            if focus == "transaction" else
            f"{activity['start_date']:%d %b} – {activity['end_date']:%d %b %Y}"
        )
        result["metrics"] = [
            _metric("Money in", f"{activity['income']:,.0f} {currency}", f"{activity['income_count']} entries", "positive"),
            _metric("Money out", f"{activity['expenses']:,.0f} {currency}", f"{activity['expense_count']} expenses", "attention"),
            _metric("Net flow", f"{activity['net']:+,.0f} {currency}", "Income minus expenses", "positive" if activity["net"] >= 0 else "negative"),
        ]
        result["categories"] = [
            {
                "name": item["name"], "value": f"{item['total']:,.0f} {currency}",
                "percent": item["share"], "hint": f"{item['transactions']} transaction(s)",
            }
            for item in activity["categories"]
        ]
        result["rows"] = [
            {
                "title": item["description"], "subtitle": f"{item['category']} · {item['transaction_date']:%d %b}",
                "value": f"{item['amount']:,.0f} {currency}", "percent": 0, "kind": "expense",
            }
            for item in activity["largest_expenses"]
        ]
        if activity["expense_change_percent"] is not None:
            direction = "more" if activity["expense_change_percent"] > 0 else "less"
            result["notes"].append(
                f"You spent {abs(activity['expense_change_percent']):.1f}% {direction} than in the previous period."
                if activity["expense_change_percent"] else
                "Your spending is level with the previous period."
            )
        else:
            result["notes"].append("There is not enough previous activity for a fair comparison yet.")

        if focus == "transaction" and context["transaction_analysis"]:
            item = context["transaction_analysis"]
            result["title"] = item["description"]
            result["subtitle"] = f"Expense review · {item['amount']:,.0f} {currency}"
            result["score"] = item["score"]
            result["verdict"] = dict(ExpenseAnalysis.VERDICTS).get(item["verdict"], "Review")
            result["confidence"] = item["confidence"].title()
            result["summary"] = item["summary"]
            result["breakdown"] = [
                {
                    "label": detail["label"], "points": detail["points"],
                    "maximum": detail["maximum"], "percent": detail["percentage"],
                }
                for detail in item["score_breakdown"].values()
            ]
            result["metrics"] = [
                _metric("Expense amount", f"{item['amount']:,.0f} {currency}", "Recorded transaction", "attention"),
                _metric("Financial score", f"{item['score']}/100", result["verdict"], "positive" if item["score"] >= 75 else "attention"),
                _metric("Confidence", result["confidence"], "Based on available records", "neutral"),
            ]
            result["notes"] = item["reasoning"]
            result["deterministic_recommendations"] = item["recommendations"]
            result["alternatives"] = item["alternatives"]

    elif focus in {"budgets", "budget"}:
        selected = context["selected_budget"]
        items = [selected] if selected else budgets["items"]
        total_limit = sum((item["amount"] for item in items), Decimal("0"))
        total_spent = sum((item["spent"] for item in items), Decimal("0"))
        remaining = total_limit - total_spent
        result["title"] = selected["name"] if selected else "Your budget health"
        result["subtitle"] = selected["period_label"] if selected else f"{len(items)} budget plan(s) · {currency}"
        result["metrics"] = [
            _metric("Planned limits", f"{total_limit:,.0f} {currency}", f"{len(items)} budget(s)", "neutral"),
            _metric("Already spent", f"{total_spent:,.0f} {currency}", "Recorded expenses", "attention"),
            _metric("Still available", f"{remaining:,.0f} {currency}", "Across these limits", "positive" if remaining >= 0 else "negative"),
        ]
        result["rows"] = [
            {
                "title": item["name"], "subtitle": f"{item['category']} · {item['period_label']}",
                "value": f"{item['spent']:,.0f} / {item['amount']:,.0f} {currency}",
                "percent": min(100, max(0, item["percent_used"])),
                "hint": item["advice"], "kind": "budget",
                "status": "over" if item["is_over"] else "near" if item["is_near"] else "healthy",
            }
            for item in items
        ]
        if budgets["over_limit_count"]:
            result["notes"].append(
                f"{budgets['over_limit_count']} budget(s) have passed their recorded limit. Give essentials room first."
            )
        elif items:
            result["notes"].append("Your recorded spending is still within the combined budget limits.")
        else:
            result["notes"].append("You have not created a budget in this currency yet.")

    elif focus in {"goals", "goal"}:
        selected = context["selected_goal"]
        items = [selected] if selected else goals["items"]
        total_saved = sum((item["saved"] for item in items), Decimal("0"))
        total_remaining = sum((item["remaining"] for item in items), Decimal("0"))
        result["title"] = selected["name"] if selected else "Your goals roadmap"
        result["subtitle"] = f"{len(items)} savings goal(s) · {currency}"
        result["metrics"] = [
            _metric("Already saved", f"{total_saved:,.0f} {currency}", "Across selected goals", "positive"),
            _metric("Still to go", f"{total_remaining:,.0f} {currency}", "Remaining target amount", "neutral"),
            _metric("Active goals", str(sum(1 for item in items if item["status"] == "active")), "Goals you are building", "positive"),
        ]
        result["rows"] = [
            {
                "title": item["name"],
                "subtitle": f"Target · {item['target_date']:%d %b %Y}" if item["target_date"] else "No target date set",
                "value": f"{item['saved']:,.0f} / {item['target']:,.0f} {currency}",
                "percent": item["progress"], "hint": item["advice"], "kind": "goal",
            }
            for item in items
        ]
        if not items:
            result["notes"].append("You have not set a savings goal yet. Start with one goal that matters to your future.")
        elif any(item["days_left"] is not None and item["days_left"] < 0 and item["remaining"] > 0 for item in items):
            result["notes"].append("One or more target dates have passed. Reset the dates rather than putting unnecessary pressure on yourself.")
        else:
            result["notes"].append("Small, steady contributions can move these goals forward without putting essentials at risk.")

    return result


def _fallback_insights(result, persona):
    """Build a useful, data-led review when Gemini is temporarily unavailable."""
    persona = persona or {}
    scope = result.get("scope", "activity")
    metrics = {item.get("label"): item.get("value") for item in result.get("metrics", [])}
    period = (result.get("period_label") or "this period").lower()
    categories = result.get("categories") or []
    rows = result.get("rows") or []
    observations = list(result.get("notes") or [])
    recommendations = list(result.get("deterministic_recommendations") or [])
    goal_suggestions = []

    if scope == "preview":
        amount = metrics.get("Planned amount", "the amount you entered")
        summary = (
            f"You're considering {result.get('title') or 'this expense'} at {amount}. "
            "I checked it against the financial position and commitments available in your saved records. "
            "Use the score and next steps below to decide whether now is the right moment."
        )
        if not recommendations:
            recommendations = ["Protect money for essentials and planned savings before deciding on optional spending."]
    elif scope == "transaction":
        summary = result.get("summary") or (
            f"I reviewed {result.get('title') or 'this expense'} using the records available around it. "
            "The score below reflects the current budget and savings context, not a judgement about you."
        )
        if not observations:
            observations = ["This review is focused on one recorded expense rather than your entire period."]
    elif scope in {"budgets", "budget"}:
        summary = (
            f"Across your budgets, you've planned {metrics.get('Planned limits', 'an amount')} "
            f"and recorded {metrics.get('Already spent', 'some spending')}. "
            f"That leaves {metrics.get('Still available', 'the balance shown below')} against those limits."
        )
        most_used = max(rows, key=lambda item: float(item.get("percent") or 0), default=None)
        if most_used:
            observations.insert(0, f"{most_used['title']} is currently the tightest budget at {round(float(most_used.get('percent') or 0))}% used.")
            if not recommendations:
                recommendations.append(
                    f"Review the next planned {most_used['title'].lower()} expense before spending more in this category."
                )
        if not recommendations:
            recommendations.append("Keep a little room for unexpected essentials instead of assigning every remaining franc.")
    elif scope in {"goals", "goal"}:
        summary = (
            f"You've put {metrics.get('Already saved', 'money')} towards your goals, "
            f"with {metrics.get('Still to go', 'more to save')} remaining. "
            "The progress bars show which milestones are closest and which may need a little more time."
        )
        closest = max(rows, key=lambda item: float(item.get("percent") or 0), default=None)
        if closest:
            observations.insert(0, f"{closest['title']} is your furthest-along goal at {round(float(closest.get('percent') or 0))}% of its target.")
        if not recommendations:
            recommendations.append("Choose a contribution that leaves food, transport, school and other essentials covered.")
        if not rows and persona.get("ambition_label"):
            goal_suggestions.append(
                f"Consider one small milestone that supports your {persona['ambition_label'].lower()} ambition."
            )
    else:
        summary = (
            f"For {period}, your records show {metrics.get('Money in', 'no recorded income')} coming in "
            f"and {metrics.get('Money out', 'no recorded expenses')} going out. "
            f"Your recorded net flow is {metrics.get('Net flow', 'shown in the figures below')}."
        )
        if categories:
            top = categories[0]
            summary += f" {top['name']} is the largest spending category at {top['value']}."
            observations.insert(0, f"{top['name']} represents {top.get('percent', 0)}% of recorded spending in this period.")
            if not recommendations:
                recommendations.append(f"Keep an eye on the next {top['name'].lower()} expense and compare it with the rest of this period.")
        if rows:
            largest = rows[0]
            observations.append(f"The largest individual expense in this review is {largest['title']} at {largest['value']}.")
        if not recommendations:
            recommendations.append("Keep recording transactions so your next review can identify changes more confidently.")
        if not categories:
            observations.append("There is not enough category-level activity in this period to identify a leading spending area.")

    vision = persona.get("future_vision") or ""
    ambition = persona.get("ambition_label") or ""
    career = persona.get("desired_career") or ""
    if vision and len(recommendations) < 4:
        recommendations.append(f"Keep your long-term plan in view: {vision[:110]}")
    elif career and len(recommendations) < 4:
        recommendations.append(f"Let your money choices support the career you're building in {career[:80]}.")
    if ambition and not goal_suggestions and scope in {"activity", "budgets", "budget"}:
        goal_suggestions.append(f"A realistic next milestone connected to your goal of {ambition.lower()}.")

    encouragement = (
        f"You're working towards {vision[:100]}. You don't have to solve everything today; one thoughtful next step counts."
        if vision else
        "You don't have to get everything perfect today. One thoughtful next step is enough to keep moving."
    )
    return {
        "summary": summary,
        "observations": observations[:4],
        "reasoning": observations[:4],
        "recommendations": recommendations[:4],
        "alternatives": result.get("alternatives") or [],
        "goal_suggestions": goal_suggestions[:3],
        "encouragement": encouragement,
    }

@login_required
@require_GET
def analyzer_view(request):
    """Analysis centre: choose what to understand without leaving this page again."""
    period = request.GET.get("period", "week").strip().lower()
    if period not in {"day", "week", "month", "year", "custom"}:
        period = "week"
    today = __import__("django.utils.timezone", fromlist=["localdate"]).localdate()
    selected_start_date = selected_end_date = None
    if period == "custom":
        try:
            selected_start_date = date.fromisoformat(request.GET.get("start_date", ""))
            selected_end_date = date.fromisoformat(request.GET.get("end_date", ""))
        except (TypeError, ValueError):
            period = "week"
            selected_start_date = selected_end_date = None
    recent_expenses = Transaction.objects.filter(
        owner=request.user,
        kind="expense",
        currency__iexact=(request.user.currency or "XAF"),
    ).order_by("-transaction_date", "-created_at")[:6]
    has_personalization = AIPersonalization.objects.filter(
        user=request.user, setup_completed=True
    ).exists()
    return render(request, "expense_analyzer/analyzer.html", {
        "period": period,
        "today": today,
        "selected_start_date": selected_start_date,
        "selected_end_date": selected_end_date,
        "recent_expenses": recent_expenses,
        "has_personalization": has_personalization,
    })


def _build_transaction_preview(user, payload):
    if (payload.get("kind") or "expense") != "expense":
        raise ValueError("TIANA can preview an expense before it is saved. Income does not need a spending check.")
    try:
        amount = Decimal(str(payload.get("amount", "")).replace(",", "").strip())
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Add the expense amount first, then ask TIANA to look at it.") from exc
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Enter an amount greater than zero.")

    return analyze_planned_purchase(
        user,
        amount=amount,
        category=(payload.get("category") or "General").strip(),
        description=(payload.get("description") or "").strip(),
        is_essential=str(payload.get("is_essential", "")).lower() in {"1", "true", "yes", "on"},
        persist=False,
    )


def _personalization_required(user):
    return AIPersonalization.objects.filter(user=user, setup_completed=True).exists()


@login_required
async def analyzer_personalization_view(request):
    if request.method == "GET":
        profile = await sync_to_async(_profile_for, thread_sensitive=True)(request.user)
        return JsonResponse({"persona": _persona_payload(profile) if profile else None})
    if request.method != "POST":
        return JsonResponse({"error": "Use POST to save your preferences."}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        persona = await sync_to_async(_save_personalization, thread_sensitive=True)(request.user, payload)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, ValidationError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"saved": True, "persona": persona})


@login_required
async def analyzer_transaction_preview_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Use POST to analyze an expense preview."}, status=405)
    if not await sync_to_async(_personalization_required, thread_sensitive=True)(request.user):
        return JsonResponse({"personalization_required": True}, status=409)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        if not isinstance(payload, dict):
            raise ValueError("The expense details are not valid.")
        report = await sync_to_async(_build_transaction_preview, thread_sensitive=True)(
            request.user, payload
        )
        persona = await sync_to_async(_profile_for, thread_sensitive=True)(request.user)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, ValidationError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    result = {
        "scope": "preview",
        "title": (payload.get("description") or payload.get("category") or "Planned expense")[:100],
        "subtitle": "Before you save · read-only preview",
        "currency": report["currency"],
        "score": report["score"],
        "verdict": dict(ExpenseAnalysis.VERDICTS).get(report["verdict"], "Review"),
        "confidence": str(report["confidence"]).title(),
        "summary": report["summary"],
        "metrics": [
            _metric("Planned amount", f"{report['amount']:,.0f} {report['currency']}", payload.get("category") or "General", "attention"),
            _metric("Financial score", f"{report['score']}/100", dict(ExpenseAnalysis.VERDICTS).get(report["verdict"], "Review"), "positive" if report["score"] >= 75 else "attention"),
        ],
        "breakdown": [
            {"label": item["label"], "points": item["points"], "maximum": item["maximum"], "percent": item["percentage"]}
            for item in report["score_breakdown"].values()
        ],
        "categories": [],
        "rows": [],
        "notes": report["reasoning"],
        "deterministic_recommendations": report["recommendations"],
        "alternatives": report["alternatives"],
    }
    ai_payload = {
        "analysis_type": "planned_expense_preview",
        "currency": report["currency"],
        "amount": str(report["amount"]),
        "category": (payload.get("category") or "General")[:50],
        "description": (payload.get("description") or "")[:255],
        "score": report["score"],
        "verdict": result["verdict"],
        "safe_to_spend": report["financial_impact"].get("safe_to_spend_before"),
        "deterministic_summary": report["summary"],
        "recommendations": report["recommendations"],
        "score_breakdown": report["score_breakdown"],
        "future_vision": persona.future_vision,
    }
    try:
        insights = await generate_money_insights(ai_payload, _persona_payload(persona))
        ai_enhanced = True
        ai_error = ""
    except ExpenseAIUnavailable as exc:
        insights = _fallback_insights(result, _persona_payload(persona))
        ai_enhanced = False
        ai_error = str(exc)
    return JsonResponse({
        "result": result,
        "insights": insights,
        "ai_enhanced": ai_enhanced,
        "ai_error": ai_error,
    })


@login_required
async def analyzer_insight_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Use POST to request an analysis."}, status=405)
    if not await sync_to_async(_personalization_required, thread_sensitive=True)(request.user):
        return JsonResponse({"personalization_required": True}, status=409)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        if not isinstance(payload, dict):
            raise ValueError("The analysis request is not valid.")
        period = (payload.get("period") or "week").strip().lower()
        if period not in {"day", "week", "month", "year", "custom"}:
            period = "week"
        start_date = end_date = None
        if period == "custom":
            try:
                start_date = date.fromisoformat(str(payload.get("start_date") or ""))
                end_date = date.fromisoformat(str(payload.get("end_date") or ""))
            except (TypeError, ValueError) as exc:
                raise ValueError("Choose a valid start date and end date.") from exc
        focus = (payload.get("scope") or "activity").strip().lower()
        if focus not in {"activity", "transaction", "budget", "budgets", "goal", "goals"}:
            focus = "activity"
        object_id = payload.get("object_id")
        context = await sync_to_async(build_workspace_context, thread_sensitive=True)(
            request.user, period=period, focus=focus, object_id=object_id,
            start_date=start_date, end_date=end_date,
        )
        persona = await sync_to_async(_profile_for, thread_sensitive=True)(request.user)
        result = await sync_to_async(_modal_result, thread_sensitive=True)(context)
        ai_payload = context["ai_payload"]
        ai_payload["selected_view"] = {
            "title": result["title"],
            "subtitle": result["subtitle"],
            "metrics": result["metrics"],
            "score": result["score"],
            "verdict": result["verdict"],
        }
        ai_payload["future_vision"] = persona.future_vision
        ai_payload["desired_career"] = persona.desired_career
        ai_payload["ambition"] = persona.get_ambition_display() if persona.ambition else ""
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, ValidationError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    try:
        insights = await generate_money_insights(ai_payload, _persona_payload(persona))
        ai_enhanced = True
        ai_error = ""
    except ExpenseAIUnavailable as exc:
        insights = _fallback_insights(result, _persona_payload(persona))
        ai_enhanced = False
        ai_error = str(exc)

    return JsonResponse({
        "result": result,
        "insights": insights,
        "ai_enhanced": ai_enhanced,
        "ai_error": ai_error,
    })
