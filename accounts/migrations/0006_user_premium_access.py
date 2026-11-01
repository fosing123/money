from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_weekly_budget_allocations"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_premium",
            field=models.BooleanField(default=False, help_text="Grant Premium access after verified payment or an authorised support decision."),
        ),
        migrations.AddField(
            model_name="user",
            name="premium_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
