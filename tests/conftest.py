"""Pytest configuration for Wagtail Feathers tests."""

import pytest
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def pytest_configure(config):
    """Configure pytest environment for wagtail_feathers package testing."""
    import sys
    print("Python path:", sys.path)
    original_engine = settings.DATABASES["default"]["ENGINE"].split(".")[-1]
    original_name = settings.DATABASES["default"]["NAME"]
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
    print(f"Database override: '{original_engine}:{original_name}' -> 'sqlite3::memory:'")
    try:
        import wagtail
        print("Wagtail found at:", wagtail.__file__)
        from wagtail import VERSION
        print("Wagtail version:", VERSION)

    except ImportError as e:
        print("Failed to import:", e)
        print("Current sys.modules keys:", [k for k in sys.modules.keys() if "wagtail" in k])
