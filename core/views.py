from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from budgets.models import Budget
from finance.models import Account, Transaction
from goals.models import Goal
from notifications.services import evaluate_spending_alerts


def home_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard" if request.user.onboarding_completed else "onboarding_setup")
    return render(request, "core/landing.html")


@login_required
def dashboard_view(request):
    user = request.user
    if not user.onboarding_completed:
        return redirect("onboarding_setup")
    today = timezone.localdate()
    month_start = today.replace(day=1)
    accounts = Account.objects.filter(owner=user, is_active=True)
    total_balance = accounts.aggregate(total=Sum("balance"))["total"] or Decimal("0.00")
    month_transactions = Transaction.objects.filter(owner=user, transaction_date__gte=month_start, transaction_date__lte=today)
    income_total = month_transactions.filter(kind__in=["income", "refund", "transfer_in"]).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    expense_total = month_transactions.filter(kind__in=["expense", "transfer_out"]).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    recent_transactions = Transaction.objects.filter(owner=user).select_related("account")[:6]
    evaluate_spending_alerts(user)
    budgets = Budget.objects.filter(owner=user)[:4]
    goals = Goal.objects.filter(owner=user, status="active").prefetch_related("contributions__transaction")[:4]
    all_goals = Goal.objects.filter(owner=user).prefetch_related("contributions__transaction")
    goal_savings_total = sum((goal.saved_amount for goal in all_goals), Decimal("0.00"))
    budget_amount = sum((item.amount for item in budgets), Decimal("0.00"))
    budget_spent = sum((item.spent_amount for item in budgets), Decimal("0.00"))
    budget_usage_percent = min(100, float(budget_spent / budget_amount * 100)) if budget_amount > 0 else 0
    categories = list(month_transactions.filter(kind="expense").values("category").annotate(amount=Sum("amount")).order_by("-amount")[:4])
    category_total = sum((item["amount"] or Decimal("0.00") for item in categories), Decimal("0.00"))
    percentages = [int(item["amount"] / category_total * 100) if category_total else 0 for item in categories]
    category_one_percent = percentages[0] if len(percentages) > 0 else 0
    category_two_end = category_one_percent + (percentages[1] if len(percentages) > 1 else 0)
    category_three_end = category_two_end + (percentages[2] if len(percentages) > 2 else 0)
    coach_tip = (
        "Get guidance shaped around your savings goals, weekly plan and recent activity. "
        "Ask TIANA for a practical next step or help deciding what to prioritise."
    )
    return render(request, "core/dashboard.html", {
        "accounts": accounts,
        "total_balance": total_balance,
        "income_total": income_total,
        "expense_total": expense_total,
        "net_cash_flow": income_total - expense_total,
        "recent_transactions": recent_transactions,
        "budgets": budgets,
        "goals": goals,
        "goal_savings_total": goal_savings_total,
        "budget_usage_percent": budget_usage_percent,
        "expense_categories": categories,
        "category_one_percent": category_one_percent,
        "category_two_end": category_two_end,
        "category_three_end": category_three_end,
        "coach_tip": coach_tip,
    })


def health_check_view(request):
    return JsonResponse({"status": "ok", "service": "tiana"})