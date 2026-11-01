# Add theme preference and the first-run money setup fields.
import decimal
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [
        migrations.AddField(model_name="user", name="theme", field=models.CharField(choices=[("violet", "Violet dream"), ("mint", "Fresh mint"), ("ocean", "Calm ocean"), ("sunset", "Warm sunset"), ("midnight", "Midnight")], default="violet", max_length=16)),
        migrations.AddField(model_name="user", name="onboarding_completed", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="user", name="weekly_income", field=models.DecimalField(decimal_places=2, default=decimal.Decimal("0"), max_digits=14)),
        migrations.AddField(model_name="user", name="weekly_savings_target", field=models.DecimalField(decimal_places=2, default=decimal.Decimal("0"), max_digits=14)),
        migrations.AddField(model_name="user", name="payday_weekday", field=models.PositiveSmallIntegerField(blank=True, choices=[(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday")], null=True)),
        migrations.AddField(model_name="user", name="financial_priorities", field=models.JSONField(blank=True, default=list)),
    ]