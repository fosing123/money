from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()

PRIORITY_CHOICES = [
    ("school_fees", "Save for school fees"),
    ("laptop", "Buy a laptop"),
    ("daily_expenses", "Manage daily expenses"),
    ("trip", "Save for a trip"),
    ("business", "Start a small business"),
    ("emergency", "Build an emergency fund"),
    ("freedom", "Feel more financially free"),
]


class RegisterForm(forms.Form):
    full_name = forms.CharField(
        max_length=101,
        label="Full name",
        widget=forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Your full name"}),
    )
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        label="Phone number",
        widget=forms.TelInput(attrs={"autocomplete": "tel", "inputmode": "tel", "placeholder": "+237 6XX XXX XXX"}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "placeholder": "Create a strong password"}),
    )

    def clean_full_name(self):
        full_name = " ".join(self.cleaned_data["full_name"].split())
        first_name, _, last_name = full_name.partition(" ")
        if not first_name or len(first_name) > 50 or len(last_name) > 50:
            raise forms.ValidationError("Please enter a first name and a surname of up to 50 characters each.")
        return full_name

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_phone_number(self):
        return (self.cleaned_data.get("phone_number") or "").strip()

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password1")
        full_name = cleaned.get("full_name") or ""
        first_name, _, last_name = full_name.partition(" ")
        if password and not self.errors.get("password1"):
            candidate = User(
                username=(cleaned.get("email") or "new-user").split("@")[0],
                email=cleaned.get("email") or "",
                first_name=first_name,
                last_name=last_name,
            )
            try:
                validate_password(password, user=candidate)
            except ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "currency", "phone_number", "theme"]
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone_number": forms.TelInput(attrs={"autocomplete": "tel"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        exists = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists()
        if exists:
            raise forms.ValidationError("This email address is already in use.")
        return email


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Email or username",
        widget=forms.TextInput(attrs={"autocomplete": "username", "placeholder": "Email address or username"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "placeholder": "Your password"}),
    )


class OnboardingSetupForm(forms.Form):
    weekly_income = forms.DecimalField(label="Usual weekly income (FCFA)", min_value=0, max_digits=14, decimal_places=2, initial=10000, widget=forms.NumberInput(attrs={"min": "0", "step": "500", "inputmode": "decimal"}))
    opening_balance = forms.DecimalField(label="Money you have right now (FCFA)", min_value=0, max_digits=14, decimal_places=2, initial=5000, widget=forms.NumberInput(attrs={"min": "0", "step": "500", "inputmode": "decimal"}))
    weekly_savings_target = forms.DecimalField(label="Weekly savings goal (FCFA)", min_value=0, max_digits=14, decimal_places=2, initial=2000, widget=forms.NumberInput(attrs={"min": "0", "step": "500", "inputmode": "decimal"}))
    account_name = forms.ChoiceField(label="Where do you keep most of your money?", choices=[("Cash", "Cash"), ("MTN Mobile Money", "MTN Mobile Money"), ("Orange Money", "Orange Money"), ("Bank account", "Bank account")])
    payday_weekday = forms.TypedChoiceField(
        label="When do you usually get paid?",
        choices=[("", "Choose a day (optional)")] + [(i, label) for i, label in User.WEEKDAYS],
        coerce=lambda value: int(value) if value != "" else None,
        empty_value=None,
        required=False,
    )
    financial_priorities = forms.MultipleChoiceField(label="What matters to you right now? Choose any that fit.", choices=PRIORITY_CHOICES, required=False, widget=forms.CheckboxSelectMultiple)

    def clean(self):
        cleaned = super().clean()
        income = cleaned.get("weekly_income") or 0
        savings = cleaned.get("weekly_savings_target") or 0
        if income and savings > income:
            self.add_error("weekly_savings_target", "Your savings target is higher than your weekly income. Try a smaller goal that still feels meaningful.")
        return cleaned
