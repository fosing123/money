from django import forms

from .models import Account, Transaction


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["name", "account_type", "currency", "opening_balance"]
        widgets = {
            "opening_balance": forms.NumberInput(attrs={"min": "0", "step": "100"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["name"].widget.attrs.update({"placeholder": "e.g. Daily money"})
        self.fields["currency"].initial = getattr(user, "currency", "XAF")


class TransactionForm(forms.ModelForm):
    amount = forms.DecimalField(min_value=0.01, max_digits=14, decimal_places=2, widget=forms.NumberInput(attrs={"min": "0.01", "step": "1", "inputmode": "decimal"}))

    class Meta:
        model = Transaction
        fields = ["account", "kind", "amount", "currency", "category", "description", "merchant", "transaction_date"]
        widgets = {
            "transaction_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.TextInput(attrs={"placeholder": "e.g. Lunch with friends"}),
            "merchant": forms.TextInput(attrs={"placeholder": "Optional shop or person"}),
            "category": forms.TextInput(attrs={"placeholder": "e.g. Food, transport, school"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["account"].queryset = Account.objects.filter(owner=user, is_active=True)
            self.fields["currency"].initial = getattr(user, "currency", "XAF")
        self.fields["amount"].help_text = "Use the amount of this one transaction—not your account balance."
        self.fields["account"].empty_label = "Choose your account"