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
    def progress_percentage(self):
        if self.target_amount <= 0:
            return 100 if self.status == "completed" else 0
        return min(100, int((self.current_amount / self.target_amount) * 100))

    @property
    def remaining_amount(self):
        return max(self.target_amount - self.current_amount, Decimal("0.00"))

    def __str__(self):
        return self.name