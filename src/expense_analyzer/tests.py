import json
from unittest.mock import patch
from datetime import date, timedelta
from decimal import Decimal

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from budgets.models import Budget
from ai_assistant.services import AIUsageLimitError
from expense_analyzer.ai import _parse_response, _system_instruction
from expense_analyzer.models import AIPersonalization, ExpenseAnalysis
from expense_analyzer.scoring import analyze_completed_expense, analyze_planned_purchase
from finance.models import Account, Transaction
from goals.models import Goal
from expense_analyzer.views import _fallback_insights
from expense_analyzer.workspace import _activity_analysis


User = get_user_model()


class ExpenseAnalyzerWorkspaceTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.user = User.objects.create_user(
            username="analysis-member",
            email="analysis-member@example.com",
            password="StrongPass123!",
            currency="XAF",
            weekly_savings_target="2000.00",
            onboarding_completed=True,
        )
        self.account = Account.objects.create(
            owner=self.user, name="Daily cash", account_type="cash",
            currency="XAF", opening_balance="12000.00", balance="12000.00",
        )
        self.client.force_login(self.user)

    def create_personalization(self, **kwargs):
        defaults = {
            "voice_style": "friendly",
            "ambition": "financial_freedom",
            "current_stage": "student",
            "future_vision": "Build a successful business and help my family.",
            "desired_career": "Software developer",
            "why_it_matters": "I want to create more opportunities.",
            "setup_completed": True,
        }
        defaults.update(kwargs)
        return AIPersonalization.objects.create(user=self.user, **defaults)

    def create_expense(self, amount="1500.00", category="Food", description="Lunch", currency="XAF"):
        account = self.account
        if currency != account.currency:
            account = Account.objects.create(
                owner=self.user, name="Other currency", account_type="cash",
                currency=currency, opening_balance="100.00", balance="100.00",
            )
        return Transaction.objects.create(
            owner=self.user, account=account, amount=amount, currency=currency,
            kind="expense", category=category, description=description,
            transaction_date=self.today,
        )

    def post_json(self, url_name, payload):
        return self.client.post(
            reverse(url_name),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_analyzer_page_is_a_choice_centre_not_a_long_report_page(self):
        self.create_expense(description="School lunch")
        response = self.client.get(reverse("analyzer"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "expense_analyzer/analyzer.html")
        self.assertContains(response, "What would you like to understand?")
        self.assertContains(response, "My spending & activity")
        self.assertContains(response, "My budgets")
        self.assertContains(response, "My savings goals")
        self.assertContains(response, "Personalise TIANA")
        self.assertContains(response, "School lunch")
        self.assertNotContains(response, "This week at a glance")

    def test_day_week_month_year_and_custom_periods_are_supported_in_the_choice_centre(self):
        for period in ["day", "week", "month", "year"]:
            response = self.client.get(reverse("analyzer"), {"period": period})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["period"], period)
        start = self.today - timedelta(days=4)
        response = self.client.get(reverse("analyzer"), {
            "period": "custom", "start_date": start.isoformat(), "end_date": self.today.isoformat(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["period"], "custom")
        self.assertEqual(response.context["selected_start_date"], start)
        self.assertContains(response, 'data-centre-period="custom"')

    def test_daily_analysis_uses_today_only_not_the_whole_week(self):
        self.create_expense(amount="900.00", description="Today lunch")
        yesterday = self.today - timedelta(days=1)
        Transaction.objects.create(
            owner=self.user, account=self.account, amount="1500.00", currency="XAF",
            kind="expense", category="Food", description="Yesterday lunch",
            transaction_date=yesterday,
        )
        activity = _activity_analysis(self.user, "day", self.today)
        self.assertEqual(activity["start_date"], self.today)
        self.assertEqual(activity["end_date"], self.today)
        self.assertEqual(activity["expenses"], Decimal("900.00"))
        self.assertEqual(activity["expense_count"], 1)

    def test_custom_analysis_includes_only_the_selected_date_window(self):
        start = self.today - timedelta(days=2)
        Transaction.objects.create(
            owner=self.user, account=self.account, amount="1200.00", currency="XAF",
            kind="expense", category="Food", description="Inside range",
            transaction_date=start,
        )
        Transaction.objects.create(
            owner=self.user, account=self.account, amount="600.00", currency="XAF",
            kind="expense", category="Food", description="Outside range",
            transaction_date=start - timedelta(days=1),
        )
        activity = _activity_analysis(self.user, "custom", self.today, start_date=start, end_date=start)
        self.assertEqual(activity["start_date"], start)
        self.assertEqual(activity["end_date"], start)
        self.assertEqual(activity["expenses"], Decimal("1200.00"))

    def test_custom_analysis_rejects_future_dates_and_ranges_over_one_year(self):
        with self.assertRaises(ValueError):
            _activity_analysis(self.user, "custom", self.today, start_date=self.today, end_date=self.today + timedelta(days=1))
        with self.assertRaises(ValueError):
            _activity_analysis(self.user, "custom", self.today, start_date=self.today - timedelta(days=366), end_date=self.today)

    def test_activity_has_one_period_analysis_action_not_a_button_on_every_expense(self):
        self.create_expense(description="School lunch")
        response = self.client.get(reverse("transactions"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-analysis-scope="activity"')
        self.assertNotContains(response, "Analyze this expense")

    def test_analyzer_insight_requires_personalisation_on_first_use(self):
        response = self.post_json("analyzer_insight", {"scope": "activity", "period": "week"})
        self.assertEqual(response.status_code, 409)
        self.assertTrue(response.json()["personalization_required"])

    @override_settings(AI_PROVIDER="none", GEMINI_API_KEY="", AI_API_KEY="")
    def test_custom_date_range_flows_through_to_analysis_results(self):
        self.create_personalization()
        start = self.today - timedelta(days=3)
        self.create_expense(amount="2400.00", description="Selected date expense")
        response = self.post_json("analyzer_insight", {
            "scope": "activity", "period": "custom",
            "start_date": start.isoformat(), "end_date": self.today.isoformat(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"]["subtitle"], f"{start:%d %b} – {self.today:%d %b %Y}")

    def test_custom_date_range_requires_both_valid_dates(self):
        self.create_personalization()
        response = self.post_json("analyzer_insight", {
            "scope": "activity", "period": "custom", "start_date": self.today.isoformat(),
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("start date and end date", response.json()["error"])

    @override_settings(AI_PROVIDER="none", GEMINI_API_KEY="", AI_API_KEY="")
    def test_transaction_analysis_opens_a_read_only_result_for_its_owner(self):
        self.create_personalization()
        expense = self.create_expense(description="School lunch")

        response = self.post_json("analyzer_insight", {
            "scope": "transaction", "object_id": expense.pk, "period": "week",
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["result"]["title"], "School lunch")
        self.assertGreaterEqual(payload["result"]["score"], 0)
        self.assertIn("insights", payload)
        self.assertFalse(ExpenseAnalysis.objects.exists())

    def test_transaction_analysis_cannot_open_another_members_transaction(self):
        self.create_personalization()
        other = User.objects.create_user(
            username="other-analysis-member", email="other-analysis@example.com",
            password="StrongPass123!", currency="XAF",
        )
        other_account = Account.objects.create(
            owner=other, name="Private cash", currency="XAF",
            opening_balance="7000.00", balance="7000.00",
        )
        foreign = Transaction.objects.create(
            owner=other, account=other_account, amount="500.00",
            currency="XAF", kind="expense", category="Food",
            transaction_date=self.today,
        )

        response = self.post_json("analyzer_insight", {
            "scope": "transaction", "object_id": foreign.pk, "period": "week",
        })

        self.assertEqual(response.status_code, 404)

    @override_settings(AI_PROVIDER="none", GEMINI_API_KEY="", AI_API_KEY="")
    def test_budget_and_goal_scopes_return_the_selected_record_in_the_modal_payload(self):
        self.create_personalization()
        budget = Budget.objects.create(
            owner=self.user, name="Transport", category="Transport",
            amount="3000.00", currency="XAF", period="weekly",
        )
        goal = Goal.objects.create(
            owner=self.user, name="Laptop", target_amount="60000.00",
            current_amount="10000.00", currency="XAF", status="active",
            target_date=self.today + timedelta(days=90),
        )

        budget_response = self.post_json("analyzer_insight", {
            "scope": "budget", "object_id": budget.pk, "period": "month",
        })
        goal_response = self.post_json("analyzer_insight", {
            "scope": "goal", "object_id": goal.pk, "period": "month",
        })

        self.assertEqual(budget_response.status_code, 200)
        self.assertEqual(budget_response.json()["result"]["title"], "Transport")
        self.assertEqual(goal_response.status_code, 200)
        self.assertEqual(goal_response.json()["result"]["title"], "Laptop")

    @override_settings(AI_PROVIDER="none", GEMINI_API_KEY="", AI_API_KEY="")
    def test_all_budgets_and_goals_can_be_analyzed_without_a_selected_id(self):
        self.create_personalization()
        Budget.objects.create(
            owner=self.user, name="Food", category="Food", amount="5000.00",
            currency="XAF", period="weekly",
        )
        Goal.objects.create(
            owner=self.user, name="Laptop", target_amount="60000.00",
            current_amount="10000.00", currency="XAF", status="active",
        )
        budget_response = self.post_json("analyzer_insight", {"scope": "budgets"})
        goal_response = self.post_json("analyzer_insight", {"scope": "goals"})

        self.assertEqual(budget_response.status_code, 200)
        self.assertEqual(budget_response.json()["result"]["scope"], "budgets")
        self.assertEqual(goal_response.status_code, 200)
        self.assertEqual(goal_response.json()["result"]["scope"], "goals")

    @override_settings(AI_PROVIDER="none", GEMINI_API_KEY="", AI_API_KEY="")
    def test_add_transaction_preview_is_read_only_and_returns_a_designed_result_payload(self):
        self.create_personalization()
        self.account.refresh_from_db()
        before = self.account.balance
        response = self.post_json("analyzer_transaction_preview", {
            "kind": "expense", "amount": "2000", "category": "School",
            "description": "Notebooks", "is_essential": True,
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("score", response.json()["result"])
        self.assertIn("breakdown", response.json()["result"])
        self.assertIn("recommendations", response.json()["insights"])
        self.assertFalse(ExpenseAnalysis.objects.exists())
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, before)

    @override_settings(AI_PROVIDER="none", GEMINI_API_KEY="", AI_API_KEY="")
    def test_add_transaction_preview_rejects_income(self):
        self.create_personalization()
        response = self.post_json("analyzer_transaction_preview", {
            "kind": "income", "amount": "2000", "category": "Allowance",
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("expense", response.json()["error"])

    def test_personalization_is_saved_and_can_be_loaded_for_editing(self):
        payload = {
            "voice_style": "motherly",
            "ambition": "business_owner",
            "current_stage": "student",
            "future_vision": "Open a small technology company.",
            "desired_career": "Entrepreneur",
            "why_it_matters": "I want to support my family.",
        }
        response = self.post_json("analyzer_personalization", payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["saved"])
        self.assertEqual(response.json()["persona"]["voice_style"], "motherly")

        loaded = self.client.get(reverse("analyzer_personalization"))
        self.assertEqual(loaded.status_code, 200)
        self.assertEqual(loaded.json()["persona"]["ambition"], "business_owner")
        self.assertEqual(loaded.json()["persona"]["future_vision"], "Open a small technology company.")

    def test_personalization_validates_voice_choices(self):
        response = self.post_json("analyzer_personalization", {"voice_style": "robot"})
        self.assertEqual(response.status_code, 400)

    def test_selected_voice_changes_the_system_instruction(self):
        fatherly = _system_instruction({"voice_style": "fatherly", "future_vision": "Build a business."})
        motherly = _system_instruction({"voice_style": "motherly"})
        self.assertIn("fatherly warmth", fatherly)
        self.assertIn("motherly warmth", motherly)
        self.assertIn("member_profile object", fatherly)
        self.assertNotIn("Build a business.", fatherly)

    def test_gemini_reasoning_is_exposed_to_the_observations_component(self):
        model_result = {
            "summary": "You spent more on Food this week.",
            "reasoning": ["Food is the largest category.", "Your transport budget has room."],
            "recommendations": ["Review your next Food purchase."],
            "alternatives": [],
            "goal_suggestions": [],
            "encouragement": "Small steps add up.",
        }
        body = json.dumps({"candidates": [{"content": {"parts": [{"text": json.dumps(model_result)}]}}]})
        insights = _parse_response(body)
        self.assertEqual(insights["observations"], model_result["reasoning"])
        self.assertEqual(insights["reasoning"], model_result["reasoning"])

    def test_daily_free_ai_limit_blocks_gemini_and_returns_a_premium_path(self):
        self.create_personalization()
        with patch(
            "expense_analyzer.views._reserve_ai_request",
            side_effect=AIUsageLimitError("You've used today's 3 free TIANA AI requests."),
        ), patch("expense_analyzer.views.generate_money_insights") as generate:
            response = self.post_json("analyzer_insight", {
                "scope": "activity", "period": "week",
            })

        self.assertEqual(response.status_code, 429)
        self.assertTrue(response.json()["upgrade_required"])
        self.assertEqual(response.json()["upgrade_url"], "/premium/")
        self.assertEqual(response["Cache-Control"], "private, no-store, max-age=0")
        generate.assert_not_called()

    def test_ai_fallback_uses_period_totals_and_the_actual_top_category(self):
        result = {
            "scope": "activity",
            "period_label": "This week",
            "metrics": [
                {"label": "Money in", "value": "10,000 XAF"},
                {"label": "Money out", "value": "5,000 XAF"},
                {"label": "Net flow", "value": "+5,000 XAF"},
            ],
            "categories": [{"name": "Food", "value": "3,000 XAF", "percent": 60}],
            "rows": [{"title": "School lunch", "value": "1,500 XAF"}],
            "notes": ["You spent 8% less than in the previous period."],
            "deterministic_recommendations": [],
        }
        result = _fallback_insights(result, {"future_vision": "Build a small business."})
        self.assertIn("10,000 XAF", result["summary"])
        self.assertIn("Food", result["summary"])
        self.assertIn("60%", result["observations"][0])
        self.assertTrue(result["recommendations"])


class ExpenseAnalyzerScoringTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.user = User.objects.create_user(
            username="analyzer-score-member",
            email="analyzer-score@example.com",
            password="StrongPass123!",
            currency="XAF",
            weekly_savings_target="2000.00",
        )
        self.account = Account.objects.create(
            owner=self.user, name="Cash", account_type="cash", currency="XAF",
            opening_balance="10000.00", balance="10000.00",
        )

    def test_planned_purchase_can_be_saved_as_a_report(self):
        report = analyze_planned_purchase(
            self.user, amount="1500.00", category="School", description="Notebooks",
        )
        self.assertIsInstance(report, ExpenseAnalysis)
        self.assertEqual(report.analysis_type, ExpenseAnalysis.PLANNED)
        self.assertGreaterEqual(report.score, 0)
        self.assertLessEqual(report.score, 100)

    def test_planned_purchase_preview_does_not_create_a_report(self):
        report = analyze_planned_purchase(
            self.user, amount="1500.00", category="School",
            description="Notebooks", persist=False,
        )
        self.assertIsInstance(report, dict)
        self.assertIn("score", report)
        self.assertFalse(ExpenseAnalysis.objects.exists())

    def test_completed_expense_preview_does_not_change_the_ledger_or_save_a_report(self):
        expense = Transaction.objects.create(
            owner=self.user, account=self.account, amount="900.00",
            currency="XAF", kind="expense", category="Food",
            description="Lunch", transaction_date=self.today,
        )
        self.account.refresh_from_db()
        balance = self.account.balance
        report = analyze_completed_expense(self.user, expense, persist=False)

        self.assertEqual(report["amount"], Decimal("900.00"))
        self.assertGreaterEqual(report["score"], 0)
        self.assertFalse(ExpenseAnalysis.objects.exists())
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, balance)

    def test_completed_analysis_rejects_non_expense_transactions(self):
        income = Transaction.objects.create(
            owner=self.user, account=self.account, amount="1000.00",
            currency="XAF", kind="income", category="Allowance",
            transaction_date=self.today,
        )
        with self.assertRaises(ValueError):
            analyze_completed_expense(self.user, income, persist=False)

    def test_active_savings_goals_are_included_in_the_purchase_context(self):
        Goal.objects.create(
            owner=self.user, name="New laptop", target_amount="80000.00",
            current_amount="12000.00", currency="XAF", status="active",
            target_date=self.today + timedelta(days=90),
        )
        report = analyze_planned_purchase(
            self.user, amount="1000.00", category="Food", description="Lunch",
        )
        self.assertEqual(report.financial_context["active_goal_count"], 1)
        self.assertEqual(report.financial_context["active_goals"][0]["name"], "New laptop")
        self.assertEqual(report.financial_context["active_goals"][0]["remaining_amount"], "68000.00")
