from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import CompletedExpenseForm, PlannedExpenseForm
from .models import ExpenseAnalysis
from .scoring import analyze_completed_expense, analyze_planned_purchase


@login_required
@require_http_methods(["GET", "POST"])
def analyzer_view(request):
    report = None
    planned_form = PlannedExpenseForm()
    completed_form = CompletedExpenseForm(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action", "").strip()
        if action == "planned":
            planned_form = PlannedExpenseForm(request.POST)
            if planned_form.is_valid():
                try:
                    report = analyze_planned_purchase(
                        request.user,
                        amount=planned_form.cleaned_data["amount"],
                        category=planned_form.cleaned_data["category"],
                        description=planned_form.cleaned_data["description"],
                        is_essential=planned_form.cleaned_data["is_essential"],
                        purchase_date=planned_form.cleaned_data["purchase_date"],
                    )
                    messages.success(request, "Your planned-purchase assessment is ready.")
                except (ValueError, ValidationError) as exc:
                    planned_form.add_error(None, str(exc))
        elif action == "completed":
            completed_form = CompletedExpenseForm(request.POST, user=request.user)
            if completed_form.is_valid():
                try:
                    report = analyze_completed_expense(
                        request.user,
                        completed_form.cleaned_data["transaction"],
                        is_essential=completed_form.cleaned_data["is_essential"],
                    )
                    messages.success(request, "Your spending-impact assessment is ready.")
                except (ValueError, ValidationError) as exc:
                    completed_form.add_error(None, str(exc))
        else:
            messages.error(request, "Choose an analysis type to continue.")

    history = (
        ExpenseAnalysis.objects.filter(user=request.user)
        .select_related("transaction")
        .order_by("-created_at")[:8]
    )
    return render(request, "expense_analyzer/analyzer.html", {
        "planned_form": planned_form,
        "completed_form": completed_form,
        "report": report,
        "history": history,
    })
