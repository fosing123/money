from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    THEME_CHOICES = [
        ("violet", "Nkem violet"),
        ("mint", "Fresh mint"),
        ("ocean", "Calm ocean"),
        ("sunset", "Warm sunset"),
        ("midnight", "Midnight"),
        ("custom", "My own palette"),
    ]
    WEEKDAYS = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
        (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
    ]

    email = models.EmailField(unique=True)
    currency = models.CharField(max_length=10, default="XAF")
    timezone = models.CharField(max_length=64, default="Africa/Douala")
    phone_number = models.CharField(max_length=20, blank=True, default="")
    is_verified = models.BooleanField(default=False)
    theme = models.CharField(max_length=16, choices=THEME_CHOICES, default="violet")
    custom_palette = models.JSONField(default=dict, blank=True)
    onboarding_completed = models.BooleanField(default=False)
    weekly_income = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    weekly_savings_target = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    payday_weekday = models.PositiveSmallIntegerField(choices=WEEKDAYS, null=True, blank=True)
    financial_priorities = models.JSONField(default=list, blank=True)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.get_full_name() or self.username
