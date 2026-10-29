from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finance.models import Account

User = get_user_model()


class OnboardingFlowTests(TestCase):
    def test_registration_continues_to_personal_setup(self):
        response = self.client.post(reverse("register"), {
            "first_name": "Kams",
            "last_name": "Student",
            "email": "kams@example.test",
            "password1": "Saffron-Planet-2026!",
            "password2": "Saffron-Planet-2026!",
        })
        self.assertRedirects(response, reverse("onboarding_setup"))
        user = User.objects.get(email="kams@example.test")
        self.assertTrue(Account.objects.filter(owner=user).exists())
        self.assertFalse(user.onboarding_completed)

    def test_setup_saves_plan_and_opening_balance(self):
        user = User.objects.create_user(username="setup-user", email="setup@example.test", password="Saffron-Planet-2026!")
        Account.objects.create(owner=user, name="Daily money")
        self.client.force_login(user)
        response = self.client.post(reverse("onboarding_setup"), {
            "weekly_income": "10000",
            "opening_balance": "5000",
            "weekly_savings_target": "2000",
            "account_name": "MTN Mobile Money",
            "payday_weekday": "1",
            "financial_priorities": ["laptop", "school_fees"],
        })
        self.assertRedirects(response, reverse("dashboard"))
        user.refresh_from_db()
        account = Account.objects.get(owner=user)
        self.assertTrue(user.onboarding_completed)
        self.assertEqual(user.weekly_income, Decimal("10000"))
        self.assertEqual(user.weekly_savings_target, Decimal("2000"))
        self.assertEqual(account.account_type, "mtn_momo")
        self.assertEqual(account.opening_balance, Decimal("5000"))
        self.assertEqual(account.balance, Decimal("5000"))