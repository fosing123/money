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
        self.assertContains(
            response,
            'src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1554607983371431"',
        )
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


class PWAOfflineAndPremiumTests(TestCase):
    def test_welcome_page_exposes_the_installable_pwa(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "manifest.webmanifest")
        self.assertContains(response, "tiana-install-button")
        self.assertContains(response, "nkem/pwa.js")

    def test_root_service_worker_is_served_with_root_scope_permission(self):
        response = self.client.get(reverse("service_worker"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("javascript", response["Content-Type"])
        self.assertEqual(response["Service-Worker-Allowed"], "/")
        self.assertContains(response, "tiana-pwa-shell-v1")
        self.assertNotContains(response, "caches.put(event.request")

    def test_offline_bootstrap_requires_a_signed_in_member(self):
        response = self.client.get(reverse("offline_bootstrap"))
        self.assertEqual(response.status_code, 302)

    def test_offline_bootstrap_contains_only_the_signed_in_members_snapshot(self):
        from django.contrib.auth import get_user_model
        from finance.models import Account

        user = get_user_model().objects.create_user(
            username="offline-member",
            email="offline-member@example.com",
            password="StrongPass123!",
        )
        Account.objects.create(owner=user, name="Daily cash", opening_balance="2500", balance="2500")
        self.client.force_login(user)
        response = self.client.get(reverse("offline_bootstrap"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store, max-age=0")
        self.assertEqual(response.json()["accounts"][0]["name"], "Daily cash")

    def test_premium_page_explains_the_current_checkout_status(self):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(
            username="premium-member",
            email="premium-member@example.com",
            password="StrongPass123!",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("premium"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "3 AI coach requests per day")
        self.assertContains(response, "20 AI coach requests per day")
        self.assertContains(response, "Premium checkout is not connected yet")


    def test_money_school_exposes_the_adsense_verification_code_but_no_ad_units(self):
        response = self.client.get(reverse("money_school"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student Money School")
        self.assertContains(response, "budget")
        self.assertContains(
            response,
            'src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1554607983371431"',
        )
        self.assertNotContains(response, '<ins class="adsbygoogle"')

    def test_authenticated_financial_pages_do_not_load_the_adsense_script(self):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(
            username="ads-private-member",
            email="ads-private-member@example.com",
            password="StrongPass123!",
            onboarding_completed=True,
        )
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "pagead2.googlesyndication.com")
