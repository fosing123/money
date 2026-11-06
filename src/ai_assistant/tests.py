from unittest.mock import AsyncMock, patch
import json

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from ai_assistant.models import AIUsage
from ai_assistant.services import AIServiceError, AIUsageLimitError, generate_money_guidance

User = get_user_model()


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

class LegacyAIURLCompatibilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="legacy-ai-route-user",
            email="legacy-ai-route@example.com",
            password="StrongPass123!",
        )
        self.client.force_login(self.user)

    def test_legacy_ai_url_opens_the_expense_analyzer_not_a_chat(self):
        response = self.client.get(reverse("ai_chat"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "expense_analyzer/analyzer.html")
        self.assertContains(response, "What would you like to understand?")
        self.assertContains(response, "My budgets")
        self.assertContains(response, "My savings goals")
        self.assertNotContains(response, "Your private conversation")


class AIUsesMoneyIntelligenceSnapshotTests(TestCase):
    def test_ai_snapshot_uses_the_shared_safe_to_spend_calculation(self):
        from decimal import Decimal
        from django.utils import timezone
        from finance.models import Account, Transaction
        from ai_assistant.services import _user_snapshot

        user = User.objects.create_user(
            username="ai-money-snapshot",
            email="ai-money-snapshot@example.com",
            password="StrongPass123!",
            currency="XAF",
            weekly_savings_target="2000.00",
        )
        cash = Account.objects.create(
            owner=user, name="Daily cash", account_type="cash", currency="XAF",
            opening_balance="10000.00", balance="10000.00",
        )
        Account.objects.create(
            owner=user, name="Savings reserve", account_type="savings",
            currency="XAF", opening_balance="5000.00", balance="5000.00",
        )
        Transaction.objects.create(
            owner=user, account=cash, amount="500.00", currency="XAF",
            kind="transfer_out", category="Savings",
            transaction_date=timezone.localdate(),
        )

        snapshot = _user_snapshot(user)

        self.assertEqual(snapshot["safe_to_spend_this_week"], "8000.00")
        self.assertEqual(snapshot["weekly_savings_still_to_protect"], "1500.00")
        self.assertIn("Future bills are not included", snapshot["safe_to_spend_basis"])
        self.assertNotIn("Daily cash", str(snapshot))
        self.assertNotIn("Savings reserve", str(snapshot))
