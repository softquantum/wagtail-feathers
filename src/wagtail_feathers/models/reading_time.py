"""
Reading time functionality for Wagtail Feathers pages.

Provides automatic reading time calculation for content-heavy pages,
with SEO integration and customizable word-per-minute rates.
"""

import re
from django.db import models
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel


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
