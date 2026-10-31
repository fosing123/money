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


    def test_registration_uses_the_new_welcome_step_and_saves_optional_phone(self):
        response = self.client.post(reverse("register"), {
            "first_name": "Ada",
            "last_name": "Ndi",
            "email": "ada.new@example.com",
            "phone_number": "+237 670 000 000",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertRedirects(response, reverse("registration_welcome"))
        user = User.objects.get(email="ada.new@example.com")
        self.assertEqual(user.phone_number, "+237 670 000 000")
        self.assertTrue(self.client.session.get("_auth_user_id"))
        self.assertTrue(Account.objects.filter(owner=user, name="Daily money").exists())

        welcome = self.client.get(reverse("registration_welcome"))
        self.assertEqual(welcome.status_code, 200)
        self.assertTemplateUsed(welcome, "accounts/registration_welcome.html")
        self.assertContains(welcome, "Welcome to")
        self.assertContains(welcome, "Let's build my money plan")
        self.assertContains(welcome, reverse("onboarding_setup"))

    def test_registration_welcome_requires_authentication(self):
        response = self.client.get(reverse("registration_welcome"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_registration_and_login_pages_use_the_new_tiana_auth_experience(self):
        register = self.client.get(reverse("register"))
        login = self.client.get(reverse("login"))
        for response in (register, login):
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "nkem/auth.css")
            self.assertContains(response, "tiana-auth-campus.webp")
            self.assertContains(response, "data-password-toggle")
        self.assertContains(register, "Phone number")
        self.assertContains(login, "Sign in to TIANA")

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

    def test_tiana_welcome_and_onboarding_static_assets_exist(self):
        assets = (
            "assets/tiana-logo-transparent.png",
            "assets/tiana-welcome-student-campus-4k.jpg",
            "assets/tiana-onboarding-money-clarity-4k.webp",
            "assets/tiana-onboarding-savings-goals-4k.webp",
            "assets/tiana-onboarding-ai-coach-4k.webp",
        )
        for asset in assets:
            with self.subTest(asset=asset):
                self.assertIsNotNone(finders.find(asset), msg=f"Missing static asset: {asset}")

    def test_onboarding_uses_4k_photography_and_no_fake_status_bar(self):
        response = self.client.get(reverse("onboarding"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/onboarding.html")
        for asset in (
            "assets/tiana-logo-transparent.png",
            "assets/tiana-onboarding-money-clarity-4k.webp",
            "assets/tiana-onboarding-savings-goals-4k.webp",
            "assets/tiana-onboarding-ai-coach-4k.webp",
        ):
            with self.subTest(asset=asset):
                self.assertContains(response, asset)
        self.assertContains(response, "Skip")
        self.assertContains(response, "Next")
        self.assertNotContains(response, "onboarding-status")
        self.assertNotContains(response, "onboarding-status-icons")
        self.assertNotContains(response, "9:41")
