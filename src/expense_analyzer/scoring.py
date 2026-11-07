"""Deterministic, currency-safe expense scoring for TIANA.

The score is calculated from Django finance records. A language model may later
explain these results, but must never invent or override the underlying values.
"""
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Avg, Count
from django.utils import timezone

from budgets.models import Budget
from core.money_intelligence import build_money_snapshot
from finance.models import Transaction

from .models import ExpenseAnalysis


ZERO = Decimal("0.00")


def _money(value):
    return Decimal(str(value or ZERO))


def _rounded_points(value):
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _verdict(score):
    if score >= 90:
        return ExpenseAnalysis.EXCELLENT
    if score >= 75:
        return ExpenseAnalysis.GOOD
    if score >= 60:
        return ExpenseAnalysis.FAIR
    if score >= 40:
        return ExpenseAnalysis.POOR
    return ExpenseAnalysis.CRITICAL


def _category_budget(user, currency, category):
    candidates = Budget.objects.filter(
        owner=user,
        currency__iexact=currency,
        period__in=["weekly", "monthly"],
    ).order_by("-period", "-created_at")
    category_key = (category or "").strip().casefold()
    for budget in candidates:
        # A named budget without a category may represent an overall limit.
        # Do not treat it as a category budget: its spent_amount covers all
        # expenses in that period and would produce a misleading category score.
        budget_key = (budget.category or "").strip().casefold()
        if budget_key and budget_key == category_key:
            return budget
    return None


def _category_history(user, currency, category, *, exclude_transaction=None, today=None):
    today = today or timezone.localdate()
    query = Transaction.objects.filter(
        owner=user,
        currency__iexact=currency,
        kind="expense",
        category__iexact=(category or "General").strip(),
        transaction_date__gte=today - timedelta(days=90),
        transaction_date__lte=today,
    )
    if exclude_transaction is not None:
        query = query.exclude(pk=exclude_transaction.pk)
    result = query.aggregate(average=Avg("amount"), count=Count("id"))
    return _money(result["average"]), int(result["count"] or 0)


def _pattern_points(amount, average, count):
    if count == 0 or average <= ZERO:
        return 7
    ratio = amount / average
    if ratio <= Decimal("1.25"):
        return 10
    if ratio <= Decimal("1.75"):
        return 7
    if ratio <= Decimal("2.5"):
        return 4
    return 1


def _breakdown(values):
    maxima = {
        "budget_fit": ("Category budget", 30),
        "savings_protection": ("Weekly savings protection", 25),
        "balance_resilience": ("Available balance", 20),
        "priority_fit": ("Essential-spending priority", 15),
        "spending_pattern": ("Spending pattern", 10),
    }
    output = {}
    for key, points in values.items():
        label, maximum = maxima[key]
        output[key] = {
            "label": label,
            "points": _rounded_points(points),
            "maximum": maximum,
            "percentage": min(100, max(0, _rounded_points(Decimal(str(points)) / maximum * 100))),
        }
    return output


def _shared_context(user, category, *, today=None, exclude_transaction=None):
    today = today or timezone.localdate()
    snapshot = build_money_snapshot(user, today=today)
    currency = snapshot["currency"]
    budget = _category_budget(user, currency, category)
    average, history_count = _category_history(
        user, currency, category,
        exclude_transaction=exclude_transaction,
        today=today,
    )
    budget_data = None
    if budget:
        budget_data = {
            "name": budget.name,
            "limit": str(budget.amount),
            "spent": str(budget.spent_amount),
            "remaining": str(budget.remaining_amount),
            "period": budget.period,
        }
    active_goals = [
        {
            "name": goal.name,
            "target_amount": str(goal.target_amount),
            "saved_amount": str(goal.saved_amount),
            "remaining_amount": str(goal.remaining_amount),
            "target_date": goal.target_date.isoformat() if goal.target_date else None,
        }
        for goal in snapshot["goals"]
    ]
    context = {
        "currency": currency,
        "account_count": snapshot["account_count"],
        "spendable_balance": str(snapshot["spendable_balance"]),
        "safe_to_spend": str(snapshot["safe_to_spend"]),
        "safe_to_spend_shortfall": str(snapshot["safe_to_spend_shortfall"]),
        "weekly_savings_remaining": str(snapshot["weekly_savings_remaining"]),
        "active_goal_count": snapshot["active_goal_count"],
        "active_goals": active_goals,
        "budget": budget_data,
        "category_average_90d": str(average),
        "category_history_count_90d": history_count,
        "safe_to_spend_basis": (
            "Active non-savings accounts in the primary currency, less the unfilled "
            "weekly savings target. Scheduled bills are not included."
        ),
    }
    return snapshot, budget, average, history_count, context


