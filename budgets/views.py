from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import BudgetForm, WeeklyBudgetAllocationForm
from .models import Budget


@login_required
def budget_list_view(request):
    budgets = Budget.objects.filter(owner=request.user)
    return render(request, "budgets/budgets.html", {"budgets": budgets})


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
