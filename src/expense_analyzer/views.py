from asgiref.sync import sync_to_async
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .ai import ExpenseAIUnavailable, generate_expense_insights
from .forms import CompletedExpenseForm, PlannedExpenseForm
from .models import ExpenseAnalysis
from .scoring import analyze_completed_expense, analyze_planned_purchase


def _process_submission(user, post_data):
    """Keep Django ORM and form validation work in a synchronous thread."""
    report = None
    planned_form = PlannedExpenseForm()
    completed_form = CompletedExpenseForm(user=user)
    error = ""

    action = post_data.get("action", "").strip()
    if action == "planned":
        planned_form = PlannedExpenseForm(post_data)
        if planned_form.is_valid():
            try:
                report = analyze_planned_purchase(
                    user,
                    amount=planned_form.cleaned_data["amount"],
                    category=planned_form.cleaned_data["category"],
                    description=planned_form.cleaned_data["description"],
                    is_essential=planned_form.cleaned_data["is_essential"],
                    purchase_date=planned_form.cleaned_data["purchase_date"],
                )
            except (ValueError, ValidationError) as exc:
                planned_form.add_error(None, str(exc))
    elif action == "completed":
        completed_form = CompletedExpenseForm(post_data, user=user)
        if completed_form.is_valid():
            try:
                report = analyze_completed_expense(
                    user,
                    completed_form.cleaned_data["transaction"],
                    is_essential=completed_form.cleaned_data["is_essential"],
                )
            except (ValueError, ValidationError) as exc:
                completed_form.add_error(None, str(exc))
    else:
        error = "Choose an analysis type to continue."

    return planned_form, completed_form, report, error


def _render_analyzer(request, planned_form, completed_form, report, ai_enhanced, ai_error, error):
    history = list(
        ExpenseAnalysis.objects.filter(user=request.user)
        .select_related("transaction")
        .order_by("-created_at")[:8]
    )
    return render(request, "expense_analyzer/analyzer.html", {
        "planned_form": planned_form,
        "completed_form": completed_form,
        "report": report,
        "history": history,
        "ai_enhanced": ai_enhanced,
        "ai_error": ai_error,
        "analyzer_error": error,
    })


@login_required
@require_http_methods(["GET", "POST"])
async @login_required
def analyzer_view(request):
    report = None
    ai_enhanced = False
    ai_error = ""
    error = ""

    if request.method == "POST":
        planned_form, completed_form, report, error = await sync_to_async(
            _process_submission, thread_sensitive=True
        )(request.user, request.POST)
    else:
        planned_form = await sync_to_async(PlannedExpenseForm, thread_sensitive=True)()
        completed_form = await sync_to_async(
            CompletedExpenseForm, thread_sensitive=True
        )(user=request.user)

    if report is not None:
        try:
            insights = await generate_expense_insights(report)
            report.summary = insights["summary"]
            report.reasoning = insights["reasoning"]
            report.recommendations = insights["recommendations"]
            report.alternatives = insights["alternatives"]
            await sync_to_async(report.save, thread_sensitive=True)(
                update_fields=["summary", "reasoning", "recommendations", "alternatives"]
            )
            ai_enhanced = True
        except ExpenseAIUnavailable as exc:
            # The transparent, deterministic assessment remains useful even if
            # Gemini is temporarily unavailable. Never replace it with fake AI.
            ai_error = str(exc)

    return await sync_to_async(_render_analyzer, thread_sensitive=True)(
        request,
        planned_form,
        completed_form,
        report,
        ai_enhanced,
        ai_error,
        error,
    )
