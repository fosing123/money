from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction as db_transaction
from django.utils import timezone


class Account(models.Model):
    ACCOUNT_TYPES = [
        ("cash", "Cash"), ("mtn_momo", "MTN Mobile Money"),
        ("orange_money", "Orange Money"), ("bank", "Bank account"),
        ("savings", "Savings"), ("card", "Card"),
    ]
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default="cash")
    currency = models.CharField(max_length=10, default="XAF")
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def recalculate_balance(self):
        ledger_total = sum((item.signed_amount for item in self.transactions.all()), Decimal("0.00"))
        self.balance = Decimal(str(self.opening_balance or 0)) + ledger_total
        self.save(update_fields=["balance", "updated_at"])
        return self.balance

    def __str__(self):
        return f"{self.name} ({self.currency})"


class Transaction(models.Model):
    KIND_CHOICES = [
        ("income", "Income"), ("expense", "Expense"),
        ("transfer_in", "Transfer in"), ("transfer_out", "Transfer out"),
        ("refund", "Refund"),
    ]
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    currency = models.CharField(max_length=10, default="XAF")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="expense")
    category = models.CharField(max_length=50, default="General")
    description = models.CharField(max_length=255, blank=True)
    merchant = models.CharField(max_length=120, blank=True)
    transaction_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-transaction_date", "-created_at"]
        indexes = [
            models.Index(fields=["owner", "transaction_date"], name="finance_owner_date_idx"),
            models.Index(fields=["owner", "kind", "transaction_date"], name="finance_owner_kind_date_idx"),
        ]

    @staticmethod
    def amount_sign(kind, amount):
        value = Decimal(str(amount or 0))
        if kind in {"income", "refund", "transfer_in"}:
            return value
        if kind in {"expense", "transfer_out"}:
            return -value
        return Decimal("0.00")

    @property
    def signed_amount(self):
        return self.amount_sign(self.kind, self.amount)

    def save(self, *args, **kwargs):
        self.amount = Decimal(str(self.amount))
        with db_transaction.atomic():
            previous = Transaction.objects.select_for_update().filter(pk=self.pk).first() if self.pk else None
            account = Account.objects.select_for_update().filter(pk=self.account_id, owner_id=self.owner_id).first()
            if account is None:
                raise ValidationError({"account": "Choose an account that belongs to your own profile."})
            if self.amount <= 0:
                raise ValidationError({"amount": "Transaction amounts must be greater than zero."})
            super().save(*args, **kwargs)
            affected_ids = {self.account_id}
            if previous:
                affected_ids.add(previous.account_id)
            for account_id in affected_ids:
                account_to_update = Account.objects.select_for_update().filter(pk=account_id).first()
                if account_to_update:
                    account_to_update.recalculate_balance()

    def delete(self, *args, **kwargs):
        account_id = self.account_id
        with db_transaction.atomic():
            super().delete(*args, **kwargs)
            account = Account.objects.select_for_update().filter(pk=account_id).first()
            if account:
                account.recalculate_balance()

    def __str__(self):
        return f"{self.kind}: {self.amount} {self.currency}"