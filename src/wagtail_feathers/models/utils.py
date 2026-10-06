"""Utility functions and variables for the wagtail_feathers.models package."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# List to store all FeatherPage models
FEATHER_PAGE_MODELS = []

DEFAULT_PAGE_MODEL = "wagtailcore.Page"


def get_page_models():
    """Return a list of all FeatherPage models."""
    return FEATHER_PAGE_MODELS


def check_default_page_model():
    """Raise ImproperlyConfigured when the project swaps Wagtail's Page model."""
    page_model = getattr(settings, "WAGTAIL_PAGE_MODEL", DEFAULT_PAGE_MODEL)
    if page_model.lower() != DEFAULT_PAGE_MODEL.lower():
        raise ImproperlyConfigured(
            f"wagtail-feathers requires Wagtail's default Page model, but WAGTAIL_PAGE_MODEL is set to "
            f"'{page_model}'. Custom base page models are not supported: remove the WAGTAIL_PAGE_MODEL "
            f"setting and add your shared page fields to a subclass of FeatherPage instead."
        )
