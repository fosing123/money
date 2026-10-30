from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_user_preferences")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="custom_palette",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="user",
            name="theme",
            field=models.CharField(
                choices=[
                    ("violet", "Nkem violet"),
                    ("mint", "Fresh mint"),
                    ("ocean", "Calm ocean"),
                    ("sunset", "Warm sunset"),
                    ("midnight", "Midnight"),
                    ("custom", "My own palette"),
                ],
                default="violet",
                max_length=16,
            ),
        ),
    ]
