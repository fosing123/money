from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finance.models import Account, Transaction
from goals.models import Goal, GoalContribution

User = get_user_model()


class GoalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="goalie",
            email="goalie@example.com",
            password="StrongPass123!",
        )
        self.account = Account.objects.create(
            owner=self.user,
            name="Daily money",
            account_type="cash",
            currency="XAF",
            opening_balance=Decimal("5000.00"),
            balance=Decimal("5000.00"),
        )
        self.goal = Goal.objects.create(
            owner=self.user,
            name="School laptop",
            target_amount=Decimal("50000.00"),
            current_amount=Decimal("20000.00"),
            currency="XAF",
        )
        self.client.force_login(self.user)

    def test_goal_progress_percentage_uses_initial_saved_amount(self):
        self.assertEqual(self.goal.progress_percentage, 40)

    def test_goal_top_up_debits_account_and_increases_goal_progress(self):
        response = self.client.post(
            reverse("goal_contribute", kwargs={"pk": self.goal.pk}),
            {
                "amount": "1000",
                "account": str(self.account.pk),
                "note": "This week's savings",
            },
        )

        self.assertRedirects(response, reverse("goals"))
        self.goal.refresh_from_db()
        self.account.refresh_from_db()

        self.assertEqual(self.goal.saved_amount, Decimal("21000.00"))
        self.assertEqual(self.goal.progress_percentage, 42)
        self.assertEqual(self.goal.remaining_amount, Decimal("29000.00"))
        self.assertEqual(self.account.balance, Decimal("4000.00"))

        contribution = GoalContribution.objects.get(goal=self.goal, owner=self.user)
        self.assertEqual(contribution.transaction.kind, "transfer_out")
        self.assertEqual(contribution.transaction.amount, Decimal("1000.00"))
        self.assertEqual(contribution.transaction.category, "Savings")
        self.assertEqual(contribution.note, "This week's savings")

    def test_goal_top_up_cannot_exceed_available_account_balance(self):
        response = self.client.post(
            reverse("goal_contribute", kwargs={"pk": self.goal.pk}),
            {"amount": "6000", "account": str(self.account.pk), "note": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "only has")
        self.assertEqual(GoalContribution.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("5000.00"))

    def test_goal_top_up_cannot_exceed_remaining_target(self):
        response = self.client.post(
            reverse("goal_contribute", kwargs={"pk": self.goal.pk}),
            {"amount": "31000", "account": str(self.account.pk), "note": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "only need")
        self.assertEqual(GoalContribution.objects.count(), 0)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("5000.00"))

    def test_user_cannot_add_money_to_another_users_goal(self):
        other = User.objects.create_user(
            username="another",
            email="another@example.com",
            password="StrongPass123!",
        )
        other_goal = Goal.objects.create(
            owner=other,
            name="Private goal",
            target_amount=Decimal("10000.00"),
            currency="XAF",
        )
        response = self.client.get(reverse("goal_contribute", kwargs={"pk": other_goal.pk}))
        self.assertEqual(response.status_code, 404)

    def test_filling_goal_marks_it_completed(self):
        goal = Goal.objects.create(
            owner=self.user,
            name="Exam fees",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("500.00"),
            currency="XAF",
        )
        response = self.client.post(
            reverse("goal_contribute", kwargs={"pk": goal.pk}),
            {"amount": "500", "account": str(self.account.pk), "note": ""},
        )
        self.assertRedirects(response, reverse("goals"))
        goal.refresh_from_db()
        self.assertEqual(goal.saved_amount, Decimal("1000.00"))
        self.assertEqual(goal.status, "completed")

    def test_deleting_a_goal_top_up_reverses_the_goal_and_account(self):
        self.client.post(
            reverse("goal_contribute", kwargs={"pk": self.goal.pk}),
            {"amount": "1000", "account": str(self.account.pk), "note": ""},
        )
        transaction = Transaction.objects.get(owner=self.user, kind="transfer_out")
        response = self.client.post(reverse("transaction_delete", kwargs={"pk": transaction.pk}))

        self.assertRedirects(response, reverse("transactions"))
        self.goal.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(self.goal.saved_amount, Decimal("20000.00"))
        self.assertEqual(self.goal.status, "active")
        self.assertEqual(self.account.balance, Decimal("5000.00"))
        self.assertEqual(GoalContribution.objects.count(), 0)


    def test_deleting_goal_reverses_linked_topups_and_removes_goal(self):
        contribution_response = self.client.post(
            reverse("goal_contribute", kwargs={"pk": self.goal.pk}),
            {"amount": "1000", "account": str(self.account.pk), "note": "Goal top-up"},
        )
        self.assertRedirects(contribution_response, reverse("goals"))
        transfer = Transaction.objects.get(owner=self.user, kind="transfer_out")

        confirm = self.client.get(reverse("goal_delete", kwargs={"pk": self.goal.pk}))
        self.assertEqual(confirm.status_code, 200)
        self.assertContains(confirm, "top-up")

        response = self.client.post(reverse("goal_delete", kwargs={"pk": self.goal.pk}))
        self.assertRedirects(response, reverse("goals"))
        self.assertFalse(Goal.objects.filter(pk=self.goal.pk).exists())
        self.assertFalse(GoalContribution.objects.exists())
        self.assertFalse(Transaction.objects.filter(pk=transfer.pk).exists())

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("5000.00"))

    def test_user_cannot_delete_another_users_goal(self):
        other = User.objects.create_user(
            username="goaldeleteother",
            email="goaldeleteother@example.com",
            password="StrongPass123!",
        )
        other_goal = Goal.objects.create(
            owner=other,
            name="Private goal",
            target_amount=Decimal("12000"),
            currency="XAF",
        )
        self.assertEqual(
            self.client.get(reverse("goal_delete", kwargs={"pk": other_goal.pk})).status_code,
            404,
        )
