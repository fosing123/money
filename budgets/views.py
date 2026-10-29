from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Budget


@login_required
def budget_list_view(request):
    budgets = Budget.objects.filter(owner=request.user)
    return render(request, 'budgets/budgets.html', {'budgets': budgets})


@login_required
def budget_create_view(request):
    if request.method == 'POST':
        budget = Budget.objects.create(
            owner=request.user,
            name=request.POST.get('name', 'New budget'),
            amount=request.POST.get('amount', 0),
            currency=request.POST.get('currency', request.user.currency),
            category=request.POST.get('category', ''),
            period=request.POST.get('period', 'monthly'),
        )
        messages.success(request, f'Budget {budget.name} created.')
        return redirect('budgets')
    return render(request, 'budgets/budget_form.html')
