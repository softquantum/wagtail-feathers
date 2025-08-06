# Migration to add TranslatableMixin fields to Category

from django.db import migrations, models
import django.db.models.deletion
import uuid


def populate_category_translation_keys(apps, schema_editor):
    """
    Populate translation_key and locale for existing Category instances.
    Each instance gets a unique translation_key to avoid constraint violations.
    """
    Locale = apps.get_model('wagtailcore', 'Locale')
    Category = apps.get_model('wagtail_feathers', 'Category')
    
    # Get the default locale (usually 'en')
    default_locale = Locale.objects.filter(language_code='en').first()
    if not default_locale:
        # If 'en' doesn't exist, get the first available locale
        default_locale = Locale.objects.first()
    
    if not default_locale:
        raise RuntimeError("No locales found. Please ensure at least one locale exists.")
    
    # Update Category instances
    for category in Category.objects.filter(translation_key__isnull=True):
        category.translation_key = uuid.uuid4()
        category.locale = default_locale
        category.save(update_fields=['translation_key', 'locale'])


def reverse_populate_translation_keys(apps, schema_editor):
    """
    Reverse operation - set translation_key and locale to null.
    """
    Category = apps.get_model('wagtail_feathers', 'Category')
    Category.objects.update(translation_key=None, locale=None)


class Migration(migrations.Migration):

    dependencies = [
        ('wagtail_feathers', '0008_classifiergroup_slug'),
        ('wagtailcore', '0094_alter_page_locale'),
    ]

    operations = [
        # First add the fields as nullable
        migrations.AddField(
            model_name='category',
            name='translation_key',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='category',
            name='locale',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        
        # Populate the fields with unique values
        migrations.RunPython(
            populate_category_translation_keys,
            reverse_populate_translation_keys,
        ),
        
        # Make fields non-nullable
        migrations.AlterField(
            model_name='category',
            name='translation_key',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AlterField(
            model_name='category',
            name='locale',
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        
        # Add the unique constraint
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(
                fields=('translation_key', 'locale'),
                name='unique_translation_key_locale_wagtail_feathers_category'
            ),
        ),
    ]