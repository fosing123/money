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