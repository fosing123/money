from django.db import migrations, models


def rename_default_nkem_brand(apps, schema_editor):
    AppAppearance = apps.get_model("core", "AppAppearance")
    AppAppearance.objects.filter(app_name="TIANA").update(app_name="Nkem")
    AppAppearance.objects.filter(tagline="Your money friend").update(
        tagline="Smart Money. Brighter You."
    )


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]

    operations = [
        migrations.RunPython(rename_default_nkem_brand, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="appappearance",
            name="app_name",
            field=models.CharField(default="Nkem", max_length=50),
        ),
        migrations.AlterField(
            model_name="appappearance",
            name="tagline",
            field=models.CharField(default="Smart Money. Brighter You.", max_length=120),
        ),
    ]
