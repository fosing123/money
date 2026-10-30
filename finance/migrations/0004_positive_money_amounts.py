import decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("finance", "0003_account_choices_and_transaction_indexes")]
    operations = [
        migrations.AlterField(
            model_name="account",
            name="opening_balance",
            field=models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))]),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="amount",
            field=models.DecimalField(decimal_places=2, max_digits=14, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.01"))]),
        ),
    ]