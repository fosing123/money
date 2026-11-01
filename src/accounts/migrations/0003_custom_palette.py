from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_user_preferences")]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="theme",
            field=models.CharField(
                choices=[
                    ("violet", "Violet dream"),
                    ("mint", "Fresh mint"),
                    ("ocean", "Calm ocean"),
                    ("sunset", "Warm sunset"),
                    ("midnight", "Midnight"),
                ],
                default="violet",
                max_length=16,
            ),
        ),
    ]
