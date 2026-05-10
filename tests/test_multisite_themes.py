"""Tests for multisite theme functionality using pytest."""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from wagtail.models import Locale, Page, Site

from wagtail_feathers.models.settings import SiteSettings
from wagtail_feathers.themes import (
    TemplateLoader,
    ThemeRegistry,
    _current_site,
    get_active_theme_info,
    get_current_site,
    invalidate_active_theme_info,
    theme_registry,
    use_site,
)


@pytest.fixture
def default_locale():
    """Create default locale for Wagtail."""
    locale, created = Locale.objects.get_or_create(
        language_code='en',
        defaults={'language_code': 'en'}
    )
    return locale


@pytest.fixture
def multisite_setup(default_locale):
    """Set up multiple sites for testing."""
    # Get or create root page
    root_page = Page.objects.first()
    if not root_page:
        root_page = Page.add_root(title="Root", locale=default_locale)
    
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


@pytest.fixture
def two_themes_two_sites(multisite_setup):
    """Set up two real on-disk themes wired to two sites' SiteSettings."""
    sites = multisite_setup
    with tempfile.TemporaryDirectory() as temp_dir:
        themes_dir = Path(temp_dir) / "themes"
        themes_dir.mkdir()

        for theme_name in ("corporate", "blog"):
            tdir = themes_dir / theme_name
            tdir.mkdir()
            (tdir / "templates").mkdir()
            (tdir / "templates" / "base.html").write_text(f"<html>{theme_name}</html>")
            with open(tdir / "theme.json", "w") as f:
                json.dump({"name": theme_name, "display_name": theme_name.title()}, f)

        with patch.object(theme_registry, "themes_dir", themes_dir):
            theme_registry.discover_themes(force_refresh=True)

            main_ss = SiteSettings.for_site(sites["main"])
            main_ss.active_theme = "corporate"
            main_ss.save()

            blog_ss = SiteSettings.for_site(sites["blog"])
            blog_ss.active_theme = "blog"
            blog_ss.save()

            # Clear caches so the new settings are picked up fresh
            theme_registry._clear_theme_caches()
            yield {"sites": sites, "themes_dir": themes_dir}


@pytest.mark.django_db
def test_template_loader_resolves_per_site_via_contextvar(two_themes_two_sites):
    """Loader returns the active theme for the site in the contextvar."""
    sites = two_themes_two_sites["sites"]
    themes_dir = two_themes_two_sites["themes_dir"]
    loader = TemplateLoader(None, dirs=["/default/dir"])

    with use_site(sites["main"]):
        dirs_main = loader.get_dirs()
    with use_site(sites["blog"]):
        dirs_blog = loader.get_dirs()

    assert str(themes_dir / "corporate" / "templates") in dirs_main
    assert str(themes_dir / "blog" / "templates") not in dirs_main
    assert str(themes_dir / "blog" / "templates") in dirs_blog
    assert str(themes_dir / "corporate" / "templates") not in dirs_blog


@pytest.mark.django_db
def test_active_theme_precedence_django_setting_over_database(two_themes_two_sites):
    """Precedence: Django setting > per-site SiteSettings > no theme."""
    sites = two_themes_two_sites["sites"]

    # Without override: per-site DB settings win
    assert theme_registry.get_active_theme(site=sites["main"]).name == "corporate"
    assert theme_registry.get_active_theme(site=sites["blog"]).name == "blog"

    # With Django override: all sites get the override
    with patch("wagtail_feathers.themes.settings") as mock_settings:
        mock_settings.WAGTAIL_FEATHERS_ACTIVE_THEME = "blog"
        assert theme_registry.get_active_theme(site=sites["main"]).name == "blog"
        assert theme_registry.get_active_theme(site=sites["blog"]).name == "blog"


def test_use_site_context_manager_sets_and_resets():
    """`use_site` sets the contextvar inside the block and restores prior value on exit."""
    assert get_current_site() is None
    sentinel = object()
    with use_site(sentinel):
        assert get_current_site() is sentinel
    assert get_current_site() is None

    # Nested use_site
    outer = object()
    inner = object()
    with use_site(outer):
        assert get_current_site() is outer
        with use_site(inner):
            assert get_current_site() is inner
        assert get_current_site() is outer
    assert get_current_site() is None


