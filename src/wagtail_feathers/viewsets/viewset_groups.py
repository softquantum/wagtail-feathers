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
    menu_icon = "group"
    menu_order = 410
    add_to_settings_menu = False
    items = (PersonViewSet, PersonGroupViewSet)


# For Settings Menu:
# === === === === ===
class FeathersNavigationViewSetGroup(SnippetViewSetGroup):
    """Admin viewset for managing Settings specific to Wagtail Feathers."""

    menu_label = "Navigation"
    menu_icon = "wagtail-icon"
    menu_order = 100
    add_to_admin_menu = False
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
    add_to_admin_menu = False
    items = (
        CategoryViewSet,
        ClassifierGroupViewSet,
    )

class FeathersAuthorshipViewSetGroup(SnippetViewSetGroup):
    """Admin viewset for managing Settings specific to Wagtail Feathers."""

    menu_label = "Authorship"
    menu_icon = "wagtail-icon"
    menu_order = 120
    add_to_admin_menu = False
    items = (
        AuthorTypeViewSet,
    )


class FeathersSiteComponentsViewSetGroup(SnippetViewSetGroup):
    """Admin viewset for managing site components."""

    menu_label = "Components"
    menu_icon = "wagtail-icon"
    menu_order = 130
    add_to_admin_menu = False
    items = (
        FooterViewSet,
        SocialMediaSettingsViewSet,
    )


class WagtailFeathersViewSetGroup(SnippetViewSetGroup):
    """Admin viewset for managing Wagtail Feathers components."""

    menu_label = "Wagtail Feathers"
    menu_icon = "snippet"
    menu_order = 110
    add_to_settings_menu = True
    items = (
        FeathersNavigationViewSetGroup,
        FeathersTaxonomyViewSetGroup,
        FeathersAuthorshipViewSetGroup,
        FeathersSiteComponentsViewSetGroup,
    )
