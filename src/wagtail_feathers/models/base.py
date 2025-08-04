from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, QuerySet
from django.db.models.functions import Greatest
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import (
    FieldPanel,
    InlinePanel,
    MultipleChooserPanel,
    ObjectList,
    TabbedInterface,
)
from wagtail.fields import RichTextField, StreamField
from wagtail.images import get_image_model_string
from wagtail.models import Page, PageBase, PageManager
from wagtail.query import PageQuerySet
from wagtail.utils.decorators import cached_classmethod

from wagtail_feathers.blocks import CommonContentBlock, HeroContentBlock, PageHeaderBlock
from wagtail_feathers.forms import TemplateVariantPageForm
from wagtail_feathers.panels import EnhancedClassifierInlinePanel

from ..utils.query import order_by_pk_position
from .reading_time import ReadingTimeMixin
from .seo import SeoMixin
from .utils import FEATHER_PAGE_MODELS


class CustomWagtailPage(Page):
    """Abstract foundation for all custom pages in Wagtail Feathers.

    This class decouples Wagtail's Page model and your application.

    """

    class Meta:
        abstract = True


class FeatherBasePageMeta(PageBase):
    """Metaclass for FeatherBasePage to register non-abstract page models.

    Automatically registers page models in FEATHER_PAGE_MODELS for
    dynamic discovery and configuration throughout the application.
    """

    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)
        if not cls._meta.abstract and getattr(cls, "is_creatable", True):  # noqa
            FEATHER_PAGE_MODELS.append(cls)
        return cls


class FeatherBasePageTag(TaggedItemBase):
    """Tag model for FeatherBasePage model.

    Any newly created tags will be added to django-taggit's default Tag model,
    which will be shared by all other models using the same recipe as well
    as Wagtail's image and document models.
    """

    content_object = ParentalKey("wagtail_feathers.FeatherBasePage", related_name="tagged_items")


