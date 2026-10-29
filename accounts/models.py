from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    currency = models.CharField(max_length=10, default='XAF')
    timezone = models.CharField(max_length=64, default='Africa/Douala')
    phone_number = models.CharField(max_length=20, blank=True, default='')
    is_verified = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.get_full_name() or self.username
