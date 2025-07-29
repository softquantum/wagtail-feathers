from wagtail.snippets.views.snippets import SnippetViewSet

from wagtail_feathers.models import SocialMediaSettings


class SocialMediaSettingsViewSet(SnippetViewSet):
    """Admin viewset for managing SocialMediaSettings in admin interface."""

    model = SocialMediaSettings
    icon = "heroicons-users-outline"
    list_filter = ("locale", "site",)
    list_per_page = 10