from models import FAQCategory
from wagtail.snippets.views.snippets import SnippetViewSet


class PersonGroupViewSet(SnippetViewSet):
    """Admin viewset for managing PersonGroup snippets in the Wagtail admin interface."""

    model = FAQCategory
    menu_icon = "heroicons-user-group-outline"
    search_fields = "question"