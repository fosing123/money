from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finance.models import Account

User = get_user_model()


class AccountTests(TestCase):
    def test_user_registration_can_create_user(self):
        user = User.objects.create_user(username="ada", email="ada@example.com", password="StrongPass123!")
        self.assertEqual(user.email, "ada@example.com")

    def test_duplicate_email_is_not_allowed(self):
        User.objects.create_user(username="ada", email="ada@example.com", password="StrongPass123!")
        with self.assertRaises(Exception):
            User.objects.create_user(username="ada2", email="ada@example.com", password="StrongPass123!")

    def test_public_home_renders_onboarding(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Make your money work with you.")
        self.assertContains(response, "Create your account")
        self.assertContains(response, "Track transactions")

    def test_new_user_is_sent_to_first_run_setup(self):
        user = User.objects.create_user(username="ada", email="ada@example.com", password="StrongPass123!")
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("onboarding_setup"))

    def test_setup_accepts_blank_optional_payday(self):
        user = User.objects.create_user(username="setupblank", email="setupblank@example.com", password="StrongPass123!")
        self.client.force_login(user)

        response = self.client.post(reverse("onboarding_setup"), {
            "weekly_income": "10000",
            "opening_balance": "5000",
            "weekly_savings_target": "2000",
            "account_name": "Cash",
            "payday_weekday": "",
            "financial_priorities": ["freedom"],
        })

        self.assertRedirects(response, reverse("dashboard"))
        user.refresh_from_db()
        self.assertIsNone(user.payday_weekday)
        self.assertTrue(user.onboarding_completed)
        account = Account.objects.get(owner=user)
        self.assertEqual(str(account.opening_balance), "5000.00")

    def test_setup_preserves_monday_as_valid_payday_zero(self):
        user = User.objects.create_user(username="setupmonday", email="setupmonday@example.com", password="StrongPass123!")
        self.client.force_login(user)

        response = self.client.post(reverse("onboarding_setup"), {
            "weekly_income": "10000",
            "opening_balance": "5000",
            "weekly_savings_target": "2000",
            "account_name": "Cash",
            "payday_weekday": "0",
            "financial_priorities": ["freedom"],
        })

        self.assertRedirects(response, reverse("dashboard"))
        user.refresh_from_db()
        self.assertEqual(user.payday_weekday, 0)
