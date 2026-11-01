from decimal import Decimal
import csv
from io import StringIO
import json
import uuid

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

    def test_transaction_form_uses_the_refreshed_amount_first_layout(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("transaction_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "finance/transaction_form.html")
        for marker in (
            "transaction-refresh-page",
            "transaction-amount-panel",
            "data-transaction-amount",
            "data-transaction-category",
            "Save transaction",
        ):
            with self.subTest(marker=marker):
                self.assertContains(response, marker)


    def test_offline_sync_is_idempotent_and_updates_the_account_once(self):
        self.client.force_login(self.user)
        entry_id = str(uuid.uuid4())
        payload = {
            "items": [{
                "id": entry_id,
                "kind": "expense",
                "account_id": self.account.pk,
                "amount": "1200.00",
                "currency": "XAF",
                "category": "Food",
                "description": "Lunch",
                "transaction_date": "2026-11-01",
            }]
        }

        first = self.client.post(
            reverse("offline_sync"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["results"][0]["status"], "synced")
        self.assertEqual(Transaction.objects.filter(offline_id=entry_id).count(), 1)

        second = self.client.post(
            reverse("offline_sync"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json()["results"][0]["duplicate"])
        self.assertEqual(Transaction.objects.filter(offline_id=entry_id).count(), 1)

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("3800.00"))

    def test_offline_sync_rejects_transfer_entries(self):
        self.client.force_login(self.user)
        payload = {
            "items": [{
                "id": str(uuid.uuid4()),
                "kind": "transfer_out",
                "account_id": self.account.pk,
                "amount": "500.00",
                "currency": "XAF",
                "transaction_date": "2026-11-01",
            }]
        }
        response = self.client.post(
            reverse("offline_sync"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["status"], "rejected")
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("5000.00"))


    def test_transaction_csv_export_is_authenticated_and_scoped_to_the_current_user(self):
        other = User.objects.create_user(username="bob", email="bob@example.com", password="StrongPass123!")
        other_account = Account.objects.create(owner=other, name="Private wallet")
        Transaction.objects.create(
            owner=self.user,
            account=self.account,
            kind="expense",
            amount=Decimal("1250.50"),
            currency="XAF",
            description="Lunch",
            category="Food",
            transaction_date="2026-11-01",
        )
        Transaction.objects.create(
            owner=other,
            account=other_account,
            kind="income",
            amount=Decimal("99999.00"),
            currency="XAF",
            description="Private income",
            transaction_date="2026-11-01",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("transaction_export"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Disposition"].startswith("attachment;"))
        self.assertEqual(response["Cache-Control"], "private, no-store, max-age=0")
        rows = list(csv.reader(StringIO(response.content.decode("utf-8-sig"))))
        self.assertEqual(rows[0], [
            "Date", "Description", "Merchant", "Type", "Category",
            "Account", "Amount", "Currency",
        ])
        self.assertEqual(len(rows), 2)
        self.assertIn("Lunch", rows[1])
        self.assertNotIn("Private income", response.content.decode("utf-8-sig"))

    def test_transaction_csv_export_never_allows_spreadsheet_formulas_in_text(self):
        Transaction.objects.create(
            owner=self.user,
            account=self.account,
            kind="expense",
            amount=Decimal("100"),
            currency="XAF",
            description="=HYPERLINK(\"https://example.invalid\",\"click\")",
            category="Food",
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("transaction_export"))
        rows = list(csv.reader(StringIO(response.content.decode("utf-8-sig"))))
        self.assertEqual(rows[1][1], "'=HYPERLINK(\"https://example.invalid\",\"click\")")

    def test_transaction_csv_export_requires_login(self):
        response = self.client.get(reverse("transaction_export"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])
