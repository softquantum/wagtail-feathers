"""
SEO functionality for Wagtail Feathers pages.

Extends Wagtail's built-in SEO capabilities with additional features like
Open Graph, Twitter Cards, structured data, and enhanced meta tag management.
Uses Wagtail's existing seo_title and search_description fields.
"""

import json
from urllib.parse import urljoin

from django.db import models
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.images import get_image_model_string

try:
    from wagtail_localize.fields import TranslatableField
    WAGTAIL_LOCALIZE_AVAILABLE = True
except ImportError:
    WAGTAIL_LOCALIZE_AVAILABLE = False


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
    
    # SEO panel for admin
    seo_panels = [
        FieldPanel('og_image'),
        FieldPanel('canonical_url'),
        FieldPanel('seo_content_type'),
        FieldPanel('twitter_card_type'),
        FieldPanel('no_index'),
        FieldPanel('no_follow'),
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