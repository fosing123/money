from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_POST

from budgets.models import Budget
from finance.models import Account
from .forms import LoginForm, OnboardingSetupForm, ProfileForm, RegisterForm
from .models import User


def onboarding_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard" if request.user.onboarding_completed else "onboarding_setup")
    return render(request, "accounts/onboarding.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard" if request.user.onboarding_completed else "onboarding_setup")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].strip()
            base_username = email.split("@")[0][:140] or "tiana"
            username, counter = base_username, 1
            while User.objects.filter(username__iexact=username).exists():
                username = f"{base_username[:140-len(str(counter))]}{counter}"
                counter += 1
            first_name, _, last_name = form.cleaned_data["full_name"].strip().partition(" ")
            user = User.objects.create_user(
                username=username,
                email=email,
                password=form.cleaned_data["password1"],
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                phone_number=form.cleaned_data.get("phone_number", "").strip(),
            )
            Account.objects.create(owner=user, name="Daily money", account_type="cash", currency=user.currency)
            login(request, user)
            return redirect("registration_welcome")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def registration_welcome_view(request):
    if request.user.onboarding_completed:
        return redirect("dashboard")
    return render(request, "accounts/registration_welcome.html")


def login_view(request):
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if request.user.is_authenticated:
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(next_url)
        return redirect("dashboard" if request.user.onboarding_completed else "onboarding_setup")
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["username"].strip()
            candidate = User.objects.filter(email__iexact=identifier).first()
            if candidate is None:
                candidate = User.objects.filter(username__iexact=identifier).first()
            authenticated = authenticate(request, username=candidate.username, password=form.cleaned_data["password"]) if candidate else None
            if authenticated:
                login(request, authenticated)
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                    return redirect(next_url)
                return redirect("dashboard" if authenticated.onboarding_completed else "onboarding_setup")
            form.add_error(None, "That sign-in didn't work. Check your details and try again.")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have been securely signed out.")
    return redirect("login")


@login_required
def onboarding_setup_view(request):
    if request.user.onboarding_completed:
        return redirect("dashboard")
    account = Account.objects.filter(owner=request.user).order_by("created_at").first()
    initial = {
        "weekly_income": request.user.weekly_income or 10000,
        "opening_balance": account.opening_balance if account else 5000,
        "weekly_savings_target": request.user.weekly_savings_target or 2000,
        "account_name": "Cash",
        "payday_weekday": request.user.payday_weekday,
        "financial_priorities": request.user.financial_priorities or [],
    }
    form = OnboardingSetupForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        user = request.user
        user.weekly_income = data["weekly_income"]
        user.weekly_savings_target = data["weekly_savings_target"]
        payday_weekday = data.get("payday_weekday")
        # Optional choice fields may be submitted blank. Persist SQL NULL, never "".
        # Use an explicit check so Monday (0) remains a valid weekday.
        user.payday_weekday = None if payday_weekday in (None, "") else int(payday_weekday)
        user.financial_priorities = data["financial_priorities"]
        user.onboarding_completed = True
        user.save(update_fields=["weekly_income", "weekly_savings_target", "payday_weekday", "financial_priorities", "onboarding_completed"])
        type_map = {"Cash": "cash", "MTN Mobile Money": "mtn_momo", "Orange Money": "orange_money", "Bank account": "bank"}
        account = Account.objects.filter(owner=user).order_by("created_at").first()
        if account is None:
            account = Account(owner=user, name=data["account_name"], account_type=type_map[data["account_name"]], currency=user.currency)
        account.name = data["account_name"]
        account.account_type = type_map[data["account_name"]]
        account.opening_balance = data["opening_balance"]
        account.currency = user.currency
        account.save()
        account.recalculate_balance()
        if data["weekly_income"] > 0 and not Budget.objects.filter(owner=user).exists():
            Budget.objects.create(
                owner=user,
                name="Weekly essentials",
                amount=data["weekly_income"],
                currency=user.currency,
                period="weekly",
                start_date=timezone.localdate(),
            )
        messages.success(request, "Your starting plan is saved. There is no perfect budget—just a useful place to begin.")
        return redirect("dashboard")
    return render(request, "accounts/setup.html", {"form": form})


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("profile")
    return render(request, "accounts/profile.html", {"form": form})
