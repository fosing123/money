from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from budgets.models import Budget
from finance.models import Account, Transaction
from goals.models import Goal


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')


@login_required
def dashboard_view(request):
    accounts = Account.objects.filter(owner=request.user)
    total_balance = sum((account.balance for account in accounts), Decimal('0.00'))

    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    income_total = sum(
        (item.amount for item in Transaction.objects.filter(owner=request.user, kind='income', transaction_date__gte=month_start.date())),
        Decimal('0.00'),
    )
    expense_total = sum(
        (item.amount for item in Transaction.objects.filter(owner=request.user, kind='expense', transaction_date__gte=month_start.date())),
        Decimal('0.00'),
    )
    recent_transactions = Transaction.objects.filter(owner=request.user)[:6]
    budgets = Budget.objects.filter(owner=request.user)[:4]
    goals = Goal.objects.filter(owner=request.user)[:4]

    return render(request, 'core/dashboard.html', {
        'accounts': accounts,
        'total_balance': total_balance,
        'income_total': income_total,
        'expense_total': expense_total,
        'net_cash_flow': income_total - expense_total,
        'recent_transactions': recent_transactions,
        'budgets': budgets,
        'goals': goals,
    })


def health_check_view(request):
    return JsonResponse({'status': 'ok', 'service': 'nkem'})
