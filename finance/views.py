from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AccountForm, TransactionForm
from .models import Account, Transaction


@login_required
def account_create_view(request):
    form = AccountForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        account = form.save(commit=False)
        account.owner = request.user
        account.balance = account.opening_balance
        account.save()
        messages.success(request, f"{account.name} is ready to use.")
        return redirect("dashboard")
    return render(request, "finance/account_form.html", {"form": form})


@login_required
def transaction_list_view(request):
    transactions = Transaction.objects.filter(owner=request.user).select_related("account")
    selected_kind = request.GET.get("kind", "").strip()
    selected_account = request.GET.get("account", "").strip()
    if selected_kind in dict(Transaction.KIND_CHOICES):
        transactions = transactions.filter(kind=selected_kind)
    if selected_account.isdigit():
        transactions = transactions.filter(account_id=int(selected_account))
    summary = transactions.aggregate(
        total_income=Sum("amount", filter=Q(kind__in=["income", "refund", "transfer_in"])),
        total_expense=Sum("amount", filter=Q(kind__in=["expense", "transfer_out"])),
    )
    return render(request, "finance/transactions.html", {
        "transactions": transactions,
        "accounts": Account.objects.filter(owner=request.user, is_active=True),
        "kind_choices": Transaction.KIND_CHOICES,
        "selected_kind": selected_kind,
        "selected_account": selected_account,
        "income_total": summary["total_income"] or Decimal("0.00"),
        "expense_total": summary["total_expense"] or Decimal("0.00"),
    })


@login_required
def transaction_create_view(request):
    form = TransactionForm(request.POST or None, user=request.user, initial={"currency": request.user.currency})
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.owner = request.user
        if not Account.objects.filter(pk=item.account_id, owner=request.user, is_active=True).exists():
            form.add_error("account", "Choose one of your own active accounts.")
        else:
            item.save()
            messages.success(request, "Transaction saved. Your balance has been recalculated.")
            return redirect("transactions")
    return render(request, "finance/transaction_form.html", {"form": form, "title": "Add transaction"})


@login_required
def transaction_update_view(request, pk):
    item = get_object_or_404(Transaction, pk=pk, owner=request.user)
    form = TransactionForm(request.POST or None, instance=item, user=request.user)
    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        updated.owner = request.user
        if not Account.objects.filter(pk=updated.account_id, owner=request.user, is_active=True).exists():
            form.add_error("account", "Choose one of your own active accounts.")
        else:
            updated.save()
            messages.success(request, "Transaction updated and account balance refreshed.")
            return redirect("transactions")
    return render(request, "finance/transaction_form.html", {"form": form, "title": "Edit transaction"})


@login_required
def transaction_delete_view(request, pk):
    item = get_object_or_404(Transaction, pk=pk, owner=request.user)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Transaction removed and account balance refreshed.")
        return redirect("transactions")
    return render(request, "finance/transaction_confirm_delete.html", {"transaction": item})