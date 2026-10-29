# Generated for TIANA brand appearance and admin-managed image slots.
import django.core.validators
import django.db.models.deletion
import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="AppAppearance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("app_name", models.CharField(default="TIANA", max_length=50)),
                ("tagline", models.CharField(default="Your money friend", max_length=120)),
                ("primary_color", models.CharField(default="#7757F6", max_length=7, validators=[django.core.validators.RegexValidator(message="Use a six-digit hex colour, for example #7757F6.", regex="^#[0-9A-Fa-f]{6}$")])),
                ("dark_color", models.CharField(default="#392187", max_length=7, validators=[django.core.validators.RegexValidator(message="Use a six-digit hex colour, for example #7757F6.", regex="^#[0-9A-Fa-f]{6}$")])),
                ("soft_color", models.CharField(default="#EFEAFF", max_length=7, validators=[django.core.validators.RegexValidator(message="Use a six-digit hex colour, for example #7757F6.", regex="^#[0-9A-Fa-f]{6}$")])),
                ("background_color", models.CharField(default="#F7F6FC", max_length=7, validators=[django.core.validators.RegexValidator(message="Use a six-digit hex colour, for example #7757F6.", regex="^#[0-9A-Fa-f]{6}$")])),
                ("text_color", models.CharField(default="#201A3A", max_length=7, validators=[django.core.validators.RegexValidator(message="Use a six-digit hex colour, for example #7757F6.", regex="^#[0-9A-Fa-f]{6}$")])),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "App appearance", "verbose_name_plural": "App appearance"},
        ),
        migrations.CreateModel(
            name="BrandAsset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(choices=[("logo", "Brand logo"), ("onboarding_welcome", "Onboarding — welcome"), ("onboarding_control", "Onboarding — money control"), ("onboarding_goals", "Onboarding — goals"), ("onboarding_ai", "Onboarding — AI coach"), ("onboarding_account", "Onboarding — account creation"), ("dashboard_hero", "Dashboard — hero artwork"), ("coach_avatar", "AI coach — avatar"), ("marketplace_cover", "Marketplace — cover"), ("profile_avatar", "Default profile avatar"), ("empty_state", "Empty-state illustration")], max_length=40, unique=True)),
                ("title", models.CharField(max_length=120)),
                ("image", models.ImageField(upload_to="tiana/brand-assets/%Y/%m/", validators=[core.validators.validate_uploaded_image])),
                ("alt_text", models.CharField(blank=True, max_length=180)),
                ("is_active", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["key"], "verbose_name": "Brand image", "verbose_name_plural": "Brand images"},
        ),
    ]