from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="source",
            field=models.CharField(
                choices=[("system", "System"), ("ai", "AI")],
                default="system",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="dedupe_key",
            field=models.CharField(blank=True, default="", max_length=160),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.UniqueConstraint(
                condition=~models.Q(("dedupe_key", "")),
                fields=("user", "dedupe_key"),
                name="notification_user_dedupe_unique",
            ),
        ),
    ]
