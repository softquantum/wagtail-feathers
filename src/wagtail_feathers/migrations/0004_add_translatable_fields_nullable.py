# Generated manually to add TranslatableMixin fields as nullable

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtail_feathers', '0003_alter_classifiergroup_options'),
        ('wagtailcore', '0094_alter_page_locale'),
    ]

    operations = [
        migrations.AddField(
            model_name='classifier',
            name='translation_key',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='classifiergroup',
            name='translation_key',
            field=models.UUIDField(null=True, editable=False),
        ),
        
        migrations.AddField(
            model_name='classifier',
            name='locale',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        migrations.AddField(
            model_name='classifiergroup',
            name='locale',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
    ]
