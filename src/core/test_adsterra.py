from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


TEST_AD_CODE = (
    '<script async src="https://pl.example-adsterra.test/native.js"></script>'
    '<div id="container-test-slot"></div>'
)


@override_settings(ADSENSE_ENABLED=False)
class AdsterraPlacementTests(TestCase):
    @override_settings(
        ADSTERRA_ENABLED=True,
        ADSTERRA_WEBSITE_ID="6182605",
        ADSTERRA_NATIVE_BANNER_CODE=TEST_AD_CODE,
    )
    def test_money_school_renders_configured_adsterra_code_for_free_visitor(self):
        response = self.client.get(reverse("money_school"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-adsterra-site-id="6182605"')
        self.assertContains(response, "container-test-slot")
        self.assertContains(response, "ADVERTISEMENT")

    @override_settings(
        ADSTERRA_ENABLED=True,
        ADSTERRA_WEBSITE_ID="6182605",
        ADSTERRA_NATIVE_BANNER_CODE=TEST_AD_CODE,
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
        self.assertNotContains(response, "container-test-slot")
        self.assertNotContains(response, "data-adsterra-site-id")

    @override_settings(
        ADSTERRA_ENABLED=False,
        ADSTERRA_WEBSITE_ID="6182605",
        ADSTERRA_NATIVE_BANNER_CODE=TEST_AD_CODE,
    )
    def test_ad_code_is_not_rendered_until_explicitly_enabled(self):
        response = self.client.get(reverse("money_school"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "container-test-slot")
        self.assertNotContains(response, "data-adsterra-site-id")

    @override_settings(
        ADSTERRA_ENABLED=True,
        ADSTERRA_WEBSITE_ID="6182605",
        ADSTERRA_NATIVE_BANNER_CODE=TEST_AD_CODE,
    )
    def test_adsterra_script_is_not_loaded_on_the_public_landing_page(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "container-test-slot")
        self.assertNotContains(response, "data-adsterra-site-id")
