# Initial TIANA student opportunity catalogue.
import decimal
import django.core.validators
import django.utils.timezone
import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Opportunity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=140)),
                ("kind", models.CharField(choices=[("service", "Service"), ("product", "Product"), ("job", "Gig or opportunity"), ("event", "Student event")], default="service", max_length=20)),
                ("category", models.CharField(default="General", max_length=60)),
                ("description", models.TextField()),
                ("price_amount", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))])),
                ("currency", models.CharField(default="XAF", max_length=10)),
                ("location", models.CharField(default="Bafoussam", max_length=120)),
                ("seller_name", models.CharField(blank=True, max_length=120)),
                ("image", models.ImageField(blank=True, null=True, upload_to="tiana/opportunities/%Y/%m/", validators=[core.validators.validate_uploaded_image])),
                ("contact_url", models.URLField(blank=True)),
                ("is_featured", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("published_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-is_featured", "-published_at", "name"]},
        ),
        migrations.AddIndex(
            model_name="opportunity",
            index=models.Index(fields=["is_active", "kind", "published_at"], name="marketplace_is_act_2e3a8e_idx"),
        ),
        migrations.AddIndex(
            model_name="opportunity",
            index=models.Index(fields=["is_active", "category"], name="marketplace_is_act_4c6b8a_idx"),
        ),
    ]