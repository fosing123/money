from django.test import TestCase
from django.urls import reverse


class WelcomePageTests(TestCase):
    def test_home_renders_the_tiana_welcome_screen(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/landing.html")
        self.assertContains(response, "TIANA — Your Money Friend Always")
        self.assertContains(response, "Take control")
        self.assertContains(response, "of your money")
        self.assertContains(response, "Track expenses, save for your goals")
        self.assertContains(response, reverse("onboarding"))
        self.assertContains(response, "assets/tiana-logo-transparent.png")
        self.assertContains(response, "assets/tiana-welcome-student-campus-4k.jpg")
        self.assertNotContains(response, "assets/tiana-welcome-student-campus-4k.webp")
        self.assertNotContains(response, "welcome-status")
        self.assertNotContains(response, "welcome-time")

    def test_onboarding_is_a_three_slide_photo_flow_without_fake_status_bar(self):
        response = self.client.get(reverse("onboarding"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/onboarding.html")
        self.assertContains(response, "Take control of your money")
        self.assertContains(response, "Reach your goals faster")
        self.assertContains(response, "Your AI money coach")
        self.assertContains(response, "assets/tiana-logo-transparent.png")
        self.assertContains(response, "assets/tiana-onboarding-money-clarity-4k.webp")
        self.assertContains(response, "assets/tiana-onboarding-savings-goals-4k.webp")
        self.assertContains(response, "assets/tiana-onboarding-ai-coach-4k.webp")
        self.assertContains(response, reverse("register"))
        self.assertNotContains(response, "onboarding-status")
        self.assertNotContains(response, "onboarding-status-icons")
        self.assertNotContains(response, "9:41")
