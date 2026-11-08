from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


TEST_320X50_CODE = (
    '<script>atOptions = {"key":"test-320x50","format":"iframe","height":50,"width":320};</script>'
    '<script src="https://ads.example.test/22/test-320x50"></script>'
)
TEST_300X250_CODE = (
    '<script>atOptions = {"key":"test-300x250","format":"iframe","height":250,"width":300};</script>'
    '<script src="https://ads.example.test/22/test-300x250"></script>'
)


AD_SETTINGS = {
    "ADSTERRA_ENABLED": True,
    "ADSTERRA_WEBSITE_ID": "6182605",
    "ADSTERRA_BANNER_320X50_CODE": TEST_320X50_CODE,
    "ADSTERRA_BANNER_300X250_CODE": TEST_300X250_CODE,
}


@override_settings(ADSENSE_ENABLED=False)
class AdsterraPlacementTests(TestCase):
    @override_settings(**AD_SETTINGS)
    def test_money_school_renders_two_sandboxed_banner_slots(self):
        response = self.client.get(reverse("money_school"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-ad-network="adsterra"')
        self.assertContains(response, 'data-adsterra-site-id="6182605"')
        self.assertContains(response, 'data-ad-size="320x50"')
        self.assertContains(response, 'data-ad-size="300x250"')
        self.assertContains(response, "test-320x50")
        self.assertContains(response, "test-300x250")
        self.assertContains(response, "&lt;script")
        self.assertEqual(response.content.count(b"ADVERTISEMENT"), 2)

    @override_settings(**AD_SETTINGS)
    def test_authenticated_free_members_get_banners_on_finance_and_profile_pages(self):
        user = get_user_model().objects.create_user(
            username="free-ad-member",
            email="free-ad-member@example.com",
            password="StrongPass123!",
            onboarding_completed=True,
        )
        self.client.force_login(user)

        for route_name in (
            "dashboard",
            "transactions",
            "budgets",
            "goals",
            "insights",
            "profile",
        ):
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'data-ad-size="320x50"')
                self.assertContains(response, 'data-ad-size="300x250"')
                self.assertContains(response, "ads.example.test")

    @override_settings(**AD_SETTINGS)
    def test_ai_coach_and_analyzer_show_sponsored_pause_before_ai_requests(self):
        user = get_user_model().objects.create_user(
            username="ai-ad-member",
            email="ai-ad-member@example.com",
            password="StrongPass123!",
            onboarding_completed=True,
        )
        self.client.force_login(user)

        for route_name in ("ai_chat", "analyzer"):
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'data-ad-size="320x50"')
                self.assertContains(response, 'data-tiana-ai-ad-gate')
                self.assertContains(response, 'data-ad-size="300x250"')
                self.assertContains(response, "Help keep TIANA AI available")
                self.assertContains(response, "you never need to click the advertisement")

    @override_settings(**AD_SETTINGS)
    def test_premium_members_remain_ad_free(self):
        user = get_user_model().objects.create_user(
            username="premium-ad-free",
            email="premium-ad-free@example.com",
            password="StrongPass123!",
            is_premium=True,
            onboarding_completed=True,
        )
        self.client.force_login(user)

        for route_name in ("dashboard", "profile", "ai_chat", "analyzer", "money_school"):
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "ads.example.test")
                self.assertNotContains(response, "data-adsterra-site-id")
                self.assertNotContains(response, "data-tiana-ai-ad-gate")

    @override_settings(
        ADSTERRA_ENABLED=False,
        ADSTERRA_WEBSITE_ID="6182605",
        ADSTERRA_BANNER_320X50_CODE=TEST_320X50_CODE,
        ADSTERRA_BANNER_300X250_CODE=TEST_300X250_CODE,
    )
    def test_ad_codes_are_not_rendered_until_explicitly_enabled(self):
        response = self.client.get(reverse("money_school"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "ads.example.test")
        self.assertNotContains(response, "data-adsterra-site-id")

    @override_settings(**AD_SETTINGS)
    def test_anonymous_welcome_page_can_show_banner_inventory(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-ad-size="320x50"')
        self.assertContains(response, 'data-ad-size="300x250"')