def _confidence(snapshot, budget, history_count):
    missing = 0
    if not snapshot["account_count"]:
        missing += 2
    if budget is None:
        missing += 1
    if history_count == 0:
        missing += 1
    if snapshot["active_goal_count"] == 0:
        missing += 1
    return "LOW" if missing >= 4 else "MEDIUM" if missing >= 2 else "HIGH"


def _summary_for_planned(amount, currency, score, safe_to_spend):
    if safe_to_spend <= ZERO:
        return (
            "Your current safe-to-spend amount is zero. This purchase would need "
            "to wait until more money is available or your weekly plan changes."
        )
    if amount > safe_to_spend:
        excess = amount - safe_to_spend
        return (
            f"This purchase is {excess:,.0f} {currency} above your current "
            "safe-to-spend amount. Consider reducing the cost or postponing it."
        )
    if score >= 75:
        return "This purchase fits within your current safe-to-spend amount. Check the category budget and keep your savings plan protected."
    return "The purchase may be possible, but it leaves less room for other priorities. Review the category budget before proceeding."


def _summary_for_completed(amount, currency, score, shortfall):
    if shortfall > ZERO:
        return (
            f"This expense leaves your current spendable accounts {shortfall:,.0f} "
            f"{currency} below the savings amount you planned to protect this week. "
            "Focus on the remaining budget rather than judging the purchase."
        )
    if score >= 75:
        return "This expense appears manageable against the financial information recorded in TIANA. Keep tracking the rest of the week."
    return "This expense has tightened your available room. Review the remaining category budget and protect essential spending first."


