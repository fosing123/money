from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Account(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=[('cash', 'Cash'), ('bank', 'Bank'), ('savings', 'Savings'), ('card', 'Card')], default='cash')
    currency = models.CharField(max_length=10, default='XAF')
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.currency})'


class Transaction(models.Model):
    KIND_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer_in', 'Transfer in'),
        ('transfer_out', 'Transfer out'),
        ('refund', 'Refund'),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey('finance.Account', on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=10, default='XAF')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='expense')
    category = models.CharField(max_length=50, default='General')
    description = models.CharField(max_length=255, blank=True)
    merchant = models.CharField(max_length=120, blank=True)
    transaction_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transaction_date', '-created_at']

    @property
    def signed_amount(self):
        amount = Decimal(str(self.amount))
        if self.kind in {'income', 'refund', 'transfer_in'}:
            return amount
        if self.kind in {'expense', 'transfer_out'}:
            return -amount
        return Decimal('0.00')

    def save(self, *args, **kwargs):
        self.amount = Decimal(str(self.amount))
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.account.balance = (self.account.balance or Decimal('0.00')) + self.signed_amount
            self.account.save(update_fields=['balance', 'updated_at'])

    def __str__(self):
        return f'{self.kind}: {self.amount} {self.currency}'
