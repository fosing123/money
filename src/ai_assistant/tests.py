from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from ai_assistant.models import ChatMessage

User = get_user_model()


@override_settings(AI_PROVIDER="none", AI_API_KEY="", GEMINI_API_KEY="")
class MoneyCoachFallbackTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="coach-user", email="coach@example.com", password="StrongPass123!")
        self.user.onboarding_completed = True
        self.user.save(update_fields=["onboarding_completed"])
        self.client.force_login(self.user)

    def test_chat_is_clear_when_live_ai_is_not_configured(self):
        response = self.client.get(reverse("ai_chat"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Preview mode")
        self.assertContains(response, "won't pretend a live AI response has been generated")

    def test_fallback_is_saved_to_the_member_chat_history(self):
        response = self.client.post(reverse("ai_chat"), {"prompt": "Help me plan food spending"})
        self.assertEqual(response.status_code, 302)
        saved = ChatMessage.objects.get(user=self.user)
        self.assertEqual(saved.prompt, "Help me plan food spending")
        self.assertIn("not connected to Gemini", saved.response)

from unittest.mock import MagicMock, patch
import json

from ai_assistant.models import AIUsage
from ai_assistant.services import AIUsageLimitError, generate_money_guidance


@override_settings(AI_PROVIDER="gemini", GEMINI_API_KEY="ci-test-key", AI_API_KEY="")
class AIRequestCostControlTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ai-cost-user",
            email="ai-cost-user@example.com",
            password="StrongPass123!",
        )

    @staticmethod
    def fake_gemini_response(*args, **kwargs):
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = json.dumps({
            "candidates": [{
                "content": {"parts": [{"text": "Try setting aside a small amount first."}]}
            }]
        }).encode("utf-8")
        return response

    def test_identical_prompt_and_financial_snapshot_use_cached_answer(self):
        with patch("ai_assistant.services.urlopen", side_effect=self.fake_gemini_response) as provider:
            first = generate_money_guidance(self.user, "Help me plan food spending")
            second = generate_money_guidance(self.user, "  help me plan food spending  ")

        self.assertEqual(first, second)
        self.assertEqual(provider.call_count, 1)
        usage = AIUsage.objects.get(user=self.user)
        self.assertEqual(usage.request_count, 1)

    def test_free_member_is_limited_to_three_live_requests_per_day(self):
        with patch("ai_assistant.services.urlopen", side_effect=self.fake_gemini_response) as provider:
            for number in range(3):
                generate_money_guidance(self.user, "Different planning question " + str(number))
            with self.assertRaises(AIUsageLimitError):
                generate_money_guidance(self.user, "A fourth unique planning question")

        self.assertEqual(provider.call_count, 3)
        self.assertEqual(AIUsage.objects.get(user=self.user).request_count, 3)

    def test_premium_member_receives_higher_daily_ai_allowance(self):
        self.user.is_premium = True
        self.user.save(update_fields=["is_premium"])
        with patch("ai_assistant.services.urlopen", side_effect=self.fake_gemini_response) as provider:
            for number in range(4):
                generate_money_guidance(self.user, "Premium planning question " + str(number))

        self.assertEqual(provider.call_count, 4)
        self.assertEqual(AIUsage.objects.get(user=self.user).request_count, 4)
