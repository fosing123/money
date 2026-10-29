from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Goal


@login_required
def goal_list_view(request):
    goals = Goal.objects.filter(owner=request.user)
    return render(request, 'goals/goals.html', {'goals': goals})


@login_required
def goal_create_view(request):
    if request.method == 'POST':
        goal = Goal.objects.create(
            owner=request.user,
            name=request.POST.get('name', 'New goal'),
            target_amount=request.POST.get('target_amount', 0),
            current_amount=request.POST.get('current_amount', 0),
            currency=request.POST.get('currency', request.user.currency),
            description=request.POST.get('description', ''),
        )
        messages.success(request, f'Goal {goal.name} created.')
        return redirect('goals')
    return render(request, 'goals/goal_form.html')
