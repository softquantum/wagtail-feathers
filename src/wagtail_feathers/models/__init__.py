"""Wagtail_feathers models."""

from .author import AuthorType, PageAuthor
from .base import (
    CustomWagtailPage,
    FeatherBasePage,
    FeatherBasePageMeta,
    FeatherBasePageTag,
    FeatherPage,
    IndexPage,
    ItemPage,
    WebBasePage,
)
from .errors import ErrorPage
from .faq import FAQ, FAQItem
from .geographic import CountryGroup, PageCountry
from .inline import RelatedDocument, RelatedExternalLink, RelatedPage
from .navigation import FlatMenu, Footer, FooterNavigation, Menu, MenuItem, NestedMenu
from .person import Person, PersonGroup
from .settings import SiteSettings
from .social import SocialMediaLink, SocialMediaSettings
from .specialized_pages import FAQBasePage, FormBasePage
from .taxonomy import (
    Category,
    Classifier,
    ClassifierGroup,
    PageCategory,
    PageClassifier,
)
from .utils import FEATHER_PAGE_MODELS, get_page_models

__all__ = [
    "AuthorType",
    "Category",
    "Classifier",
    "ClassifierGroup",
    "CountryGroup",
    "CustomWagtailPage",
    "ErrorPage",
    "FAQItem",
    "FAQBasePage",
    "FAQ",
    "FeatherBasePage",
    "FeatherPage",
    "FeatherBasePageMeta",
    "FeatherBasePageTag",
    "Footer",
    "FooterNavigation",
    "FormBasePage",
    "IndexPage",
    "ItemPage",
    "get_page_models",
    "PageAuthor",
    "PageCategory",
    "PageClassifier",
    "PageCountry",
    "Person",
    "PersonGroup",
    "SiteSettings",
    "SocialMediaLink",
    "SocialMediaSettings",
    "Menu",
    "MenuItem",
    "NestedMenu",
    "FlatMenu",
    "RelatedPage",
    "RelatedDocument",
    "RelatedExternalLink",
    "WebBasePage",
]
