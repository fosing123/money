from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.validators import validate_uploaded_image


class Goal(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    target_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    current_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    currency = models.CharField(max_length=10, default="XAF")
    target_date = models.DateField(blank=True, null=True)
    image = models.ImageField(upload_to="tiana/goals/%Y/%m/", blank=True, null=True, validators=[validate_uploaded_image])
    status = models.CharField(max_length=20, choices=[("active", "Active"), ("completed", "Completed"), ("archived", "Archived")], default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "target_date", "-created_at"]

    @property
    def contributed_amount(self):
        return sum(
            (item.transaction.amount for item in self.contributions.all()),
            Decimal("0.00"),
        )

    @property
    def saved_amount(self):
        return Decimal(str(self.current_amount or 0)) + self.contributed_amount

    @property
    def progress_percentage(self):
        target = Decimal(str(self.target_amount or 0))
        current = self.saved_amount
        if target <= 0:
            return 100 if self.status == "completed" else 0
        return min(100, int((current / target) * 100))

    @property
    def remaining_amount(self):
        target = Decimal(str(self.target_amount or 0))
        current = self.saved_amount
        return max(target - current, Decimal("0.00"))

    def __str__(self):
        return self.name


class GoalContribution(models.Model):
    """A goal top-up paired with a real transfer out of the user's account."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="goal_contributions",
    )
    goal = models.ForeignKey(
        Goal,
        on_delete=models.PROTECT,
        related_name="contributions",
    )
    transaction = models.OneToOneField(
        "finance.Transaction",
        on_delete=models.PROTECT,
        related_name="goal_contribution",
    )
    note = models.CharField(max_length=160, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.goal_id and self.owner_id and self.goal.owner_id != self.owner_id:
            raise ValidationError({"goal": "This goal does not belong to this account."})
        if self.transaction_id and self.owner_id and self.transaction.owner_id != self.owner_id:
            raise ValidationError({"transaction": "This transaction does not belong to this account."})
        if self.transaction_id and self.transaction.kind != "transfer_out":
            raise ValidationError({"transaction": "A goal contribution must be recorded as a transfer out."})

    def __str__(self):
        return f"{self.goal.name} · {self.transaction.amount} {self.transaction.currency}"
