# Extend account methods and add owner-scoped transaction indexes.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("finance", "0002_account_opening_balance")]
    operations = [
        migrations.AlterField(
            model_name="account",
            name="account_type",
            field=models.CharField(choices=[("cash", "Cash"), ("mtn_momo", "MTN Mobile Money"), ("orange_money", "Orange Money"), ("bank", "Bank account"), ("savings", "Savings"), ("card", "Card")], default="cash", max_length=20),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["owner", "transaction_date"], name="finance_owner_date_idx"),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["owner", "kind", "transaction_date"], name="finance_owner_kind_date_idx"),
        ),
    ]