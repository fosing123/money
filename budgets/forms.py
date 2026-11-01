from django import forms

from .models import Budget


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ["name", "amount", "currency", "period", "category", "start_date", "end_date"]
        widgets = {
            "amount": forms.NumberInput(attrs={"min": "1", "step": "100"}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "name": forms.TextInput(attrs={"placeholder": "e.g. Weekly essentials"}),
            "category": forms.TextInput(attrs={"placeholder": "e.g. Food, transport, school"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["amount"].min_value = 1
        self.fields["currency"].initial = getattr(user, "currency", "XAF")

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_date"), cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "The end date must be on or after the start date.")
        return cleaned


class WeeklyBudgetAllocationForm(forms.Form):
    allocation_food = forms.DecimalField(label="Food", min_value=0, max_digits=14, decimal_places=2, required=False, initial=0, widget=forms.NumberInput(attrs={"min":"0","step":"100","inputmode":"decimal"}))
    allocation_transport = forms.DecimalField(label="Transport", min_value=0, max_digits=14, decimal_places=2, required=False, initial=0, widget=forms.NumberInput(attrs={"min":"0","step":"100","inputmode":"decimal"}))
    allocation_internet = forms.DecimalField(label="Internet & airtime", min_value=0, max_digits=14, decimal_places=2, required=False, initial=0, widget=forms.NumberInput(attrs={"min":"0","step":"100","inputmode":"decimal"}))
    allocation_school = forms.DecimalField(label="School", min_value=0, max_digits=14, decimal_places=2, required=False, initial=0, widget=forms.NumberInput(attrs={"min":"0","step":"100","inputmode":"decimal"}))
    allocation_personal = forms.DecimalField(label="Personal", min_value=0, max_digits=14, decimal_places=2, required=False, initial=0, widget=forms.NumberInput(attrs={"min":"0","step":"100","inputmode":"decimal"}))
    allocation_emergency = forms.DecimalField(label="Emergency", min_value=0, max_digits=14, decimal_places=2, required=False, initial=0, widget=forms.NumberInput(attrs={"min":"0","step":"100","inputmode":"decimal"}))

    CATEGORY_FIELDS = (
        ("food", "Food"),
        ("transport", "Transport"),
        ("internet", "Internet & airtime"),
        ("school", "School"),
        ("personal", "Personal"),
        ("emergency", "Emergency"),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        initial = dict(kwargs.pop("initial", {}) or {})
        if user is not None:
            saved = user.weekly_budget_allocations or {}
            for key, _label in self.CATEGORY_FIELDS:
                initial.setdefault(f"allocation_{key}", saved.get(key, 0))
        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    @property
    def allocation_fields(self):
        return [
            (label, self[f"allocation_{key}"], key)
            for key, label in self.CATEGORY_FIELDS
        ]

    def clean(self):
        cleaned = super().clean()
        if self.user is None:
            return cleaned
        total = sum(
            (cleaned.get(f"allocation_{key}") or 0)
            for key, _label in self.CATEGORY_FIELDS
        )
        available = (
            (self.user.weekly_income or 0)
            - (self.user.weekly_savings_target or 0)
        )
        if total > available:
            self.add_error(
                None,
                "Your category limits must fit within your weekly income after savings.",
            )
        return cleaned
