from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


TEST_320X50_CODE = (
    '<script>atOptions = {"key":"test-320x50","format":"iframe","height":50,"width":320};</script>'
    '<script src="https://bauval.org/22/test-320x50"></script>'
)
TEST_300X250_CODE = (
    '<script>atOptions = {"key":"test-300x250","format":"iframe","height":250,"width":300};</script>'
    '<script src="https://bauval.org/22/test-300x250"></script>'
)


@override_settings(ADSENSE_ENABLED=False)
class AdsterraPlacementTests(TestCase):
    @override_settings(
        ADSTERRA_ENABLED=True,
        ADSTERRA_WEBSITE_ID="6182605",
        ADSTERRA_BANNER_320X50_CODE=TEST_320X50_CODE,
        ADSTERRA_BANNER_300X250_CODE=TEST_300X250_CODE,
    )
    def test_money_school_renders_distinct_mobile_and_rectangle_banner_slots(self):
        response = self.client.get(reverse("money_school"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-ad-network="adsterra"')
        self.assertContains(response, 'data-adsterra-site-id="6182605"')
        self.assertContains(response, 'data-ad-size="320x50"')
        self.assertContains(response, 'data-ad-size="300x250"')
        self.assertContains(response, "test-320x50")
        self.assertContains(response, "test-300x250")
        self.assertEqual(response.content.count(b"ADVERTISEMENT"), 2)

    @override_settings(
        ADSTERRA_ENABLED=True,
        ADSTERRA_WEBSITE_ID="6182605",
        ADSTERRA_BANNER_320X50_CODE=TEST_320X50_CODE,
        ADSTERRA_BANNER_300X250_CODE=TEST_300X250_CODE,
    )
    def test_premium_member_does_not_receive_third_party_ad_code(self):
        user = get_user_model().objects.create_user(
            username="premium-ad-free",
            email="premium-ad-free@example.com",
            password="StrongPass123!",
            is_premium=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("money_school"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "bauval.org")
        self.assertNotContains(response, "data-adsterra-site-id")

    @override_settings(
        ADSTERRA_ENABLED=False,
        ADSTERRA_WEBSITE_ID="6182605",
        ADSTERRA_BANNER_320X50_CODE=TEST_320X50_CODE,
        ADSTERRA_BANNER_300X250_CODE=TEST_300X250_CODE,
    )
    def test_ad_codes_are_not_rendered_until_explicitly_enabled(self):
        response = self.client.get(reverse("money_school"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "bauval.org")
        self.assertNotContains(response, "data-adsterra-site-id")

    @override_settings(
        ADSTERRA_ENABLED=True,
        ADSTERRA_WEBSITE_ID="6182605",
        ADSTERRA_BANNER_320X50_CODE=TEST_320X50_CODE,
        ADSTERRA_BANNER_300X250_CODE=TEST_300X250_CODE,
    )
    def test_adsterra_scripts_are_not_loaded_on_public_landing_page(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "bauval.org")
        self.assertNotContains(response, "data-adsterra-site-id")

    @override_settings(
        ADSTERRA_ENABLED=True,
        ADSTERRA_WEBSITE_ID="6182605",
        ADSTERRA_BANNER_320X50_CODE=TEST_320X50_CODE,
        ADSTERRA_BANNER_300X250_CODE=TEST_300X250_CODE,
    )
    def test_adsterra_scripts_are_not_loaded_on_private_finance_or_ai_pages(self):
        user = get_user_model().objects.create_user(
            username="private-ad-test",
            email="private-ad-test@example.com",
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
            "ai_chat",
            "analyzer",
        ):
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "bauval.org")
                self.assertNotContains(response, "data-adsterra-site-id")
