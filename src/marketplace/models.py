from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.validators import validate_uploaded_image


class Opportunity(models.Model):
    KIND_CHOICES = [("service", "Service"), ("product", "Product"), ("job", "Gig or opportunity"), ("event", "Student event")]
    name = models.CharField(max_length=140)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="service")
    category = models.CharField(max_length=60, default="General")
    description = models.TextField()
    price_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    currency = models.CharField(max_length=10, default="XAF")
    location = models.CharField(max_length=120, default="Bafoussam")
    seller_name = models.CharField(max_length=120, blank=True)
    image = models.ImageField(upload_to="tiana/opportunities/%Y/%m/", blank=True, null=True, validators=[validate_uploaded_image])
    contact_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "-published_at", "name"]
        indexes = [
            models.Index(fields=["is_active", "kind", "published_at"], name="marketplace_is_act_2e3a8e_idx"),
            models.Index(fields=["is_active", "category"], name="marketplace_is_act_4c6b8a_idx"),
        ]

    def __str__(self):
        return self.name