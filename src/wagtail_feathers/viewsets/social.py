from wagtail.snippets.views.snippets import SnippetViewSet

from wagtail_feathers.mixins import LocaleAwareMixin
from wagtail_feathers.models import SocialMediaSettings


class SocialMediaSettingsViewSet(LocaleAwareMixin, SnippetViewSet):
    """Admin viewset for managing SocialMediaSettings in admin interface."""

    model = SocialMediaSettings
    icon = "heroicons-users-outline"
    _base_list_filter = ("site",)
    list_per_page = 10