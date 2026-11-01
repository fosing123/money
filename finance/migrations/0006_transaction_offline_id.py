from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0005_alter_transaction_transaction_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="offline_id",
            field=models.UUIDField(blank=True, editable=False, null=True, unique=True),
        ),
    ]
