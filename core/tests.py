from django.test import TestCase
from django.urls import reverse


class WelcomePageTests(TestCase):
    def test_home_renders_the_nkem_welcome_screen(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/landing.html")
        self.assertContains(response, "Nkem")
        self.assertContains(response, "Smart Money. Brighter You.")
        self.assertContains(response, "For students. For a better tomorrow.")
        self.assertContains(response, reverse("register"))
        self.assertContains(response, "nkem-welcome-hero-4k.webp")

    def test_onboarding_entry_uses_the_same_welcome_screen(self):
        response = self.client.get(reverse("onboarding"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/onboarding.html")
        self.assertContains(response, "Nkem")
        self.assertContains(response, "Get Started")
