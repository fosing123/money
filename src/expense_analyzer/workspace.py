"""Read-only financial analysis workspace for TIANA."""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.http import Http404
from django.utils import timezone

from budgets.models import Budget
from finance.models import Transaction
from goals.models import Goal

from .scoring import analyze_completed_expense


ZERO = Decimal("0.00")
PERIOD_LABELS = {
    "day": "Today",
    "week": "This week",
    "month": "This month",
    "year": "This year",
    "custom": "Selected period",
}


def _period_bounds(period, today, start_date=None, end_date=None):
    if period == "day":
        start = end = today
    elif period == "week":
        start, end = today - timedelta(days=today.weekday()), today
    elif period == "month":
        start, end = today.replace(day=1), today
    elif period == "year":
        start, end = today.replace(month=1, day=1), today
    elif period == "custom":
        if not isinstance(start_date, date) or not isinstance(end_date, date):
            raise ValueError("Choose both a start date and an end date for your custom analysis.")
        if start_date > end_date:
            raise ValueError("The start date must be on or before the end date.")
        if end_date > today:
            raise ValueError("Choose an end date that is today or earlier.")
        if (end_date - start_date).days > 365:
            raise ValueError("A custom analysis can cover up to one year at a time.")
        start, end = start_date, end_date
    else:
        raise ValueError("Choose a valid analysis period.")
    return period, start, end


def _cash_flow(queryset):
    values = queryset.aggregate(
        expenses=Sum("amount", filter=Q(kind="expense")),
        income=Sum("amount", filter=Q(kind__in=["income", "refund"])),
        expense_count=Count("id", filter=Q(kind="expense")),
        income_count=Count("id", filter=Q(kind__in=["income", "refund"])),
    )
    expenses = values["expenses"] or ZERO
    income = values["income"] or ZERO
    return {
        "expenses": expenses, "income": income, "net": income - expenses,
        "expense_count": values["expense_count"] or 0,
        "income_count": values["income_count"] or 0,
    }


def _activity_analysis(user, period, today, start_date=None, end_date=None):
    period, start, end = _period_bounds(period, today, start_date, end_date)
    currency = (user.currency or "XAF").upper()
    base = Transaction.objects.filter(
        owner=user, currency__iexact=currency,
        transaction_date__range=(start, end),
    ).exclude(kind__in=["transfer_in", "transfer_out"])
    current = _cash_flow(base)

    days = (end - start).days + 1
    previous_end = start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)
    previous = _cash_flow(
        Transaction.objects.filter(
            owner=user, currency__iexact=currency,
            transaction_date__range=(previous_start, previous_end),
        ).exclude(kind__in=["transfer_in", "transfer_out"])
    )

    category_rows = list(
        base.filter(kind="expense").values("category")
        .annotate(total=Sum("amount"), transactions=Count("id"))
        .order_by("-total")[:6]
    )
    categories = [
        {
            "name": (item["category"] or "General").strip() or "General",
            "total": item["total"] or ZERO,
            "transactions": item["transactions"],
            "share": round(float((item["total"] or ZERO) / current["expenses"] * 100), 1)
            if current["expenses"] else 0,
        }
        for item in category_rows
    ]
    largest = list(
        base.filter(kind="expense").order_by("-amount", "-transaction_date")[:5]
        .values("id", "description", "category", "amount", "transaction_date")
    )
    for item in largest:
        item["description"] = item["description"] or item["category"] or "Expense"
        item["category"] = item["category"] or "General"

    change = None
    if previous["expenses"] > ZERO:
        change = round(float((current["expenses"] - previous["expenses"]) / previous["expenses"] * 100), 1)
    elif current["expenses"] > ZERO:
        change = 100.0

    period_label = PERIOD_LABELS[period]
    if period == "custom":
        period_label = f"{start:%d %b} – {end:%d %b %Y}"

    return {
        "period": period, "period_label": period_label,
        "start_date": start, "end_date": end, "days": days, "currency": currency,
        "expenses": current["expenses"], "income": current["income"], "net": current["net"],
        "expense_count": current["expense_count"], "income_count": current["income_count"],
        "transaction_count": current["expense_count"] + current["income_count"],
        "previous_expenses": previous["expenses"], "previous_income": previous["income"],
        "expense_change_percent": change, "categories": categories,
        "largest_expenses": largest,
        "has_activity": current["expense_count"] + current["income_count"] > 0,
    }


