import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0002_nkem_brand_identity")]

    operations = [
        migrations.AlterField(
            model_name="brandasset",
            name="image",
            field=models.ImageField(
                upload_to="nkem/brand-assets/%Y/%m/",
                validators=[core.validators.validate_uploaded_image],
            ),
        ),
    ]
