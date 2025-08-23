"""Viewsets for wagtail_feathers."""
from .author import AuthorTypeViewSet
from .choosers import classifier_chooser_viewset
from .components import FAQItemViewSet, FAQViewSet
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
    "FAQViewSet",
    "FAQItemViewSet",
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