def test_async_middleware_propagates_contextvar():
    """Async middleware sets the contextvar; it survives await and resets on exit."""
    from wagtail_feathers.middleware import theme_site_middleware

    sentinel_site = object()
    captured = {}

    async def fake_view(request):
        # An await before reading proves the var survives task scheduling.
        await asyncio.sleep(0)
        captured["site"] = get_current_site()

        class _Resp:
            status_code = 200
        return _Resp()

    middleware = theme_site_middleware(fake_view)

    class _Req:
        pass

    with patch.object(Site, "find_for_request", return_value=sentinel_site):
        asyncio.run(middleware(_Req()))

    assert captured["site"] is sentinel_site
    # contextvar must be reset after the middleware returns
    assert _current_site.get() is None


def test_sync_middleware_propagates_and_resets_contextvar():
    """The sync middleware path sets and resets the contextvar correctly."""
    from wagtail_feathers.middleware import theme_site_middleware

    sentinel_site = object()
    captured = {}

    def fake_view(request):
        captured["site"] = get_current_site()

        class _Resp:
            status_code = 200
        return _Resp()

    middleware = theme_site_middleware(fake_view)

    class _Req:
        pass

    with patch.object(Site, "find_for_request", return_value=sentinel_site):
        middleware(_Req())

    assert captured["site"] is sentinel_site
    assert _current_site.get() is None


@pytest.mark.django_db
def test_save_site_settings_invalidates_cache(two_themes_two_sites):
    """Saving SiteSettings.active_theme busts the per-site theme info cache."""
    sites = two_themes_two_sites["sites"]

    # Prime cache for the blog site
    info_before = get_active_theme_info(site=sites["blog"])
    assert info_before["name"] == "blog"

    # Change the active theme on that site
    blog_settings = SiteSettings.for_site(sites["blog"])
    blog_settings.active_theme = "corporate"
    blog_settings.save()

    info_after = get_active_theme_info(site=sites["blog"])
    assert info_after["name"] == "corporate"

    # Clean up explicitly — the fixture's invalidation does the same on teardown
    invalidate_active_theme_info(site=sites["blog"])
    invalidate_active_theme_info(site=sites["main"])


@pytest.mark.django_db
def test_theme_aware_cached_loader_keys_by_site(two_themes_two_sites):
    """ThemeAwareCachedLoader caches each (site, template_name) pair separately."""
    from django.template import Engine

    from wagtail_feathers.themes import TemplateLoader, ThemeAwareCachedLoader

    sites = two_themes_two_sites["sites"]
    engine = Engine(dirs=[], app_dirs=False)
    loader = ThemeAwareCachedLoader(
        engine,
        ["wagtail_feathers.themes.TemplateLoader"],
    )

    with use_site(sites["main"]):
        key_main = loader.cache_key("base.html")
    with use_site(sites["blog"]):
        key_blog = loader.cache_key("base.html")
    key_no_site = loader.cache_key("base.html")

    assert key_main != key_blog
    assert str(sites["main"].id) in key_main
    assert str(sites["blog"].id) in key_blog
    # Without a site, fall back to the unqualified key (compat with vanilla cached.Loader)
    assert key_no_site == "base.html"

    # Sanity: the loader actually wraps our TemplateLoader
    assert any(isinstance(child, TemplateLoader) for child in loader.loaders)


@pytest.mark.django_db
def test_get_all_theme_template_dirs_returns_every_theme(two_themes_two_sites):
    """get_all_theme_template_dirs returns one entry per discovered theme."""
    themes_dir = two_themes_two_sites["themes_dir"]
    dirs = theme_registry.get_all_theme_template_dirs()

    assert (themes_dir / "corporate" / "templates") in dirs
    assert (themes_dir / "blog" / "templates") in dirs
    assert len(dirs) == 2


@pytest.mark.django_db
def test_variant_discovery_unions_across_themes(two_themes_two_sites):
    """Admin variant discovery surfaces variants from every installed theme,
    not just the default site's."""
    themes_dir = two_themes_two_sites["themes_dir"]

    # Drop a variant into each theme; they should both surface in discovery.
    (themes_dir / "corporate" / "templates" / "pages").mkdir(parents=True)
    (themes_dir / "corporate" / "templates" / "pages" / "article--minimal.html").write_text("x")
    (themes_dir / "blog" / "templates" / "pages").mkdir(parents=True)
    (themes_dir / "blog" / "templates" / "pages" / "article--magazine.html").write_text("x")

    class _Cls:
        template = "pages/article.html"

    from wagtail_feathers.models.base import FeatherBasePage

    variants = FeatherBasePage.get_available_template_variants.__func__(_Cls)
    assert "minimal" in variants
    assert "magazine" in variants