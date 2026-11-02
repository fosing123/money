"""Query-efficient budget spending calculations shared by dashboard and alerts."""
from decimal import Decimal

from django.db.models import Q, Sum

from finance.models import Transaction


def attach_budget_spending(budgets, owner=None):
    """Attach each budget's spent total with one conditional aggregate query."""
    budgets = list(budgets)
    if not budgets:
        return budgets

    owner_id = owner.pk if owner is not None else budgets[0].owner_id
    expressions = {}
    aliases = []

    for budget in budgets:
        start, end = budget._current_window()
        alias = f"spent_budget_{budget.pk}"
        if end < start:
            setattr(budget, "_spent_amount_cache", Decimal("0.00"))
            continue

        condition = Q(
            currency=budget.currency,
            transaction_date__range=(start, end),
        )
        if budget.category:
            condition &= Q(category__iexact=budget.category.strip())

        expressions[alias] = Sum("amount", filter=condition)
        aliases.append((budget, alias))

    if expressions:
        totals = Transaction.objects.filter(
            owner_id=owner_id,
            kind="expense",
        ).aggregate(**expressions)
        for budget, alias in aliases:
            setattr(
                budget,
                "_spent_amount_cache",
                totals.get(alias) or Decimal("0.00"),
            )

    return budgets
