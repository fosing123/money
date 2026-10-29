from django import forms

from .models import Budget


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ["name", "amount", "currency", "period", "category", "end_date"]
        widgets = {
            "amount": forms.NumberInput(attrs={"min": "1", "step": "100"}),
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
        end = cleaned.get("end_date")
        if end:
            from django.utils import timezone
            period = cleaned.get("period")
            today = timezone.localdate()
            if period == "weekly":
                start = today - timezone.timedelta(days=today.weekday())
            elif period == "monthly":
                start = today.replace(day=1)
            else:
                start = today.replace(month=1, day=1)
            if end < start:
                self.add_error("end_date", "Choose an end date in the current budget period or later.")
        return cleaned