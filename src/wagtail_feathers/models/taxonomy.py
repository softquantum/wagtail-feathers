# from abc import ABC, abstractmethod  # Cannot use due to metaclass conflicts with MP_Node
from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models, transaction
from django.db.models import Count, Q
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from treebeard.mp_tree import MP_Node
from wagtail.admin.panels import FieldPanel, HelpPanel, InlinePanel, MultiFieldPanel
from wagtail.models import Orderable, TranslatableMixin
from wagtail.search import index

try:
    from wagtail_localize.fields import SynchronizedField, TranslatableField
    WAGTAIL_LOCALIZE_AVAILABLE = True
except ImportError:
    WAGTAIL_LOCALIZE_AVAILABLE = False

WAGTAIL_I18N_ENABLED = getattr(settings, "WAGTAIL_I18N_ENABLED", False)


"""
Taxonomy models for hierarchical categorization and content classification.
"""


class TaxonomyConstants:
    """Central location for taxonomy-related constants."""

    ROOT_CATEGORY_NAME = "_root_category"
    DEFAULT_ICON = "heroicons-tag-outline"
    CACHE_TIMEOUT = 3600
    CACHE_VERSION = "v1"
    MAX_BREADCRUMB_LENGTH = 80


class TaxonomyError(Exception):
    """Base exception for taxonomy-related errors."""

    pass


class TreeIntegrityError(TaxonomyError):
    """Raised when tree structure integrity is compromised."""

    pass


class CategoryCache:
    """Centralized cache management for categories."""

    @classmethod
    def make_key(cls, prefix: str, category_id: int) -> str:
        """Generate a versioned cache key."""
        return f"category_{TaxonomyConstants.CACHE_VERSION}_{prefix}_{category_id}"

    @classmethod
    def invalidate_all(cls):
        """Invalidate all category caches by incrementing version."""
        # In production, you'd update CACHE_VERSION in settings
        cache.clear()  # For now, clear all

    @classmethod
    def get_descendants_key(cls, category_id: int) -> str:
        return cls.make_key("descendants", category_id)

    @classmethod
    def get_content_count_key(cls, category_id: int) -> str:
        return cls.make_key("content_count", category_id)


class BaseMPNode(index.Indexed, MP_Node):
    """Represents a single nestable Node in the corporate taxonomy."""

    name = models.CharField(
        max_length=255,
        help_text=_("Keep the name short (3 to 100 characters), max is 255 but you better not."),
        validators=[MinLengthValidator(3)],
    )

    live = models.BooleanField(
        default=True,
        verbose_name="live",
        help_text=_("soft disable the node"),
    )

    aliases = models.TextField(
        max_length=255,
        blank=True,
        help_text=_("What else is this known as or referred to as?"),
    )

    order_index = models.IntegerField(blank=True, default=0, editable=False)

    node_order_by = ["order_index", "name"]

    # Default cache timeout - subclasses can override
    cache_timeout = TaxonomyConstants.CACHE_TIMEOUT

    panels = [
        FieldPanel("name", widget=forms.TextInput()),
        FieldPanel("aliases", widget=forms.Textarea(attrs={"rows": "4"})),
    ]

    def get_name_display(self):
        """Build HTML representation of node with title and depth indication."""
        raise NotImplementedError("get_name_display() must be implemented by subclasses")

    @property
    def full_name(self):
        """Searchable full name of node."""
        raise NotImplementedError("full_name must be implemented by subclasses")

    @cached_property
    def ancestors_list(self):
        """Cached list of ancestors for breadcrumb building."""
        return list(self.get_ancestors().filter(live=True).select_related())

    @cached_property
    def descendant_ids(self):
        """Cached list of descendant IDs for filtering."""
        cache_key = CategoryCache.get_descendants_key(self.pk)
        descendant_ids = cache.get(cache_key)

        if descendant_ids is None:
            descendant_ids = list(self.get_descendants().filter(live=True).values_list("pk", flat=True))
            cache.set(cache_key, descendant_ids, self.cache_timeout)

        return descendant_ids

    def get_visible_children(self):
        """Get visible children of this node."""
        return self.get_children().filter(live=True)

    def get_navigation_children(self):
        """Get children suitable for navigation menus."""
        return self.get_children().filter(live=True).order_by("order_index", "name")

    def get_visible_descendants(self):
        """Get all visible descendants of this node."""
        return self.get_descendants().filter(live=True)

    def get_breadcrumb_trail(self):
        """Get breadcrumb trail excluding any hidden root nodes."""
        ancestors = self.ancestors_list
        # Remove hidden root if present (subclasses can override this logic)
        if ancestors and hasattr(ancestors[0], "is_hidden_root") and ancestors[0].is_hidden_root():
            ancestors = ancestors[1:]
        return ancestors

    def get_depth_display(self):
        """Get display depth (adjusted for hidden root if present)."""
        actual_depth = self.get_depth()
        # Check if this node is a hidden root
        if hasattr(self, "is_hidden_root") and self.is_hidden_root():
            return 0
        # Subtract 1 to account for hidden root if ancestors contain one
        ancestors = list(self.get_ancestors())
        if ancestors and hasattr(ancestors[0], "is_hidden_root") and ancestors[0].is_hidden_root():
            return max(0, actual_depth - 1)
        return actual_depth

    def is_visible(self):
        """Check if this node should be visible to users."""
        # Default implementation - subclasses can override
        if hasattr(self, "is_hidden_root") and self.is_hidden_root():
            return False
        return self.live

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


