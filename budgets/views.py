from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import BudgetForm
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