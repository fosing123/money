from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from expense_analyzer.models import ExpenseAnalysis
from finance.models import Account, Transaction


User = get_user_model()


class ExpenseAnalyzerAccessTests(TestCase):
    def test_analyzer_requires_authentication(self):
        response = self.client.get(reverse("analyzer"))
        self.assertEqual(response.status_code, 302)

    def test_analyzer_page_offers_both_analysis_modes(self):
        user = User.objects.create_user(
            username="analyzer-page",
            email="analyzer-page@example.com",
            password="StrongPass123!",
            onboarding_completed=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("analyzer"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planned purchase")
        self.assertContains(response, "Completed expense")
        self.assertContains(response, "Expense Analyzer")


class ExpenseAnalyzerScoringTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.user = User.objects.create_user(
            username="analyzer-member",
            email="analyzer-member@example.com",
            password="StrongPass123!",
            currency="XAF",
            weekly_savings_target="2000.00",
            onboarding_completed=True,
        )
        self.account = Account.objects.create(
            owner=self.user,
            name="Daily cash",
            account_type="cash",
            currency="XAF",
            opening_balance="10000.00",
            balance="10000.00",
        )
        self.client.force_login(self.user)

    def test_planned_purchase_is_scored_and_saved_without_changing_balance(self):
        response = self.client.post(
            reverse("analyzer"),
            {
                "action": "planned",
                "description": "School shoes",
                "amount": "1500.00",
                "category": "Shopping",
                "purchase_date": self.today.isoformat(),
                "is_essential": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        report = ExpenseAnalysis.objects.get(user=self.user, analysis_type="PLANNED")
        self.account.refresh_from_db()
        self.assertGreaterEqual(report.score, 0)
        self.assertLessEqual(report.score, 100)
        self.assertEqual(report.currency, "XAF")
        self.assertIsNone(report.transaction_id)
        self.assertEqual(self.account.balance, Decimal("10000.00"))
        self.assertContains(response, "School shoes")

    def test_completed_analysis_is_linked_to_only_the_members_expense(self):
        expense = Transaction.objects.create(
            owner=self.user,
            account=self.account,
            amount="1200.00",
            currency="XAF",
            kind="expense",
            category="Food",
            description="Lunch",
            transaction_date=self.today,
        )

        response = self.client.post(
            reverse("analyzer"),
            {
                "action": "completed",
                "transaction": str(expense.pk),
                "is_essential": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        report = ExpenseAnalysis.objects.get(user=self.user, analysis_type="COMPLETED")
        self.assertEqual(report.transaction_id, expense.pk)
        self.assertEqual(report.amount, Decimal("1200.00"))
        self.assertEqual(report.score, sum(
            item["points"] for item in report.score_breakdown.values()
        ))
        self.assertContains(response, "Lunch")

    def test_completed_analysis_cannot_select_another_users_transaction(self):
        other = User.objects.create_user(
            username="other-analyzer",
            email="other-analyzer@example.com",
            password="StrongPass123!",
            currency="XAF",
        )
        other_account = Account.objects.create(
            owner=other,
            name="Other cash",
            account_type="cash",
            currency="XAF",
            opening_balance="5000.00",
            balance="5000.00",
        )
        foreign_expense = Transaction.objects.create(
            owner=other,
            account=other_account,
            amount="500.00",
            currency="XAF",
            kind="expense",
            category="Food",
            transaction_date=self.today,
        )

        response = self.client.post(
            reverse("analyzer"),
            {"action": "completed", "transaction": str(foreign_expense.pk)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ExpenseAnalysis.objects.filter(user=self.user).exists())
        self.assertContains(response, "Select a valid choice")

    def test_completed_analysis_rejects_non_expense_transactions(self):
        income = Transaction.objects.create(
            owner=self.user,
            account=self.account,
            amount="1000.00",
            currency="XAF",
            kind="income",
            category="Allowance",
            transaction_date=self.today,
        )

        from expense_analyzer.scoring import analyze_completed_expense
        with self.assertRaises(ValueError):
            analyze_completed_expense(self.user, income)
