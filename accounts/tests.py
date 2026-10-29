from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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
        self.assertContains(response, "Your money.")
        self.assertContains(response, "Create my free account")

    def test_new_user_is_sent_to_first_run_setup(self):
        user = User.objects.create_user(username="ada", email="ada@example.com", password="StrongPass123!")
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("onboarding_setup"))