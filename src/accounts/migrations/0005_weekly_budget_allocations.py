from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_user_avatar"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="weekly_budget_allocations",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
