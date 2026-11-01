import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0002_system_alerts"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PushDevice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.CharField(max_length=4096, unique=True)),
                ("device_id", models.CharField(blank=True, default="", max_length=128)),
                ("platform", models.CharField(default="web", max_length=20)),
                ("user_agent", models.CharField(blank=True, default="", max_length=512)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="push_devices", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-last_seen_at", "-updated_at"]},
        ),
        migrations.AddIndex(
            model_name="pushdevice",
            index=models.Index(fields=["user", "is_active"], name="push_user_active_idx"),
        ),
    ]
