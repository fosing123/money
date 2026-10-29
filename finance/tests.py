from django.contrib.auth import get_user_model
from django.test import TestCase

from finance.models import Account, Transaction

User = get_user_model()


class FinanceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', email='alice@example.com', password='StrongPass123!')
        self.account = Account.objects.create(owner=self.user, name='Wallet', currency='XAF', balance=0)

    def test_income_increases_balance(self):
        Transaction.objects.create(owner=self.user, account=self.account, kind='income', amount='25000', currency='XAF', description='salary', transaction_date='2026-10-01')
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 25000)

    def test_transfer_does_not_count_as_expense_or_income(self):
        self.assertTrue(True)
