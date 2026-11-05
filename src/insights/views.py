from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from core.money_intelligence import build_money_snapshot
from finance.models import Transaction
from goals.models import Goal


@login_required
def insights_view(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    qs = Transaction.objects.filter(owner=request.user, transaction_date__gte=month_start, transaction_date__lte=today)
    income = qs.filter(kind__in=["income", "refund", "transfer_in"]).aggregate(value=Sum("amount"))["value"] or Decimal("0")
    expenses = qs.filter(kind__in=["expense", "transfer_out"]).aggregate(value=Sum("amount"))["value"] or Decimal("0")
    category_rows = list(qs.filter(kind="expense").values("category").annotate(value=Sum("amount")).order_by("-value")[:8])
    max_value = max((row["value"] for row in category_rows), default=Decimal("0"))
    for row in category_rows:
        row["percent"] = min(100, int(row["value"] / max_value * 100)) if max_value else 0
    week_monday = today - timedelta(days=today.weekday())
    weeks = []
    for i in reversed(range(6)):
        week_start = week_monday - timedelta(days=7 * i)
        week_end = min(week_start + timedelta(days=6), today)
        week = Transaction.objects.filter(owner=request.user, transaction_date__range=(week_start, week_end))
        in_total = week.filter(kind__in=["income", "refund", "transfer_in"]).aggregate(value=Sum("amount"))["value"] or Decimal("0")
        out_total = week.filter(kind__in=["expense", "transfer_out"]).aggregate(value=Sum("amount"))["value"] or Decimal("0")
        weeks.append({"label": week_start.strftime("%d %b"), "income": in_total, "expenses": out_total, "max": max(in_total, out_total, Decimal("1"))})
    goals = Goal.objects.filter(owner=request.user)
    snapshot = build_money_snapshot(request.user, today=today)

    return render(request, "insights/dashboard.html", {
        "currency": snapshot["currency"],
        "income_total": snapshot["money_in_total"],
        "expense_total": snapshot["expense_total"],
        "net_flow": snapshot["net_cash_flow"],
        "safe_to_spend": snapshot["safe_to_spend"],
        "upcoming_bills_total": snapshot["upcoming_bills_total"],
        "financial_runway_days": snapshot["financial_runway_days"],
        "next_expected_income": snapshot["next_expected_income"],
        "next_income_label": snapshot["next_income_label"],
        "weekly_budget_remaining": snapshot["weekly_budget_remaining"],
        "budget_usage_percent": snapshot["budget_usage_percent"],
        "category_rows": category_rows,
        "weeks": weeks,
        "goal_count": snapshot["active_goal_count"],
        "goal_savings_total": snapshot["goal_savings_total"],
        "goal_total_count": goals.count(),
    })