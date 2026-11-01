import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finance.models import Account, Transaction
from notifications.models import PushDevice


User = get_user_model()


class PushDeviceAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="StrongPass123!")
        self.client.force_login(self.user)

    def test_register_device_is_scoped_to_authenticated_user(self):
        token = "fcm-registration-token-" + ("x" * 40)
        response = self.client.post(reverse("push_register"), data=json.dumps({"token": token, "platform": "web", "device_id": "phone-1"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        device = PushDevice.objects.get(token=token)
        self.assertEqual(device.user, self.user)
        self.assertTrue(device.is_active)

    def test_unregister_cannot_revoke_another_users_device(self):
        other = User.objects.create_user(username="bob", email="bob@example.com", password="StrongPass123!")
        device = PushDevice.objects.create(user=other, token="other-token-" + ("z" * 40))
        response = self.client.post(reverse("push_unregister"), data=json.dumps({"token": device.token}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        device.refresh_from_db()
        self.assertTrue(device.is_active)


class AccountBackupAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="StrongPass123!")
        self.client.force_login(self.user)
        self.account = Account.objects.create(owner=self.user, name="Cash", account_type="cash", currency="XAF", opening_balance=Decimal("1000.00"))
        Transaction.objects.create(owner=self.user, account=self.account, amount=Decimal("250.00"), currency="XAF", kind="expense", category="Food", description="Lunch", transaction_date="2026-11-01")

    def test_export_is_private_and_has_portable_versioned_format(self):
        response = self.client.get(reverse("backup_export"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store, max-age=0")
        payload = json.loads(response.content)
        self.assertEqual(payload["format"], "tiana.account-backup")
        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["transactions"][0]["description"], "Lunch")

    def test_restore_is_additive_and_recalculates_finance_ledger(self):
        payload = json.loads(self.client.get(reverse("backup_export")).content)
        response = self.client.post(reverse("backup_restore"), data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Account.objects.filter(owner=self.user).count(), 2)
        self.assertEqual(Transaction.objects.filter(owner=self.user).count(), 2)

    def test_restore_rejects_unknown_format(self):
        response = self.client.post(reverse("backup_restore"), data=json.dumps({"format": "unknown", "version": 1}), content_type="application/json")
        self.assertEqual(response.status_code, 400)
