from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from finance.models import Account, Transaction

from .forms import GoalContributionForm, GoalForm
from .models import Goal, GoalContribution


@login_required
def goal_list_view(request):
    goals = Goal.objects.filter(owner=request.user).prefetch_related("contributions__transaction")
    total_saved = sum((goal.saved_amount for goal in goals), Decimal("0.00"))
    active_goals = [goal for goal in goals if goal.status == "active"]
    return render(request, "goals/goals.html", {
        "goals": goals,
        "total_saved": total_saved,
        "active_goals_count": len(active_goals),
    })


@login_required
def goal_create_view(request):
    form = GoalForm(request.POST or None, request.FILES or None, user=request.user, initial={"currency": request.user.currency})
    if request.method == "POST" and form.is_valid():
        goal = form.save(commit=False)
        goal.owner = request.user
        goal.save()
        messages.success(request, f"{goal.name} is ready. Add to it whenever you like.")
        return redirect("goals")
    return render(request, "goals/goal_form.html", {"form": form})


@login_required
def goal_contribute_view(request, pk):
    goal = get_object_or_404(
        Goal.objects.prefetch_related("contributions__transaction"),
        pk=pk,
        owner=request.user,
    )
    if goal.status != "active" or goal.remaining_amount <= 0:
        messages.info(request, "This goal has reached its target.")
        return redirect("goals")

    form = GoalContributionForm(request.POST or None, user=request.user, goal=goal)
    if request.method == "POST" and form.is_valid():
        success = False
        amount = form.cleaned_data["amount"]
        account_id = form.cleaned_data["account"].pk
        note = form.cleaned_data.get("note", "").strip()

        with db_transaction.atomic():
            locked_goal = Goal.objects.select_for_update().get(pk=goal.pk, owner=request.user)
            locked_account = Account.objects.select_for_update().filter(
                pk=account_id,
                owner=request.user,
                is_active=True,
                currency=locked_goal.currency,
            ).first()

            if locked_account is None:
                form.add_error("account", "Choose one of your own active accounts in the goal currency.")
            elif amount > locked_goal.remaining_amount:
                form.add_error("amount", f"You only need {locked_goal.remaining_amount:,.0f} {locked_goal.currency} to reach this goal.")
            elif amount > locked_account.balance:
                form.add_error("amount", f"Your {locked_account.name} account only has {locked_account.balance:,.0f} {locked_account.currency} available.")
            elif locked_goal.status != "active":
                form.add_error(None, "This goal has already been completed.")
            else:
                transfer = Transaction.objects.create(
                    owner=request.user,
                    account=locked_account,
                    amount=amount,
                    currency=locked_goal.currency,
                    kind="transfer_out",
                    category="Savings",
                    description=f"Contribution to {locked_goal.name}"[:255],
                    merchant=locked_goal.name[:120],
                    transaction_date=timezone.localdate(),
                )
                GoalContribution.objects.create(
                    owner=request.user,
                    goal=locked_goal,
                    transaction=transfer,
                    note=note,
                )
                if locked_goal.saved_amount >= locked_goal.target_amount:
                    locked_goal.status = "completed"
                    locked_goal.save(update_fields=["status", "updated_at"])
                success = True

        if success:
            messages.success(request, f"{amount:,.0f} {goal.currency} added to {goal.name}. Your progress is updated!")
            return redirect("goals")

    goal.refresh_from_db()
    return render(request, "goals/goal_contribute.html", {
        "goal": goal,
        "form": form,
        "accounts_available": form.fields["account"].queryset.exists(),
    })
