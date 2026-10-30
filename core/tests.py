from django.test import TestCase
from django.urls import reverse


class WelcomePageTests(TestCase):
    def test_home_renders_the_nkem_splash_screen(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/landing.html")
        self.assertContains(response, "Nkem")
        self.assertContains(response, "Smart Money. Brighter You.")
        self.assertContains(response, "For students. For a better tomorrow.")
        self.assertContains(response, reverse("onboarding"))
        self.assertContains(response, "nkem-welcome-hero-4k.avif")

    def test_onboarding_is_a_three_slide_feature_flow(self):
        response = self.client.get(reverse("onboarding"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/onboarding.html")
        self.assertContains(response, "Take control of your money")
        self.assertContains(response, "Reach your goals faster")
        self.assertContains(response, "Your AI money coach")
        self.assertContains(response, "assets/onboarding-control.svg")
        self.assertContains(response, "assets/onboarding-goals.svg")
        self.assertContains(response, "assets/onboarding-ai.svg")
        self.assertContains(response, reverse("register"))
