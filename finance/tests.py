from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import TransactionForm
from .models import Account, Transaction

User = get_user_model()


class LedgerBalanceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="kams", email="kams@example.test", password="Saffron-Planet-2026!")
        self.account = Account.objects.create(owner=self.user, name="Cash", currency="XAF", opening_balance=Decimal("5000.00"), balance=Decimal("5000.00"))

    def test_create_update_delete_recalculate_balance_from_ledger(self):
        income = Transaction.objects.create(owner=self.user, account=self.account, amount=Decimal("10000.00"), kind="income", category="Allowance")
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("15000.00"))

        expense = Transaction.objects.create(owner=self.user, account=self.account, amount=Decimal("2000.00"), kind="expense", category="Food")
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("13000.00"))

        expense.amount = Decimal("3000.00")
        expense.save()
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("12000.00"))

        expense.delete()
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("15000.00"))

    def test_transaction_form_only_offers_accounts_owned_by_current_user(self):
        other = User.objects.create_user(username="other", email="other@example.test", password="Saffron-Planet-2026!")
        other_account = Account.objects.create(owner=other, name="Other cash")
        form = TransactionForm(user=self.user)
        self.assertIn(self.account, form.fields["account"].queryset)
        self.assertNotIn(other_account, form.fields["account"].queryset)

    def test_user_cannot_edit_another_users_transaction(self):
        other = User.objects.create_user(username="other2", email="other2@example.test", password="Saffron-Planet-2026!")
        other_account = Account.objects.create(owner=other, name="Other cash")
        item = Transaction.objects.create(owner=other, account=other_account, amount=Decimal("500.00"), kind="expense")
        self.client.force_login(self.user)
        response = self.client.get(reverse("transaction_update", args=[item.pk]))
        self.assertEqual(response.status_code, 404)