""" Categories
"""


class CategoryQuerySet(models.QuerySet):
    """Custom QuerySet for Category with performance optimizations."""

    def with_counts(self):
        """Annotate categories with page counts."""
        return self.annotate(page_count=Count("pages", distinct=True), child_count=Count("children", distinct=True))

    def active(self):
        """Only live categories."""
        return self.filter(live=True)

    def visible(self):
        """Return only visible categories (excluding hidden root)."""
        return self.filter(live=True).exclude(name=TaxonomyConstants.ROOT_CATEGORY_NAME)

    def root_level(self):
        """Get root level categories (children of hidden root)."""
        return self.filter(depth=2)

    def for_sitemap(self):
        """Categories suitable for sitemap generation."""
        return self.active().filter(numchild__gt=0)


class Category(TranslatableMixin, BaseMPNode):
    """A category for grouping related items using a hierarchical tree structure."""

    if WAGTAIL_LOCALIZE_AVAILABLE:
        override_translatable_fields = [
            SynchronizedField("slug"),
            SynchronizedField("icon"),
        ]

    ROOT_CATEGORY = TaxonomyConstants.ROOT_CATEGORY_NAME

    slug = AutoSlugField(populate_from="name", editable=True)
    icon = models.CharField(max_length=100, blank=True, help_text=_("Choose the icon from the admin/styleguide."))

    cache_timeout = TaxonomyConstants.CACHE_TIMEOUT

    objects = CategoryQuerySet.as_manager()

    panels = [
        FieldPanel("name", widget=forms.TextInput()),
        FieldPanel("slug", help_text=_("Leave blank to auto-generate from name")),
        FieldPanel("icon", help_text=_("CSS class or icon identifier")),
        FieldPanel("aliases", widget=forms.Textarea(attrs={"rows": "4"})),
        FieldPanel("live"),
    ]

    search_fields = [
        index.SearchField("name", boost=10),
        index.AutocompleteField("name"),
        index.SearchField("full_name", boost=5),
        index.AutocompleteField("full_name"),
        index.SearchField("aliases", boost=0.5),
        index.FilterField("name"),  # do not remove
        index.FilterField("live"),
        index.FilterField("depth"),
    ]
    
    if WAGTAIL_I18N_ENABLED:
        search_fields.append(index.FilterField("locale_id"))

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["path"]
        constraints = [
            models.UniqueConstraint(
                fields=('translation_key', 'locale'),
                name='unique_translation_key_locale_wagtail_feathers_category'
            ),
        ]
        indexes = [
            models.Index(fields=["live", "path"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["depth", "live"]),
        ]

    def invalidate_cache(self):
        """Invalidate category caches when structure changes."""
        # Invalidate own caches
        cache.delete(CategoryCache.get_descendants_key(self.pk))
        cache.delete(CategoryCache.get_content_count_key(self.pk))

        # Clear cached properties
        if hasattr(self, "_ancestors_list"):
            del self._ancestors_list
        if hasattr(self, "_descendant_ids"):
            del self._descendant_ids

        # Invalidate ancestor caches
        for ancestor in self.get_ancestors():
            cache.delete(CategoryCache.get_descendants_key(ancestor.pk))
            cache.delete(CategoryCache.get_content_count_key(ancestor.pk))

        # Invalidate descendant caches
        for descendant in self.get_descendants():
            cache.delete(CategoryCache.get_descendants_key(descendant.pk))
            cache.delete(CategoryCache.get_content_count_key(descendant.pk))

    @property
    def full_name(self):
        """Return searchable string with category names."""
        if self.is_hidden_root():
            return ""
        trail = self.get_breadcrumb_trail()
        trail.append(self)
        names = [cat.name for cat in trail]
        return " ".join(names)

    def __str__(self):
        if self.is_hidden_root():
            return "[Hidden Root]"

        # Get breadcrumb trail (excluding hidden root)
        trail = self.get_breadcrumb_trail()
        trail.append(self)

        names = [cat.name for cat in trail]
        breadcrumb = " :: ".join(names)
        max_length = TaxonomyConstants.MAX_BREADCRUMB_LENGTH
        if len(breadcrumb) > max_length:
            if len(names) > 3:
                short_breadcrumb = " :: ".join(names[-2:])
                if len(short_breadcrumb) <= max_length:
                    return f"...> {short_breadcrumb}"

            if len(self.name) > max_length - 3:
                return f"{self.name[: max_length - 3]}..."
            else:
                return self.name

        return breadcrumb

    def clean(self):
        """Validate category before saving."""
        super().clean()

        # Validate root category
        if self.name == TaxonomyConstants.ROOT_CATEGORY_NAME and self.live:
            raise ValidationError("Root category must not be live")

        # Validate name length
        if len(self.name) > 100:
            raise ValidationError("Category name should not exceed 100 characters for optimal display")

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Override save to ensure hidden root exists and validate tree integrity."""
        # Handle new categories without tree structure
        if not self.pk and (not hasattr(self, "path") or self.path is None or self.path == ""):
            if self.name == TaxonomyConstants.ROOT_CATEGORY_NAME:
                # Validate that we're not trying to create multiple roots
                existing_root = Category.objects.filter(name=TaxonomyConstants.ROOT_CATEGORY_NAME).first()
                if existing_root:
                    raise TreeIntegrityError("Hidden root category already exists")
                # For root category, use normal save
                super().save(*args, **kwargs)
            else:
                # This is a new regular category - automatically add as child of hidden root
                hidden_root = self.get_or_create_hidden_root()

                # Create the category using add_child, which handles tree structure
                # Let slug auto-generate if not provided
                slug_value = getattr(self, "slug", "") or None
                new_category = hidden_root.add_child(
                    name=self.name,
                    slug=slug_value,
                    icon=getattr(self, "icon", ""),
                    aliases=getattr(self, "aliases", ""),
                    live=getattr(self, "live", True),
                )

                # Copy the new category's attributes to this instance
                self.pk = new_category.pk
                self.path = new_category.path
                self.depth = new_category.depth
                self.numchild = new_category.numchild
                self.slug = new_category.slug

        else:
            # For categories that already have tree structure or are being created via treebeard
            super().save(*args, **kwargs)

        self.invalidate_cache()

    @transaction.atomic
    def delete(self, *args, **kwargs):
        """Override delete to prevent deletion of hidden root."""
        if self.is_hidden_root():
            raise TreeIntegrityError("Cannot delete hidden root category")

        self.invalidate_cache()
        super().delete(*args, **kwargs)

    def is_hidden_root(self):
        """Check if this category is the hidden root."""
        return self.name == TaxonomyConstants.ROOT_CATEGORY_NAME

    @classmethod
    def get_or_create_hidden_root(cls):
        """Get or create the hidden root category."""
        try:
            # Use objects.all() to include hidden categories
            root = cls.objects.filter(name=TaxonomyConstants.ROOT_CATEGORY_NAME).first()
            if root:
                return root
        except cls.DoesNotExist:
            pass

        # Create new hidden root using treebeard's add_root method
        root = cls.add_root(
            name=TaxonomyConstants.ROOT_CATEGORY_NAME,
            slug="hidden-root",
            live=False,
            aliases="System root category - do not modify",
        )
        return root

    @classmethod
    def get_visible_root_categories(cls):
        """Get all top-level visible categories (children of hidden root)."""
        hidden_root = cls.get_or_create_hidden_root()
        return hidden_root.get_children().filter(live=True).order_by("path")

    @classmethod
    def get_category_tree(cls):
        """Get the full category tree excluding the hidden root."""
        return cls.objects.visible().order_by("path")

    @classmethod
    def get_tree_for_display(cls):
        """Get optimized tree for admin display."""
        return cls.objects.active().order_by("path")

    def get_name_display(self):
        """Get clean display name for admin interface without action buttons."""
        from django.utils.html import format_html
        from django.utils.safestring import mark_safe

        depth = self.get_depth_display()
        indent = depth * 1.5
        status_class = "category-live" if self.live else "category-disabled"
        icon_value = self.icon if self.icon else TaxonomyConstants.DEFAULT_ICON
        icon_html = mark_safe(f'<svg class="icon" aria-hidden="true"><use href="#icon-{icon_value}"></use></svg>')

        return format_html(
            '<span class="category-item {}" style="padding-left: {}rem;">{}<span class="category-name">{}</span></span>',
            status_class,
            indent,
            icon_html,
            self.name,
        )

    get_name_display.short_description = _("Category")
    get_name_display.admin_order_field = "path"

    def get_url_path(self):
        """Get URL path for this category based on breadcrumb trail."""
        trail = self.get_breadcrumb_trail()
        trail.append(self)
        return "/".join([cat.slug for cat in trail])

    @classmethod
    def add_root_category(cls, name, **kwargs):
        """Add a new root-level category (child of hidden root)."""
        hidden_root = cls.get_or_create_hidden_root()
        return hidden_root.add_child(name=name, **kwargs)

    def add_child_category(self, name, **kwargs):
        """Add a child category to this category."""
        return self.add_child(name=name, **kwargs)

    def move_to_parent(self, parent):
        """Move this category to a new parent."""
        if self.is_hidden_root():
            raise ValueError("Cannot move hidden root category")
        self.move(parent, pos="sorted-child")

    def move_to_root(self):
        """Move this category to root level (child of hidden root)."""
        if self.is_hidden_root():
            raise ValueError("Cannot move hidden root category")
        hidden_root = self.get_or_create_hidden_root()
        self.move(hidden_root, pos="sorted-child")


""" Classifiers
"""


class ClassifierGroupQuerySet(models.QuerySet):
    """QuerySet for ClassifierGroup with useful filters."""

    def subjects(self):
        return self.filter(type="Subject")

    def attributes(self):
        return self.filter(type="Attribute")

    def with_classifier_counts(self):
        return self.annotate(
            classifier_count=Count("classifiers"),
            active_classifier_count=Count("classifiers", filter=Q(classifiers__pages__isnull=False), distinct=True),
        )


class ClassifierGroup(index.Indexed, TranslatableMixin, ClusterableModel):
    """A group for organizing classifiers by type."""

    objects = ClassifierGroupQuerySet.as_manager()

    if WAGTAIL_LOCALIZE_AVAILABLE:
        override_translatable_fields = [
            SynchronizedField("slug"),
        ]

    TYPE_CHOICES = [
        ("Subject", _("Subject")),
        ("Attribute", _("Attribute")),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from="name", editable=True)
    max_selections = models.PositiveIntegerField(default=0, help_text=_("Maximum number of selections allowed. 0 for unlimited"))

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("type"),
                FieldPanel("name"),
                FieldPanel("max_selections"),
            ],
            heading=_("Classifier Group"),
        ),
        InlinePanel("classifiers", label=_("Classifiers")),
        HelpPanel(
            content="""
                <div class="help-block help-info">
                <svg class="icon icon-help icon" aria-hidden="true"><use href="#icon-help"></use></svg>
                <strong>Classification by cross-cutting topics that span multiple categories or by content attributes.</strong>
                <hr>
                <ul> 
                    <li><strong>A Subject</strong> (or Topic if you prefer) is what the content is about.</li>
                    <table style="width: 100%; margin-top: 10px;">
                        <thead>
                            <tr>
                                <th style="text-align: left; padding-right: 10px;">Subjects examples</th>
                                <th style="text-align: left;">Terms examples</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding-right: 10px;"><strong>Business</strong></td>
                                <td>Digital Transformation, Customer Experience, Data Analytics, Innovation Strategy</td>
                            </tr>
                            <tr>
                                <td style="padding-right: 10px;"><strong>Technology</strong></td>
                                <td>Artificial Intelligence, Cloud Computing, Cybersecurity, Web Development</td>
                            </tr>
                            <tr>
                                <td style="padding-right: 10px;"><strong>Healthcare</strong></td>
                                <td>Telehealth, Precision Medicine, Patient Safety, Healthcare Informatics</td>
                            </tr>
                            <tr>
                                <td style="padding-right: 10px;"><strong>Agriculture</strong></td>
                                <td>Sustainable Farming, Crop Science, Precision Agriculture, Food Security</td>
                            </tr>
                        </tbody>
                    </table>
                </ul>
                <hr>
                <ul>
                    <li><strong>An Attribute</strong> is how the content is classified by form or genre or other characteristics.</li>
                    <table style="width: 100%; margin-top: 10px;">
                        <thead>
                            <tr>
                                <th style="text-align: left; padding-right: 10px;">Attributes examples</th>
                                <th style="text-align: left;">Terms examples</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding-right: 10px;"><strong>Content Type</strong></td>
                                <td>Article, Video, Course, Tool, Dataset</td>
                            </tr>
                            <tr>
                                <td style="padding-right: 10px;"><strong>Complexity</strong></td>
                                <td>Introductory, Intermediate, Advanced, Expert</td>
                            </tr>
                            <tr>
                                <td style="padding-right: 10px;"><strong>Approach</strong></td>
                                <td>Theoretical, Practical, Case Study, Tutorial</td>
                            </tr>
                            <tr>
                                <td style="padding-right: 10px;"><strong>Audience</strong></td>
                                <td>Student, Professional, Researcher, General Public</td>
                            </tr>
                            <tr>
                                <td style="padding-right: 10px;"><strong>Recency</strong></td>
                                <td>Historical, Current, Trending, Emerging</td>
                            </tr>
                            <tr>
                                <td style="padding-right: 10px;"><strong>Audience level</strong></td>
                                <td>Beginner, Advanced, Expert</td>
                            </tr>
                        </tbody>
                    </table>
                </ul>
            </div>
            """,
        ),
    ]

    search_fields = [
        index.SearchField("name", boost=10),
        index.SearchField("slug"),
        index.AutocompleteField("name"),
        index.FilterField("type"),
    ]

    if WAGTAIL_I18N_ENABLED:
        search_fields.append(index.FilterField("locale_id"))

    def __str__(self):
        return f"{self.name} ({self.type})"

    def get_popular_classifiers(self, limit=10):
        """Get most used classifiers in this group."""
        return (
            self.classifiers.annotate(usage_count=Count("pages"))
            .filter(usage_count__gt=0)
            .order_by("-usage_count")[:limit]
        )

    def classifiers_list(self):
        """Get a list of classifiers in this group."""
        classifiers = list(self.classifiers.values_list('name', flat=True)[:6])

        if not classifiers:
            return ""

        display_classifiers = classifiers[:5]
        names = display_classifiers
        result = ", ".join(names)

        if len(classifiers) > 5:
            total_count = self.classifiers.count()
            result += f" (+{total_count - 5} more)"

        return result

    classifiers_list.short_description = "Classifiers"

    class Meta:
        verbose_name = _("Group of classifiers")
        verbose_name_plural = _("Groups of classifiers")
        ordering = ["type", "name"]
        constraints = [
            models.UniqueConstraint(fields=["type", "name", "locale"], name="unique_classifier_group_type_name_locale"),
            models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_translation_key_locale_wagtail_feathers_classifiergroup')
        ]
        indexes = [
            models.Index(fields=["id"]),
        ]


class ClassifierQuerySet(models.QuerySet):
    """QuerySet for Classifier with useful filters."""

    def subjects(self):
        return self.filter(group__type="Subject")

    def attributes(self):
        return self.filter(group__type="Attribute")

    def popular(self, threshold=5):
        """Get classifiers used at least 'threshold' times."""
        return self.annotate(usage_count=Count("pages")).filter(usage_count__gte=threshold)

    def for_autocomplete(self, search_term=""):
        """Optimized query for autocomplete widgets."""
        qs = self.select_related("group")
        if search_term:
            qs = qs.filter(Q(name__icontains=search_term) | Q(group__name__icontains=search_term))
        return qs.order_by("group__type", "group__name", "name")


class Classifier(index.Indexed, TranslatableMixin, Orderable):
    """A classifier for tagging and organizing content."""

    objects = ClassifierQuerySet.as_manager()

    if WAGTAIL_LOCALIZE_AVAILABLE:
        override_translatable_fields = [
            SynchronizedField("slug"),
        ]

    group = ParentalKey(ClassifierGroup, on_delete=models.CASCADE, related_name="classifiers")
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from="name", editable=True)

    panels = [
        FieldPanel("group"),
        FieldPanel("name"),
        FieldPanel("slug", help_text=_("Leave blank to auto-generate a unique slug.")),
    ]

    # Build search fields dynamically based on i18n configuration
    search_fields = [
        index.SearchField("name", boost=10),
        index.SearchField("slug"),
        index.AutocompleteField("name"),
        index.FilterField("name"),
        index.FilterField("group"),
        index.RelatedFields(
                "group",
                [
                    index.SearchField("name"),
                    index.FilterField("type"),
                ],
        )
    ]
    
    if WAGTAIL_I18N_ENABLED:
        search_fields.append(index.FilterField("locale_id"))

    def get_related_classifiers(self, limit=5):
        """Find classifiers commonly used together."""
        page_ids = list(self.pages.values_list("page_id", flat=True)[:100])

        return (
            Classifier.objects.filter(pages__page_id__in=page_ids)
            .exclude(pk=self.pk)
            .annotate(co_occurrence=Count("pages", distinct=True))
            .select_related("group")
            .order_by("-co_occurrence")[:limit]
        )

    def __str__(self):
        return f"{self.group.name} – {self.name} ({self.group.type})"

    class Meta:
        verbose_name = _("Classifier")
        verbose_name_plural = _("Classifiers")
        ordering = ["sort_order"]
        constraints = [
            models.UniqueConstraint(fields=["group", "name", "locale"], name="unique_classifier_group_name_locale"),
            models.UniqueConstraint(fields=('translation_key', 'locale'), name='unique_translation_key_locale_wagtail_feathers_classifier')
        ]
        indexes = [
            models.Index(fields=["group", "name"]),
            models.Index(fields=["slug"]),
        ]


""" Intermediate models for taxonomy relationships.
- PageCategory
- PageClassifier
"""


class PageCategory(Orderable):
    """Categories for pages."""

    page = ParentalKey("wagtailcore.Page", on_delete=models.CASCADE, related_name="categories")
    category = models.ForeignKey("wagtail_feathers.Category", on_delete=models.CASCADE, related_name="pages")

    panels = [
        FieldPanel("category"),
    ]

    class Meta:
        constraints = [models.UniqueConstraint(fields=["page", "category"], name="unique_page_category")]


class PageClassifier(Orderable):
    """Classifiers for pages."""

    page = ParentalKey("wagtailcore.Page", on_delete=models.CASCADE, related_name="classifiers")
    classifier = models.ForeignKey("wagtail_feathers.Classifier", on_delete=models.CASCADE, related_name="pages")

    panels = [
        FieldPanel("classifier"),
    ]

    class Meta:
        constraints = [models.UniqueConstraint(fields=["page", "classifier"], name="unique_page_classifier")]