def analyze_planned_purchase(user, *, amount, category, description="", is_essential=False, purchase_date=None, persist=True):
    """Score a proposed purchase; persist=False returns a read-only preview."""
    amount = _money(amount)
    if amount <= ZERO:
        raise ValueError("Enter an amount greater than zero.")

    category = (category or "General").strip()[:50] or "General"
    today = timezone.localdate()
    snapshot, budget, average, history_count, context = _shared_context(
        user, category, today=today
    )
    currency = snapshot["currency"]
    balance = _money(snapshot["spendable_balance"])
    safe = _money(snapshot["safe_to_spend"])

    if budget is None:
        budget_points = Decimal("18")
    else:
        remaining = _money(budget.remaining_amount)
        budget_points = Decimal("30") if amount <= remaining else (
            Decimal("30") * max(remaining, ZERO) / amount
        )

    savings_points = Decimal("25") if amount <= safe else (
        Decimal("25") * safe / amount if safe > ZERO else ZERO
    )
    balance_points = (
        Decimal("20") * (Decimal("1") - (amount / balance) * Decimal("0.5"))
        if balance >= amount and balance > ZERO else ZERO
    )
    priority_points = Decimal("15") if is_essential else Decimal("10")
    pattern_points = Decimal(str(_pattern_points(amount, average, history_count)))

    breakdown = _breakdown({
        "budget_fit": budget_points,
        "savings_protection": savings_points,
        "balance_resilience": balance_points,
        "priority_fit": priority_points,
        "spending_pattern": pattern_points,
    })
    score = min(100, max(0, sum(item["points"] for item in breakdown.values())))
    verdict = _verdict(score)
    budget_remaining_after = (
        _money(budget.remaining_amount) - amount if budget else None
    )
    safe_after = safe - amount
    balance_after = balance - amount
    reasoning = [
        f"The purchase costs {amount:,.0f} {currency}.",
        f"Your recorded safe-to-spend amount is {safe:,.0f} {currency}.",
    ]
    if context["active_goals"]:
        names = ", ".join(goal["name"] for goal in context["active_goals"][:3])
        reasoning.append(
            f"Your active savings goal(s) include {names}. TIANA protects only the "
            "weekly savings amount you have configured; it does not assume an "
            "unrecorded contribution schedule for these longer-term goals."
        )
    reasoning.extend([
        (
            f"The current {budget.period} {category} budget has "
            f"{_money(budget.remaining_amount):,.0f} {currency} remaining."
            if budget else "No matching category budget is recorded, so the budget part of this assessment is estimated."
        ),
        (
            f"TIANA has {history_count} comparable expense record(s) in the last 90 days."
            if history_count else "There is not enough category history to compare this purchase with your past spending."
        ),
    ])
    recommendations = []
    alternatives = []
    if amount > safe:
        recommendations.append("Reduce the planned amount or postpone the purchase until your safe-to-spend amount increases.")
        recommendations.append("Protect essential costs and the savings target you already set before committing to this purchase.")
        if safe > ZERO:
            alternatives.append(f"Set a temporary spending ceiling of {safe:,.0f} {currency}, then reassess the purchase.")
        else:
            alternatives.append("Wait until you record additional income or update your plan after essential costs are covered.")
    else:
        recommendations.append("The purchase fits within your current safe-to-spend amount; keep the rest of your weekly plan intact.")
        if budget and budget_remaining_after is not None and budget_remaining_after < ZERO:
            recommendations.append("This purchase would exceed the remaining category budget. Adjust the category limit or choose a lower amount.")
    if not is_essential:
        alternatives.append("Compare the purchase with a lower-cost option or postpone it for a few days before deciding.")
    if not recommendations:
        recommendations.append("Record the final amount after purchase so TIANA can compare the plan with what actually happened.")

    if score >= 75 and amount <= safe:
        next_action = ExpenseAnalysis.PROCEED
    elif score >= 60:
        next_action = ExpenseAnalysis.ADJUST
    else:
        next_action = ExpenseAnalysis.POSTPONE

    report_data = {
        "user": user, "analysis_type": ExpenseAnalysis.PLANNED,
        "description": (description or "").strip()[:255], "category": category,
        "amount": amount, "currency": currency, "is_essential": bool(is_essential),
        "purchase_date": purchase_date, "score": score, "verdict": verdict,
        "score_breakdown": breakdown, "financial_context": context,
        "financial_impact": {
            "spendable_balance_before": str(balance),
            "estimated_spendable_balance_after": str(balance_after),
            "safe_to_spend_before": str(safe), "safe_to_spend_after": str(safe_after),
            "weekly_savings_remaining_to_protect": str(snapshot["weekly_savings_remaining"]),
            "category_budget_remaining_after": str(budget_remaining_after) if budget_remaining_after is not None else None,
        },
        "summary": _summary_for_planned(amount, currency, score, safe),
        "reasoning": reasoning, "recommendations": recommendations,
        "alternatives": alternatives, "next_action": next_action,
        "confidence": _confidence(snapshot, budget, history_count),
    }
    return ExpenseAnalysis.objects.create(**report_data) if persist else report_data


