import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("goals", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="goal",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="tiana/goals/%Y/%m/", validators=[core.validators.validate_uploaded_image]),
        ),
    ]