"""Viewsets for wagtail_feathers."""
from .author import AuthorTypeViewSet
from .navigation import FlatMenuViewSet, FooterNavigationViewSet, FooterViewSet, MenuViewSet, NestedMenuViewSet
from .person import PersonGroupViewSet, PersonViewSet
from .social import SocialMediaSettingsViewSet
from .taxonomy import CategoryFilterSet, CategoryViewSet, ClassifierGroupViewSet, ClassifierViewSet
from .viewset_groups import (
    FeathersAuthorshipViewSetGroup,
    FeathersNavigationViewSetGroup,
    FeathersSiteComponentsViewSetGroup,
    FeathersTaxonomyViewSetGroup,
    PersonViewSetGroup,
)

__all__ = [
    "AuthorTypeViewSet",
    "CategoryViewSet",
    "ClassifierViewSet",
    "ClassifierGroupViewSet",
    "CategoryFilterSet",
    "FooterNavigationViewSet",
    "FooterViewSet",
    "MenuViewSet",
    "NestedMenuViewSet",
    "FlatMenuViewSet",
    "PersonViewSet",
    "PersonGroupViewSet",
    "FeathersNavigationViewSetGroup",
    "FeathersTaxonomyViewSetGroup",
    "FeathersAuthorshipViewSetGroup",
    "PersonViewSetGroup",
    "FeathersSiteComponentsViewSetGroup",
    "SocialMediaSettingsViewSet",
]