def _budget_analysis(user, currency):
    budgets = Budget.objects.filter(owner=user, currency__iexact=currency).order_by("period", "name")
    output = []
    for budget in budgets:
        spent = Decimal(str(budget.spent_amount or 0))
        limit = Decimal(str(budget.amount or 0))
        remaining = limit - spent
        percent = round(float(spent / limit * 100), 1) if limit > ZERO else 0
        output.append({
            "id": budget.pk, "name": budget.name,
            "category": budget.category or "All categories",
            "period": budget.period, "period_label": budget.get_period_display(),
            "amount": limit, "spent": spent, "remaining": remaining,
            "percent_used": percent, "is_over": remaining < ZERO,
            "is_near": percent >= 80,
            "advice": (
                "This budget is over its limit. Pause optional spending in this category and review the remaining period."
                if remaining < ZERO else
                "Most of this limit has been used. Check upcoming essentials before adding more spending."
                if percent >= 80 else
                "This category still has room. Keep recording purchases to maintain an accurate picture."
            ),
        })
    total_limit = sum((item["amount"] for item in output), ZERO)
    total_spent = sum((item["spent"] for item in output), ZERO)
    return {
        "items": output, "count": len(output), "total_limit": total_limit,
        "total_spent": total_spent, "total_remaining": total_limit - total_spent,
        "over_limit_count": sum(1 for item in output if item["is_over"]),
    }


def _goal_analysis(user, currency, today):
    goals = Goal.objects.filter(owner=user, currency__iexact=currency).exclude(status="archived") \
        .prefetch_related("contributions__transaction").order_by("target_date", "name")
    output = []
    for goal in goals:
        saved = Decimal(str(goal.saved_amount or 0))
        target = Decimal(str(goal.target_amount or 0))
        remaining = max(target - saved, ZERO)
        progress = min(100, int(saved / target * 100)) if target > ZERO else 0
        days_left = (goal.target_date - today).days if goal.target_date else None
        output.append({
            "id": goal.pk, "name": goal.name, "status": goal.status,
            "target": target, "saved": saved, "remaining": remaining,
            "progress": progress, "target_date": goal.target_date, "days_left": days_left,
            "advice": (
                "This goal has reached its target. You can celebrate it or set a new milestone."
                if remaining <= ZERO else
                "The target date has passed. Adjust the date or the amount needed to make the goal realistic."
                if days_left is not None and days_left < 0 else
                "Keep contributions regular and protect money needed for your essentials first."
            ),
        })
    return {
        "items": output, "count": len(output),
        "active_count": sum(1 for item in output if item["status"] == "active"),
        "total_saved": sum((item["saved"] for item in output), ZERO),
        "total_remaining": sum((item["remaining"] for item in output), ZERO),
    }


def _transaction_assessment(user, transaction):
    report = analyze_completed_expense(user, transaction, persist=False)
    return {
        "description": report["description"] or report["category"],
        "amount": report["amount"], "currency": report["currency"],
        "score": report["score"], "verdict": report["verdict"],
        "summary": report["summary"], "reasoning": report["reasoning"],
        "recommendations": report["recommendations"],
        "alternatives": report["alternatives"],
        "score_breakdown": report["score_breakdown"],
        "confidence": report["confidence"],
    }


