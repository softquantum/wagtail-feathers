"""Simple test to verify multisite theme capability using pytest."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from wagtail.models import Page, Site

from wagtail_feathers.models.settings import SiteSettings
from wagtail_feathers.themes import ThemeRegistry


@pytest.fixture
def simple_multisite_setup():
    """Set up simple multisite environment for testing."""
    # Get or create root page
    root_page = Page.objects.first()
    if not root_page:
        root_page = Page.add_root(title="Root")
    
    # Clear existing sites
    Site.objects.all().delete()
    
    # Create multiple sites
    site_main = Site.objects.create(
        hostname='main.example.com',
        port=80,
        root_page=root_page,
        is_default_site=True,
        site_name='Main Site'
    )
    
    site_blog = Site.objects.create(
        hostname='blog.example.com',
        port=80,
        root_page=root_page,
        is_default_site=False,
        site_name='Blog Site'
    )
    
    return {
        'main': site_main,
        'blog': site_blog
    }


@pytest.mark.django_db
def test_site_specific_theme_resolution(simple_multisite_setup):
    """Test that themes are resolved per site."""
    sites = simple_multisite_setup
    
    # Create temporary themes
    with tempfile.TemporaryDirectory() as temp_dir:
        themes_dir = Path(temp_dir) / "themes"
        themes_dir.mkdir()
        
        # Create corporate theme
        corporate_dir = themes_dir / "corporate"
        corporate_dir.mkdir()
        (corporate_dir / "templates").mkdir()
        (corporate_dir / "templates" / "base.html").write_text("<html>Corporate</html>")
        
        corporate_json = {"name": "corporate", "display_name": "Corporate Theme"}
        with open(corporate_dir / "theme.json", "w") as f:
            json.dump(corporate_json, f)
        
        # Create blog theme
        blog_dir = themes_dir / "blog"
        blog_dir.mkdir()
        (blog_dir / "templates").mkdir()
        (blog_dir / "templates" / "base.html").write_text("<html>Blog</html>")
        
        blog_json = {"name": "blog", "display_name": "Blog Theme"}
        with open(blog_dir / "theme.json", "w") as f:
            json.dump(blog_json, f)
        
        # Create registry with test themes
        registry = ThemeRegistry()
        with patch.object(registry, 'themes_dir', themes_dir):
            registry.discover_themes()
            
            # Set different themes for each site
            main_settings = SiteSettings.for_site(sites['main'])
            main_settings.active_theme = "corporate"
            main_settings.save()
            
            blog_settings = SiteSettings.for_site(sites['blog'])
            blog_settings.active_theme = "blog"
            blog_settings.save()
            
            # Test site-specific theme resolution
            main_theme = registry.get_active_theme(sites['main'])
            blog_theme = registry.get_active_theme(sites['blog'])
            
            # Verify correct themes are returned
            assert main_theme.name == "corporate"
            assert blog_theme.name == "blog"
            
            # Verify themes are different
            assert main_theme.name != blog_theme.name


@pytest.mark.django_db
def test_site_specific_theme_setting(simple_multisite_setup):
    """Test setting themes for specific sites."""
    sites = simple_multisite_setup
    
    with tempfile.TemporaryDirectory() as temp_dir:
        themes_dir = Path(temp_dir) / "themes"
        themes_dir.mkdir()
        
        # Create test theme
        theme_dir = themes_dir / "test_theme"
        theme_dir.mkdir()
        (theme_dir / "templates").mkdir()
        (theme_dir / "templates" / "base.html").write_text("<html>Test</html>")
        
        theme_json = {"name": "test_theme", "display_name": "Test Theme"}
        with open(theme_dir / "theme.json", "w") as f:
            json.dump(theme_json, f)
        
        registry = ThemeRegistry()
        with patch.object(registry, 'themes_dir', themes_dir):
            registry.discover_themes()
            
            # Set theme for specific site
            success = registry.set_active_theme("test_theme", site=sites['blog'])
            assert success is True
            
            # Verify it was set for the blog site
            blog_settings = SiteSettings.for_site(sites['blog'])
            assert blog_settings.active_theme == "test_theme"
            
            # Verify other site was not affected
            main_settings = SiteSettings.for_site(sites['main'])
            assert main_settings.active_theme == ""


@pytest.mark.django_db
def test_default_site_fallback(simple_multisite_setup):
    """Test that default site is used when no specific site provided."""
    sites = simple_multisite_setup
    
    with tempfile.TemporaryDirectory() as temp_dir:
        themes_dir = Path(temp_dir) / "themes"
        themes_dir.mkdir()
        
        # Create test theme
        theme_dir = themes_dir / "test_theme"
        theme_dir.mkdir()
        (theme_dir / "templates").mkdir()
        (theme_dir / "templates" / "base.html").write_text("<html>Test</html>")
        
        theme_json = {"name": "test_theme", "display_name": "Test Theme"}
        with open(theme_dir / "theme.json", "w") as f:
            json.dump(theme_json, f)
        
        registry = ThemeRegistry()
        with patch.object(registry, 'themes_dir', themes_dir):
            registry.discover_themes()
            
            # Set theme without specifying site (should use default site)
            success = registry.set_active_theme("test_theme")
            assert success is True
            
            # Verify it was set for the default site (main.example.com)
            main_settings = SiteSettings.for_site(sites['main'])
            assert main_settings.active_theme == "test_theme"
            
            # Get theme without specifying site (should use default site)
            theme = registry.get_active_theme()
            assert theme.name == "test_theme"