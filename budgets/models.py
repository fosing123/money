from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Budget(models.Model):
    PERIOD_CHOICES = [("weekly", "Weekly"), ("monthly", "Monthly"), ("yearly", "Yearly")]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    name = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=10, default="XAF")
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default="monthly")
    category = models.CharField(max_length=50, blank=True, default="")
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def _current_window(self):
        today = timezone.localdate()
        if self.period == "weekly":
            start = today - timedelta(days=today.weekday())
        elif self.period == "monthly":
            start = today.replace(day=1)
        elif self.period == "yearly":
            start = today.replace(month=1, day=1)
        else:
            start = self.start_date
        # A budget means "this week/month/year" even if it was created today.
        # End date remains available for intentionally closing a budget window.
        end = min(self.end_date, today) if self.end_date else today
        return start, end

    @property
    def spent_amount(self):
        from finance.models import Transaction
        start, end = self._current_window()
        if end < start:
            return Decimal("0.00")
        qs = Transaction.objects.filter(
            owner=self.owner,
            kind="expense",
            currency=self.currency,
            transaction_date__range=(start, end),
        )
        if self.category:
            qs = qs.filter(category__iexact=self.category.strip())
        return sum((item.amount for item in qs), Decimal("0.00"))

    @property
    def remaining_amount(self):
        return max(self.amount - self.spent_amount, Decimal("0.00"))

    @property
    def percent_used(self):
        if self.amount <= 0:
            return 0
        return float(self.spent_amount / self.amount * 100)

    def __str__(self):
        return f"{self.name} ({self.amount} {self.currency})"