from django import template
from wagtail.models import Locale, Site

from wagtail_feathers.models.social import SocialMediaSettings

register = template.Library()


@register.inclusion_tag("wagtail_feathers/templatetags/social_media_links.html", takes_context=True)
def social_media_links(context, variant="default", show_names=False):
    """
    Renders social media links with theme variants.

    Usage:
    {% social_media_links %}
    {% social_media_links "sidebar" %}
    {% social_media_links variant="sidebar" show_names=True %}

    """
    request = context.get("request")
    site = Site.find_for_request(request) if request else None

    social_links = []
    if site:
        try:
            current_locale = Locale.get_active()
            social_settings = SocialMediaSettings.objects.filter(
                    site=site,
                    locale=current_locale
            ).first()

            if social_settings:
                social_links = social_settings.social_media_links.all()

        except SocialMediaSettings.DoesNotExist:
            social_settings = SocialMediaSettings.objects.filter(site=site).first()
            if social_settings:
                social_links = social_settings.social_media_links.all()

    return {
        "social_links": social_links,
        "request": request,
        "variant": variant,
        "show_names": show_names,
    }