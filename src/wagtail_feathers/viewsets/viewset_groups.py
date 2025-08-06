from wagtail.snippets.views.snippets import SnippetViewSetGroup

from wagtail_feathers.viewsets import (
    AuthorTypeViewSet,
    CategoryViewSet,
    ClassifierGroupViewSet,
    FlatMenuViewSet,
    FooterNavigationViewSet,
    FooterViewSet,
    MenuViewSet,
    NestedMenuViewSet,
    PersonGroupViewSet,
    PersonViewSet,
    SocialMediaSettingsViewSet,
)


class PersonViewSetGroup(SnippetViewSetGroup):
    """Admin viewset for managing Person snippets in the Wagtail admin interface."""

    menu_label = "People"
    menu_icon = "heroicons-user-group-solid"
    menu_order = 410  # 000 being 1st, 100 2nd, etc.
    items = (PersonViewSet, PersonGroupViewSet)


class FeathersNavigationViewSetGroup(SnippetViewSetGroup):
    """Admin viewset for managing Settings specific to Wagtail Feathers."""

    menu_label = "Navigation"
    menu_icon = "wagtail-icon"
    menu_order = 100
    add_to_settings_menu = True
    items = (
        MenuViewSet,
        FlatMenuViewSet,
        NestedMenuViewSet,
        FooterNavigationViewSet,
    )

class FeathersTaxonomyViewSetGroup(SnippetViewSetGroup):
    """Admin viewset for managing Settings specific to Wagtail Feathers."""

    menu_label = "Taxonomy"
    menu_icon = "wagtail-icon"
    menu_order = 110
    add_to_settings_menu = True
    items = (
        CategoryViewSet,
        ClassifierGroupViewSet,
    )

class FeathersAuthorshipViewSetGroup(SnippetViewSetGroup):
    """Admin viewset for managing Settings specific to Wagtail Feathers."""

    menu_label = "Authorship"
    menu_icon = "wagtail-icon"
    menu_order = 120
    add_to_settings_menu = True
    items = (
        AuthorTypeViewSet,
    )


class FeathersSiteComponentsViewSetGroup(SnippetViewSetGroup):
    """Admin viewset for managing site components."""

    menu_label = "Components"
    menu_icon = "wagtail-icon"
    menu_order = 130
    add_to_settings_menu = True
    items = (
        FooterViewSet,
        SocialMediaSettingsViewSet,
    )

