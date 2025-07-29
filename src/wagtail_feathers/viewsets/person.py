from wagtail.snippets.views.snippets import SnippetViewSet

from wagtail_feathers.models import Person, PersonGroup


class PersonViewSet(SnippetViewSet):
    """Admin viewset for managing Person snippets in the Wagtail admin interface."""

    model = Person
    menu_label = "Person"
    icon = "heroicons-user-outline"
    list_display = ("first_name", "last_name", "display_name", "thumb_image", "user_email")
    list_export = ("first_name", "last_name", "display_name", "user_email")


class PersonGroupViewSet(SnippetViewSet):
    """Admin viewset for managing PersonGroup snippets in the Wagtail admin interface."""

    model = PersonGroup
    menu_icon = "heroicons-user-group-outline"
    search_fields = "name"
