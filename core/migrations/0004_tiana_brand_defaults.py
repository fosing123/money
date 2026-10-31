from django.db import migrations, models


def restore_tiana_brand(apps, schema_editor):
    AppAppearance = apps.get_model("core", "AppAppearance")
    AppAppearance.objects.filter(app_name="Nkem").update(app_name="TIANA")
    AppAppearance.objects.filter(tagline__in=["Smart Money. Brighter You.", "Your money friend"]).update(
        tagline="Your Money Friend Always"
    )


class Migration(migrations.Migration):
    dependencies = [("core", "0003_nkem_brand_asset_path")]

    operations = [
        migrations.RunPython(restore_tiana_brand, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="appappearance",
            name="app_name",
            field=models.CharField(default="TIANA", max_length=50),
        ),
        migrations.AlterField(
            model_name="appappearance",
            name="tagline",
            field=models.CharField(default="Your Money Friend Always", max_length=120),
        ),
    ]
