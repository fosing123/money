import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("finance", "0004_positive_money_amounts")]
    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="transaction_date",
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]