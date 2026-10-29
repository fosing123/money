from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from finance.models import Account, Transaction

User = get_user_model()


class FinanceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="StrongPass123!")
        self.account = Account.objects.create(owner=self.user, name="Wallet", currency="XAF", opening_balance=Decimal("5000"), balance=Decimal("5000"))

    def test_income_increases_opening_balance(self):
        Transaction.objects.create(owner=self.user, account=self.account, kind="income", amount="25000", currency="XAF", description="salary", transaction_date="2026-10-01")
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("30000"))

    def test_edit_and_delete_recalculate_balance(self):
        item = Transaction.objects.create(owner=self.user, account=self.account, kind="income", amount="25000", currency="XAF", transaction_date="2026-10-01")
        item.amount = Decimal("12000")
        item.save()
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("17000"))
        item.delete()
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("5000"))

    def test_expense_reduces_balance(self):
        Transaction.objects.create(owner=self.user, account=self.account, kind="expense", amount="300", currency="XAF")
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("4700"))

    def test_transaction_cannot_use_another_users_account(self):
        other = User.objects.create_user(username="bob", email="bob@example.com", password="StrongPass123!")
        other_account = Account.objects.create(owner=other, name="Private wallet")
        item = Transaction(owner=self.user, account=other_account, kind="income", amount=100)
        with self.assertRaises(ValidationError):
            item.save()

    def test_member_cannot_edit_another_users_transaction(self):
        other = User.objects.create_user(username="bob", email="bob@example.com", password="StrongPass123!")
        other_account = Account.objects.create(owner=other, name="Private wallet")
        item = Transaction.objects.create(owner=other, account=other_account, kind="income", amount=100)
        self.client.force_login(self.user)
        response = self.client.get(reverse("transaction_update", args=[item.pk]))
        self.assertEqual(response.status_code, 404)