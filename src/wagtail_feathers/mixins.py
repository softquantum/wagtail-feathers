import json
import re
from urllib.parse import urljoin

from django import forms
from django.db import models
from modelcluster.fields import ParentalManyToManyField
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel, ObjectList, TabbedInterface
from wagtail.images import get_image_model_string
from wagtail.utils.decorators import cached_classmethod

try:
    from wagtail_localize.fields import TranslatableField

    WAGTAIL_LOCALIZE_AVAILABLE = True
except ImportError:
    WAGTAIL_LOCALIZE_AVAILABLE = False


class TimestampMixin(models.Model):
    """Mixin to add timestamp fields to models."""

    created_at = models.DateTimeField(_("Created at"), default=timezone.now, editable=False)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        abstract = True


class ReadingTimeMixin(models.Model):
    """
    Mixin providing reading time calculation for pages with substantial text content.

    Features:
    - Automatic word count from StreamField and RichTextField content
    - Configurable words-per-minute rate
    - Manual override capability
    - SEO integration (structured data, Twitter Cards)
    - Multi-language support

    Best used with: Blog posts, articles, documentation, long-form content
    """

    reading_time_minutes = models.PositiveIntegerField(
            null=True,
            blank=True,
            help_text=_("Estimated reading time in minutes (leave blank to auto-calculate from content)")
    )

    # Admin panels
    reading_time_panels = [
        FieldPanel('reading_time_minutes'),
    ]

    class Meta:
        abstract = True

    def get_words_per_minute(self):
        """Get words per minute from site settings, with fallback to default."""
        try:
            from wagtail_feathers.models.settings import SiteSettings
            # Try to get site from page model
            if hasattr(self, 'get_site'):
                site = self.get_site()
            else:
                # Fallback to default site
                from wagtail.models import Site
                site = Site.objects.filter(is_default_site=True).first()

            if site:
                site_settings = SiteSettings.for_site(site)
                return site_settings.words_per_minute
        except (ImportError, AttributeError, Exception):
            pass

        # Fallback to default if site settings not available
        return 200

    def save(self, *args, **kwargs):
        """Auto-calculate reading time on save."""
        # Calculate reading time before saving, but only if not in a partial update
        # or if reading_time_minutes is specifically being updated
        update_fields = kwargs.get('update_fields')

        if not update_fields or 'reading_time_minutes' in update_fields:
            calculated_time = self.calculate_reading_time()
            if self.reading_time_minutes != calculated_time:
                self.reading_time_minutes = calculated_time
                # Add reading_time_minutes to update_fields if it exists
                if update_fields:
                    update_fields = set(update_fields)
                    update_fields.add('reading_time_minutes')
                    kwargs['update_fields'] = list(update_fields)

        return super().save(*args, **kwargs)

    def calculate_reading_time(self):
        """
        Calculate reading time based on content using site-wide words per minute setting.

        Returns:
            int: Reading time in minutes (minimum 1)
        """
        word_count = self.get_word_count()

        if word_count == 0:
            return 1

        # Get words per minute from site settings
        words_per_minute = self.get_words_per_minute()

        # Calculate reading time in minutes, minimum 1 minute
        reading_time = max(1, round(word_count / words_per_minute))
        return reading_time

    def get_word_count(self):
        """
        Extract and count words from all text content on the page.

        Returns:
            int: Total word count
        """
        total_words = 0

        # Count words in StreamField body content
        if hasattr(self, 'body') and self.body:
            total_words += self._count_streamfield_words(self.body)

        # Count words in RichTextField introduction
        if hasattr(self, 'introduction') and self.introduction:
            total_words += self._count_text_words(str(self.introduction))

        # Count words in title
        if hasattr(self, 'title') and self.title:
            total_words += self._count_text_words(self.title)

        # Allow subclasses to add more text sources
        additional_words = self.get_additional_word_sources()
        total_words += additional_words

        return total_words

    def get_additional_word_sources(self):
        """
        Override this method to include additional text sources in word count.

        Returns:
            int: Additional word count from custom fields

        Example:
            def get_additional_word_sources(self):
                words = 0
                if hasattr(self, 'summary') and self.summary:
                    words += self._count_text_words(self.summary)
                if hasattr(self, 'conclusion') and self.conclusion:
                    words += self._count_text_words(str(self.conclusion))
                return words
        """
        return 0

    def _count_streamfield_words(self, streamfield):
        """Count words in StreamField content."""
        total_words = 0

        for block in streamfield:
            if hasattr(block.value, 'source'):  # RichTextBlock
                total_words += self._count_text_words(block.value.source)
            elif block.block_type == 'paragraph_block':
                total_words += self._count_text_words(str(block.value))
            elif block.block_type == 'markdown_block':
                total_words += self._count_text_words(str(block.value))
            elif block.block_type == 'heading_block':
                # Extract text from heading block
                if hasattr(block.value, 'get'):
                    text = block.value.get('text', '')
                    total_words += self._count_text_words(text)
            elif hasattr(block.value, '__str__'):
                # Fallback for other text-containing blocks
                text_content = str(block.value)
                if len(text_content) > 10:  # Only count substantial text
                    total_words += self._count_text_words(text_content)

        return total_words

    def _count_text_words(self, text):
        """
        Count words in a text string, handling HTML and special characters.

        Args:
            text (str): Text content to count

        Returns:
            int: Word count
        """
        if not text or not isinstance(text, str):
            return 0

        # Strip HTML tags
        clean_text = strip_tags(text)

        # Remove extra whitespace and special characters that aren't word separators
        clean_text = re.sub(r'[^\w\s]', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)

        # Split into words and filter out empty strings
        words = [word.strip() for word in clean_text.split() if word.strip()]

        return len(words)

    def get_reading_time_display(self, format_type="default"):
        """
        Get formatted reading time for display.

        Args:
            format_type (str): Display format ("default", "short", "long", "seo")

        Returns:
            str: Formatted reading time string
        """
        if not self.reading_time_minutes:
            return ""

        minutes = self.reading_time_minutes

        if format_type == "short":
            return f"{minutes}m"
        elif format_type == "long":
            if minutes == 1:
                return _("1 minute read")
            else:
                return _("%(minutes)d minutes read") % {"minutes": minutes}
        elif format_type == "seo":
            # ISO 8601 duration format for structured data
            return f"PT{minutes}M"
        else:  # default
            if minutes == 1:
                return _("1 min read")
            else:
                return _("%(minutes)d min read") % {"minutes": minutes}

    def get_reading_time_for_seo(self):
        """
        Get reading time in format suitable for SEO/structured data.

        Returns:
            dict: SEO-related reading time data
        """
        if not self.reading_time_minutes:
            return {}

        return {
            'duration_iso': self.get_reading_time_display('seo'),
            'duration_text': self.get_reading_time_display('long'),
            'minutes': self.reading_time_minutes,
            'twitter_label': _("Reading time"),
            'twitter_data': self.get_reading_time_display('default'),
        }

    # Extension points for SEO integration
    def get_custom_twitter_tags(self):
        """Add reading time to Twitter Card tags."""
        tags = {}

        # Call parent method if it exists
        if hasattr(super(), 'get_custom_twitter_tags'):
            tags.update(super().get_custom_twitter_tags())

        # Add reading time if available
        if self.reading_time_minutes:
            seo_data = self.get_reading_time_for_seo()
            tags.update({
                'twitter:label1': seo_data['twitter_label'],
                'twitter:data1': seo_data['twitter_data'],
            })

        return tags

    def get_custom_meta_tags(self):
        """Add reading time to meta tags."""
        tags = {}

        # Call parent method if it exists
        if hasattr(super(), 'get_custom_meta_tags'):
            tags.update(super().get_custom_meta_tags())

        # Add reading time if available
        if self.reading_time_minutes:
            tags['article:reading_time'] = str(self.reading_time_minutes)

        return tags

    def _enhance_article_schema(self, schema):
        """Add reading time to article structured data."""
        if self.reading_time_minutes:
            seo_data = self.get_reading_time_for_seo()
            schema['timeRequired'] = seo_data['duration_iso']
        return schema

    def get_structured_data(self):
        """Override to add reading time to structured data."""
        # Get parent structured data
        if hasattr(super(), 'get_structured_data'):
            schema_str = super().get_structured_data()
            if schema_str and self.reading_time_minutes:
                import json
                try:
                    schema = json.loads(schema_str)
                    if schema.get('@type') == 'Article':
                        schema = self._enhance_article_schema(schema)
                        return json.dumps(schema, ensure_ascii=False)
                except (json.JSONDecodeError, AttributeError):
                    pass
            return schema_str

        return None

    class Meta:
        abstract = True


