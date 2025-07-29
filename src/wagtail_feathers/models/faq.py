"""
FAQ models for structured question and answer content.

Provides translatable FAQ items organized by categories with admin management.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, TranslatableMixin
from wagtail.search import index

try:
    from wagtail_localize.fields import TranslatableField
    WAGTAIL_LOCALIZE_AVAILABLE = True
except ImportError:
    WAGTAIL_LOCALIZE_AVAILABLE = False


class FAQCategory(TranslatableMixin, ClusterableModel):
    """Category for organizing FAQ items."""
    
    name = models.CharField(
        max_length=100,
        help_text=_("Category name")
    )
    
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text=_("URL-friendly version of the name")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Optional description of this FAQ category")
    )
    
    # Admin panels
    panels = [
        FieldPanel('name'),
        FieldPanel('slug'),
        FieldPanel('description'),
        InlinePanel('faqs', label=_("FAQ Items")),
    ]
    
    # Translation support
    if WAGTAIL_LOCALIZE_AVAILABLE:
        translatable_fields = [
            TranslatableField('name'),
            TranslatableField('description'),
        ]
    
    class Meta:
        verbose_name = _("FAQ Category")
        verbose_name_plural = _("FAQ Categories")
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=["translation_key", "locale"], name="unique_faqcategory_translation_key_locale"
            )
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def published_faqs(self):
        """Get published FAQ items for this category."""
        return self.faqs.filter(live=True).order_by('sort_order')


class FAQ(TranslatableMixin, index.Indexed, Orderable):
    """Individual FAQ item within a category."""
    
    category = ParentalKey(
        FAQCategory,
        on_delete=models.CASCADE,
        related_name='faqs'
    )
    
    question = models.CharField(
        max_length=200,
        help_text=_("The FAQ question")
    )
    
    answer = RichTextField(
        features=['bold', 'italic', 'link', 'ul', 'ol'],
        help_text=_("The answer to the question")
    )
    
    live = models.BooleanField(
        default=True,
        help_text=_("Whether this FAQ is published and visible")
    )
    
    # Admin panels
    panels = [
        FieldPanel('question'),
        FieldPanel('answer'),
        FieldPanel('live'),
    ]

    search_fields = [
        index.SearchField('question'),
        index.SearchField('answer'),
    ]
    
    # Translation support
    if WAGTAIL_LOCALIZE_AVAILABLE:
        translatable_fields = [
            TranslatableField('question'),
            TranslatableField('answer'),
        ]
    
    class Meta:
        verbose_name = _("FAQ Item")
        verbose_name_plural = _("FAQ Items")
        ordering = ['sort_order']
        constraints = [
            models.UniqueConstraint(
                fields=["translation_key", "locale"], name="unique_faq_translation_key_locale"
            )
        ]
    
    def __str__(self):
        return self.question