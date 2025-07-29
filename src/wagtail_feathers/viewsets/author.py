from wagtail.snippets.views.snippets import SnippetViewSet

from wagtail_feathers.models import AuthorType


class AuthorTypeViewSet(SnippetViewSet):
    """Admin viewset for managing Person snippets in the Wagtail admin interface."""

    model = AuthorType
    menu_label = "Author Types"
    icon = "heroicons-user-plus-outline"
    list_display = ("name", "description")
