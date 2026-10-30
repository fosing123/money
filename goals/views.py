from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import GoalForm
from .models import Goal


@login_required
def goal_list_view(request):
    goals = Goal.objects.filter(owner=request.user)
    return render(request, "goals/goals.html", {"goals": goals})


@login_required
def goal_create_view(request):
    form = GoalForm(request.POST or None, request.FILES or None, user=request.user, initial={"currency": request.user.currency})
    if request.method == "POST" and form.is_valid():
        goal = form.save(commit=False)
        goal.owner = request.user
        goal.save()
        messages.success(request, f"Your {goal.name} goal is saved. Every little step counts.")
        return redirect("goals")
    return render(request, "goals/goal_form.html", {"form": form})