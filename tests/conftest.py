"""Pytest configuration for Wagtail Feathers tests."""

import logging

import pytest

logger = logging.getLogger(__name__)


def pytest_configure(config):
    """Configure pytest environment for wagtail_feathers package testing."""
    import sys
    print("Python path:", sys.path)
    try:
        import wagtail
        print("Wagtail found at:", wagtail.__file__)
        from wagtail import VERSION
        print("Wagtail version:", VERSION)

    except ImportError as e:
        print("Failed to import:", e)
        print("Current sys.modules keys:", [k for k in sys.modules.keys() if "wagtail" in k])
