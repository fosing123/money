from django.core.validators import RegexValidator
from django.db import models

from .validators import validate_uploaded_image


hex_colour = RegexValidator(regex=r"^#[0-9A-Fa-f]{6}$", message="Use a six-digit hex colour, for example #7757F6.")


class AppAppearance(models.Model):
    """Single, admin-managed brand and palette configuration for TIANA."""
    app_name = models.CharField(max_length=50, default="TIANA")
    tagline = models.CharField(max_length=120, default="Smart Money. Brighter You.")
    primary_color = models.CharField(max_length=7, default="#7757F6", validators=[hex_colour])
    dark_color = models.CharField(max_length=7, default="#392187", validators=[hex_colour])
    soft_color = models.CharField(max_length=7, default="#EFEAFF", validators=[hex_colour])
    background_color = models.CharField(max_length=7, default="#F7F6FC", validators=[hex_colour])
    text_color = models.CharField(max_length=7, default="#201A3A", validators=[hex_colour])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "App appearance"
        verbose_name_plural = "App appearance"

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.app_name} appearance"


class BrandAsset(models.Model):
    """Admin-managed image slots used by onboarding, dashboard and coach."""
    PLACEMENTS = [
        ("logo", "Brand logo"),
        ("onboarding_welcome", "Onboarding — welcome"),
        ("onboarding_control", "Onboarding — money control"),
        ("onboarding_goals", "Onboarding — goals"),
        ("onboarding_ai", "Onboarding — AI coach"),
        ("onboarding_account", "Onboarding — account creation"),
        ("dashboard_hero", "Dashboard — hero artwork"),
        ("coach_avatar", "AI coach — avatar"),
        ("marketplace_cover", "Marketplace — cover"),
        ("profile_avatar", "Default profile avatar"),
        ("empty_state", "Empty-state illustration"),
    ]
    key = models.CharField(max_length=40, choices=PLACEMENTS, unique=True)
    title = models.CharField(max_length=120)
    image = models.ImageField(upload_to="nkem/brand-assets/%Y/%m/", validators=[validate_uploaded_image])
    alt_text = models.CharField(max_length=180, blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key"]
        verbose_name = "Brand image"
        verbose_name_plural = "Brand images"

    def __str__(self):
        return self.title or self.get_key_display()