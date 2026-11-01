import decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("goals", "0002_goal_image")]
    operations = [
        migrations.AlterField(
            model_name="goal",
            name="target_amount",
            field=models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))]),
        ),
        migrations.AlterField(
            model_name="goal",
            name="current_amount",
            field=models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))]),
        ),
        migrations.AlterModelOptions(
            name="goal",
            options={"ordering": ["status", "target_date", "-created_at"]},
        ),
    ]