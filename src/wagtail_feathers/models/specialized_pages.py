"""
Specialized abstract page models for common website functionality.

These models provide foundations for form-based pages and FAQ pages.
They include the essential fields while remaining flexible for customization.
"""

from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.fields import RichTextField, StreamField

from wagtail_feathers.blocks import CommonContentBlock
from wagtail_feathers.forms import TemplateVariantFormPageForm

from .base import FeatherPage


class FormBasePage(AbstractEmailForm):
    """Abstract base for pages with form handling capabilities.
    
    Provides essential form fields and submission handling for any type of form
    (contact, subscription, registration, etc.) with email notification support.
    
    IMPORTANT: When extending this class, you must also create a FormField model:
    
        class MyFormField(AbstractFormField):
            page = ParentalKey('MyFormPage', on_delete=models.CASCADE, related_name='form_fields')
    
    Examples:
        # Contact form
        class ContactPage(FormBasePage):
            office_hours = models.TextField(blank=True)
            map_embed = models.TextField(blank=True)
        
        class ContactFormField(AbstractFormField):
            page = ParentalKey(ContactPage, on_delete=models.CASCADE, related_name='form_fields')
        
        # Subscription form
        class SubscriptionPage(FormBasePage):
            subscription_type = models.CharField(max_length=50)
            frequency = models.CharField(max_length=20)
        
        class SubscriptionFormField(AbstractFormField):
            page = ParentalKey(SubscriptionPage, on_delete=models.CASCADE, related_name='form_fields')

        Wagtail Convention:
        The FormMixin class (which AbstractEmailForm inherits) has a get_landing_page_template()
        method that automatically appends "_landing" to your template name.
    """
    template = "pages/form_page.html"
    base_form_class = TemplateVariantFormPageForm
    heading = RichTextField(blank=True, features=["bold", "italic"])
    body = RichTextField(blank=True, features=["h2", "h3", "superscript", "subscript", "strikethrough", "bold", "italic", "link", "document-link", "embed"])
    action_text = models.CharField(
        max_length=32,
        blank=True,
        help_text='Form action text.',
    )
    thank_you_text = RichTextField(blank=True, features=["h2", "h3", "superscript", "subscript", "strikethrough", "bold", "italic", "link", "document-link", "embed"])
    
    # Template variant selection
    template_variant = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional template variant (e.g., 'contact', 'newsletter'). Leave empty for default template.",
        verbose_name="Template Variant"
    )

    content_panels = AbstractEmailForm.content_panels + [
        FormSubmissionsPanel(),
        FieldPanel('heading'),
        FieldPanel('body'),
        InlinePanel('form_fields', label="Form fields"),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldPanel('from_address'),
            FieldPanel('to_address'),
            FieldPanel('subject'),
            FieldPanel('action_text'),
        ], "Email"),
    ]

    settings_panels = AbstractEmailForm.settings_panels + [
        FieldPanel("template_variant"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Validate that form_fields relation exists
        if not self._meta.abstract and not hasattr(self, 'form_fields'):
            raise NotImplementedError(
                f"{self.__class__.__name__} must have a related FormField model. "
                f"Create a FormField model with: "
                f"page = ParentalKey('{self.__class__.__name__}', on_delete=models.CASCADE, related_name='form_fields')"
            )

    def get_template(self, request, *args, **kwargs):
        """Override template selection to support variants."""
        if self.template_variant:
            # Construct variant template name
            base_template = getattr(self, 'template', None)
            if base_template:
                variant_template = base_template.replace('.html', f'--{self.template_variant}.html')
                
                # Check if variant template exists
                try:
                    from django.template.loader import get_template
                    get_template(variant_template)
                    return variant_template
                except:
                    # Fall back to default template if variant doesn't exist
                    pass
        
        return super().get_template(request, *args, **kwargs)

    def get_landing_page_template(self, request, *args, **kwargs):
        """Override landing page template selection to support variants."""
        if self.template_variant:
            # Construct variant landing template name
            base_template = getattr(self, 'template', None)
            if base_template:
                variant_landing_template = base_template.replace('.html', f'--{self.template_variant}_landing.html')
                
                # Check if variant landing template exists
                try:
                    from django.template.loader import get_template
                    get_template(variant_landing_template)
                    return variant_landing_template
                except:
                    # Fall back to default landing template if variant doesn't exist
                    pass
        
        return super().get_landing_page_template(request, *args, **kwargs)

    @classmethod
    def get_available_template_variants(cls):
        """Discover available template variants using theme system."""
        if not hasattr(cls, 'template') or not cls.template:
            return []
        
        from pathlib import Path

        from wagtail_feathers.themes import theme_registry
        
        base_template = cls.template
        variants = []
        
        try:
            # Parse the template path
            template_path = Path(base_template)
            template_dir = template_path.parent
            template_name = template_path.stem  # filename without extension
            
            # Get template directories from active theme
            theme_template_dirs = theme_registry.get_theme_template_dirs()
            
            for theme_template_dir in theme_template_dirs:
                # Look in the same directory structure as the template
                search_dir = theme_template_dir / template_dir
                if search_dir.exists():
                    # Scan for variants in the appropriate directory
                    for filename in search_dir.iterdir():
                        if filename.is_file() and filename.stem.startswith(f"{template_name}--"):
                            # Exclude landing pages from variant discovery
                            if not filename.name.endswith('_landing.html'):
                                variant = filename.stem.replace(f"{template_name}--", '')
                                if variant not in variants:
                                    variants.append(variant)
        except Exception:
            # Fallback to empty list if theme system fails
            pass
        
        return sorted(variants)

    class Meta:
        abstract = True
        verbose_name = _("Form Base Page")


class FAQBasePage(FeatherPage):
    """Abstract base for FAQ pages with model-based structured Q&A.
    
    Uses FAQ models for better translation support and data management.
    Supports category filtering and pagination.
    
    Example:
        class ProductFAQPage(FAQBasePage):
            product = models.ForeignKey('Product', on_delete=models.CASCADE)
            items_per_page = 20
    """
    
    introduction = RichTextField(
        blank=True,
        help_text=_("Introduction text for the FAQ page")
    )
    
    # FAQ categories to display
    faq_categories = models.ManyToManyField(
        'wagtail_feathers.FAQCategory',
        blank=True,
        help_text=_("Select FAQ categories to display on this page")
    )
    
    # Pagination settings
    items_per_page = models.PositiveIntegerField(
        default=10,
        help_text=_("Number of FAQ items to show per page")
    )
    
    # Additional content
    body = StreamField(CommonContentBlock(), blank=True)
    
    # Contact information for unanswered questions
    contact_note = RichTextField(
        blank=True,
        help_text=_("Note about contacting for questions not covered in FAQ")
    )
    
    # Admin panels
    content_panels = FeatherPage.content_panels + [
        FieldPanel('introduction'),
        FieldPanel('faq_categories', widget=forms.CheckboxSelectMultiple),
        FieldPanel('items_per_page'),
        FieldPanel('body'),
        FieldPanel('contact_note'),
    ]
    
    def get_faqs(self):
        """Get all FAQ items from selected categories."""
        if not self.faq_categories.exists():
            return []
        
        from .faq import FAQ
        return FAQ.objects.filter(
            category__in=self.faq_categories.all(),
            live=True
        ).select_related('category').order_by('category__name', 'sort_order')
    
    def get_context(self, request, *args, **kwargs):
        """Add paginated FAQs to context."""
        context = super().get_context(request, *args, **kwargs)
        
        from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
        
        faqs = self.get_faqs()
        paginator = Paginator(faqs, self.items_per_page)
        
        page = request.GET.get('page', 1)
        try:
            paginated_faqs = paginator.page(page)
        except PageNotAnInteger:
            paginated_faqs = paginator.page(1)
        except EmptyPage:
            paginated_faqs = paginator.page(paginator.num_pages)
        
        context.update({
            'faqs': paginated_faqs,
            'faq_categories': self.faq_categories.all(),
        })
        
        return context
    
    class Meta:
        abstract = True
        verbose_name = _("FAQ Base Page")
