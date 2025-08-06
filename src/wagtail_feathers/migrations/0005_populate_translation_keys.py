# Data migration to populate unique translation_keys

from django.db import migrations
import uuid


def populate_translation_keys(apps, schema_editor):
    """Populate translation_key and locale for existing Classifier and ClassifierGroup instances.

    Each instance gets a unique translation_key to avoid constraint violations.
    """
    Locale = apps.get_model('wagtailcore', 'Locale')
    Classifier = apps.get_model('wagtail_feathers', 'Classifier')
    ClassifierGroup = apps.get_model('wagtail_feathers', 'ClassifierGroup')
    
    default_locale = Locale.objects.filter(language_code='en').first()
    if not default_locale:
        default_locale = Locale.objects.first()
    
    if not default_locale:
        raise RuntimeError("No locales found. Please ensure at least one locale exists.")
    
    for group in ClassifierGroup.objects.filter(translation_key__isnull=True):
        group.translation_key = uuid.uuid4()
        group.locale = default_locale
        group.save(update_fields=['translation_key', 'locale'])
    
    for classifier in Classifier.objects.filter(translation_key__isnull=True):
        classifier.translation_key = uuid.uuid4()
        classifier.locale = default_locale
        classifier.save(update_fields=['translation_key', 'locale'])


def reverse_populate_translation_keys(apps, schema_editor):
    """Reverse operation - set translation_key and locale to null."""
    Classifier = apps.get_model('wagtail_feathers', 'Classifier')
    ClassifierGroup = apps.get_model('wagtail_feathers', 'ClassifierGroup')
    
    ClassifierGroup.objects.update(translation_key=None, locale=None)
    Classifier.objects.update(translation_key=None, locale=None)


class Migration(migrations.Migration):

    dependencies = [
        ('wagtail_feathers', '0004_add_translatable_fields_nullable'),
    ]

    operations = [
        migrations.RunPython(
            populate_translation_keys,
            reverse_populate_translation_keys,
        ),
    ]
