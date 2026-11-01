import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("goals", "0004_goal_contributions")]

    operations = [
        migrations.AlterField(
            model_name="goalcontribution",
            name="goal",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="contributions",
                to="goals.goal",
            ),
        ),
    ]
