from django.utils.translation import get_language, get_language_info

from wagtail_feathers.models import Category
from wagtail_feathers.themes import get_active_theme_info


def active_theme_info(request):  # noqa
    """Django context processor to add theme information to all templates.

    Adds 'theme' variable to template context with active theme info, resolved
    against the current request's Wagtail Site (cache-keyed per site).
    """
    from wagtail.models import Site

    try:
        site = Site.find_for_request(request)
        return {"theme": get_active_theme_info(site=site)}
    except Exception:
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