def build_workspace_context(user, period="week", focus="activity", object_id=None, start_date=None, end_date=None):
    """Build a private, read-only analysis payload from the member's own records."""
    today = timezone.localdate()
    activity = _activity_analysis(user, period, today, start_date=start_date, end_date=end_date)
    currency = activity["currency"]
    budgets = _budget_analysis(user, currency)
    goals = _goal_analysis(user, currency, today)

    selected_transaction = transaction_analysis = selected_budget = selected_goal = None
    try:
        selected_id = int(object_id) if object_id is not None else None
    except (TypeError, ValueError):
        raise Http404("This analysis item could not be found in your account.")

    if focus == "transaction" and selected_id:
        selected_transaction = Transaction.objects.filter(
            owner=user, pk=selected_id, kind="expense", currency__iexact=currency,
        ).select_related("account").first()
        if selected_transaction is None:
            raise Http404("This expense could not be found in your account.")
        transaction_analysis = _transaction_assessment(user, selected_transaction)
    elif focus == "budget" and selected_id:
        selected_budget = next((item for item in budgets["items"] if item["id"] == selected_id), None)
        if selected_budget is None:
            raise Http404("This budget could not be found in your account.")
    elif focus == "goal" and selected_id:
        selected_goal = next((item for item in goals["items"] if item["id"] == selected_id), None)
        if selected_goal is None:
            raise Http404("This goal could not be found in your account.")
    elif focus == "budget":
        focus = "budgets"
    elif focus == "goal":
        focus = "goals"
    elif focus not in {"activity", "budgets", "goals"}:
        focus = "activity"

    focus_labels = {
        "activity": "Activity analysis", "transaction": "Expense analysis",
        "budget": "Budget analysis", "budgets": "Budget overview",
        "goal": "Savings goal analysis", "goals": "Savings goals overview",
    }
    ai_payload = {
        "currency": currency, "focus": focus, "period": activity["period_label"],
        "date_range": {"from": activity["start_date"].isoformat(), "to": activity["end_date"].isoformat()},
        "activity": {
            "income": str(activity["income"]), "expenses": str(activity["expenses"]),
            "net": str(activity["net"]), "expense_count": activity["expense_count"],
            "previous_period_expenses": str(activity["previous_expenses"]),
            "expense_change_percent": activity["expense_change_percent"],
            "categories": [
                {"name": item["name"], "spent": str(item["total"]), "share_percent": item["share"]}
                for item in activity["categories"]
            ],
        },
        "budgets": [
            {"name": item["name"], "category": item["category"], "period": item["period"],
             "limit": str(item["amount"]), "spent": str(item["spent"]),
             "remaining": str(item["remaining"]), "used_percent": item["percent_used"]}
            for item in budgets["items"][:12]
        ],
        "goals": [
            {"name": item["name"], "target": str(item["target"]), "saved": str(item["saved"]),
             "remaining": str(item["remaining"]), "progress_percent": item["progress"],
             "target_date": item["target_date"].isoformat() if item["target_date"] else None}
            for item in goals["items"][:12]
        ],
    }
    if transaction_analysis:
        ai_payload["selected_expense"] = {
            "description": transaction_analysis["description"],
            "amount": str(transaction_analysis["amount"]), "score": transaction_analysis["score"],
            "summary": transaction_analysis["summary"], "reasoning": transaction_analysis["reasoning"],
            "recommendations": transaction_analysis["recommendations"],
        }
    if selected_budget:
        ai_payload["selected_budget"] = {
            "name": selected_budget["name"], "limit": str(selected_budget["amount"]),
            "spent": str(selected_budget["spent"]), "remaining": str(selected_budget["remaining"]),
            "used_percent": selected_budget["percent_used"], "period": selected_budget["period"],
        }
    if selected_goal:
        ai_payload["selected_goal"] = {
            "name": selected_goal["name"], "target": str(selected_goal["target"]),
            "saved": str(selected_goal["saved"]), "remaining": str(selected_goal["remaining"]),
            "progress_percent": selected_goal["progress"],
            "target_date": selected_goal["target_date"].isoformat() if selected_goal["target_date"] else None,
        }

    return {
        "activity": activity, "budgets": budgets, "goals": goals,
        "focus": focus, "focus_title": focus_labels[focus],
        "selected_transaction": selected_transaction, "transaction_analysis": transaction_analysis,
        "selected_budget": selected_budget, "selected_goal": selected_goal,
        "ai_payload": ai_payload,
    }
