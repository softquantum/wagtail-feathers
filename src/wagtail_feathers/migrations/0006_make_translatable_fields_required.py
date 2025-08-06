# Migration to make TranslatableMixin fields non-nullable and add constraints

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('wagtail_feathers', '0005_populate_translation_keys'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classifier',
            name='translation_key',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AlterField(
            model_name='classifiergroup',
            name='translation_key',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        
        migrations.AlterField(
            model_name='classifier',
            name='locale',
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        migrations.AlterField(
            model_name='classifiergroup',
            name='locale',
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='classifiergroup',
            constraint=models.UniqueConstraint(
                fields=('translation_key', 'locale'),
                name='unique_translation_key_locale_wagtail_feathers_classifiergroup'
            ),
        ),
        migrations.AddConstraint(
            model_name='classifier',
            constraint=models.UniqueConstraint(
                fields=('translation_key', 'locale'),
                name='unique_translation_key_locale_wagtail_feathers_classifier'
            ),
        ),
    ]
