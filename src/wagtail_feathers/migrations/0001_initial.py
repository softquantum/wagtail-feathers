import django.core.validators
import django.db.models.deletion
import django_countries.fields
import django_extensions.db.fields
import modelcluster.contrib.taggit
import modelcluster.fields
import uuid
import wagtail.fields
import wagtail.search.index
from wagtail.documents import get_document_model_string
from wagtail.images import get_image_model_string

import wagtail_feathers.blocks
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('taggit', '0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx'),
        ('wagtailcore', '0094_alter_page_locale'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(get_image_model_string()),
        migrations.swappable_dependency(get_document_model_string()),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Name')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
            ],
            options={
                'verbose_name': 'Author Type',
                'verbose_name_plural': 'Author Types',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CountryGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Name for this country group (e.g., 'ACP Countries', 'EU Countries', 'West Africa')", max_length=100, unique=True)),
                ('description', models.TextField(blank=True, help_text='Optional description of this country group')),
                ('countries', django_countries.fields.CountryField(blank=True, help_text='Select countries that belong to this group', max_length=746, multiple=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this group is available for selection')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Country Group',
                'verbose_name_plural': 'Country Groups',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PersonGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('name', models.CharField(max_length=254, unique=True, verbose_name='name')),
            ],
            options={
                'verbose_name': 'Group',
                'verbose_name_plural': 'Groups',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=255, unique=True)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('name', models.CharField(help_text='Keep the name short (3 to 100 characters), max is 255 but you better not.', max_length=255, validators=[django.core.validators.MinLengthValidator(3)])),
                ('live', models.BooleanField(default=True, help_text='soft disable the node', verbose_name='live')),
                ('aliases', models.TextField(blank=True, help_text='What else is this known as or referred to as?', max_length=255)),
                ('order_index', models.IntegerField(blank=True, default=0, editable=False)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='name')),
                ('icon', models.CharField(blank=True, help_text='Choose the icon from the admin/styleguide.', max_length=100)),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale')),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
                'ordering': ['path'],
            },
            bases=(wagtail.search.index.Indexed, models.Model),
        ),
        migrations.CreateModel(
            name='ClassifierGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('type', models.CharField(choices=[('Subject', 'Subject'), ('Attribute', 'Attribute')], max_length=20)),
                ('name', models.CharField(max_length=255)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='name')),
                ('max_selections', models.PositiveIntegerField(default=0, help_text='Maximum number of selections allowed. 0 for unlimited')),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale')),
            ],
            options={
                'verbose_name': 'Group of classifiers',
                'verbose_name_plural': 'Groups of classifiers',
                'ordering': ['type', 'name'],
            },
            bases=(wagtail.search.index.Indexed, models.Model),
        ),
        migrations.CreateModel(
            name='Classifier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='name')),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale')),
                ('group', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='classifiers', to='wagtail_feathers.classifiergroup')),
            ],
            options={
                'verbose_name': 'Classifier',
                'verbose_name_plural': 'Classifiers',
                'ordering': ['sort_order'],
            },
            bases=(wagtail.search.index.Indexed, models.Model),
        ),
        migrations.CreateModel(
            name='ErrorPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('error_code', models.CharField(choices=[('400', '400 - Bad Request'), ('403', '403 - Permission Denied'), ('404', '404 - Page Not Found'), ('500', '500 - Internal Server Error')], max_length=3, unique=True)),
                ('heading', models.CharField(default='Oops! Something went wrong', max_length=255)),
                ('message', wagtail.fields.RichTextField(blank=True, help_text='Custom message to display on the error page')),
                ('image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=get_image_model_string())),
            ],
            options={
                'verbose_name': 'Error Page',
                'verbose_name_plural': 'Error Pages',
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='FAQ',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('name', models.CharField(max_length=150)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from='name')),
                ('description', models.TextField(blank=True, help_text='Optional description of this FAQ category')),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale')),
            ],
            options={
                'verbose_name': 'FAQ',
                'verbose_name_plural': 'FAQs',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='FAQItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('question', models.CharField(help_text='The FAQ question', max_length=255)),
                ('answer', wagtail.fields.RichTextField(help_text='The answer to the question')),
                ('live', models.BooleanField(default=True, help_text='Whether this FAQ is published and visible')),
                ('faq', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='faqs', to='wagtail_feathers.faq')),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale')),
            ],
            options={
                'verbose_name': 'FAQ Item',
                'verbose_name_plural': 'FAQ Items',
                'ordering': ['sort_order'],
            },
            bases=(wagtail.search.index.Indexed, models.Model),
        ),
        migrations.CreateModel(
            name='FeatherBasePage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('canonical_url', models.URLField(blank=True, help_text='Canonical URL if different from page URL (for duplicate content)')),
                ('seo_content_type', models.CharField(choices=[('website', 'Website'), ('article', 'Article'), ('product', 'Product'), ('event', 'Event'), ('organization', 'Organization'), ('person', 'Person')], default='website', help_text='Content type for structured data markup', max_length=20)),
                ('twitter_card_type', models.CharField(choices=[('summary', 'Summary'), ('summary_large_image', 'Summary with Large Image')], default='summary', help_text='Twitter card display style', max_length=20)),
                ('no_index', models.BooleanField(default=False, help_text='Prevent search engines from indexing this page')),
                ('no_follow', models.BooleanField(default=False, help_text='Prevent search engines from following links on this page')),
                ('body', wagtail.fields.StreamField([('heading_block', 3), ('paragraph_block', 4), ('markdown_block', 5), ('image_block', 9), ('image_grid', 12), ('block_quote', 16), ('embed_block', 17), ('cta_block', 32), ('faq_block', 38), ('table_block', 39)], blank=True, block_lookup={0: ('wagtail.blocks.CharBlock', (), {'required': True}), 1: ('wagtail.blocks.ChoiceBlock', [], {'blank': True, 'choices': [('', 'Select a header size'), ('h2', 'H2'), ('h3', 'H3'), ('h4', 'H4'), ('h5', 'H5'), ('h6', 'H6')], 'required': False}), 2: ('wagtail_feathers.blocks.ThemeVariantChooserBlock', (), {'component_type': 'heading', 'default': 'default', 'help_text': 'Select a theme variant for this component', 'label': 'Theme variant', 'required': False}), 3: ('wagtail.blocks.StructBlock', [[('heading_text', 0), ('size', 1), ('theme_variant', 2)]], {'label': 'Heading'}), 4: ('wagtail.blocks.RichTextBlock', (), {'description': 'A rich text paragraph', 'features': ['h2', 'h3', 'h4', 'h5', 'bold', 'italic', 'link', 'image', 'document-link', 'ul', 'ol', 'superscript', 'subscript'], 'icon': 'pilcrow', 'label': 'Paragraph', 'preview_value': '\n            <h2>Our scientific commitment</h2>\n            <p>In the realm of science, <b>discovery</b> has <i>always</i> been our driving force.\n            <a href="https://en.wikipedia.org/wiki/Scientific_method">Scientific methods</a>\n            are crucial for progress, and – research is the most rewarding of all.\n            We take pride in transforming hypotheses and experiments into groundbreaking\n            findings with precision and rigor.</p>\n            ', 'template': 'wagtail_feathers/blocks/paragraph_block.html'}), 5: ('wagtailmarkdown.blocks.MarkdownBlock', (), {'icon': 'code', 'label': 'Markdown'}), 6: ('wagtail.images.blocks.ImageChooserBlock', (), {'required': True}), 7: ('wagtail.blocks.CharBlock', (), {'help_text': "If left blank, the image's global alt text will be used.", 'required': False}), 8: ('wagtail_feathers.blocks.ThemeVariantChooserBlock', (), {'component_type': 'image', 'default': 'default', 'help_text': 'Select a theme variant for this component', 'label': 'Theme variant', 'required': False}), 9: ('wagtail.blocks.StructBlock', [[('image', 6), ('image_alt_text', 7), ('theme_variant', 8)]], {'label': 'Image'}), 10: ('wagtail.blocks.StructBlock', [[('image', 6), ('image_alt_text', 7), ('theme_variant', 8)]], {}), 11: ('wagtail.blocks.ListBlock', (10,), {'help_text': 'Add images to display in the grid', 'label': 'Images'}), 12: ('wagtail.blocks.StructBlock', [[('images', 11)]], {'label': 'Image Grid'}), 13: ('wagtail.blocks.RichTextBlock', (), {'required': True}), 14: ('wagtail.blocks.CharBlock', (), {'blank': True, 'label': 'e.g. Maxime Decooman', 'required': False}), 15: ('wagtail_feathers.blocks.ThemeVariantChooserBlock', (), {'component_type': 'quote', 'default': 'default', 'help_text': 'Select a theme variant for this component', 'label': 'Theme variant', 'required': False}), 16: ('wagtail.blocks.StructBlock', [[('quote', 13), ('attribution', 14), ('theme_variant', 15)]], {'label': 'Quote'}), 17: ('wagtail.embeds.blocks.EmbedBlock', (), {'description': 'An embedded video or other media', 'help_text': 'Insert an embed URL e.g https://www.youtube.com/watch?v=SGJFWirQ3ks', 'icon': 'media', 'label': 'Embed Block', 'preview_template': 'wagtail_feathers/preview/static_embed_block.html', 'preview_value': 'https://www.youtube.com/watch?v=mwrGSfiB1Mg', 'template': 'wagtail_feathers/blocks/embed_block.html'}), 18: ('wagtail.blocks.CharBlock', (), {'help_text': 'Call-to-action heading', 'max_length': 100}), 19: ('wagtail.blocks.RichTextBlock', (), {'features': ['bold', 'italic'], 'help_text': 'Supporting text for the call-to-action', 'required': False}), 20: ('wagtail.blocks.CharBlock', (), {'help_text': 'Text for the action button', 'max_length': 50}), 21: ('wagtail.blocks.PageChooserBlock', (), {'required': False}), 22: ('wagtail.documents.blocks.DocumentChooserBlock', (), {'required': False}), 23: ('wagtail.blocks.CharBlock', (), {'help_text': "Leave blank to use link's title.", 'required': False}), 24: ('wagtail.blocks.StructBlock', [[('page', 21), ('document', 22), ('title', 23)]], {}), 25: ('wagtail.blocks.URLBlock', (), {}), 26: ('wagtail.blocks.CharBlock', (), {'required': False}), 27: ('wagtail.blocks.BooleanBlock', (), {'help_text': 'Open the link in a new tab', 'required': False}), 28: ('wagtail.blocks.StructBlock', [[('link', 25), ('title', 26), ('link_target', 27)]], {}), 29: ('wagtail.blocks.StreamBlock', [[('internal', 24), ('external', 28)]], {'help_text': 'Link for the action button', 'max_num': 1}), 30: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('default', 'Default'), ('primary', 'Primary'), ('secondary', 'Secondary'), ('accent', 'Accent')], 'help_text': 'Background color theme for the CTA section'}), 31: ('wagtail_feathers.blocks.ThemeVariantChooserBlock', (), {'component_type': 'cta', 'default': 'default', 'help_text': 'Select a theme variant for this component', 'label': 'Theme variant', 'required': False}), 32: ('wagtail.blocks.StructBlock', [[('heading', 18), ('text', 19), ('button_text', 20), ('button_link', 29), ('background_color', 30), ('theme_variant', 31)]], {'label': 'Call to Action'}), 33: ('wagtail.blocks.ChoiceBlock', [], {'choices': wagtail_feathers.blocks.get_faq_choices, 'help_text': 'Select a FAQ to display'}), 34: ('wagtail.blocks.IntegerBlock', (), {'default': 10, 'help_text': 'Maximum number of FAQ items to show, default 10, maximum 20.', 'max_value': 20, 'min_value': 1}), 35: ('wagtail.blocks.BooleanBlock', (), {'default': True, 'help_text': "Show 'View All FAQs' link", 'required': False}), 36: ('wagtail.blocks.PageChooserBlock', (), {'help_text': "Link to full FAQ page (for 'View All' link)", 'required': False}), 37: ('wagtail_feathers.blocks.ThemeVariantChooserBlock', (), {'component_type': 'faq_embed', 'default': 'default', 'help_text': 'Select a theme variant for this component', 'label': 'Theme variant', 'required': False}), 38: ('wagtail.blocks.StructBlock', [[('faq', 33), ('max_items', 34), ('show_view_all_link', 35), ('faq_page', 36), ('theme_variant', 37)]], {'label': 'FAQ Section'}), 39: ('wagtail.contrib.table_block.blocks.TableBlock', (), {'label': 'Table'})})),
                ('template_variant', models.CharField(blank=True, help_text="Optional template variant (e.g., 'landing', 'portfolio'). Leave empty for default template.", max_length=50, verbose_name='Template Variant')),
                ('og_image', models.ForeignKey(blank=True, help_text='Image for social media sharing (Open Graph/Twitter). Recommended: 1200x630px', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=get_image_model_string())),
            ],
            options={
                'verbose_name': 'Feather Base Page',
                'ordering': ['-first_published_at'],
            },
            bases=('wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='FeatherBasePageTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_object', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='tagged_items', to='wagtail_feathers.featherbasepage')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_items', to='taggit.tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='featherbasepage',
            name='tags',
            field=modelcluster.contrib.taggit.ClusterTaggableManager(blank=True, help_text='A comma-separated list of tags.', through='wagtail_feathers.FeatherBasePageTag', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.CreateModel(
            name='FlatMenu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('name', models.CharField(help_text="Name for this menu (e.g., 'Main Navigation', 'Header Menu')", max_length=100)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, help_text='Auto-generated from name, but can be edited', populate_from='name', unique=True)),
                ('menu_items', wagtail.fields.StreamField([('internal', 3), ('external', 7)], blank=True, block_lookup={0: ('wagtail.blocks.PageChooserBlock', (), {'required': False}), 1: ('wagtail.documents.blocks.DocumentChooserBlock', (), {'required': False}), 2: ('wagtail.blocks.CharBlock', (), {'help_text': "Leave blank to use link's title.", 'required': False}), 3: ('wagtail.blocks.StructBlock', [[('page', 0), ('document', 1), ('title', 2)]], {}), 4: ('wagtail.blocks.URLBlock', (), {}), 5: ('wagtail.blocks.CharBlock', (), {'required': False}), 6: ('wagtail.blocks.BooleanBlock', (), {'help_text': 'Open the link in a new tab', 'required': False}), 7: ('wagtail.blocks.StructBlock', [[('link', 4), ('title', 5), ('link_target', 6)]], {})})),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale')),
            ],
            options={
                'verbose_name': 'Flat Menu',
                'verbose_name_plural': 'Flat Menus',
            },
        ),
        migrations.CreateModel(
            name='FooterNavigation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('name', models.CharField(max_length=100)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, help_text='Auto-generated from name, but can be edited', populate_from='name', unique=True)),
                ('menu_sections', wagtail.fields.StreamField([('menu_section', 15)], blank=True, block_lookup={0: ('wagtail.blocks.CharBlock', (), {}), 1: ('wagtail.blocks.PageChooserBlock', (), {'help_text': 'Select a page to use its children as menu items', 'required': True}), 2: ('wagtail.blocks.IntegerBlock', (), {'default': 1, 'help_text': 'Maximum number of levels to show from page hierarchy', 'max_value': 5, 'min_value': 1}), 3: ('wagtail.blocks.BooleanBlock', (), {'default': False, 'help_text': 'Include the parent page as a menu item', 'required': False}), 4: ('wagtail.blocks.CharBlock', (), {'help_text': 'Optional title to display instead of the parent page title', 'max_length': 100, 'required': False}), 5: ('wagtail.blocks.StructBlock', [[('parent_page', 1), ('max_levels', 2), ('show_parent', 3), ('title', 4)]], {}), 6: ('wagtail.blocks.PageChooserBlock', (), {'required': False}), 7: ('wagtail.documents.blocks.DocumentChooserBlock', (), {'required': False}), 8: ('wagtail.blocks.CharBlock', (), {'help_text': "Leave blank to use link's title.", 'required': False}), 9: ('wagtail.blocks.StructBlock', [[('page', 6), ('document', 7), ('title', 8)]], {}), 10: ('wagtail.blocks.URLBlock', (), {}), 11: ('wagtail.blocks.CharBlock', (), {'required': False}), 12: ('wagtail.blocks.BooleanBlock', (), {'help_text': 'Open the link in a new tab', 'required': False}), 13: ('wagtail.blocks.StructBlock', [[('link', 10), ('title', 11), ('link_target', 12)]], {}), 14: ('wagtail.blocks.StreamBlock', [[('page_links', 5), ('internal', 9), ('external', 13)]], {}), 15: ('wagtail.blocks.StructBlock', [[('section_heading', 0), ('links', 14)]], {})})),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale')),
            ],
            options={
                'verbose_name': 'Footer Navigation Menu',
                'verbose_name_plural': 'Footer Navigation Menus',
            },
        ),
        migrations.CreateModel(
            name='Footer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('name', models.CharField(help_text="Name for this footer configuration (e.g., 'Main Footer', 'A/B Test Footer')", max_length=100)),
                ('copyright_text', models.CharField(help_text="Copyright text (e.g., '© 2024 Company Name')", max_length=200)),
                ('footer_text', models.TextField(blank=True, help_text='Additional footer text or description')),
                ('footer_links', wagtail.fields.StreamField([('internal', 3), ('external', 7)], blank=True, block_lookup={0: ('wagtail.blocks.PageChooserBlock', (), {'required': False}), 1: ('wagtail.documents.blocks.DocumentChooserBlock', (), {'required': False}), 2: ('wagtail.blocks.CharBlock', (), {'help_text': "Leave blank to use link's title.", 'required': False}), 3: ('wagtail.blocks.StructBlock', [[('page', 0), ('document', 1), ('title', 2)]], {}), 4: ('wagtail.blocks.URLBlock', (), {}), 5: ('wagtail.blocks.CharBlock', (), {'required': False}), 6: ('wagtail.blocks.BooleanBlock', (), {'help_text': 'Open the link in a new tab', 'required': False}), 7: ('wagtail.blocks.StructBlock', [[('link', 4), ('title', 5), ('link_target', 6)]], {})}, help_text='Additional footer links (Legal, Terms of Service, Privacy Policy, etc.)')),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale')),
                ('site', models.ForeignKey(help_text='Site this footer configuration belongs to', on_delete=django.db.models.deletion.CASCADE, to='wagtailcore.site')),
                ('footer_navigation', models.ForeignKey(blank=True, help_text='Optional footer navigation menu', null=True, on_delete=django.db.models.deletion.SET_NULL, to='wagtail_feathers.footernavigation')),
            ],
            options={
                'verbose_name': 'Footer',
                'verbose_name_plural': 'Footers',
            },
        ),
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('name', models.CharField(max_length=100)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, help_text='Auto-generated from name, but can be edited', populate_from='name', unique=True)),
                ('description', models.TextField(blank=True)),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale')),
            ],
            options={
                'verbose_name': 'Menu',
                'verbose_name_plural': 'Menus',
            },
        ),
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('title', models.CharField(help_text='Title of menu item, 100 characters max.', max_length=100)),
                ('menu_item', wagtail.fields.StreamField([('internal', 3), ('external', 7)], blank=True, block_lookup={0: ('wagtail.blocks.PageChooserBlock', (), {'required': False}), 1: ('wagtail.documents.blocks.DocumentChooserBlock', (), {'required': False}), 2: ('wagtail.blocks.CharBlock', (), {'help_text': "Leave blank to use link's title.", 'required': False}), 3: ('wagtail.blocks.StructBlock', [[('page', 0), ('document', 1), ('title', 2)]], {}), 4: ('wagtail.blocks.URLBlock', (), {}), 5: ('wagtail.blocks.CharBlock', (), {'required': False}), 6: ('wagtail.blocks.BooleanBlock', (), {'help_text': 'Open the link in a new tab', 'required': False}), 7: ('wagtail.blocks.StructBlock', [[('link', 4), ('title', 5), ('link_target', 6)]], {})})),
                ('menu', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='menu_items', to='wagtail_feathers.menu')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='wagtail_feathers.menuitem')),
            ],
            options={
                'verbose_name': 'Menu Item',
                'verbose_name_plural': 'Menu Items',
                'ordering': ['sort_order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='NestedMenu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('name', models.CharField(max_length=100)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, help_text='Auto-generated from name, but can be edited', populate_from='name', unique=True)),
                ('menu_items', wagtail.fields.StreamField([('submenu', 21), ('internal', 4), ('external', 8), ('page_links', 17)], blank=True, block_lookup={0: ('wagtail.blocks.CharBlock', (), {'label': 'Submenu Display Title', 'max_length': 100}), 1: ('wagtail.blocks.PageChooserBlock', (), {'required': False}), 2: ('wagtail.documents.blocks.DocumentChooserBlock', (), {'required': False}), 3: ('wagtail.blocks.CharBlock', (), {'help_text': "Leave blank to use link's title.", 'required': False}), 4: ('wagtail.blocks.StructBlock', [[('page', 1), ('document', 2), ('title', 3)]], {}), 5: ('wagtail.blocks.URLBlock', (), {}), 6: ('wagtail.blocks.CharBlock', (), {'required': False}), 7: ('wagtail.blocks.BooleanBlock', (), {'help_text': 'Open the link in a new tab', 'required': False}), 8: ('wagtail.blocks.StructBlock', [[('link', 5), ('title', 6), ('link_target', 7)]], {}), 9: ('wagtail.blocks.CharBlock', (), {'help_text': 'Optional label for the divider section', 'max_length': 50, 'required': False}), 10: ('wagtail.blocks.StructBlock', [[('label', 9)]], {}), 11: ('wagtail.blocks.StreamBlock', [[('internal_link', 4), ('external_link', 8), ('divider', 10)]], {}), 12: ('wagtail.blocks.StructBlock', [[('title', 0), ('menu_items', 11)]], {'_depth': 3}), 13: ('wagtail.blocks.PageChooserBlock', (), {'help_text': 'Select a page to use its children as menu items', 'required': True}), 14: ('wagtail.blocks.IntegerBlock', (), {'default': 1, 'help_text': 'Maximum number of levels to show from page hierarchy', 'max_value': 5, 'min_value': 1}), 15: ('wagtail.blocks.BooleanBlock', (), {'default': False, 'help_text': 'Include the parent page as a menu item', 'required': False}), 16: ('wagtail.blocks.CharBlock', (), {'help_text': 'Optional title to display instead of the parent page title', 'max_length': 100, 'required': False}), 17: ('wagtail.blocks.StructBlock', [[('parent_page', 13), ('max_levels', 14), ('show_parent', 15), ('title', 16)]], {}), 18: ('wagtail.blocks.StreamBlock', [[('submenu', 12), ('autofill_submenu', 17), ('internal_link', 4), ('external_link', 8), ('divider', 10)]], {}), 19: ('wagtail.blocks.StructBlock', [[('title', 0), ('menu_items', 18)]], {'_depth': 2}), 20: ('wagtail.blocks.StreamBlock', [[('submenu', 19), ('autofill_submenu', 17), ('internal_link', 4), ('external_link', 8), ('divider', 10)]], {}), 21: ('wagtail.blocks.StructBlock', [[('title', 0), ('menu_items', 20)]], {'_depth': 1})})),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale')),
            ],
            options={
                'verbose_name': 'Nested Menu',
                'verbose_name_plural': 'Nested Menus',
            },
        ),
        migrations.CreateModel(
            name='PageCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pages', to='wagtail_feathers.category')),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='wagtailcore.page')),
            ],
        ),
        migrations.CreateModel(
            name='PageClassifier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('classifier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pages', to='wagtail_feathers.classifier')),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='classifiers', to='wagtailcore.page')),
            ],
        ),
        migrations.CreateModel(
            name='PageCountry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('countries', django_countries.fields.CountryField(blank=True, default=list, max_length=2, verbose_name='Countries')),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='countries', to='wagtailcore.page')),
            ],
            options={
                'verbose_name': 'Page Countries',
                'verbose_name_plural': 'Page Countries',
            },
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=254, verbose_name='First name')),
                ('last_name', models.CharField(max_length=254, verbose_name='Last name')),
                ('email', models.EmailField(blank=True, error_messages={'unique': 'A person with that email already exists.'}, max_length=254, unique=True, verbose_name='email address')),
                ('display_name', models.CharField(blank=True, max_length=254, verbose_name='Display name')),
                ('bio', wagtail.fields.RichTextField(blank=True)),
                ('image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=get_image_model_string())),
                ('user', models.OneToOneField(blank=True, help_text='Link to a system user account, if this person is a registered user.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='person_profile', to=settings.AUTH_USER_MODEL)),
                ('groups', modelcluster.fields.ParentalManyToManyField(blank=True, help_text='Select all that apply', to='wagtail_feathers.persongroup')),
            ],
            options={
                'verbose_name': 'Person',
                'verbose_name_plural': 'People',
            },
            bases=(wagtail.search.index.Indexed, models.Model),
        ),
        migrations.CreateModel(
            name='PageAuthor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='authors', to='wagtail_feathers.featherbasepage')),
                ('type', models.ForeignKey(blank=True, help_text="Select the author's role or type", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtail_feathers.authortype', verbose_name='Type')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtail_feathers.person', verbose_name='Person')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RelatedDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('title', models.CharField(blank=True, max_length=255)),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='related_documents', to='wagtailcore.page')),
                ('url', models.ForeignKey(help_text='Document download', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=get_document_model_string())),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RelatedExternalLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('title', models.CharField(max_length=255)),
                ('url', models.URLField(blank=True, verbose_name='url')),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='related_links', to='wagtailcore.page')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RelatedPage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('title', models.CharField(blank=True, max_length=255)),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='page_related_pages', to='wagtailcore.page')),
                ('url', models.ForeignKey(help_text='Internal page', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailcore.page')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title_suffix', models.CharField(default='Feathers Library', help_text="The suffix for the title meta tag e.g. ' | Feathers Library'", max_length=255, verbose_name='Title suffix')),
                ('active_theme', models.CharField(blank=True, default='', help_text='Select the active theme for this site', max_length=100, verbose_name='Active theme')),
                ('words_per_minute', models.PositiveIntegerField(default=200, help_text='Average reading speed for reading time calculation. Default: 200 WPM (average adult reading speed)', verbose_name='Words per minute')),
                ('placeholder_image', models.ForeignKey(blank=True, help_text='Choose the image you wish to be displayed as a placeholder image.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=get_image_model_string())),
                ('site', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, to='wagtailcore.site')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SocialMediaSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('name', models.CharField(default='Social Media', help_text='Name for this social media configuration', max_length=100)),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale')),
                ('site', models.ForeignKey(help_text='Site this social media configuration belongs to', on_delete=django.db.models.deletion.CASCADE, to='wagtailcore.site')),
            ],
            options={
                'verbose_name': 'Social Media Settings',
                'verbose_name_plural': 'Social Media Settings',
            },
        ),
        migrations.CreateModel(
            name='SocialMediaLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('name', models.CharField(help_text='Name of the social media platform', max_length=100)),
                ('url', models.URLField(help_text='URL to your social media profile')),
                ('handle', models.CharField(blank=True, help_text='Optional handle or ID if a URL is not available', max_length=100)),
                ('icon', models.CharField(blank=True, help_text='Icon to use', max_length=50)),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale')),
                ('setting', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_media_links', to='wagtail_feathers.socialmediasettings')),
            ],
            options={
                'verbose_name': 'Social Media Link',
                'verbose_name_plural': 'Social Media Links',
            },
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['live', 'path'], name='wagtail_fea_live_e3418e_idx'),
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['slug'], name='wagtail_fea_slug_19ce11_idx'),
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['depth', 'live'], name='wagtail_fea_depth_a1509a_idx'),
        ),
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_translation_key_locale_wagtail_feathers_category'),
        ),
        migrations.AddIndex(
            model_name='classifiergroup',
            index=models.Index(fields=['id'], name='wagtail_fea_id_87f5bb_idx'),
        ),
        migrations.AddConstraint(
            model_name='classifiergroup',
            constraint=models.UniqueConstraint(fields=('type', 'name', 'locale'), name='unique_classifier_group_type_name_locale'),
        ),
        migrations.AddConstraint(
            model_name='classifiergroup',
            constraint=models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_translation_key_locale_wagtail_feathers_classifiergroup'),
        ),
        migrations.AddIndex(
            model_name='classifier',
            index=models.Index(fields=['group', 'name'], name='wagtail_fea_group_i_de4b37_idx'),
        ),
        migrations.AddIndex(
            model_name='classifier',
            index=models.Index(fields=['slug'], name='wagtail_fea_slug_c7af7d_idx'),
        ),
        migrations.AddConstraint(
            model_name='classifier',
            constraint=models.UniqueConstraint(fields=('group', 'name', 'locale'), name='unique_classifier_group_name_locale'),
        ),
        migrations.AddConstraint(
            model_name='classifier',
            constraint=models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_translation_key_locale_wagtail_feathers_classifier'),
        ),
        migrations.AddConstraint(
            model_name='faq',
            constraint=models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_faq_translation_key_locale'),
        ),
        migrations.AddConstraint(
            model_name='faqitem',
            constraint=models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_faq_item_translation_key_locale'),
        ),
        migrations.AddConstraint(
            model_name='flatmenu',
            constraint=models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_flatnavigationmenu_translation_key_locale'),
        ),
        migrations.AddConstraint(
            model_name='footernavigation',
            constraint=models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_footernavigation_translation_key_locale'),
        ),
        migrations.AddConstraint(
            model_name='footer',
            constraint=models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_footer_translation_key_locale'),
        ),
        migrations.AddConstraint(
            model_name='menu',
            constraint=models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_menu_translation_key_locale'),
        ),
        migrations.AddConstraint(
            model_name='nestedmenu',
            constraint=models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_nestedmenu_translation_key_locale'),
        ),
        migrations.AddConstraint(
            model_name='pagecategory',
            constraint=models.UniqueConstraint(fields=('page', 'category'), name='unique_page_category'),
        ),
        migrations.AddConstraint(
            model_name='pageclassifier',
            constraint=models.UniqueConstraint(fields=('page', 'classifier'), name='unique_page_classifier'),
        ),
        migrations.AddConstraint(
            model_name='socialmediasettings',
            constraint=models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_socialmediasettings_translation_key_locale'),
        ),
        migrations.AddConstraint(
            model_name='socialmedialink',
            constraint=models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_socialmedialink_translation_key_locale'),
        ),
    ]
