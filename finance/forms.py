from django import forms

from .models import Account, Transaction


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'account_type', 'currency']


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['account', 'kind', 'amount', 'currency', 'category', 'description', 'merchant', 'transaction_date']
        widgets = {
            'transaction_date': forms.DateInput(attrs={'type': 'date'}),
        }
