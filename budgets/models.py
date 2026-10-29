from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Budget(models.Model):
    PERIOD_CHOICES = [('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=10, default='XAF')
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='monthly')
    category = models.CharField(max_length=50, blank=True, default='')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def spent_amount(self):
        from finance.models import Transaction

        qs = self.owner.transactions.filter(kind='expense', currency=self.currency)
        if self.category:
            qs = qs.filter(category=self.category)
        if self.start_date and self.end_date:
            qs = qs.filter(transaction_date__range=[self.start_date, self.end_date])
        total = sum((item.amount for item in qs), Decimal('0.00'))
        return total

    @property
    def remaining_amount(self):
        return self.amount - self.spent_amount

    @property
    def percent_used(self):
        if self.amount == 0:
            return 0
        return float((self.spent_amount / self.amount) * 100)

    def __str__(self):
        return f'{self.name} ({self.amount} {self.currency})'
