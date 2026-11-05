import json
from datetime import timedelta
from decimal import Decimal

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from budgets.models import Budget
from expense_analyzer.models import ExpenseAnalysis
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

    def test_analyzer_is_a_read_only_workspace_for_activity_budgets_and_goals(self):
        self.create_expense()
        Budget.objects.create(
            owner=self.user, name="Food", category="Food", amount="5000.00",
            currency="XAF", period="weekly", start_date=self.today,
        )
        Goal.objects.create(
            owner=self.user, name="New laptop", target_amount="80000.00",
            current_amount="12000.00", currency="XAF", status="active",
            target_date=self.today + timedelta(days=90),
        )

        response = self.client.get(reverse("analyzer") + "?period=week")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "expense_analyzer/workspace.html")
        self.assertContains(response, "This week at a glance")
        self.assertContains(response, "Where your money went")
        self.assertContains(response, "Are your limits working?")
        self.assertContains(response, "Are your goals on track?")
        self.assertContains(response, "New laptop")
        self.assertFalse(ExpenseAnalysis.objects.exists())
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("10500.00"))

    def test_week_month_and_year_periods_are_supported(self):
        for period, label in [("week", "This week"), ("month", "This month"), ("year", "This year")]:
            response = self.client.get(reverse("analyzer"), {"period": period})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["activity"]["period_label"], label)

    def test_transaction_analysis_reads_only_the_members_expense(self):
        expense = self.create_expense(description="School lunch")
        response = self.client.get(reverse("analyzer"), {
            "scope": "transaction", "transaction_id": expense.pk,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A closer look at this expense")
        self.assertContains(response, "School lunch")
        self.assertEqual(response.context["transaction_analysis"]["currency"], "XAF")
        self.assertFalse(ExpenseAnalysis.objects.exists())

    def test_transaction_analysis_cannot_open_another_members_transaction(self):
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

        response = self.client.get(reverse("analyzer"), {
            "scope": "transaction", "transaction_id": foreign.pk,
        })

        self.assertEqual(response.status_code, 404)

    @override_settings(AI_PROVIDER="none", GEMINI_API_KEY="", AI_API_KEY="")
    def test_add_transaction_preview_is_read_only_and_returns_a_score(self):
        before = self.account.balance
        payload = {
            "kind": "expense", "amount": "2000", "category": "School",
            "description": "Notebooks", "is_essential": True,
        }
        response = async_to_sync(self.async_client.post)(
            reverse("analyzer_transaction_preview"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("score", response.json())
        self.assertIn("summary", response.json())
        self.assertFalse(ExpenseAnalysis.objects.exists())
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, before)

    @override_settings(AI_PROVIDER="none", GEMINI_API_KEY="", AI_API_KEY="")
    def test_add_transaction_preview_rejects_income(self):
        payload = {"kind": "income", "amount": "2000", "category": "Allowance"}
        response = async_to_sync(self.async_client.post)(
            reverse("analyzer_transaction_preview"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("expenses", response.json()["error"])

    def test_budget_and_goal_focus_links_are_owner_scoped(self):
        budget = Budget.objects.create(
            owner=self.user, name="Transport", category="Transport",
            amount="3000.00", currency="XAF", period="weekly",
        )
        goal = Goal.objects.create(
            owner=self.user, name="Laptop", target_amount="60000.00",
            current_amount="10000.00", currency="XAF", status="active",
        )
        budget_response = self.client.get(reverse("analyzer"), {
            "scope": "budget", "budget_id": budget.pk,
        })
        goal_response = self.client.get(reverse("analyzer"), {
            "scope": "goal", "goal_id": goal.pk,
        })
        self.assertEqual(budget_response.status_code, 200)
        self.assertEqual(budget_response.context["selected_budget"]["id"], budget.pk)
        self.assertEqual(goal_response.status_code, 200)
        self.assertEqual(goal_response.context["selected_goal"]["id"], goal.pk)


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
            self.user, amount="1500.00", category="School",
            description="Notebooks",
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
