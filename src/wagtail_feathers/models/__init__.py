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
from .faq import FAQ, FAQCategory
from .geographic import PageCountry
from .inline import RelatedDocument, RelatedExternalLink, RelatedPage
from .navigation import FlatMenu, Footer, FooterNavigation, Menu, MenuItem, NestedMenu
from .person import Person, PersonGroup
from .reading_time import ReadingTimeMixin
from .seo import SeoMixin, SeoContentType, TwitterCardType
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
    "CustomWagtailPage",
    "ErrorPage",
    "FAQ",
    "FAQBasePage",
    "FAQCategory",
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
    "ReadingTimeMixin",
    "SeoMixin",
    "SeoContentType",
    "TwitterCardType",
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
