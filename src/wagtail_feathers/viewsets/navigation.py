from django.utils.translation import gettext_lazy as _
from wagtail.snippets.views.snippets import SnippetViewSet

from wagtail_feathers.models import FlatMenu, Footer, FooterNavigation, Menu, NestedMenu


class MenuViewSet(SnippetViewSet):
    """Admin viewset for managing hierarchical Menu snippets in the Wagtail admin interface."""

    model = Menu
    menu_label = _("Menus")
    icon = "list-ul"
    list_display = ("name", "slug", "menu_items_count")
    list_filter = ("locale",)
    search_fields = ("name", "description")

    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return self.model.objects.select_related("locale").prefetch_related("menu_items")


class NestedMenuViewSet(SnippetViewSet):
    """Admin viewset for managing Navigation snippets in the Wagtail admin interface."""

    model = NestedMenu
    menu_label = _("Nested Menus")
    icon = "heroicons-queue-list-outline"
    list_display = ("name", "slug")
    list_filter = ("locale",)
    search_fields = ("name",)


class FlatMenuViewSet(SnippetViewSet):
    """Admin viewset for managing Structured Menu snippets in the Wagtail admin interface."""

    model = FlatMenu
    menu_label = _("Flat Menus")
    icon = "heroicons-bars-3-outline"
    list_display = ("name", "slug")
    list_filter = ("locale",)
    search_fields = ("name",)
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return self.model.objects.select_related("locale")


class FooterNavigationViewSet(SnippetViewSet):
    """Admin viewset for managing Footer Navigation snippets in the Wagtail admin interface."""

    model = FooterNavigation
    menu_label = "Footer Navigation"
    icon = "heroicons-queue-list-outline"
    list_display = ("name", "slug")


class FooterViewSet(SnippetViewSet):
    """Admin viewset for managing Footer snippets in the Wagtail admin interface."""

    model = Footer
    menu_label = _("Footers")
    icon = "heroicons-window-outline"
    list_display = ("name", "copyright_text", "footer_navigation")
    list_filter = ("locale", "footer_navigation")
    search_fields = ("name", "copyright_text", "footer_text")
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return self.model.objects.select_related("locale", "footer_navigation")
