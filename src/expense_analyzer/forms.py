from django import forms

from finance.models import Transaction


class PlannedExpenseForm(forms.Form):
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. New sneakers", "autocomplete": "off"}),
    )
    amount = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={"min": "0.01", "step": "0.01", "placeholder": "0"}),
    )
    category = forms.CharField(
        max_length=50,
        initial="Shopping",
        widget=forms.TextInput(attrs={"placeholder": "Food, transport, shopping…"}),
    )
    purchase_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    is_essential = forms.BooleanField(
        required=False,
        label="This is an essential purchase",
    )


class ExpenseTransactionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, transaction):
        title = transaction.description or transaction.category or "Expense"
        return (
            f"{title[:42]} · {transaction.amount:,.0f} {transaction.currency} "
            f"· {transaction.transaction_date:%d %b}"
        )


class CompletedExpenseForm(forms.Form):
    transaction = ExpenseTransactionChoiceField(
        queryset=Transaction.objects.none(),
        empty_label="Choose a completed expense",
    )
    is_essential = forms.BooleanField(
        required=False,
        label="This was an essential expense",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["transaction"].queryset = (
                Transaction.objects.filter(
                    owner=user,
                    kind="expense",
                    currency__iexact=(user.currency or "XAF"),
                )
                .select_related("account")
                .order_by("-transaction_date", "-created_at")[:100]
            )
