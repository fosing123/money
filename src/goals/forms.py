from django import forms

from finance.models import Account

from .models import Goal


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ["name", "description", "target_amount", "current_amount", "currency", "target_date", "image"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Why does this matter to you?"}),
            "target_amount": forms.NumberInput(attrs={"min": "1", "step": "100", "inputmode": "decimal"}),
            "current_amount": forms.NumberInput(attrs={"min": "0", "step": "100", "inputmode": "decimal"}),
            "target_date": forms.DateInput(attrs={"type": "date"}),
            "name": forms.TextInput(attrs={"placeholder": "e.g. New laptop"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["currency"].initial = getattr(user, "currency", "XAF")
        self.fields["image"].required = False

    def clean(self):
        cleaned = super().clean()
        target, current = cleaned.get("target_amount"), cleaned.get("current_amount")
        if target is not None and current is not None and current > target > 0:
            self.add_error("current_amount", "Saved so far cannot be greater than the target. You can mark a goal complete instead.")
        return cleaned


class GoalContributionForm(forms.Form):
    amount = forms.DecimalField(
        label="Amount to add",
        min_value=0.01,
        max_digits=14,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "min": "1",
            "step": "1",
            "inputmode": "decimal",
            "placeholder": "e.g. 1000",
            "autofocus": True,
        }),
    )
    account = forms.ModelChoiceField(
        label="Take money from",
        queryset=Account.objects.none(),
        empty_label="Choose an account",
    )
    note = forms.CharField(
        label="Note",
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Optional · e.g. Weekly savings"}),
    )

    def __init__(self, *args, user=None, goal=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.goal = goal
        if user is not None and goal is not None:
            self.fields["account"].queryset = Account.objects.filter(
                owner=user,
                is_active=True,
                currency=goal.currency,
            ).order_by("name")

    def clean(self):
        cleaned = super().clean()
        amount = cleaned.get("amount")
        account = cleaned.get("account")

        if amount is not None and self.goal is not None:
            if amount > self.goal.remaining_amount:
                self.add_error(
                    "amount",
                    f"You only need {self.goal.remaining_amount:,.0f} {self.goal.currency} to reach this goal.",
                )

        if account is not None and amount is not None:
            if self.user is None or account.owner_id != self.user.pk:
                self.add_error("account", "Choose one of your own accounts.")
            elif not account.is_active:
                self.add_error("account", "This account is not active.")
            elif self.goal is not None and account.currency != self.goal.currency:
                self.add_error("account", "The account and goal must use the same currency.")
            elif amount > account.balance:
                self.add_error(
                    "amount",
                    f"Your {account.name} account only has {account.balance:,.0f} {account.currency} available.",
                )
        return cleaned
