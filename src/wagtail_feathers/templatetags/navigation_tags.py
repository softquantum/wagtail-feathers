from django import template
from wagtail.models import Locale, Page, Site

register = template.Library()


def has_children(page):
    # Generically allow index pages to list their children
    return page.get_children().live().exists()


def is_active(page, current_page):
    # To give us an active state on the main navigation
    return current_page.url_path.startswith(page.url_path) if current_page else False


@register.simple_tag(takes_context=True)
def get_site_root(context):
    """Return a core.Page.

    The main menu needs to have the site.root_page defined else will
    return an object attribute error ('str' object has no attribute 'get_children')
    If no site root for the active locale, revert to English.
    """
    active_locale = Locale.get_active()
    site = Site.find_for_request(context["request"])
    site_root = site.root_page
    if site_root.locale != active_locale:
        site_root = Page.objects.filter(locale=active_locale, depth=2).first()
        if not site_root:
            english_locale = Locale.objects.get(language_code="en")
            site_root = Page.objects.filter(locale=english_locale, depth=2).first()
    return site_root


@register.inclusion_tag("wagtail_feathers/templatetags/_top_menu_items.html", takes_context=True)
def top_menu_items(context, parent, calling_page=None):
    """Retrieve the top menu items - the immediate children of the parent page that have 'show_in_menus' turned on.

    Implementation in your template:
    {% load wagtailcore_tags %}
    {% wagtail_site.root_page as site_root %}
    ...
    {% top_menu_items parent=site_root calling_page=self %}
    ...
    """
    #TODO: should I take the locale from context instead ? or at least try ?
    active_locale = Locale.get_active()
    menuitems = (
        parent.get_children()
        .live()
        .in_menu()
        .filter(locale=active_locale)
        .select_related('content_type', 'locale')
        .specific()
    )

    for menuitem in menuitems:
        # We don't directly check if calling_page is None since the template
        # engine can pass an empty string to calling_page
        # if the variable passed as calling_page does not exist.
        menuitem.active = calling_page.url_path.startswith(menuitem.url_path) if calling_page else False
    return {
        "calling_page": calling_page,
        "menuitems": menuitems,
        "request": context["request"],  # required by the pageurl tag if used
    }


@register.inclusion_tag("wagtail_feathers/templatetags/_mobile_menu_items.html", takes_context=True)
def mobile_menu_items(context, parent, calling_page=None):
    """Retrieve the mobile menu items - same as top_menu_items but with mobile-specific styling."""
    active_locale = Locale.get_active()
    menuitems = (
        parent.get_children()
        .live()
        .in_menu()
        .filter(locale=active_locale)
        .select_related('content_type', 'locale')
        .specific()
    )

    for menuitem in menuitems:
        menuitem.active = calling_page.url_path.startswith(menuitem.url_path) if calling_page else False
    return {
        "calling_page": calling_page,
        "menuitems": menuitems,
        "request": context["request"],
    }


@register.inclusion_tag("wagtail_feathers/templatetags/breadcrumbs.html", takes_context=True)
def breadcrumbs(context):
    self = context.get("self")
    if self is None or self.depth <= 2:
        # When on the home page, displaying breadcrumbs is irrelevant.
        ancestors = ()
    else:
        ancestors = Page.objects.ancestor_of(self, inclusive=True).filter(depth__gt=1)
    return {
        "ancestors": ancestors,
        "request": context["request"],
    }


@register.simple_tag(takes_context=True)
def get_footer_for_site(context):
    """Get the Footer instance for the current site and locale.
    
    Returns the first Footer object matching both the current site and locale.
    Falls back to any footer for the current site if no locale match is found.
    Falls back to None if no footer exists for the site.
    """
    from wagtail_feathers.models import Footer
    
    try:
        # Get current site from request
        site = Site.find_for_request(context.get('request'))
        if not site:
            return None
            
        # Get current locale
        active_locale = Locale.get_active()
        
        # Try to get footer for current site and locale with optimized queries
        footer = (
            Footer.objects
            .filter(site=site, locale=active_locale)
            .select_related('footer_navigation', 'locale', 'site')
            .first()
        )
        
        # Fallback to any footer for this site if no locale match
        if not footer:
            footer = (
                Footer.objects
                .filter(site=site)
                .select_related('footer_navigation', 'locale', 'site')
                .first()
            )
            
        return footer
    
    except Exception:
        return None


@register.simple_tag
def get_footer_page_children(parent_page):
    """Get children of a page optimized for footer navigation.
    
    This tag is used in footer templates to avoid N+1 queries when
    displaying page children in navigation menus.
    """
    if not parent_page:
        return []
    
    return (
        parent_page.get_children()
        .live()
        .in_menu()
        .select_related('content_type', 'locale')
        .specific()
    )


