from django.db import migrations, models


def convert_old_default_to_zero(apps, schema_editor):
    SiteSettings = apps.get_model("wagtail_feathers", "SiteSettings")
    SiteSettings.objects.filter(words_per_minute=200).update(words_per_minute=0)


def restore_old_default(apps, schema_editor):
    SiteSettings = apps.get_model("wagtail_feathers", "SiteSettings")
    SiteSettings.objects.filter(words_per_minute=0).update(words_per_minute=200)


class Migration(migrations.Migration):

    dependencies = [
        ("wagtail_feathers", "0005_alter_featherbasepage_body"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="words_per_minute",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Override reading speed (WPM). Leave at 0 to use language-specific defaults (e.g., English: 238, French: 214).",
                verbose_name="Words per minute",
            ),
        ),
        migrations.RunPython(convert_old_default_to_zero, restore_old_default),
    ]