"""Transparent money intelligence calculations for the signed-in member.

All money totals are scoped to one currency. Transfers are balance movements,
not income or spending. Safe-to-spend excludes savings accounts and protects
the unfulfilled portion of the member's weekly savings target.
"""
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from django.utils import timezone

from budgets.models import Budget
from budgets.services import attach_budget_spending
from finance.models import Account, Transaction
from goals.models import Goal


ZERO = Decimal("0.00")


def _money(value):
    return Decimal(str(value or ZERO))


def _previous_month_to_date(today):
    previous_month_last_day = today.replace(day=1) - timedelta(days=1)
    previous_month_start = previous_month_last_day.replace(day=1)
    previous_month_day = min(today.day, monthrange(
        previous_month_start.year, previous_month_start.month
    )[1])
    return previous_month_start, previous_month_start.replace(day=previous_month_day)


def build_money_snapshot(user, today=None):
    """Return a currency-safe, explainable snapshot for the dashboard."""
    today = today or timezone.localdate()
    currency = (user.currency or "XAF").strip().upper() or "XAF"
    week_start = today - timedelta(days=today.weekday())
    days_remaining_in_week = 7 - today.weekday()

    all_accounts = list(
        Account.objects.filter(owner=user, is_active=True).order_by("name")
    )
    accounts = [account for account in all_accounts if account.currency.upper() == currency]
    spendable_accounts = [
        account for account in accounts if account.account_type != "savings"
    ]
    total_balance = sum((_money(account.balance) for account in accounts), ZERO)
    spendable_balance = sum(
        (_money(account.balance) for account in spendable_accounts), ZERO
    )

    # A goal top-up is already deducted from the source account balance.
    # Subtract only the part of this week's savings target not yet transferred.
    savings_target = max(_money(user.weekly_savings_target), ZERO)
    savings_funded = Transaction.objects.filter(
        owner=user,
        currency=currency,
        kind="transfer_out",
        category__iexact="savings",
        transaction_date__range=(week_start, today),
    ).aggregate(total=Sum("amount"))["total"] or ZERO
    savings_remaining = max(savings_target - _money(savings_funded), ZERO)

    unadjusted_safe_to_spend = spendable_balance - savings_remaining
    safe_to_spend_shortfall = max(-unadjusted_safe_to_spend, ZERO)
    safe_to_spend = max(unadjusted_safe_to_spend, ZERO)
    daily_safe_to_spend = (
        safe_to_spend / Decimal(days_remaining_in_week)
        if days_remaining_in_week else safe_to_spend
    )

    month_start = today.replace(day=1)
    month_transactions = Transaction.objects.filter(
        owner=user,
        currency=currency,
        transaction_date__range=(month_start, today),
    )
    month_totals = month_transactions.aggregate(
        income=Sum("amount", filter=Q(kind="income")),
        refunds=Sum("amount", filter=Q(kind="refund")),
        expenses=Sum("amount", filter=Q(kind="expense")),
    )
    income_total = _money(month_totals["income"])
    refund_total = _money(month_totals["refunds"])
    expense_total = _money(month_totals["expenses"])

    previous_start, previous_end = _previous_month_to_date(today)
    previous_expense_total = Transaction.objects.filter(
        owner=user,
        currency=currency,
        kind="expense",
        transaction_date__range=(previous_start, previous_end),
    ).aggregate(total=Sum("amount"))["total"] or ZERO
    previous_expense_total = _money(previous_expense_total)
    if previous_expense_total > ZERO:
        expense_change_percent = int(
            ((expense_total - previous_expense_total) / previous_expense_total) * 100
        )
    elif expense_total > ZERO:
        expense_change_percent = None
    else:
        expense_change_percent = 0

    categories = list(
        month_transactions.filter(kind="expense")
        .values("category")
        .annotate(amount=Sum("amount"))
        .order_by("-amount", "category")[:4]
    )
    category_total = sum((_money(item["amount"]) for item in categories), ZERO)
    percentages = [
        int((_money(item["amount"]) / category_total) * 100)
        if category_total > ZERO else 0
        for item in categories
    ]
    for item, percentage in zip(categories, percentages):
        item["percent"] = percentage
    category_one_percent = percentages[0] if len(percentages) > 0 else 0
    category_two_end = category_one_percent + (percentages[1] if len(percentages) > 1 else 0)
    category_three_end = category_two_end + (percentages[2] if len(percentages) > 2 else 0)

    weekly_budgets = list(
        Budget.objects.filter(
            owner=user, currency=currency, period="weekly"
        ).order_by("name")
    )
    attach_budget_spending(weekly_budgets, owner=user)
    weekly_budget_total = sum((_money(item.amount) for item in weekly_budgets), ZERO)
    weekly_budget_spent = sum((_money(item.spent_amount) for item in weekly_budgets), ZERO)
    weekly_budget_remaining = sum(
        (max(_money(item.remaining_amount), ZERO) for item in weekly_budgets), ZERO
    )
    budget_usage_percent = (
        min(100, float(weekly_budget_spent / weekly_budget_total * 100))
        if weekly_budget_total > ZERO else 0
    )
    budget_attention = next(
        (item for item in sorted(
            weekly_budgets, key=lambda budget: budget.percent_used, reverse=True
        ) if item.percent_used >= 80),
        None,
    )

    goals = list(
        Goal.objects.filter(owner=user, currency=currency, status="active")
        .prefetch_related("contributions__transaction")
        .order_by("target_date", "-created_at")[:4]
    )
    all_goals = list(
        Goal.objects.filter(owner=user, currency=currency)
        .prefetch_related("contributions__transaction")
    )
    goal_savings_total = sum((_money(goal.saved_amount) for goal in all_goals), ZERO)

    recent_transactions = list(
        Transaction.objects.filter(owner=user, currency=currency)
        .select_related("account")[:6]
    )

    if not accounts:
        coach_tip = "Add your cash or mobile-money account first. TIANA will then calculate what is available without guessing."
    elif safe_to_spend_shortfall > ZERO:
        coach_tip = (
            f"Your current spendable accounts are {safe_to_spend_shortfall:,.0f} {currency} "
            "below the savings amount you planned to protect this week. Pause optional "
            "spending or adjust your plan before setting money aside."
        )
    elif budget_attention and budget_attention.percent_used >= 100:
        coach_tip = (
            f"Your {budget_attention.name} plan has reached its limit for this week. "
            "Review the remaining days before making more purchases in this category."
        )
    elif budget_attention:
        coach_tip = (
            f"You have used {budget_attention.percent_used:.0f}% of your "
            f"{budget_attention.name} plan. Check the pace before the week ends."
        )
    elif expense_change_percent is not None and expense_change_percent > 10:
        top_category = categories[0]["category"] if categories else "your expenses"
        coach_tip = (
            f"Recorded spending is {expense_change_percent}% higher than the same "
            f"point last month. {top_category} is your largest expense category so far."
        )
    elif savings_remaining > ZERO:
        coach_tip = (
            f"You still have {savings_remaining:,.0f} {currency} to set aside toward "
            "this week's savings target. Your safe-to-spend figure already protects it."
        )
    else:
        coach_tip = (
            "Your weekly savings target is covered. Keep recording purchases as they "
            "happen so your budget and safe-to-spend figure stay useful."
        )

    return {
        "currency": currency,
        "today": today,
        "week_start": week_start,
        "days_remaining_in_week": days_remaining_in_week,
        "accounts": accounts,
        "account_count": len(accounts),
        "other_currency_account_count": len(all_accounts) - len(accounts),
        "total_balance": total_balance,
        "spendable_balance": spendable_balance,
        "safe_to_spend": safe_to_spend,
        "safe_to_spend_shortfall": safe_to_spend_shortfall,
        "daily_safe_to_spend": daily_safe_to_spend,
        "weekly_savings_target": savings_target,
        "weekly_savings_funded": _money(savings_funded),
        "weekly_savings_remaining": savings_remaining,
        "income_total": income_total,
        "refund_total": refund_total,
        "expense_total": expense_total,
        "net_cash_flow": income_total + refund_total - expense_total,
        "previous_expense_total": previous_expense_total,
        "expense_change_percent": expense_change_percent,
        "recent_transactions": recent_transactions,
        "weekly_budgets": weekly_budgets,
        "weekly_budget_total": weekly_budget_total,
        "weekly_budget_spent": weekly_budget_spent,
        "weekly_budget_remaining": weekly_budget_remaining,
        "budget_usage_percent": budget_usage_percent,
        "budget_attention": budget_attention,
        "goals": goals,
        "goal_savings_total": goal_savings_total,
        "active_goal_count": len(goals),
        "expense_categories": categories,
        "category_one_percent": category_one_percent,
        "category_two_end": category_two_end,
        "category_three_end": category_three_end,
        "coach_tip": coach_tip,
    }
