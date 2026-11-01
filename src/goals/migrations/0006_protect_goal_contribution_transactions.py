import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("goals", "0005_protect_goals_with_contributions")]

    operations = [
        migrations.AlterField(
            model_name="goalcontribution",
            name="transaction",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="goal_contribution",
                to="finance.transaction",
            ),
        ),
    ]
