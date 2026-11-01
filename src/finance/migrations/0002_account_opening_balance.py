# Preserve existing balances while introducing the opening-balance field.
from decimal import Decimal
from django.db import migrations, models


def preserve_opening_balances(apps, schema_editor):
    Account = apps.get_model("finance", "Account")
    Transaction = apps.get_model("finance", "Transaction")
    positives = {"income", "refund", "transfer_in"}
    negatives = {"expense", "transfer_out"}
    for account in Account.objects.all().iterator():
        ledger_total = Decimal("0.00")
        for item in Transaction.objects.filter(account_id=account.pk).only("amount", "kind").iterator():
            amount = Decimal(str(item.amount))
            if item.kind in positives:
                ledger_total += amount
            elif item.kind in negatives:
                ledger_total -= amount
        account.opening_balance = Decimal(str(account.balance)) - ledger_total
        account.save(update_fields=["opening_balance"])


class Migration(migrations.Migration):
    dependencies = [("finance", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="account",
            name="opening_balance",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=14),
        ),
        migrations.RunPython(preserve_opening_balances, migrations.RunPython.noop),
    ]