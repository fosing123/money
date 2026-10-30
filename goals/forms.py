from django import forms

from .models import Goal


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ["name", "description", "target_amount", "current_amount", "currency", "target_date", "image"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Why does this matter to you?"}),
            "target_amount": forms.NumberInput(attrs={"min": "1", "step": "100"}),
            "current_amount": forms.NumberInput(attrs={"min": "0", "step": "100"}),
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