# Generated manually to handle FAQ model renames

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtail_feathers', '0012_alter_faqcategory_slug'),
    ]

    operations = [
        # First, rename the FAQ model to FAQItem
        migrations.RenameModel(
            old_name='FAQ',
            new_name='FAQItem',
        ),
        
        # Then, rename FAQCategory to FAQ
        migrations.RenameModel(
            old_name='FAQCategory',
            new_name='FAQ',
        ),
        
        # Rename the foreign key field from category to faq
        migrations.RenameField(
            model_name='faqitem',
            old_name='category',
            new_name='faq',
        ),
        
        # Update the Meta options for FAQ (formerly FAQCategory)
        migrations.AlterModelOptions(
            name='faq',
            options={'ordering': ['name'], 'verbose_name': 'FAQ', 'verbose_name_plural': 'FAQs'},
        ),
        
        # Remove old constraints
        migrations.RemoveConstraint(
            model_name='faq',
            name='unique_faqcategory_translation_key_locale',
        ),
        migrations.RemoveConstraint(
            model_name='faqitem',
            name='unique_faq_translation_key_locale',
        ),
        
        # Add new constraints with updated names
        migrations.AddConstraint(
            model_name='faq',
            constraint=models.UniqueConstraint(
                fields=['translation_key', 'locale'],
                name='unique_faq_translation_key_locale'
            ),
        ),
        migrations.AddConstraint(
            model_name='faqitem',
            constraint=models.UniqueConstraint(
                fields=['translation_key', 'locale'],
                name='unique_faq_item_translation_key_locale'
            ),
        ),
    ]