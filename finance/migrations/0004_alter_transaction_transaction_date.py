import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("finance", "0003_account_choices_and_transaction_indexes")]
    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="transaction_date",
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]