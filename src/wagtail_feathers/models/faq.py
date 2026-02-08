"""
FAQ models for structured question and answer content.

Provides translatable FAQ items organized by categories with admin management.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, TranslatableMixin
from wagtail.search import index

try:
    from wagtail_localize.fields import SynchronizedField
    WAGTAIL_LOCALIZE_AVAILABLE = True
except ImportError:
    WAGTAIL_LOCALIZE_AVAILABLE = False


class FAQ(TranslatableMixin, ClusterableModel):
    """Group of FAQ items."""
    
    name = models.CharField(max_length=150)

    slug = AutoSlugField(populate_from="name", editable=True)
    
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
    
    # Translation support, only sync the slug, auto discover the rest
    if WAGTAIL_LOCALIZE_AVAILABLE:
        override_translatable_fields = [
            SynchronizedField('slug'),
        ]
    
    class Meta:
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQs")
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=["translation_key", "locale"], name="unique_faq_translation_key_locale"
            )
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def published_faqs(self):
        """Get published FAQ items for this FAQ."""
        return self.faqs.filter(live=True).order_by('sort_order')


class FAQItem(TranslatableMixin, index.Indexed, Orderable):
    """Individual FAQ item within a FAQ."""
    
    faq = ParentalKey(
        FAQ,
        on_delete=models.CASCADE,
        related_name='faqs'
    )
    
    question = models.CharField(
        max_length=255,
        help_text=_("The FAQ question")
    )
    
    answer = RichTextField(
        features=["bold", "italic", "link", "ul", "ol", "document-link"],
        help_text=_("The answer to the question")
    )
    
    live = models.BooleanField(
        default=True,
        help_text=_("Whether this FAQ is published and visible")
    )
    
    panels = [
        FieldPanel('question'),
        FieldPanel('answer'),
        FieldPanel('live'),
    ]

    search_fields = [
        index.SearchField('question'),
        index.SearchField('answer'),
    ]
    
    class Meta:
        verbose_name = _("FAQ Item")
        verbose_name_plural = _("FAQ Items")
        ordering = ['sort_order']
        constraints = [
            models.UniqueConstraint(
                fields=["translation_key", "locale"], name="unique_faq_item_translation_key_locale"
            )
        ]
    
    def __str__(self):
        return self.question
    