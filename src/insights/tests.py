from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from finance.models import Account, Transaction


class InsightsViewTests(TestCase):
    def test_insights_page_uses_the_live_money_snapshot(self):
        user = User.objects.create_user(
            username="insightuser",
            email="insightuser@example.com",
            password="secret123",
            currency="XAF",
            weekly_income=Decimal("125000"),
            weekly_savings_target=Decimal("30000"),
            payday_weekday=4,
            onboarding_completed=True,
        )
        account = Account.objects.create(owner=user, name="Cash", currency="XAF", balance=Decimal("200000"), account_type="cash")
        Transaction.objects.create(
            owner=user,
            account=account,
            kind="income",
            amount=Decimal("150000"),
            currency="XAF",
            category="Salary",
            transaction_date="2026-11-05",
        )
        Transaction.objects.create(
            owner=user,
            account=account,
            kind="expense",
            amount=Decimal("60000"),
            currency="XAF",
            category="Food",
            transaction_date="2026-11-05",
        )

        self.client.force_login(user)
        response = self.client.get(reverse("insights"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Money insights")
        self.assertContains(response, "Safe to spend")
        self.assertContains(response, "Next income")
        self.assertContains(response, "Runway")
        self.assertContains(response, "Forecast pulse")