class FeatherBasePage(SeoMixin, CustomWagtailPage, metaclass=FeatherBasePageMeta):
    """Concrete base class for all pages with common content, taxonomy, and SEO features.

    This is the main concrete page type that provides core functionality.
    Follows the Wagtail Page model principles.
    Should NOT be extended directly, ideally - use FeatherPage or its abstract children instead.

    Provides:
    - StreamField body with common content blocks
    - Comprehensive SEO capabilities (meta tags, Open Graph, Twitter Cards, structured data)
    - Taxonomy system (tags, subjects, attributes, categories)
    - Featured image support
    - Configurable admin panel structure
    """

    is_creatable = False
    base_form_class = TemplateVariantPageForm

    body = StreamField(CommonContentBlock(), blank=True)
    
    # Template variant selection
    template_variant = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional template variant (e.g., 'landing', 'portfolio'). Leave empty for default template.",
        verbose_name="Template Variant"
    )

    # Taxonomy fields
    tags = ClusterTaggableManager(through=FeatherBasePageTag, blank=True)

    # Panels
    content_panels = CustomWagtailPage.content_panels + [
        FieldPanel("body"),
    ]

    settings_panels = CustomWagtailPage.settings_panels + [
        FieldPanel("template_variant"),
    ]

    taxonomy_panels = [
        MultipleChooserPanel("categories", "category"),
        MultipleChooserPanel("classifiers", "classifier"),
        # EnhancedClassifierInlinePanel("classifiers", label=_("Classifiers")),
        FieldPanel("tags"),
    ]

    authorship_panels = []
    geographic_panels = []

    def clean(self):
        """Validate max_selections constraints for classifier groups."""
        super().clean()
        
        # Import here to avoid circular imports
        from wagtail_feathers.models.taxonomy import ClassifierGroup
        
        # Group classifiers by their groups
        classifier_groups = {}
        for classifier_relation in self.classifiers.all():
            group = classifier_relation.classifier.group
            if group.id not in classifier_groups:
                classifier_groups[group.id] = {
                    'group': group,
                    'count': 0,
                    'classifiers': []
                }
            classifier_groups[group.id]['count'] += 1
            classifier_groups[group.id]['classifiers'].append(classifier_relation.classifier.name)
        
        # Check max_selections constraints
        errors = []
        for group_data in classifier_groups.values():
            group = group_data['group']
            count = group_data['count']
            classifiers = group_data['classifiers']
            
            if group.max_selections > 0 and count > group.max_selections:
                if group.max_selections == 1:
                    errors.append(
                        ValidationError(
                            _('Only one classifier can be selected from group "%(group_name)s" (%(group_type)s). Currently selected: %(classifiers)s') % {
                                'group_name': group.name,
                                'group_type': group.type,
                                'classifiers': ', '.join(classifiers)
                            }
                        )
                    )
                else:
                    errors.append(
                        ValidationError(
                            _('Maximum %(max_selections)d classifiers allowed from group "%(group_name)s" (%(group_type)s). Currently selected %(count)d: %(classifiers)s') % {
                                'max_selections': group.max_selections,
                                'group_name': group.name,
                                'group_type': group.type,
                                'count': count,
                                'classifiers': ', '.join(classifiers)
                            }
                        )
                    )
        
        if errors:
            raise ValidationError(errors)

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
                            variant = filename.stem.replace(f"{template_name}--", '')
                            if variant not in variants:
                                variants.append(variant)
        except Exception:
            # Fallback to empty list if theme system fails
            pass
        
        return sorted(variants)

    @cached_classmethod
    def get_edit_handler(cls):  # noqa
        """Override to "lazily load" the panels overridden by subclasses."""
        panels = [
            ObjectList(cls.content_panels, heading=_("Content")),
            ObjectList(cls.taxonomy_panels, heading=_("Taxonomy")),
            ObjectList(cls.seo_panels, heading=_("SEO")),
            ObjectList(cls.promote_panels, heading=_("Promote")),
            ObjectList(cls.settings_panels, heading=_("Settings")),
        ]

        if cls.authorship_panels:
            panels.insert(1, ObjectList(cls.authorship_panels, heading=_("Authorship")))
        if cls.geographic_panels:
            panels.insert(2, ObjectList(cls.geographic_panels, heading=_("Geographic")))

        edit_handler = TabbedInterface(panels)
        return edit_handler.bind_to_model(cls)

    class Meta:
        verbose_name = "Feather Base Page"
        ordering = ["-first_published_at"]


class FeatherPage(FeatherBasePage):
    """Abstract base for custom page types. Allows field overrides.

    Use this instead of extending FeatherBasePage directly.

    Example:
        class ArticlePage(FeatherPage):
            body = StreamField([...]) # Override with custom blocks
    """

    @cached_property
    def related_pages(self) -> QuerySet:
        """
        Return a `PageQuerySet` of items related to this page via the
        `RelatedPage` through model, and are suitable for display.
        The result is ordered to match that specified by editors using
        the 'page_related_pages' `InlinePanel`.

        """

        # NOTE: avoiding values_list() here for compatibility with preview
        # See: https://github.com/wagtail/django-modelcluster/issues/30
        ordered_page_pks = tuple(item.page_id for item in self.page_related_pages.all())
        return order_by_pk_position(
            Page.objects.live().public().specific(),
            pks=ordered_page_pks,
            exclude_non_matches=True,
        )
    
    class Meta:
        abstract = True
        verbose_name = "Feather Page"


