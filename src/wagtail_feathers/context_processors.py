from django.utils.translation import get_language, get_language_info

from wagtail_feathers.themes import get_active_theme_info
from wagtail_feathers.models import Category


def active_theme_info(request):  # noqa
    """Django context processor to add theme information to all templates.

    Adds 'theme' variable to template context with active theme info.
    This is automatically site-aware when used within Wagtail.
    """
    from wagtail.models import Site
    from wagtail_feathers.themes import theme_registry
    
    try:
        # Get the current site for this request
        site = Site.find_for_request(request)
        
        # Get the active theme for this specific site
        active_theme = theme_registry.get_active_theme(site)
        
        if not active_theme:
            return {"theme": None}

        return {
            "theme": {
                "name": active_theme.name,
                "display_name": active_theme.display_name,
                "description": active_theme.description,
                "version": active_theme.version,
                "author": active_theme.author,
                "static_url": f"/static/themes/{active_theme.name}/",
            }
        }
    except Exception:
        # Fallback gracefully if site detection fails
        return {"theme": None}


def category_context(request):
    """Django context processor to add category information to all templates.

    Adds category navigation and tree data to template context.
    """
    try:
        return {
            "category_tree": Category.get_category_tree(),
            "root_categories": Category.get_visible_root_categories(),
        }
    except Exception:
        # Fail gracefully if categories aren't set up yet
        return {
            "category_tree": Category.objects.none(),
            "root_categories": Category.objects.none(),
        }


def admin_context(request):
    """Django context processor to add admin-specific context variables."""
    # Only add classifier data in admin context to avoid performance impact
    if hasattr(request, 'resolver_match') and request.resolver_match:
        if hasattr(request.resolver_match, 'app_names') and 'wagtailadmin' in request.resolver_match.app_names:
            try:
                from .models.taxonomy import Classifier
                return {
                    'all_classifiers': Classifier.objects.select_related('group').order_by('group__type', 'group__name', 'name')
                }
            except Exception:
                pass
    return {}
