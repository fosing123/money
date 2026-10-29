from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from budgets.models import Budget
from finance.models import Account, Transaction

User = get_user_model()


class BudgetTests(TestCase):
    def test_budget_remaining_amount_is_calculated(self):
        user = User.objects.create_user(username='budgeter', email='budgeter@example.com', password='StrongPass123!')
        account = Account.objects.create(owner=user, name='Cash', currency='XAF', balance=0)
        Transaction.objects.create(owner=user, account=account, kind='expense', amount='6000', currency='XAF', description='Groceries', transaction_date='2026-10-10')
        budget = Budget.objects.create(owner=user, name='Food', amount='10000', currency='XAF', period='monthly')
        self.assertEqual(budget.spent_amount, Decimal('6000'))
        self.assertEqual(budget.remaining_amount, Decimal('4000'))
