from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from budgets.models import Budget
from finance.models import Account, Transaction

User = get_user_model()


class BudgetTests(TestCase):
    def test_budget_remaining_amount_is_calculated(self):
        user = User.objects.create_user(username="budgeter", email="budgeter@example.com", password="StrongPass123!")
        account = Account.objects.create(owner=user, name="Cash", currency="XAF", balance=0)
        today = timezone.localdate()
        month_start = today.replace(day=1)
        Transaction.objects.create(
            owner=user,
            account=account,
            kind="expense",
            amount="6000",
            currency="XAF",
            description="Groceries",
            transaction_date=today,
        )
        budget = Budget.objects.create(
            owner=user,
            name="Food",
            amount="10000",
            currency="XAF",
            period="monthly",
            start_date=month_start,
        )
        self.assertEqual(budget.spent_amount, Decimal("6000"))
        self.assertEqual(budget.remaining_amount, Decimal("4000"))


    def test_system_spending_alerts_are_automatic_and_deduplicated(self):
        from notifications.models import Notification
        from notifications.services import evaluate_spending_alerts

        user = User.objects.create_user(
            username="alertuser",
            email="alertuser@example.com",
            password="StrongPass123!",
        )
        account = Account.objects.create(owner=user, name="Cash", currency="XAF", balance=0)
        today = timezone.localdate()
        budget = Budget.objects.create(
            owner=user,
            name="Food",
            category="Food",
            amount=Decimal("10000"),
            currency="XAF",
            period="weekly",
            start_date=today - timezone.timedelta(days=today.weekday()),
        )
        Transaction.objects.create(
            owner=user, account=account, kind="expense", amount="8500",
            currency="XAF", category="Food", transaction_date=today,
        )
        first = evaluate_spending_alerts(user)
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0].source, "system")
        self.assertEqual(first[0].kind, "warning")
        self.assertIn("85%", first[0].message)

        evaluate_spending_alerts(user)
        self.assertEqual(Notification.objects.filter(user=user, source="system").count(), 1)

        Transaction.objects.create(
            owner=user, account=account, kind="expense", amount="2000",
            currency="XAF", category="Food", transaction_date=today,
        )
        evaluate_spending_alerts(user)
        self.assertEqual(Notification.objects.filter(user=user, source="system").count(), 2)
        self.assertTrue(Notification.objects.filter(user=user, dedupe_key__endswith=":100").exists())


    def test_existing_user_can_update_weekly_category_allocations(self):
        user = User.objects.create_user(
            username="budgetplan",
            email="budgetplan@example.com",
            password="StrongPass123!",
            weekly_income=Decimal("10000"),
            weekly_savings_target=Decimal("2000"),
        )
        self.client.force_login(user)
        response = self.client.post("/budgets/allocations/", {
            "allocation_food": "3000",
            "allocation_transport": "1500",
            "allocation_internet": "1000",
            "allocation_school": "1000",
            "allocation_personal": "1000",
            "allocation_emergency": "500",
        })
        self.assertRedirects(response, "/budgets/")
        user.refresh_from_db()
        self.assertEqual(user.weekly_budget_allocations["food"], "3000")
        self.assertEqual(
            Budget.objects.get(owner=user, category="Food", period="weekly").amount,
            Decimal("3000"),
        )
        self.assertEqual(Budget.objects.filter(owner=user, category__gt="").count(), 6)


    def test_owner_can_delete_budget_and_clear_saved_allocation_and_alerts(self):
        from notifications.models import Notification

        user = User.objects.create_user(
            username="budgetdelete",
            email="budgetdelete@example.com",
            password="StrongPass123!",
            weekly_budget_allocations={"food": "3000"},
        )
        budget = Budget.objects.create(
            owner=user,
            name="Food",
            category="Food",
            amount=Decimal("3000"),
            currency="XAF",
            period="weekly",
        )
        Notification.objects.create(
            user=user,
            title="Food budget getting close",
            message="You have used 80%.",
            kind="warning",
            source="system",
            dedupe_key=f"budget:{budget.pk}:weekly:20261102:80",
        )
        self.client.force_login(user)

        confirm = self.client.get(f"/budgets/{budget.pk}/delete/")
        self.assertEqual(confirm.status_code, 200)
        response = self.client.post(f"/budgets/{budget.pk}/delete/")
        self.assertRedirects(response, "/budgets/")

        self.assertFalse(Budget.objects.filter(pk=budget.pk).exists())
        user.refresh_from_db()
        self.assertEqual(user.weekly_budget_allocations["food"], "0")
        self.assertFalse(Notification.objects.filter(user=user, dedupe_key__startswith=f"budget:{budget.pk}:").exists())

    def test_user_cannot_delete_another_users_budget(self):
        owner = User.objects.create_user(
            username="budgetowner",
            email="budgetowner@example.com",
            password="StrongPass123!",
        )
        other = User.objects.create_user(
            username="budgetother",
            email="budgetother@example.com",
            password="StrongPass123!",
        )
        budget = Budget.objects.create(owner=owner, name="Private", amount=1000)
        self.client.force_login(other)
        self.assertEqual(self.client.get(f"/budgets/{budget.pk}/delete/").status_code, 404)
