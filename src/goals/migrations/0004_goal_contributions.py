import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("finance", "0005_alter_transaction_transaction_date"),
        ("goals", "0003_goal_validators_and_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="GoalContribution",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("note", models.CharField(blank=True, default="", max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("goal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="contributions", to="goals.goal")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="goal_contributions", to=settings.AUTH_USER_MODEL)),
                ("transaction", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="goal_contribution", to="finance.transaction")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
