from typing import TYPE_CHECKING

from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, HelpPanel, InlinePanel, MultiFieldPanel
from wagtail.admin.widgets import AdminPageChooser
from wagtail.fields import StreamField
from wagtail.models import Orderable, TranslatableMixin

try:
    from wagtail_localize.fields import TranslatableField
    WAGTAIL_LOCALIZE_AVAILABLE = True
except ImportError:
    WAGTAIL_LOCALIZE_AVAILABLE = False

from wagtail_feathers.blocks import (
    FooterMenuStreamBlock,
    LinkStreamBlock,
    MenuStreamBlock,
)

if TYPE_CHECKING:
    pass


class LocaleAwareFooterNavigationWidget(forms.Select):
    """Widget that filters FooterNavigation choices based on current locale."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def get_queryset(self, request=None):
        """Get FooterNavigation queryset filtered by current locale."""
        from wagtail_feathers.models.navigation import FooterNavigation
        queryset = FooterNavigation.objects.all()
        
        # Filter by current locale if available
        if hasattr(request, 'LANGUAGE_CODE') and WAGTAIL_LOCALIZE_AVAILABLE:
            try:
                from wagtail_localize.models import Locale
                current_locale = Locale.objects.get(language_code=request.LANGUAGE_CODE)
                queryset = queryset.filter(locale=current_locale)
            except Exception:
                # Fallback to all if locale filtering fails
                pass
        
        return queryset
    
    def optgroups(self, name, value, attrs=None):
        """Override to use filtered queryset."""
        # This will be called when rendering the widget
        if hasattr(self, '_request'):
            queryset = self.get_queryset(self._request)
            self.choices = [(obj.pk, str(obj)) for obj in queryset]
        return super().optgroups(name, value, attrs)


class Menu(TranslatableMixin, ClusterableModel):
    """Traditional hierarchical menu for simple use cases with optimal performance."""
    name = models.CharField(max_length=100)
    slug = AutoSlugField(
        populate_from="name", unique=True, editable=True, help_text=_("Auto-generated from name, but can be edited")
    )
    description = models.TextField(blank=True)

    panels = [
        MultiFieldPanel([
            HelpPanel(
                    content="""
                <div class="help-block help-info">
                <svg class="icon icon-help icon" aria-hidden="true"><use href="#icon-help"></use></svg>
                <strong>Legacy-style parent-child hierarchical menus.</strong>
                <p>Best for teams migrating from traditional CMS systems who need familiar editing patterns or easier theming.</p>
                """
            ),
            FieldPanel("name"),
            FieldPanel("slug"),
            FieldPanel("description"),
        ], heading="Menu"),
        InlinePanel("menu_items"),
    ]

    def __str__(self):
        return self.name

    def menu_items_count(self, obj):
        """Display count of menu items for this menu."""
        return obj.menu_items.count()

    class Meta:
        verbose_name = _("Menu")
        verbose_name_plural = _("Menus")
        constraints = [
            models.UniqueConstraint(
                fields=["translation_key", "locale"], name="unique_menu_translation_key_locale"
            )
        ]


class MenuItem(Orderable):
    """A hierarchical menu item with parent-child relationships."""
    menu = ParentalKey(Menu, related_name="menu_items", on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    title = models.CharField(max_length=100, help_text=_("Title of menu item, 100 characters max."))
    menu_item = StreamField(LinkStreamBlock, blank=True)

    panels = [
        FieldPanel("parent"),
        FieldPanel("title"),
        FieldPanel("menu_item"),
    ]

    def clean(self):
        """Validate menu item to prevent circular references."""
        super().clean()
        if self.parent:
            # Check for circular reference
            current = self.parent
            visited = set()
            while current:
                if current.id == self.id:
                    from django.core.exceptions import ValidationError
                    raise ValidationError(_("Menu item cannot be a parent of itself."))
                if current.id in visited:
                    from django.core.exceptions import ValidationError
                    raise ValidationError(_("Circular reference detected in menu hierarchy."))
                visited.add(current.id)
                current = current.parent

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.title}"
        return self.title

    class Meta:
        verbose_name = _("Menu Item")
        verbose_name_plural = _("Menu Items")
        ordering = ['sort_order', 'title']


class NestedMenu(TranslatableMixin, ClusterableModel):
    """Setting the menus for the site.

    Cannot use the BaseSettings since we need translations for the menus.
    `wagtail.models.SlugField` is specifically designed for Wagtail models and comes
    with page-specific behaviors and constraints **Page**, hence I used AutoSlugField.

    """

    name = models.CharField(max_length=100)
    slug = AutoSlugField(
        populate_from="name", unique=True, editable=True, help_text=_("Auto-generated from name, but can be edited")
    )

    menu_items = StreamField(MenuStreamBlock(), blank=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("menu_items"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Nested Menu")
        verbose_name_plural = _("Nested Menus")
        constraints = [
            models.UniqueConstraint(
                fields=["translation_key", "locale"], name="unique_nestedmenu_translation_key_locale"
            )
        ]


class FlatMenu(TranslatableMixin, ClusterableModel):
    """Structured navigation menu using the new MenuBlock system.

    This provides a more controlled alternative to the template tag 'top_menu_items'
    """

    name = models.CharField(max_length=100, help_text=_("Name for this menu (e.g., 'Main Navigation', 'Header Menu')"))
    slug = AutoSlugField(
            populate_from="name",
            unique=True,
            editable=True,
            help_text=_("Auto-generated from name, but can be edited")
    )

    menu_items = StreamField(
            LinkStreamBlock(),
            blank=True,
    )

    panels = [
        MultiFieldPanel([
            HelpPanel(
                    content="""
            <div class="help-block help-info">
            <svg class="icon icon-help icon" aria-hidden="true"><use href="#icon-help"></use></svg>
            <p>Use this menu if the template tag 'top_menu_items' is not enough, 
            e.g., the links are not only pages and you need to control the order..</p>
            """
            ),
            FieldPanel("name"),
            FieldPanel("slug"),
        ], heading="Menu"),
        FieldPanel("menu_items"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Flat Menu")
        verbose_name_plural = _("Flat Menus")
        constraints = [
            models.UniqueConstraint(
                    fields=["translation_key", "locale"], name="unique_flatnavigationmenu_translation_key_locale"
            )
        ]


class FooterNavigation(TranslatableMixin, ClusterableModel):
    """Setting the footer navigation for the site."""

    name = models.CharField(max_length=100)
    slug = AutoSlugField(
        populate_from="name", unique=True, editable=True, help_text=_("Auto-generated from name, but can be edited")
    )

    menu_sections = StreamField(
        [
            (
                "menu_section",
                blocks.StructBlock(
                    [
                        ("section_heading", blocks.CharBlock()),
                        ("links", FooterMenuStreamBlock()),
                    ]
                ),
            )
        ],
        blank=True,
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("menu_sections"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Footer Navigation Menu")
        verbose_name_plural = _("Footer Navigation Menus")
        constraints = [
            models.UniqueConstraint(
                fields=["translation_key", "locale"], name="unique_footernavigation_translation_key_locale"
            )
        ]


class Footer(TranslatableMixin, ClusterableModel):
    """Translatable footer content with copyright, footer text, and optional navigation reference."""
    
    name = models.CharField(
        max_length=100, 
        help_text=_("Name for this footer configuration (e.g., 'Main Footer', 'A/B Test Footer')")
    )
    
    site = models.ForeignKey(
        'wagtailcore.Site',
        on_delete=models.CASCADE,
        help_text=_("Site this footer configuration belongs to")
    )
    
    copyright_text = models.CharField(
        max_length=200, 
        help_text=_("Copyright text (e.g., '© 2024 Company Name')")
    )
    
    footer_text = models.TextField(
        blank=True, 
        help_text=_("Additional footer text or description")
    )
    
    footer_navigation = models.ForeignKey(
        'wagtail_feathers.FooterNavigation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Optional footer navigation menu")
    )

    footer_links = StreamField(
        LinkStreamBlock(),
        blank=True,
        help_text=_("Additional footer links (Legal, Terms of Service, Privacy Policy, etc.)")
    )

    
    # Translation configuration - only available with wagtail-localize
    if WAGTAIL_LOCALIZE_AVAILABLE:
        translatable_fields = [
            TranslatableField('copyright_text'),
            TranslatableField('footer_text'),
            # TranslatableField('footer_links'),  # TODO: to check if needed
        ]
    
    panels = [
        MultiFieldPanel([
            FieldPanel("name"),
            FieldPanel("site"),
        ], heading=_("Footer Configuration")),
        MultiFieldPanel([
            FieldPanel("copyright_text"),
            FieldPanel("footer_text"),
        ], heading=_("Translatable Content")),
        MultiFieldPanel([
            FieldPanel("footer_navigation", widget=LocaleAwareFooterNavigationWidget),
            FieldPanel('footer_links'),
        ], heading=_("Navigation")),
    ]
    
    def __str__(self):
        return f"{self.name} ({self.site})"
    
    class Meta:
        verbose_name = _("Footer")
        verbose_name_plural = _("Footers")
        constraints = [
            models.UniqueConstraint(
                fields=["translation_key", "locale"], name="unique_footer_translation_key_locale"
            )
        ]
