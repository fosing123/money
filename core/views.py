from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from budgets.models import Budget
from finance.models import Account, Transaction
from goals.models import Goal


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
    budgets = Budget.objects.filter(owner=user)[:4]
    goals = Goal.objects.filter(owner=user, status="active")[:4]
    goal_savings_total = Goal.objects.filter(owner=user).aggregate(total=Sum("current_amount"))["total"] or Decimal("0.00")
    budget_amount = sum((item.amount for item in budgets), Decimal("0.00"))
    budget_spent = sum((item.spent_amount for item in budgets), Decimal("0.00"))
    budget_usage_percent = min(100, float(budget_spent / budget_amount * 100)) if budget_amount > 0 else 0
    categories = list(month_transactions.filter(kind="expense").values("category").annotate(amount=Sum("amount")).order_by("-amount")[:4])
    category_total = sum((item["amount"] or Decimal("0.00") for item in categories), Decimal("0.00"))
    percentages = [int(item["amount"] / category_total * 100) if category_total else 0 for item in categories]
    category_one_percent = percentages[0] if len(percentages) > 0 else 0
    category_two_end = category_one_percent + (percentages[1] if len(percentages) > 1 else 0)
    category_three_end = category_two_end + (percentages[2] if len(percentages) > 2 else 0)
    if expense_total > income_total and expense_total:
        coach_tip = "Your expenses are a little higher than your income this month. That can happen. Let's look at one flexible category and choose one change that feels manageable—no need to overhaul everything."
    elif budgets and any(item.percent_used >= 85 for item in budgets):
        coach_tip = "One of your budgets is getting close to its limit. That's a helpful heads-up, not a failure. Check what's still coming this week and decide what matters most."
    elif user.weekly_savings_target and user.weekly_income and user.weekly_savings_target > user.weekly_income * Decimal("0.30"):
        coach_tip = "Your savings target is ambitious compared with your usual weekly income. A smaller target you can keep up with is often kinder—and more useful—than a perfect number."
    elif recent_transactions:
        coach_tip = "You're building a clearer picture of your money. Take a quick look at your last few entries and notice one thing you want to repeat next week."
    else:
        coach_tip = "Start with one honest entry: money in, money out, or a goal you care about. You don't need a perfect spreadsheet to make a good next decision."
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