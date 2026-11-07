import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("expense_analyzer", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIPersonalization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("voice_style", models.CharField(choices=[("friendly", "Friendly"), ("fatherly", "Fatherly"), ("motherly", "Motherly"), ("mentor", "Mentor")], default="friendly", max_length=12)),
                ("ambition", models.CharField(blank=True, choices=[("financial_freedom", "Become financially independent"), ("millionaire", "Build substantial wealth"), ("business_owner", "Start or grow a business"), ("career", "Build a successful career"), ("education", "Complete my education or training"), ("support_family", "Support my family"), ("own_home", "Own a home or property"), ("other", "Something else")], default="", max_length=24)),
                ("current_stage", models.CharField(blank=True, choices=[("student", "Student"), ("training", "Learning a skill or trade"), ("employed", "Employed"), ("self_employed", "Self-employed"), ("job_seeking", "Looking for work"), ("other", "Other")], default="", max_length=16)),
                ("future_vision", models.CharField(blank=True, default="", max_length=240)),
                ("desired_career", models.CharField(blank=True, default="", max_length=120)),
                ("why_it_matters", models.CharField(blank=True, default="", max_length=180)),
                ("setup_completed", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="ai_personalization", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "AI personalisation",
                "verbose_name_plural": "AI personalisations",
            },
        ),
    ]