def analyze_completed_expense(user, transaction, *, is_essential=False, persist=True):
    """Assess an existing expense; persist=False returns a read-only preview."""
    if transaction.owner_id != user.pk:
        raise ValueError("This transaction does not belong to your account.")
    if transaction.kind != "expense":
        raise ValueError("Only completed expenses can be analyzed.")
    if transaction.currency.upper() != (user.currency or "XAF").upper():
        raise ValueError("Analyze expenses in your primary currency so TIANA does not mix currencies.")

    amount = _money(transaction.amount)
    category = (transaction.category or "General").strip()[:50] or "General"
    today = timezone.localdate()
    snapshot, budget, average, history_count, context = _shared_context(
        user, category, today=today, exclude_transaction=transaction
    )
    currency = snapshot["currency"]
    balance_after = _money(snapshot["spendable_balance"])
    safe_after = _money(snapshot["safe_to_spend"])
    shortfall = _money(snapshot["safe_to_spend_shortfall"])
    balance_before_estimate = (
        balance_after + amount
        if transaction.account.account_type != "savings"
        else balance_after
    )

    if budget is None:
        budget_points = Decimal("18")
        budget_remaining = None
    else:
        spent = _money(budget.spent_amount)
        limit = _money(budget.amount)
        usage = spent / limit if limit > ZERO else Decimal("1")
        budget_points = (
            Decimal("30") if usage <= Decimal("0.80")
            else Decimal("22") if usage <= Decimal("1.00")
            else Decimal("10") if usage <= Decimal("1.25")
            else ZERO
        )
        budget_remaining = _money(budget.remaining_amount)

    savings_points = (
        Decimal("0") if shortfall > ZERO
        else Decimal("25") if safe_after > ZERO
        else Decimal("12")
    )
    balance_points = (
        Decimal("20") * (balance_after / balance_before_estimate)
        if balance_before_estimate > ZERO else ZERO
    )
    priority_points = Decimal("15") if is_essential else Decimal("10")
    pattern_points = Decimal(str(_pattern_points(amount, average, history_count)))
    breakdown = _breakdown({
        "budget_fit": budget_points,
        "savings_protection": savings_points,
        "balance_resilience": balance_points,
        "priority_fit": priority_points,
        "spending_pattern": pattern_points,
    })
    score = min(100, max(0, sum(item["points"] for item in breakdown.values())))
    verdict = _verdict(score)
    reasoning = [
        f"The recorded expense was {amount:,.0f} {currency} on {transaction.transaction_date:%d %b %Y}.",
        f"Your current spendable balance is {balance_after:,.0f} {currency}.",
    ]
    if context["active_goals"]:
        names = ", ".join(goal["name"] for goal in context["active_goals"][:3])
        reasoning.append(
            f"Your active savings goal(s) include {names}. The weekly savings amount "
            "protected by safe-to-spend is based on your configured weekly target."
        )
    reasoning.extend([
        (
            f"The {budget.period} {category} budget is {budget.percent_used:.0f}% used."
            if budget else "No matching category budget is recorded, so TIANA cannot assess a category limit."
        ),
        (
            f"TIANA compared this with {history_count} other expense record(s) in the last 90 days."
            if history_count else "There is not enough category history for a reliable spending-pattern comparison."
        ),
    ])
    recommendations = []
    alternatives = [
        "Use the remaining budget for essential costs first.",
        "Review optional spending before adding another purchase in this category.",
    ]
    if shortfall > ZERO:
        recommendations.append("Pause optional spending while you restore the amount you planned to protect for savings.")
        recommendations.append("Review the rest of this week's food, transport and school commitments before making another purchase.")
    elif budget_remaining is not None and budget_remaining < ZERO:
        recommendations.append("This category is over its recorded budget. Reduce or pause further spending here until the next budget period.")
    else:
        recommendations.append("Keep recording expenses so your remaining budget and savings picture stay accurate.")
    if snapshot["weekly_savings_remaining"] > ZERO:
        recommendations.append(
            f"Keep your remaining weekly savings target of {snapshot['weekly_savings_remaining']:,.0f} {currency} visible when planning the rest of the week."
        )

    next_action = ExpenseAnalysis.RECOVER if shortfall > ZERO or (
        budget_remaining is not None and budget_remaining < ZERO
    ) else ExpenseAnalysis.ADJUST if score < 75 else ExpenseAnalysis.PROCEED

    report_data = {
        "user": user, "transaction": transaction,
        "analysis_type": ExpenseAnalysis.COMPLETED,
        "description": (transaction.description or "").strip()[:255],
        "category": category, "amount": amount, "currency": currency,
        "is_essential": bool(is_essential), "score": score, "verdict": verdict,
        "score_breakdown": breakdown, "financial_context": context,
        "financial_impact": {
            "spendable_balance_before_estimate": str(balance_before_estimate),
            "spendable_balance_after": str(balance_after),
            "safe_to_spend_after": str(safe_after),
            "safe_to_spend_shortfall": str(shortfall),
            "weekly_savings_remaining_to_protect": str(snapshot["weekly_savings_remaining"]),
            "category_budget_remaining_after": str(budget_remaining) if budget_remaining is not None else None,
        },
        "summary": _summary_for_completed(amount, currency, score, shortfall),
        "reasoning": reasoning, "recommendations": recommendations,
        "alternatives": alternatives, "next_action": next_action,
        "confidence": _confidence(snapshot, budget, history_count),
    }
    return ExpenseAnalysis.objects.create(**report_data) if persist else report_data
