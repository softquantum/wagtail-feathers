"""Tests for multisite theme functionality using pytest."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from wagtail.models import Page, Site

from wagtail_feathers.models.settings import SiteSettings
from wagtail_feathers.themes import ThemeRegistry


@pytest.fixture
def multisite_setup():
    """Set up multiple sites for testing."""
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
    
    site_shop = Site.objects.create(
        hostname='shop.example.com',
        port=80,
        root_page=root_page,
        is_default_site=False,
        site_name='Shop Site'
    )
    
    return {
        'main': site_main,
        'blog': site_blog,
        'shop': site_shop
    }


@pytest.mark.django_db
def test_site_settings_per_site_isolation(multisite_setup):
    """Test that each site has independent SiteSettings."""
    sites = multisite_setup
    
    # Set different themes for each site
    main_settings = SiteSettings.for_site(sites['main'])
    main_settings.active_theme = "corporate"
    main_settings.save()
    
    blog_settings = SiteSettings.for_site(sites['blog'])
    blog_settings.active_theme = "blog"
    blog_settings.save()
    
    shop_settings = SiteSettings.for_site(sites['shop'])
    shop_settings.active_theme = "shop"
    shop_settings.save()
    
    # Verify isolation
    assert SiteSettings.for_site(sites['main']).active_theme == "corporate"
    assert SiteSettings.for_site(sites['blog']).active_theme == "blog"
    assert SiteSettings.for_site(sites['shop']).active_theme == "shop"


@pytest.mark.django_db
def test_theme_resolution_with_site_parameter(multisite_setup):
    """Test theme resolution with explicit site parameter."""
    sites = multisite_setup
    
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
        
        registry = ThemeRegistry()
        with patch.object(registry, 'themes_dir', themes_dir):
            registry.discover_themes()
            
            # Set up site themes
            main_settings = SiteSettings.for_site(sites['main'])
            main_settings.active_theme = "corporate"
            main_settings.save()
            
            blog_settings = SiteSettings.for_site(sites['blog'])
            blog_settings.active_theme = "blog"
            blog_settings.save()
            
            # Test theme resolution for main site
            active_theme = registry.get_active_theme(site=sites['main'])
            assert active_theme.name == "corporate"
            
            # Test theme resolution for blog site
            active_theme = registry.get_active_theme(site=sites['blog'])
            assert active_theme.name == "blog"


@pytest.mark.django_db
def test_django_setting_overrides_all_sites(multisite_setup):
    """Test that Django setting overrides all sites (expected behavior)."""
    sites = multisite_setup
    
    with tempfile.TemporaryDirectory() as temp_dir:
        themes_dir = Path(temp_dir) / "themes"
        themes_dir.mkdir()
        
        # Create shop theme
        shop_dir = themes_dir / "shop"
        shop_dir.mkdir()
        (shop_dir / "templates").mkdir()
        (shop_dir / "templates" / "base.html").write_text("<html>Shop</html>")
        
        shop_json = {"name": "shop", "display_name": "Shop Theme"}
        with open(shop_dir / "theme.json", "w") as f:
            json.dump(shop_json, f)
        
        registry = ThemeRegistry()
        with patch.object(registry, 'themes_dir', themes_dir):
            registry.discover_themes()
            
            # Set different themes for each site in database
            main_settings = SiteSettings.for_site(sites['main'])
            main_settings.active_theme = "corporate"
            main_settings.save()
            
            blog_settings = SiteSettings.for_site(sites['blog'])
            blog_settings.active_theme = "blog"
            blog_settings.save()
            
            # Mock Django setting override
            with patch('wagtail_feathers.themes.settings') as mock_settings:
                mock_settings.WAGTAIL_FEATHERS_ACTIVE_THEME = "shop"
                
                # Both sites should get the Django setting theme
                theme_main = registry.get_active_theme(site=sites['main'])
                theme_blog = registry.get_active_theme(site=sites['blog'])
                
                assert theme_main.name == "shop"
                assert theme_blog.name == "shop"


@pytest.mark.django_db
def test_set_active_theme_with_site_parameter(multisite_setup):
    """Test that set_active_theme works with site parameter."""
    sites = multisite_setup
    
    with tempfile.TemporaryDirectory() as temp_dir:
        themes_dir = Path(temp_dir) / "themes"
        themes_dir.mkdir()
        
        # Create blog theme
        blog_dir = themes_dir / "blog"
        blog_dir.mkdir()
        (blog_dir / "templates").mkdir()
        (blog_dir / "templates" / "base.html").write_text("<html>Blog</html>")
        
        blog_json = {"name": "blog", "display_name": "Blog Theme"}
        with open(blog_dir / "theme.json", "w") as f:
            json.dump(blog_json, f)
        
        registry = ThemeRegistry()
        with patch.object(registry, 'themes_dir', themes_dir):
            registry.discover_themes()
            
            # Set theme for specific site
            success = registry.set_active_theme("blog", site=sites['blog'])
            assert success is True
            
            # Verify it was set for the blog site
            blog_settings = SiteSettings.for_site(sites['blog'])
            assert blog_settings.active_theme == "blog"
            
            # Verify other sites were not affected
            main_settings = SiteSettings.for_site(sites['main'])
            assert main_settings.active_theme == ""