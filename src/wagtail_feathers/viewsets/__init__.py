"""Viewsets for wagtail_feathers."""

import importlib

_LAZY_IMPORTS = {
    "faq_chooser_viewset": ".faq_chooser",
    "AuthorTypeViewSet": ".author",
    "classifier_chooser_viewset": ".choosers",
    "FAQItemViewSet": ".components",
    "FAQViewSet": ".components",
    "CountryGroupViewSet": ".geographic",
    "FlatMenuViewSet": ".navigation",
    "FooterNavigationViewSet": ".navigation",
    "FooterViewSet": ".navigation",
    "MenuViewSet": ".navigation",
    "NestedMenuViewSet": ".navigation",
    "PersonGroupViewSet": ".person",
    "PersonViewSet": ".person",
    "SocialMediaSettingsViewSet": ".social",
    "CategoryFilterSet": ".taxonomy",
    "CategoryViewSet": ".taxonomy",
    "ClassifierGroupViewSet": ".taxonomy",
    "FeathersAuthorshipViewSetGroup": ".viewset_groups",
    "FeathersGeographicViewSetGroup": ".viewset_groups",
    "FeathersNavigationViewSetGroup": ".viewset_groups",
    "FeathersSiteComponentsViewSetGroup": ".viewset_groups",
    "FeathersTaxonomyViewSetGroup": ".viewset_groups",
    "PersonViewSetGroup": ".viewset_groups",
}

__all__ = list(_LAZY_IMPORTS.keys())


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        module = importlib.import_module(_LAZY_IMPORTS[name], __package__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
