from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import TransactionForm
from .models import Account, Transaction


@login_required
def transaction_list_view(request):
    transactions = Transaction.objects.filter(owner=request.user)
    if request.GET.get('account'):
        transactions = transactions.filter(account_id=request.GET.get('account'))
    if request.GET.get('kind'):
        transactions = transactions.filter(kind=request.GET.get('kind'))
    accounts = Account.objects.filter(owner=request.user)
    return render(request, 'finance/transactions.html', {'transactions': transactions, 'accounts': accounts})


@login_required
def transaction_create_view(request):
    form = TransactionForm(request.POST or None, initial={'currency': request.user.currency, 'amount': Decimal('0.00')})
    if request.method == 'POST' and form.is_valid():
        transaction = form.save(commit=False)
        transaction.owner = request.user
        transaction.save()
        messages.success(request, 'Transaction saved.')
        return redirect('transactions')
    return render(request, 'finance/transaction_form.html', {'form': form, 'title': 'Add transaction'})


@login_required
def transaction_update_view(request, pk):
    transaction = Transaction.objects.get(pk=pk, owner=request.user)
    form = TransactionForm(request.POST or None, instance=transaction)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Transaction updated.')
        return redirect('transactions')
    return render(request, 'finance/transaction_form.html', {'form': form, 'title': 'Edit transaction'})


@login_required
def transaction_delete_view(request, pk):
    transaction = Transaction.objects.get(pk=pk, owner=request.user)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction removed.')
        return redirect('transactions')
    return render(request, 'finance/transaction_confirm_delete.html', {'transaction': transaction})
