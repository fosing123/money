import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_custom_palette")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="tiana/profiles/%Y/%m/",
                validators=[core.validators.validate_uploaded_image],
            ),
        ),
    ]