class AuthorShipMixin(models.Model):
    """Mixin to add author fields to pages."""

    display_authors = models.BooleanField(
        default=False,
        help_text="Display author names on the page.",
    )

    authorship_panels = [
        FieldPanel("display_authors"),
        InlinePanel("authors", label=_("Authors")),
    ]

    class Meta:
        abstract = True


class GeoMixin(models.Model):
    """Mixin to add geographic fields to pages."""

    country = CountryField(blank=True, help_text="Country linked to the page.")
    country_groups = ParentalManyToManyField(
        'wagtail_feathers.CountryGroup',
        blank=True,
        help_text=_("Select predefined country groups")
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    geographic_panels = [
        FieldPanel("country_groups", widget=forms.CheckboxSelectMultiple),
        InlinePanel("countries", label=_("Countries")),
        FieldRowPanel([
            FieldPanel("latitude"),
            FieldPanel("longitude"),
        ]),
    ]

    class Meta:
        abstract = True

    def get_all_countries(self):
        """Get all countries from both groups and individual selections."""
        countries = set()
        
        # Add countries from groups
        for group in self.country_groups.all():
            countries.update(group.get_country_codes())
        
        # Add individual country selection
        if self.country:
            countries.add(str(self.country))
        
        # Add countries from PageCountry relationships
        for page_country in self.countries.all():
            if page_country.countries:
                countries.add(str(page_country.countries))
        
        return list(countries)

    def get_countries_from_groups(self):
        """Get list of countries from selected groups only."""
        countries = set()
        for group in self.country_groups.all():
            countries.update(group.get_country_codes())
        return list(countries)

    def get_countries_display(self):
        """Get formatted display of all effective countries."""
        from django_countries import countries as all_countries
        
        country_codes = self.get_all_countries()
        if not country_codes:
            return _("No countries selected")
        
        country_names = []
        for code in country_codes:
            try:
                country_names.append(all_countries.name(code))
            except KeyError:
                country_names.append(code)
        
        return ", ".join(sorted(country_names))


"""
SEO functionality for Wagtail Feathers pages.

Extends Wagtail's built-in SEO capabilities with additional features like
Open Graph, Twitter Cards, structured data, and enhanced meta tag management.
Uses Wagtail's existing seo_title and search_description fields.
"""

class SeoContentType(models.TextChoices):
    """Content types for structured data markup.

    See: https://schema.org/docs/schemas.html
    """
    WEBSITE = 'website', _('Website')
    ARTICLE = 'article', _('Article')
    PRODUCT = 'product', _('Product')
    EVENT = 'event', _('Event')
    ORGANIZATION = 'organization', _('Organization')
    PERSON = 'person', _('Person')


class TwitterCardType(models.TextChoices):
    """Twitter card display types."""
    SUMMARY = 'summary', _('Summary')
    SUMMARY_LARGE_IMAGE = 'summary_large_image', _('Summary with Large Image')


class SeoMixin(models.Model):
    """
    Mixin providing enhanced SEO functionality for Wagtail pages.

    Included in FeatherPage model.
    Extends Wagtail's built-in SEO fields (seo_title, search_description) with:
    - Open Graph and Twitter Card support
    - Canonical URL management
    - Structured data generation
    - Smart fallbacks for missing content
    - Search engine directives

    Note: Uses Wagtail's existing seo_title and search_description fields
    to avoid duplication.
    """

    # Social media and Open Graph image
    og_image = models.ForeignKey(
            get_image_model_string(),
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name='+',
            help_text=_("Image for social media sharing (Open Graph/Twitter). Recommended: 1200x630px")
    )

    # Canonical URL override
    canonical_url = models.URLField(
            blank=True,
            help_text=_("Canonical URL if different from page URL (for duplicate content)")
    )

    # Content type and social settings
    seo_content_type = models.CharField(
            max_length=20,
            choices=SeoContentType.choices,
            default=SeoContentType.WEBSITE,
            help_text=_("Content type for structured data markup")
    )

    twitter_card_type = models.CharField(
            max_length=20,
            choices=TwitterCardType.choices,
            default=TwitterCardType.SUMMARY,
            help_text=_("Twitter card display style")
    )

    # Search engine directives
    no_index = models.BooleanField(
            default=False,
            help_text=_("Prevent search engines from indexing this page")
    )

    no_follow = models.BooleanField(
            default=False,
            help_text=_("Prevent search engines from following links on this page")
    )

    seo_panels = [
        MultiFieldPanel([
            FieldPanel('og_image'),
            FieldPanel('canonical_url'),
            FieldRowPanel([
                FieldPanel('seo_content_type'),
                FieldPanel('twitter_card_type'),
            ]),
            FieldRowPanel([
                FieldPanel('no_index'),
                FieldPanel('no_follow'),
            ]),
        ], heading=_("SEO")),
    ]

    # Translation support
    if WAGTAIL_LOCALIZE_AVAILABLE:
        override_translatable_fields = [
            TranslatableField("canonical_url"),
        ]

    class Meta:
        abstract = True

    def get_seo_title(self):
        """Get SEO title using Wagtail's built-in field with smart fallbacks."""
        # Use Wagtail's built-in seo_title field first
        if hasattr(self, 'seo_title') and self.seo_title:
            return self.seo_title

        # Fallback to page title
        if hasattr(self, 'title') and self.title:
            return self.title

        # Last resort - site name
        if hasattr(self, 'get_site') and self.get_site():
            return self.get_site().site_name

        return "Untitled"

    def get_seo_description(self):
        """Get SEO description using Wagtail's built-in field with smart fallbacks."""
        # Use Wagtail's built-in search_description field first
        if hasattr(self, 'search_description') and self.search_description:
            return self.search_description

        # Try introduction field (common in ItemPage)
        if hasattr(self, 'introduction') and self.introduction:
            return strip_tags(str(self.introduction))[:160]

        # Try extracting from body content
        if hasattr(self, 'body') and self.body:
            # Extract text from StreamField
            text_content = ""
            for block in self.body:
                if hasattr(block.value, 'source'):  # RichText block
                    text_content += strip_tags(str(block.value.source)) + " "
                elif hasattr(block.value, 'get') and 'text' in str(block.value):
                    # Handle various text blocks
                    text_content += strip_tags(str(block.value)) + " "

            if text_content.strip():
                return Truncator(text_content.strip()).chars(160)

        # Fallback to search description from Page model
        if hasattr(self, 'search_description') and self.search_description:
            return self.search_description

        return f"Learn more about {self.get_seo_title()}"

    def get_seo_image(self):
        """Get SEO image with smart fallbacks."""
        if self.og_image:
            return self.og_image

        # Try featured image (common in ItemPage)
        if hasattr(self, 'image') and self.image:
            return self.image

        # Try to extract image from body content
        if hasattr(self, 'body') and self.body:
            for block in self.body:
                if hasattr(block.value, 'get') and 'image' in str(block.value):
                    # Extract image from image blocks
                    if hasattr(block.value, 'get'):
                        image = block.value.get('image')
                        if image:
                            return image

        # TODO: Could fallback to site default logo/image
        return None

    def get_canonical_url(self):
        """Get canonical URL with fallback to page URL."""
        if self.canonical_url:
            return self.canonical_url

        if hasattr(self, 'get_full_url'):
            return self.get_full_url()

        return None

    def get_robots_content(self):
        """Generate robots meta tag content."""
        directives = []

        if self.no_index:
            directives.append('noindex')
        else:
            directives.append('index')

        if self.no_follow:
            directives.append('nofollow')
        else:
            directives.append('follow')

        return ', '.join(directives)

    def get_structured_data(self):
        """Generate JSON-LD structured data based on content type."""
        if not hasattr(self, 'get_site') or not self.get_site():
            return None

        site = self.get_site()
        base_url = site.root_url if site.root_url else f"https://{site.hostname}"

        # Base schema
        schema = {
            "@context": "https://schema.org",
            "@type": self.get_content_type_schema(),
            "name": self.get_seo_title(),
            "description": self.get_seo_description(),
            "url": urljoin(base_url, self.url) if hasattr(self, 'url') else None,
        }

        # Add image if available
        seo_image = self.get_seo_image()
        if seo_image:
            try:
                image_url = urljoin(base_url, seo_image.file.url)
                schema["image"] = {
                    "@type": "ImageObject",
                    "url": image_url,
                    "width": seo_image.width,
                    "height": seo_image.height,
                }
            except:
                pass

        # Add content-type specific fields
        if self.seo_content_type == SeoContentType.ARTICLE:
            self._add_article_schema(schema)
        elif self.seo_content_type == SeoContentType.ORGANIZATION:
            self._add_organization_schema(schema)

        return json.dumps(schema, ensure_ascii=False)

    def get_content_type_schema(self):
        """Map content type to Schema.org type."""
        mapping = {
            SeoContentType.WEBSITE: "WebPage",
            SeoContentType.ARTICLE: "Article",
            SeoContentType.PRODUCT: "Product",
            SeoContentType.EVENT: "Event",
            SeoContentType.ORGANIZATION: "Organization",
            SeoContentType.PERSON: "Person",
        }
        return mapping.get(self.seo_content_type, "WebPage")

    def _add_article_schema(self, schema):
        """Add article-specific structured data."""
        schema["@type"] = "Article"

        # Add publication date
        if hasattr(self, 'publication_date') and self.publication_date:
            schema["datePublished"] = self.publication_date.isoformat()

        if hasattr(self, 'revision_date') and self.revision_date:
            schema["dateModified"] = self.revision_date.isoformat()
        elif hasattr(self, 'last_published_at') and self.last_published_at:
            schema["dateModified"] = self.last_published_at.isoformat()

        # Add author information
        if hasattr(self, 'authors') and self.authors.exists():
            authors = []
            for page_author in self.authors.all():
                if hasattr(page_author, 'person'):
                    person = page_author.person
                    author_schema = {
                        "@type": "Person",
                        "name": f"{person.first_name} {person.last_name}".strip(),
                    }
                    if hasattr(person, 'email') and person.email:
                        author_schema["email"] = person.email
                    authors.append(author_schema)

            if authors:
                schema["author"] = authors if len(authors) > 1 else authors[0]

    def _add_organization_schema(self, schema):
        """Add organization-specific structured data."""
        schema["@type"] = "Organization"

        # Add logo if available
        seo_image = self.get_seo_image()
        if seo_image:
            try:
                site = self.get_site()
                base_url = site.root_url if site.root_url else f"https://{site.hostname}"
                schema["logo"] = urljoin(base_url, seo_image.file.url)
            except:
                pass

    # Extension points for custom implementations
    def get_custom_meta_tags(self):
        """
        Override this method to add custom meta tags.

        Returns:
            dict: Dictionary of meta tag name/content pairs

        Example:
            return {
                'keywords': 'python, django, wagtail',
                'author': 'John Doe',
                'robots': 'index, follow, max-snippet:-1'
            }
        """
        return {}

    def get_custom_og_tags(self):
        """
        Override this method to add custom Open Graph tags.

        Returns:
            dict: Dictionary of Open Graph property/content pairs

        Example:
            return {
                'og:article:author': 'https://facebook.com/johndoe',
                'og:article:section': 'Technology',
                'fb:app_id': '123456789'
            }
        """
        return {}

    def get_custom_twitter_tags(self):
        """
        Override this method to add custom Twitter Card tags.

        Returns:
            dict: Dictionary of Twitter meta name/content pairs

        Example:
            return {
                'twitter:site': '@mysite',
                'twitter:creator': '@johndoe',
                'twitter:label1': 'Reading time',
                'twitter:data1': '5 min read'
            }
        """
        return {}

    def should_include_in_sitemap(self):
        """
        Determine if this page should be included in XML sitemaps.

        Returns:
            bool: True if page should be included in sitemap
        """
        # Don't include if marked as no-index
        if self.no_index:
            return False

        # Don't include if not live
        if hasattr(self, 'live') and not self.live:
            return False

        return True

    def get_sitemap_priority(self):
        """
        Get the sitemap priority for this page (0.0 to 1.0).

        Returns:
            float: Priority value between 0.0 and 1.0
        """
        # Default priority based on content type
        if self.seo_content_type == SeoContentType.ARTICLE:
            return 0.8
        elif self.seo_content_type == SeoContentType.PRODUCT:
            return 0.9
        else:
            return 0.5

    def get_sitemap_changefreq(self):
        """
        Get the sitemap change frequency for this page.

        Returns:
            str: Change frequency ('always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never')
        """
        # Default change frequency based on content type
        if self.seo_content_type == SeoContentType.ARTICLE:
            return 'monthly'
        elif self.seo_content_type == SeoContentType.PRODUCT:
            return 'weekly'
        else:
            return 'yearly'

    class Meta:
        abstract = True
