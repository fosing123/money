from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

from finance.models import Account

User = get_user_model()


class AccountTests(TestCase):
    def test_user_registration_can_create_user(self):
        user = User.objects.create_user(username="ada", email="ada@example.com", password="StrongPass123!")
        self.assertEqual(user.email, "ada@example.com")
        self.assertEqual(user.theme, "violet")

    def test_duplicate_email_is_not_allowed(self):
        User.objects.create_user(username="ada", email="ada@example.com", password="StrongPass123!")
        with self.assertRaises(Exception):
            User.objects.create_user(username="ada2", email="ada@example.com", password="StrongPass123!")

    def test_public_home_opens_the_tiana_welcome_flow(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your Money Friend Always")
        self.assertContains(response, "Get Started")
        self.assertContains(response, reverse("onboarding"))

    def test_new_user_is_sent_to_first_run_setup(self):
        user = User.objects.create_user(username="newuser", email="newuser@example.com", password="StrongPass123!")
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("onboarding_setup"))

    def test_setup_accepts_blank_optional_payday(self):
        user = User.objects.create_user(username="setupblank", email="setupblank@example.com", password="StrongPass123!")
        self.client.force_login(user)
        response = self.client.post(reverse("onboarding_setup"), {
            "weekly_income": "10000", "opening_balance": "5000", "weekly_savings_target": "2000",
            "account_name": "Cash", "payday_weekday": "", "financial_priorities": ["freedom"],
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
            "weekly_income": "10000", "opening_balance": "5000", "weekly_savings_target": "2000",
            "account_name": "Cash", "payday_weekday": "0", "financial_priorities": ["freedom"],
        })
        self.assertRedirects(response, reverse("dashboard"))
        user.refresh_from_db()
        self.assertEqual(user.payday_weekday, 0)

    def test_profile_uses_only_the_five_supported_themes(self):
        user = User.objects.create_user(username="palette", email="palette@example.com", password="StrongPass123!")
        self.client.force_login(user)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        for theme in ("violet", "mint", "ocean", "sunset", "midnight"):
            with self.subTest(theme=theme):
                self.assertContains(response, theme)
        self.assertNotContains(response, "palette_primary")
        self.assertNotContains(response, "palette_accent")

    def test_logout_redirects_to_login(self):
        user = User.objects.create_user(username="logoutuser", email="logout@example.com", password="StrongPass123!")
        self.client.force_login(user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        dashboard = self.client.get(reverse("dashboard"))
        self.assertEqual(dashboard.status_code, 302)
        self.assertIn(reverse("login"), dashboard.url)

    def test_login_returns_user_to_safe_next_url(self):
        User.objects.create_user(username="returnuser", email="return@example.com", password="StrongPass123!", onboarding_completed=True)
        response = self.client.post(
            reverse("login") + "?next=/transactions/",
            {"username": "return@example.com", "password": "StrongPass123!", "next": "/transactions/"},
        )
        self.assertRedirects(response, "/transactions/")

    def test_login_rejects_external_next_url(self):
        User.objects.create_user(username="safeuser", email="safe@example.com", password="StrongPass123!", onboarding_completed=True)
        response = self.client.post(
            reverse("login"),
            {"username": "safe@example.com", "password": "StrongPass123!", "next": "https://evil.example/"},
        )
        self.assertRedirects(response, reverse("dashboard"))

    def test_onboarding_uses_4k_photography_and_no_fake_status_bar(self):
        response = self.client.get(reverse("onboarding"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/onboarding.html")
        self.assertContains(response, "assets/tiana-logo-transparent.png")
        for asset in (
            "assets/tiana-onboarding-money-clarity-4k.webp",
            "assets/tiana-onboarding-savings-goals-4k.webp",
            "assets/tiana-onboarding-ai-coach-4k.webp",
        ):
            with self.subTest(asset=asset):
                self.assertContains(response, asset)
                self.assertIsNotNone(finders.find(asset))
        self.assertNotContains(response, "onboarding-status")
        self.assertNotContains(response, "onboarding-status-icons")
        self.assertNotContains(response, "9:41")
