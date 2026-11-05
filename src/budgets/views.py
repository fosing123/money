from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from decimal import Decimal

from .forms import BudgetForm, WeeklyBudgetAllocationForm
from .models import Budget
from .services import attach_budget_spending


@login_required
def budget_list_view(request):
    budgets = list(Budget.objects.filter(owner=request.user))
    attach_budget_spending(budgets, owner=request.user)
    currency = (request.user.currency or "XAF").upper()
    weekly_budgets = [
        budget for budget in budgets
        if budget.period == "weekly" and budget.currency.upper() == currency
    ]
    weekly_planned = sum((Decimal(str(item.amount or 0)) for item in weekly_budgets), Decimal("0.00"))
    weekly_spent = sum((Decimal(str(item.spent_amount or 0)) for item in weekly_budgets), Decimal("0.00"))
    weekly_remaining = sum(
        (max(Decimal(str(item.remaining_amount or 0)), Decimal("0.00")) for item in weekly_budgets),
        Decimal("0.00"),
    )
    weekly_overage = sum(
        (max(-Decimal(str(item.remaining_amount or 0)), Decimal("0.00")) for item in weekly_budgets),
        Decimal("0.00"),
    )
    weekly_usage_percent = (
        float(weekly_spent / weekly_planned * 100) if weekly_planned > 0 else 0
    )
    return render(request, "budgets/budgets.html", {
        "budgets": budgets,
        "weekly_budgets": weekly_budgets,
        "weekly_planned": weekly_planned,
        "weekly_spent": weekly_spent,
        "weekly_remaining": weekly_remaining,
        "weekly_overage": weekly_overage,
        "weekly_usage_percent": weekly_usage_percent,
        "currency": currency,
    })


@login_required
def budget_create_view(request):
    form = BudgetForm(request.POST or None, user=request.user, initial={"currency": request.user.currency})
    if request.method == "POST" and form.is_valid():
        budget = form.save(commit=False)
        budget.owner = request.user
        budget.save()
        messages.success(request, f"Your {budget.name} budget is ready. You can adjust it whenever life changes.")
        return redirect("budgets")
    return render(request, "budgets/budget_form.html", {"form": form})


@login_required
def budget_allocations_view(request):
    form = WeeklyBudgetAllocationForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        user = request.user
        allocations = {}
        for key, category in WeeklyBudgetAllocationForm.CATEGORY_FIELDS:
            amount = form.cleaned_data.get(f"allocation_{key}") or 0
            allocations[key] = str(amount)
            matching = Budget.objects.filter(
                owner=user,
                period="weekly",
                category__iexact=category,
            )
            existing = matching.order_by("-created_at").first()
            if amount <= 0:
                matching.delete()
            elif existing:
                existing.name = category
                existing.category = category
                existing.amount = amount
                existing.currency = user.currency
                existing.save(update_fields=["name", "category", "amount", "currency", "updated_at"])
            else:
                Budget.objects.create(
                    owner=user,
                    name=category,
                    category=category,
                    amount=amount,
                    currency=user.currency,
                    period="weekly",
                )
        user.weekly_budget_allocations = allocations
        user.save(update_fields=["weekly_budget_allocations"])
        messages.success(request, "Your weekly category limits have been updated.")
        return redirect("budgets")
    return render(request, "budgets/allocation_form.html", {"form": form})



@login_required
def budget_delete_view(request, pk):
    from django.db import transaction as db_transaction
    from django.shortcuts import get_object_or_404
    from notifications.models import Notification

    budget = get_object_or_404(Budget, pk=pk, owner=request.user)
    if request.method == "POST":
        with db_transaction.atomic():
            budget = get_object_or_404(
                Budget.objects.select_for_update(),
                pk=pk,
                owner=request.user,
            )
            user = request.user
            category_keys = {
                "food": "food",
                "transport": "transport",
                "internet & airtime": "internet",
                "school": "school",
                "personal": "personal",
                "emergency": "emergency",
            }
            if budget.period == "weekly" and budget.category:
                key = category_keys.get(budget.category.strip().casefold())
                if key:
                    allocations = dict(user.weekly_budget_allocations or {})
                    allocations[key] = "0"
                    user.weekly_budget_allocations = allocations
                    user.save(update_fields=["weekly_budget_allocations"])

            Notification.objects.filter(
                user=user,
                dedupe_key__startswith=f"budget:{budget.pk}:",
            ).delete()
            budget_name = budget.name
            budget.delete()

        messages.success(request, f"{budget_name} budget deleted.")
        return redirect("budgets")

    return render(request, "budgets/budget_confirm_delete.html", {"budget": budget})
