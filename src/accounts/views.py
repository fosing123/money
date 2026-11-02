import traceback

from django.contrib import messages
from django.contrib.auth import SESSION_KEY, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.db import IntegrityError, transaction
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
            try:
                # User and their initial wallet/account are one operation. If any
                # step fails, roll back the user row instead of leaving a broken
                # half-created account behind.
                with transaction.atomic():
                    base_username = email.split("@")[0][:140] or "tiana"
                    username, counter = base_username, 1
                    while User.objects.filter(username__iexact=username).exists():
                        suffix = str(counter)
                        username = f"{base_username[:150-len(suffix)]}{suffix}"
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
                    Account.objects.create(
                        owner=user,
                        name="Daily money",
                        account_type="cash",
                        currency=user.currency,
                    )
                    login(request, user)
                return redirect("registration_welcome")
            except IntegrityError:
                # Do not expose SQL, credentials, or submitted form values.
                print("TIANA registration failed with a database integrity error.")
                traceback.print_exc()
                if User.objects.filter(email__iexact=email).exists():
                    form.add_error("email", "An account with this email already exists. Please sign in instead.")
                else:
                    form.add_error(None, "We couldn't complete your registration. Please check your details and try again.")
            except Exception:
                # Django's production error page hides the traceback. Emit it to
                # Worker logs with no request body or personal form values.
                print("TIANA registration failed with an unexpected application error.")
                traceback.print_exc()
                form.add_error(None, "We couldn't complete your registration just now. Please try again.")
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
    return render(request, "accounts/login.html", {"form": form, "next_url": next_url})


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
    saved_allocations = request.user.weekly_budget_allocations or {}
    for key in ("food", "transport", "internet", "school", "personal", "emergency"):
        initial[f"allocation_{key}"] = saved_allocations.get(key, 0)
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
        category_field_map = {
            "food": "allocation_food",
            "transport": "allocation_transport",
            "internet": "allocation_internet",
            "school": "allocation_school",
            "personal": "allocation_personal",
            "emergency": "allocation_emergency",
        }
        user.weekly_budget_allocations = {
            key: str(data.get(field_name) or 0)
            for key, field_name in category_field_map.items()
        }
        user.onboarding_completed = True
        user.save(update_fields=[
            "weekly_income", "weekly_savings_target", "payday_weekday",
            "financial_priorities", "weekly_budget_allocations", "onboarding_completed",
        ])
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
        category_names = {
            "food": "Food",
            "transport": "Transport",
            "internet": "Internet & airtime",
            "school": "School",
            "personal": "Personal",
            "emergency": "Emergency",
        }
        for key, category in category_names.items():
            amount = data.get(f"allocation_{key}") or 0
            if amount <= 0:
                continue
            existing = Budget.objects.filter(
                owner=user, period="weekly", category__iexact=category
            ).first()
            if existing is None:
                Budget.objects.create(
                    owner=user, name=category, category=category, amount=amount,
                    currency=user.currency, period="weekly", start_date=timezone.localdate(),
                )
        messages.success(request, "Your starting plan is saved. There is no perfect budget—just a useful place to begin.")
        return redirect("dashboard")
    return render(request, "accounts/setup.html", {"form": form})


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("profile")
    return render(request, "accounts/profile.html", {"form": form, "firebase_web_vapid_key": __import__("os").environ.get("FIREBASE_WEB_VAPID_KEY", "")})



@login_required
def application_security_view(request):
    return render(request, "accounts/security.html")


@login_required
def manage_devices_view(request):
    active_sessions = []
    for session in Session.objects.filter(expire_date__gt=timezone.now()).iterator():
        data = session.get_decoded()
        if str(data.get(SESSION_KEY, "")) == str(request.user.pk):
            active_sessions.append(session)

    current_key = request.session.session_key
    other_sessions = [session for session in active_sessions if session.session_key != current_key]

    if request.method == "POST":
        for session in other_sessions:
            session.delete()
        messages.success(request, f"Signed out of {len(other_sessions)} other session(s).")
        return redirect("manage_devices")

    return render(request, "accounts/manage_devices.html", {
        "other_session_count": len(other_sessions),
    })
