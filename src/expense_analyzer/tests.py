import json
from datetime import timedelta
from decimal import Decimal

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from budgets.models import Budget
from expense_analyzer.ai import _system_instruction
from expense_analyzer.models import AIPersonalization, ExpenseAnalysis
from expense_analyzer.scoring import analyze_completed_expense, analyze_planned_purchase
from finance.models import Account, Transaction
from goals.models import Goal


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
        return async_to_sync(self.async_client.post)(
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

    def test_week_month_and_year_periods_are_supported_in_the_choice_centre(self):
        for period in ["week", "month", "year"]:
            response = self.client.get(reverse("analyzer"), {"period": period})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["period"], period)

    def test_analyzer_insight_requires_personalisation_on_first_use(self):
        response = self.post_json("analyzer_insight", {"scope": "activity", "period": "week"})
        self.assertEqual(response.status_code, 409)
        self.assertTrue(response.json()["personalization_required"])

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

        loaded = async_to_sync(self.async_client.get)(reverse("analyzer_personalization"))
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
        self.assertIn("Build a business.", fatherly)


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
