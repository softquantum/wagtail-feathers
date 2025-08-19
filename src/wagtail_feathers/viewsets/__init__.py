"""Viewsets for wagtail_feathers."""
from .author import AuthorTypeViewSet
from .geographic import CountryGroupViewSet
from .navigation import FlatMenuViewSet, FooterNavigationViewSet, FooterViewSet, MenuViewSet, NestedMenuViewSet
from .person import PersonGroupViewSet, PersonViewSet
from .social import SocialMediaSettingsViewSet
from .taxonomy import CategoryFilterSet, CategoryViewSet, ClassifierGroupViewSet
from .viewset_groups import (
    FeathersAuthorshipViewSetGroup,
    FeathersGeographicViewSetGroup,
    FeathersNavigationViewSetGroup,
    FeathersSiteComponentsViewSetGroup,
    FeathersTaxonomyViewSetGroup,
    PersonViewSetGroup,
)
from .choosers import classifier_chooser_viewset

__all__ = [
    "AuthorTypeViewSet",
    "CategoryViewSet",
    "ClassifierGroupViewSet",
    "CategoryFilterSet",
    "CountryGroupViewSet",
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
    "FeathersGeographicViewSetGroup",
    "PersonViewSetGroup",
    "FeathersSiteComponentsViewSetGroup",
    "SocialMediaSettingsViewSet",
    "classifier_chooser_viewset"
]
