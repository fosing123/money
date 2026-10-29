from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

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
            user = User.objects.create_user(
                username=username,
                email=email,
                password=form.cleaned_data["password1"],
                first_name=form.cleaned_data["first_name"].strip(),
                last_name=form.cleaned_data["last_name"].strip(),
            )
            Account.objects.create(owner=user, name="Daily money", account_type="cash", currency=user.currency)
            login(request, user)
            messages.success(request, "Welcome to TIANA. Let's set up a plan that fits your life.")
            return redirect("onboarding_setup")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
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
                return redirect("dashboard" if authenticated.onboarding_completed else "onboarding_setup")
            messages.error(request, "That sign-in didn't work. Check your details and try again.")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("home")


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
        user.payday_weekday = data["payday_weekday"]
        user.financial_priorities = data["financial_priorities"]
        user.onboarding_completed = True
        user.save(update_fields=["weekly_income", "weekly_savings_target", "payday_weekday", "financial_priorities", "onboarding_completed"])
        type_map = {
            "Cash": "cash",
            "MTN Mobile Money": "mtn_momo",
            "Orange Money": "orange_money",
            "Bank account": "bank",
        }
        account = Account.objects.filter(owner=user).order_by("created_at").first()
        if account is None:
            account = Account(owner=user, name=data["account_name"], account_type=type_map[data["account_name"]], currency=user.currency)
        account.name = data["account_name"]
        account.account_type = type_map[data["account_name"]]
        account.opening_balance = data["opening_balance"]
        account.currency = user.currency
        account.save()
        account.recalculate_balance()
        messages.success(request, "Your starting plan is saved. There is no perfect budget—just a useful place to begin.")
        return redirect("dashboard")
    return render(request, "accounts/setup.html", {"form": form})


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile and colour theme have been updated.")
        return redirect("profile")
    return render(request, "accounts/profile.html", {"form": form})