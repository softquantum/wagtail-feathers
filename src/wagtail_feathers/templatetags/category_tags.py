from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from wagtail_feathers.models import Category

register = template.Library()


@register.simple_tag
def get_category_tree():
    """Get the complete visible category tree."""
    return Category.get_category_tree()


@register.simple_tag
def get_root_categories():
    """Get all top-level visible categories."""
    return Category.get_visible_root_categories()


@register.simple_tag
def get_category_children(category):
    """Get visible children of a category."""
    if not category:
        return Category.objects.none()
    return category.get_visible_children()


@register.simple_tag
def get_category_breadcrumbs(category):
    """Get breadcrumb trail for a category."""
    if not category:
        return []
    return category.get_breadcrumb_trail()


@register.simple_tag
def get_category_url_path(category):
    """Get URL path for a category."""
    if not category:
        return ""
    return category.get_url_path()


@register.inclusion_tag("wagtail_feathers/templatetags/category_tree.html")
def render_category_tree(categories=None, template_name=None):
    """Render a complete category tree as nested lists."""
    if categories is None:
        categories = Category.get_category_tree()

    return {"categories": categories, "template_name": template_name}


@register.inclusion_tag("wagtail_feathers/templatetags/category_navigation.html")
def render_category_navigation(categories=None, current_category=None):
    """Render category navigation menu."""
    if categories is None:
        categories = Category.get_visible_root_categories()

    return {"categories": categories, "current_category": current_category}


@register.inclusion_tag("wagtail_feathers/templatetags/category_breadcrumbs.html")
def render_category_breadcrumbs(category):
    """Render breadcrumb navigation for a category."""
    if not category:
        return {"breadcrumbs": []}

    breadcrumbs = category.get_breadcrumb_trail()
    breadcrumbs.append(category)  # Add current category

    return {"breadcrumbs": breadcrumbs}


@register.filter
def has_children(category):
    """Check if a category has visible children."""
    if not category:
        return False
    return category.get_visible_children().exists()


@register.filter
def get_depth(category):
    """Get display depth of a category."""
    if not category:
        return 0
    return category.get_depth_display()


@register.filter
def is_ancestor_of(category, other_category):
    """Check if category is an ancestor of other_category."""
    if not category or not other_category:
        return False
    return category.is_ancestor_of(other_category)


@register.filter
def is_descendant_of(category, other_category):
    """Check if category is a descendant of other_category."""
    if not category or not other_category:
        return False
    return category.is_descendant_of(other_category)


@register.simple_tag
def render_category_icon(category, css_classes=""):
    """Render category icon with optional CSS classes."""
    if not category or not category.icon:
        return ""

    icon_classes = f"{category.icon} {css_classes}".strip()
    return format_html('<i class="{}"></i>', icon_classes)


@register.simple_tag(takes_context=True)
def category_tree_json(context, categories=None):
    """Generate JSON representation of category tree for JavaScript."""
    import json

    if categories is None:
        categories = Category.get_category_tree()

    def category_to_dict(cat):
        return {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "url_path": cat.get_url_path(),
            "icon": cat.icon,
            "depth": cat.get_depth_display(),
            "live": cat.live,
            "children": [category_to_dict(child) for child in cat.get_visible_children()],
        }

    # Build tree starting from root categories
    tree_data = []
    for root_cat in Category.get_visible_root_categories():
        tree_data.append(category_to_dict(root_cat))

    return mark_safe(json.dumps(tree_data))


@register.simple_tag
def category_count():
    """Get total count of visible categories."""
    return Category.get_category_tree().count()


@register.simple_tag
def category_stats():
    """Get category statistics."""
    visible_categories = Category.get_category_tree()
    root_categories = Category.get_visible_root_categories()

    return {
        "total_visible": visible_categories.count(),
        "root_categories": root_categories.count(),
        "max_depth": max([cat.get_depth_display() for cat in visible_categories] or [0]),
    }
