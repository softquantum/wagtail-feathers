from django.utils.translation import gettext_lazy as _
from wagtail.snippets.views.snippets import SnippetViewSet

from wagtail_feathers.mixins import LocaleAwareMixin
from wagtail_feathers.models import FlatMenu, Footer, FooterNavigation, Menu, NestedMenu


class MenuViewSet(LocaleAwareMixin, SnippetViewSet):
    """Admin viewset for managing hierarchical Menu snippets in the Wagtail admin interface."""

    model = Menu
    menu_label = _("Menus")
    icon = "list-ul"
    _base_list_display = ("name", "slug", "menu_items_count")
    _base_list_filter = ()
    search_fields = ("name", "description")

    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return self.model.objects.select_related("locale").prefetch_related("menu_items")


class NestedMenuViewSet(LocaleAwareMixin, SnippetViewSet):
    """Admin viewset for managing Navigation snippets in the Wagtail admin interface."""

    model = NestedMenu
    menu_label = _("Nested Menus")
    icon = "heroicons-queue-list-outline"
    _base_list_display = ("name", "slug")
    _base_list_filter = ()
    search_fields = ("name",)


class FlatMenuViewSet(LocaleAwareMixin, SnippetViewSet):
    """Admin viewset for managing Structured Menu snippets in the Wagtail admin interface."""

    model = FlatMenu
    menu_label = _("Flat Menus")
    icon = "heroicons-bars-3-outline"
    _base_list_display = ("name", "slug")
    _base_list_filter = ()
    search_fields = ("name",)
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return self.model.objects.select_related("locale")


class FooterNavigationViewSet(LocaleAwareMixin, SnippetViewSet):
    """Admin viewset for managing Footer Navigation snippets in the Wagtail admin interface."""

    model = FooterNavigation
    menu_label = "Footer Navigation"
    icon = "heroicons-queue-list-outline"
    _base_list_filter = ()
    _base_list_display = ("name", "slug")


class FooterViewSet(LocaleAwareMixin, SnippetViewSet):
    """Admin viewset for managing Footer snippets in the Wagtail admin interface."""

    model = Footer
    menu_label = _("Footers")
    icon = "heroicons-window-outline"
    _base_list_display = ("name", "copyright_text", "footer_navigation")
    _base_list_filter = ("footer_navigation",)
    search_fields = ("name", "copyright_text", "footer_text")
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return self.model.objects.select_related("locale", "footer_navigation")
