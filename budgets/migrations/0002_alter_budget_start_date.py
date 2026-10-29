import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("budgets", "0001_initial")]
    operations = [
        migrations.AlterField(
            model_name="budget",
            name="start_date",
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]