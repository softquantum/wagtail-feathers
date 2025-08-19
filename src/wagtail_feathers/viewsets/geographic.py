"""Geographic viewsets for wagtail_feathers."""

from wagtail.snippets.views.snippets import SnippetViewSet

from wagtail_feathers.models import CountryGroup


class CountryGroupViewSet(SnippetViewSet):
    """Admin viewset for managing Country Groups."""
    
    model = CountryGroup
    menu_label = "Country Groups"
    icon = "globe-americas"
    menu_order = 100
    add_to_admin_menu = False
    
    list_display = ["name", "description", "country_count", "is_active"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "description"]
    
    def country_count(self, obj):
        """Display country count in list view."""
        return obj.country_count()
    country_count.short_description = "Countries"