from unittest.mock import AsyncMock, patch
import json

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from ai_assistant.models import AIUsage, ChatMessage
from ai_assistant.services import AIServiceError, AIUsageLimitError, generate_money_guidance

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
        self.assertContains(response, "will not pretend this is a live AI answer")

    def test_fallback_is_saved_to_the_member_chat_history(self):
        response = self.client.post(reverse("ai_chat"), {"prompt": "Help me plan food spending"})
        self.assertEqual(response.status_code, 302)
        saved = ChatMessage.objects.get(user=self.user)
        self.assertEqual(saved.prompt, "Help me plan food spending")
        self.assertIn("not connected to Gemini", saved.response)


def fake_gemini_response(*args, **kwargs):
    return 200, json.dumps({
        "candidates": [{
            "content": {"parts": [{"text": "Try setting aside a small amount first."}]}
        }]
    })


@override_settings(AI_PROVIDER="gemini", GEMINI_API_KEY="ci-test-key", AI_API_KEY="", GEMINI_MODEL="gemini-3.8-flash")
class AIRequestCostControlTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ai-cost-user",
            email="ai-cost-user@example.com",
            password="StrongPass123!",
        )

    def call_ai(self, prompt):
        return async_to_sync(generate_money_guidance)(self.user, prompt)

    def test_identical_prompt_and_financial_snapshot_use_cached_answer(self):
        provider = AsyncMock(side_effect=fake_gemini_response)
        with patch("ai_assistant.services._fetch_gemini_response", provider):
            first = self.call_ai("Help me plan food spending")
            second = self.call_ai("  help me plan food spending  ")

        self.assertEqual(first, second)
        self.assertEqual(provider.call_count, 1)
        self.assertIn("/v1beta/models/gemini-3.8-flash:generateContent", provider.call_args.args[0])
        usage = AIUsage.objects.get(user=self.user)
        self.assertEqual(usage.request_count, 1)

    def test_free_member_is_limited_to_three_live_requests_per_day(self):
        provider = AsyncMock(side_effect=fake_gemini_response)
        with patch("ai_assistant.services._fetch_gemini_response", provider):
            for number in range(3):
                self.call_ai("Different planning question " + str(number))
            with self.assertRaises(AIUsageLimitError):
                self.call_ai("A fourth unique planning question")

        self.assertEqual(provider.call_count, 3)
        self.assertEqual(AIUsage.objects.get(user=self.user).request_count, 3)

    def test_premium_member_receives_higher_daily_ai_allowance(self):
        self.user.is_premium = True
        self.user.save(update_fields=["is_premium"])
        provider = AsyncMock(side_effect=fake_gemini_response)
        with patch("ai_assistant.services._fetch_gemini_response", provider):
            for number in range(4):
                self.call_ai("Premium planning question " + str(number))

        self.assertEqual(provider.call_count, 4)
        self.assertEqual(AIUsage.objects.get(user=self.user).request_count, 4)

    def test_gemini_http_errors_are_reported_and_usage_is_released(self):
        provider = AsyncMock(return_value=(403, json.dumps({
            "error": {"message": "API key is not authorized for this API"}
        })))
        with patch("ai_assistant.services._fetch_gemini_response", provider):
            with self.assertRaises(AIServiceError) as raised:
                self.call_ai("Help me save")

        self.assertIn("rejected the configured server key", str(raised.exception))
        self.assertEqual(AIUsage.objects.get(user=self.user).request_count, 0)