class IndexPage(FeatherPage):
    """Abstract index page model with pagination support.

    Use this for pages that primarily list other child pages
    e.g., Article Index, News Index, Event Index, etc.
    
    Features:
    - Optional hero section to introduce the collection
    - Standard content blocks for additional context
    - Built-in pagination support
    - Designed for listing/navigation rather than conversion
    """

    header = StreamField(
            PageHeaderBlock(),
            blank=True,
            help_text="Page header blocks."
    )

    # Pagination settings
    items_per_page = models.PositiveIntegerField(
        default=10,
        help_text=_("Number of items to show per page")
    )
    
    content_panels = [FeatherPage.content_panels[0]] + [
        FieldPanel('header'),
        FieldPanel('items_per_page'),
    ] + FeatherPage.content_panels[1:]
    
    def get_items(self):
        """Get items to display on this index page.
        
        Override this method in subclasses to define what items to show.
        Default returns live child pages.
        """
        return (self.get_children()
                .live()
                .specific()
                .annotate(
                most_recent=Greatest(
                        F("specific__revision_date"),
                        F("specific__publication_date"),
                        F("specific__first_published_at"),
                        output_field=models.DateField(),)
                )
                .order_by("-most_recent")

                )
    
    def get_context(self, request, *args, **kwargs):
        """Add paginated items to context."""
        context = super().get_context(request, *args, **kwargs)
        
        from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
        
        items = self.get_items()
        paginator = Paginator(items, self.items_per_page)
        
        page = request.GET.get('page', 1)
        try:
            paginated_items = paginator.page(page)
        except PageNotAnInteger:
            paginated_items = paginator.page(1)
        except EmptyPage:
            paginated_items = paginator.page(paginator.num_pages)
        
        context.update({
            'items': paginated_items,
            'paginator': paginator,
        })
        
        return context

    class Meta:
        abstract = True



class ItemPageQuerySet(PageQuerySet):
    """A custom QuerySet for the ItemPage model."""
    pass



class ItemPageManager(PageManager):
    """A custom PageManager for the ItemPage model."""

    def get_queryset(self):
        return ItemPageQuerySet(self.model, using=self._db).annotate(
                latest_publication_date=Greatest(
                        'publication_date',
                        'revision_date'
                )
        )


class ItemPage(ReadingTimeMixin, FeatherPage):
    """Abstract item page model with reading time calculation.

    Use this for individual "item" pages that are usually children of an index page
    e.g., Article, News Item, Event Detail, etc.
    
    Features:
    - Automatic reading time calculation from content
    - Publication and revision date tracking
    - Featured image support
    - Author attribution system
    - Geographic tagging
    """

    objects = ItemPageManager()

    image_model = get_image_model_string()
    image = models.ForeignKey(
        image_model, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    introduction = RichTextField(blank=True)

    publication_date = models.DateField(
        default=timezone.now,
        help_text="Official first publication date.",
    )

    revision_date = models.DateField(
        null=True,
        blank=True,
        help_text="Official last revision date.",
    )

    display_authors = models.BooleanField(
        default=False,
        help_text="Display author names on the page.",
    )

    authorship_panels = [
        FieldPanel("display_authors"),
        InlinePanel("authors", label=_("Authors")),
    ]

    geographic_panels = [
        InlinePanel("countries", label=_("Countries")),
    ]
    content_panels = [FeatherPage.content_panels[0]] + [
        FieldPanel("image"),
        FieldPanel("introduction"),
        FieldPanel("body"),
    ]

    promote_panels = [
        FieldPanel("publication_date"),
        FieldPanel("revision_date"),
    ] + ReadingTimeMixin.reading_time_panels + FeatherPage.promote_panels


    class Meta:
        abstract = True


class WebBasePage(FeatherPage):
    """Abstract base page model for web pages with enhanced content blocks.

    Features:
    - PageHeaderBlock with Hero content for page headers and landing areas
    - All CommonContentBlock capabilities (paragraphs, images, CTAs, cards, etc.)
    - Maintains all FeatherPage functionality (taxonomy, authorship, etc.)
    """

    header = StreamField(
            PageHeaderBlock(),
            blank=True,
            help_text="Page header blocks."
    )

    content_panels = [FeatherPage.content_panels[0]] + [
        FieldPanel('header'),
    ] + FeatherPage.content_panels[1:]

    class Meta:
        abstract = True
        verbose_name = "Web Base Page"
