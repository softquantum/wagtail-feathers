"""Tests for the Wagtail Feathers theming system."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from wagtail_feathers.context_processors import active_theme_info
from wagtail_feathers.themes import (
    TemplateLoader,
    ThemeInfo,
    ThemeRegistry,
    get_active_theme_info,
    get_theme_variants,
    theme_registry,
)


@pytest.fixture
def temp_themes_dir(tmp_path):
    """Create a temporary themes directory for testing."""
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()
    return themes_dir


@pytest.fixture
def mock_theme_registry():
    """Create a fresh ThemeRegistry instance for testing."""
    registry = ThemeRegistry()
    return registry


@pytest.fixture
def valid_theme(temp_themes_dir):
    """Create a valid theme structure for testing."""
    theme_dir = temp_themes_dir / "test_theme"
    theme_dir.mkdir()

    # Create required directories
    templates_dir = theme_dir / "templates"
    templates_dir.mkdir()
    static_dir = theme_dir / "static"
    static_dir.mkdir()

    # Create base template
    base_template = templates_dir / "base.html"
    base_template.write_text("<html><body>{% block content %}{% endblock %}</body></html>")

    # Create theme.json
    theme_json = {
        "name": "test_theme",
        "display_name": "Test Theme",
        "description": "A test theme",
        "version": "1.0.0",
        "author": "Test Author",
        "variants": {
            "button": [{"value": "primary", "label": "Primary"}, {"value": "secondary", "label": "Secondary"}]
        },
    }

    with open(theme_dir / "theme.json", "w") as f:
        json.dump(theme_json, f)

    return theme_dir


@pytest.mark.themes
class TestThemeInfo:
    """Tests for the ThemeInfo dataclass."""

    def test_theme_info_initialization(self):
        """Test ThemeInfo initialization with minimal parameters."""
        theme_info = ThemeInfo(name="test", path=Path("/test"))

        assert theme_info.name == "test"
        assert theme_info.path == Path("/test")
        assert theme_info.display_name == "Test"  # Auto-generated from name

    def test_theme_info_with_full_parameters(self):
        """Test ThemeInfo initialization with all parameters."""
        theme_info = ThemeInfo(
            name="test_theme",
            path=Path("/test"),
            display_name="Custom Name",
            description="Test description",
            version="2.0.0",
            author="Test Author",
            author_email="test@example.com",
            author_url="https://example.com",
            supports=["feature1", "feature2"],
            requires={"package1": ">=1.0.0"},
        )

        assert theme_info.name == "test_theme"
        assert theme_info.display_name == "Custom Name"
        assert theme_info.description == "Test description"
        assert theme_info.version == "2.0.0"
        assert theme_info.author == "Test Author"
        assert theme_info.author_email == "test@example.com"
        assert theme_info.author_url == "https://example.com"
        assert theme_info.supports == ["feature1", "feature2"]
        assert theme_info.requires == {"package1": ">=1.0.0"}

    def test_templates_dir_property(self):
        """Test templates_dir property."""
        theme_info = ThemeInfo(name="test", path=Path("/test"))
        assert theme_info.templates_dir == Path("/test/templates")

    def test_static_dir_property(self):
        """Test static_dir property."""
        theme_info = ThemeInfo(name="test", path=Path("/test"))
        assert theme_info.static_dir == Path("/test/static")

    def test_is_valid_property(self, tmp_path):
        """Test is_valid property with various directory structures."""
        # Create a valid theme structure
        theme_dir = tmp_path / "valid_theme"
        theme_dir.mkdir()
        (theme_dir / "templates").mkdir()

        theme_info = ThemeInfo(name="valid_theme", path=theme_dir)
        assert theme_info.is_valid is True

        # Create an invalid theme structure (missing templates)
        invalid_dir = tmp_path / "invalid_theme"
        invalid_dir.mkdir()

        invalid_theme = ThemeInfo(name="invalid_theme", path=invalid_dir)
        assert invalid_theme.is_valid is False


@pytest.mark.themes
class TestThemeRegistry:
    """Tests for the ThemeRegistry class."""

    def test_discover_themes(self, mock_theme_registry, valid_theme, monkeypatch):
        """Test theme discovery."""
        # Set the themes_dir to our test directory
        monkeypatch.setattr(mock_theme_registry, "themes_dir", valid_theme.parent)

        # Discover themes
        mock_theme_registry.discover_themes()

        # Check if our test theme was discovered
        assert "test_theme" in mock_theme_registry._themes
        theme = mock_theme_registry._themes["test_theme"]
        assert theme.name == "test_theme"
        assert theme.display_name == "Test Theme"
        assert theme.is_valid is True

    def test_get_theme(self, mock_theme_registry, valid_theme, monkeypatch):
        """Test getting a theme by name."""
        # Set the themes_dir to our test directory
        monkeypatch.setattr(mock_theme_registry, "themes_dir", valid_theme.parent)
        mock_theme_registry.discover_themes()

        # Get theme
        theme = mock_theme_registry.get_theme("test_theme")
        assert theme is not None
        assert theme.name == "test_theme"

        # Get non-existent theme
        assert mock_theme_registry.get_theme("nonexistent") is None

    def test_theme_exists(self, mock_theme_registry, valid_theme, monkeypatch):
        """Test checking if a theme exists."""
        # Set the themes_dir to our test directory
        monkeypatch.setattr(mock_theme_registry, "themes_dir", valid_theme.parent)
        mock_theme_registry.discover_themes()

        assert mock_theme_registry.theme_exists("test_theme") is True
        assert mock_theme_registry.theme_exists("nonexistent") is False

    def test_cache_active_theme(self, mock_theme_registry, valid_theme, monkeypatch):
        """Test caching the active theme in memory."""
        # Set the themes_dir to our test directory
        monkeypatch.setattr(mock_theme_registry, "themes_dir", valid_theme.parent)
        mock_theme_registry.discover_themes()

        # Cache active theme
        mock_theme_registry._cache_active_theme("test_theme")
        assert mock_theme_registry._active_theme == "test_theme"

        # Cache non-existent theme should raise ImproperlyConfigured
        with pytest.raises(ImproperlyConfigured):
            mock_theme_registry._cache_active_theme("nonexistent")

    @pytest.mark.django_db
    def test_get_active_theme(self, mock_theme_registry, valid_theme, monkeypatch):
        """Test getting the active theme."""
        # Set the themes_dir to our test directory
        monkeypatch.setattr(mock_theme_registry, "themes_dir", valid_theme.parent)
        mock_theme_registry.discover_themes()

        # No active theme initially (no Django setting, no database theme)
        assert mock_theme_registry.get_active_theme() is None

        # Mock Django settings to provide a theme
        with monkeypatch.context() as m:
            m.setattr("wagtail_feathers.themes.settings.WAGTAIL_FEATHERS_ACTIVE_THEME", "test_theme", raising=False)
            active_theme = mock_theme_registry.get_active_theme()
            assert active_theme is not None
            assert active_theme.name == "test_theme"

    def test_validate_theme(self, mock_theme_registry, valid_theme, monkeypatch):
        """Test theme validation."""
        # Set the themes_dir to our test directory
        monkeypatch.setattr(mock_theme_registry, "themes_dir", valid_theme.parent)
        mock_theme_registry.discover_themes()

        # Validate valid theme
        issues = mock_theme_registry.validate_theme("test_theme")
        assert not issues  # No issues for valid theme

        # Create invalid theme (missing base.html)
        (valid_theme / "templates" / "base.html").unlink()
        issues = mock_theme_registry.validate_theme("test_theme")
        assert len(issues) == 1
        assert "Missing base.html template" in issues[0]

        # Validate non-existent theme
        issues = mock_theme_registry.validate_theme("nonexistent")
        assert len(issues) == 1
        assert "not found" in issues[0]

    def test_set_active_theme_success(self, mock_theme_registry, valid_theme, monkeypatch):
        """Test successful theme setting and persistence to database."""
        # Set the themes_dir to our test directory
        monkeypatch.setattr(mock_theme_registry, "themes_dir", valid_theme.parent)
        mock_theme_registry.discover_themes()
        
        # Mock database objects
        mock_site = MagicMock()
        mock_site_settings = MagicMock()
        
        mock_site_query = MagicMock()
        mock_site_query.filter.return_value.first.return_value = mock_site
        
        # Mock Site and SiteSettings
        with patch('wagtail.models.Site') as mock_site_class:
            with patch('wagtail_feathers.models.settings.SiteSettings') as mock_settings_class:
                mock_site_class.objects = mock_site_query
                mock_settings_class.for_site.return_value = mock_site_settings
                
                # Mock cache clearing
                with patch.object(mock_theme_registry, '_clear_theme_caches'):
                    # Test setting valid theme
                    result = mock_theme_registry.set_active_theme("test_theme")
                    
                    assert result is True
                    mock_site_settings.save.assert_called_once()
                    assert mock_site_settings.active_theme == "test_theme"

    def test_set_active_theme_nonexistent_theme(self, mock_theme_registry, valid_theme, monkeypatch):
        """Test setting non-existent theme fails."""
        # Set the themes_dir to our test directory
        monkeypatch.setattr(mock_theme_registry, "themes_dir", valid_theme.parent)
        mock_theme_registry.discover_themes()
        
        # Mock database objects
        mock_site = MagicMock()
        mock_site_query = MagicMock()
        mock_site_query.filter.return_value.first.return_value = mock_site
        
        with patch('wagtail.models.Site') as mock_site_class:
            mock_site_class.objects = mock_site_query
            
            # Test setting non-existent theme
            result = mock_theme_registry.set_active_theme("nonexistent")
            assert result is False

    def test_set_active_theme_no_site(self, mock_theme_registry):
        """Test setting theme when no site exists."""
        mock_site_query = MagicMock()
        mock_site_query.filter.return_value.first.return_value = None
        mock_site_query.first.return_value = None
        
        with patch('wagtail.models.Site') as mock_site_class:
            mock_site_class.objects = mock_site_query
            
            # Test setting when no site exists
            result = mock_theme_registry.set_active_theme("test_theme")
            assert result is False

    def test_set_active_theme_empty_string(self, mock_theme_registry, monkeypatch):
        """Test setting empty string (no theme) succeeds."""
        # Mock database objects
        mock_site = MagicMock()
        mock_site_settings = MagicMock()
        mock_site_query = MagicMock()
        mock_site_query.filter.return_value.first.return_value = mock_site
        
        with patch('wagtail.models.Site') as mock_site_class:
            with patch('wagtail_feathers.models.settings.SiteSettings') as mock_settings_class:
                mock_site_class.objects = mock_site_query
                mock_settings_class.for_site.return_value = mock_site_settings
                
                with patch.object(mock_theme_registry, '_clear_theme_caches'):
                    # Test setting empty string (no theme)
                    result = mock_theme_registry.set_active_theme("")
                    
                    assert result is True
                    assert mock_site_settings.active_theme == ""

    def test_set_active_theme_database_error(self, mock_theme_registry, valid_theme, monkeypatch):
        """Test setting theme handles database errors gracefully."""
        # Set the themes_dir to our test directory
        monkeypatch.setattr(mock_theme_registry, "themes_dir", valid_theme.parent)
        mock_theme_registry.discover_themes()
        
        # Mock database to raise exception
        with patch('wagtail.models.Site') as mock_site_class:
            mock_site_class.objects.filter.side_effect = Exception("Database error")
            
            # Test setting with database error
            result = mock_theme_registry.set_active_theme("test_theme")
            assert result is False

    def test_get_theme_from_database_success(self, mock_theme_registry):
        """Test getting theme from database successfully."""
        # Mock database objects
        mock_site = MagicMock()
        mock_site_settings = MagicMock()
        mock_site_settings.active_theme = "test_theme"
        
        mock_site_query = MagicMock()
        mock_site_query.filter.return_value.first.return_value = mock_site
        
        with patch('wagtail.models.Site') as mock_site_class:
            with patch('wagtail_feathers.models.settings.SiteSettings') as mock_settings_class:
                mock_site_class.objects = mock_site_query
                mock_settings_class.for_site.return_value = mock_site_settings
                
                result = mock_theme_registry._get_theme_from_database()
                assert result == "test_theme"

    def test_get_theme_from_database_no_site(self, mock_theme_registry):
        """Test getting theme from database when no site exists."""
        mock_site_query = MagicMock()
        mock_site_query.filter.return_value.first.return_value = None
        mock_site_query.first.return_value = None
        
        with patch('wagtail.models.Site') as mock_site_class:
            mock_site_class.objects = mock_site_query
            
            result = mock_theme_registry._get_theme_from_database()
            assert result is None

    def test_get_theme_from_database_exception(self, mock_theme_registry):
        """Test getting theme from database handles exceptions."""
        with patch('wagtail.models.Site') as mock_site_class:
            mock_site_class.objects.filter.side_effect = Exception("Database error")
            
            result = mock_theme_registry._get_theme_from_database()
            assert result is None

    def test_clear_theme_caches(self, mock_theme_registry):
        """Test theme cache clearing functionality."""
        # Set some initial state
        mock_theme_registry._active_theme = "test_theme"
        
        # Mock the cached function
        with patch('wagtail_feathers.themes.get_active_theme_info') as mock_cached_func:
            mock_cached_func.cache_clear = MagicMock()
            
            # Call cache clearing
            mock_theme_registry._clear_theme_caches()
            
            # Verify state was cleared
            assert mock_theme_registry._active_theme is None
            mock_cached_func.cache_clear.assert_called_once()

    def test_get_active_theme_with_django_settings(self, mock_theme_registry, valid_theme, monkeypatch):
        """Test get_active_theme with Django settings priority."""
        # Set the themes_dir to our test directory
        monkeypatch.setattr(mock_theme_registry, "themes_dir", valid_theme.parent)
        mock_theme_registry.discover_themes()
        
        # Mock Django settings
        with patch('wagtail_feathers.themes.settings') as mock_settings:
            mock_settings.WAGTAIL_FEATHERS_ACTIVE_THEME = "test_theme"
            
            theme = mock_theme_registry.get_active_theme()
            assert theme is not None
            assert theme.name == "test_theme"

    def test_get_active_theme_with_database_fallback(self, mock_theme_registry, valid_theme, monkeypatch):
        """Test get_active_theme falls back to database when no Django setting."""
        # Set the themes_dir to our test directory
        monkeypatch.setattr(mock_theme_registry, "themes_dir", valid_theme.parent)
        mock_theme_registry.discover_themes()
        
        # Mock Django settings to have no theme setting
        with patch('wagtail_feathers.themes.settings') as mock_settings:
            mock_settings.WAGTAIL_FEATHERS_ACTIVE_THEME = None
            
            # Mock database return
            with patch.object(mock_theme_registry, '_get_theme_from_database', return_value="test_theme"):
                theme = mock_theme_registry.get_active_theme()
                assert theme is not None
                assert theme.name == "test_theme"

    def test_cache_active_theme_none(self, mock_theme_registry):
        """Test caching active theme as None."""
        mock_theme_registry._cache_active_theme(None)
        assert mock_theme_registry._active_theme is None


@pytest.mark.themes
class TestTemplateLoader:
    """Tests for the TemplateLoader class."""

    def test_get_dirs(self, valid_theme, monkeypatch):
        """Test get_dirs method includes theme directories."""
        # Create a loader with some default dirs
        loader = TemplateLoader(None, dirs=["/default/dir"])

        # Mock theme_registry.get_theme_template_dirs to return our test theme
        def mock_get_theme_template_dirs():
            return [valid_theme / "templates"]

        monkeypatch.setattr(theme_registry, "get_theme_template_dirs", mock_get_theme_template_dirs)

        # Get dirs
        dirs = loader.get_dirs()

        # Check if theme dir is included and comes before default dirs
        assert str(valid_theme / "templates") in dirs
        assert "/default/dir" in dirs
        assert dirs.index(str(valid_theme / "templates")) < dirs.index("/default/dir")

    def test_get_template_sources(self, valid_theme, monkeypatch):
        """Test get_template_sources generates correct paths."""
        # Create a loader
        loader = TemplateLoader(None)

        # Mock get_dirs to return our test theme
        def mock_get_dirs():
            return [str(valid_theme / "templates")]

        monkeypatch.setattr(loader, "get_dirs", mock_get_dirs)

        # Get template sources
        sources = list(loader.get_template_sources("base.html"))

        # Check if correct path is generated
        assert len(sources) == 1
        assert sources[0].name == str(valid_theme / "templates" / "base.html")
        assert sources[0].template_name == "base.html"
        assert sources[0].loader == loader


@pytest.mark.themes
class TestThemeUtilityFunctions:
    """Tests for theme utility functions."""

    def test_get_active_theme_info(self, mock_theme_registry, valid_theme, monkeypatch):
        """Test get_active_theme_info function."""
        # Mock theme_registry.get_active_theme
        theme_info = ThemeInfo(
            name="test_theme",
            path=valid_theme,
            display_name="Test Theme",
            description="A test theme",
            version="1.0.0",
            author="Test Author",
        )

        def mock_get_active_theme():
            return theme_info

        monkeypatch.setattr(theme_registry, "get_active_theme", mock_get_active_theme)

        # Clear LRU cache to ensure our mock is used
        get_active_theme_info.cache_clear()

        # Get active theme info
        info = get_active_theme_info()

        # Check if correct info is returned
        assert info is not None
        assert info["name"] == "test_theme"
        assert info["display_name"] == "Test Theme"
        assert info["description"] == "A test theme"
        assert info["version"] == "1.0.0"
        assert info["author"] == "Test Author"
        assert info["static_url"] == "/static/themes/test_theme/"

    @pytest.mark.django_db
    def test_active_theme_info_context_processor(self, monkeypatch):
        """Test active_theme_info function."""
        from unittest.mock import Mock
        from wagtail.models import Site
        
        # Mock a request and site
        mock_request = Mock()
        mock_site = Mock()
        mock_site.hostname = "test.example.com"
        
        # Mock Site.find_for_request to return our mock site
        monkeypatch.setattr(Site, "find_for_request", lambda r: mock_site)
        
        # Mock theme_registry.get_active_theme to return a test theme
        mock_theme = Mock()
        mock_theme.name = "test_theme"
        mock_theme.display_name = "Test Theme"
        mock_theme.description = "Test Description"
        mock_theme.version = "1.0.0"
        mock_theme.author = "Test Author"
        
        # Patch the theme_registry import inside the context processor
        from wagtail_feathers.themes import theme_registry
        monkeypatch.setattr(theme_registry, "get_active_theme", lambda site: mock_theme)

        # Call context processor
        context = active_theme_info(mock_request)

        # Check if theme info is in context
        assert "theme" in context
        assert context["theme"]["name"] == "test_theme"
        assert context["theme"]["display_name"] == "Test Theme"

    def test_get_theme_variants(self, monkeypatch):
        """Test get_theme_variants function."""

        # Test with no active theme
        def mock_get_active_theme_none():
            return None

        monkeypatch.setattr(theme_registry, "get_active_theme", mock_get_active_theme_none)

        # Should return default variants
        variants = get_theme_variants("button")
        assert variants == [
            ("default", "Default"),
            ("primary", "Primary"),
            ("secondary", "Secondary"),
        ]

        # Test with active theme that has variants
        theme_info = MagicMock()
        theme_info.metadata = {
            "variants": {
                "button": [{"value": "custom1", "label": "Custom 1"}, {"value": "custom2", "label": "Custom 2"}]
            }
        }

        def mock_get_active_theme():
            return theme_info

        monkeypatch.setattr(theme_registry, "get_active_theme", mock_get_active_theme)

        # Should return theme-specific variants
        variants = get_theme_variants("button")
        assert variants == [("custom1", "Custom 1"), ("custom2", "Custom 2")]


@pytest.mark.themes  
class TestThemeDiscoveryEdgeCases:
    """Tests for edge cases in theme discovery."""

    def test_discover_themes_without_theme_json(self, mock_theme_registry, temp_themes_dir, monkeypatch):
        """Test discovering themes without theme.json files."""
        # Create theme directory without theme.json
        theme_dir = temp_themes_dir / "simple_theme"
        theme_dir.mkdir()
        (theme_dir / "templates").mkdir()
        
        monkeypatch.setattr(mock_theme_registry, "themes_dir", temp_themes_dir)
        
        mock_theme_registry.discover_themes()
        
        # Should still discover theme with default metadata
        assert "simple_theme" in mock_theme_registry._themes
        theme = mock_theme_registry._themes["simple_theme"]
        assert theme.display_name == "Simple Theme"
        assert "Theme discovered at" in theme.description

    def test_discover_themes_invalid_json(self, mock_theme_registry, temp_themes_dir, monkeypatch):
        """Test discovering themes with invalid theme.json."""
        # Create theme directory with invalid JSON
        theme_dir = temp_themes_dir / "broken_theme"
        theme_dir.mkdir()
        (theme_dir / "templates").mkdir()
        
        # Write invalid JSON
        with open(theme_dir / "theme.json", "w") as f:
            f.write("{ invalid json }")
        
        monkeypatch.setattr(mock_theme_registry, "themes_dir", temp_themes_dir)
        
        mock_theme_registry.discover_themes()
        
        # Should not discover broken theme
        assert "broken_theme" not in mock_theme_registry._themes

    def test_discover_themes_force_refresh(self, mock_theme_registry, temp_themes_dir, monkeypatch):
        """Test force refresh clears existing themes."""
        # Create initial theme
        theme_dir = temp_themes_dir / "test_theme"
        theme_dir.mkdir()
        (theme_dir / "templates").mkdir()
        
        monkeypatch.setattr(mock_theme_registry, "themes_dir", temp_themes_dir)
        
        # First discovery
        mock_theme_registry.discover_themes()
        assert len(mock_theme_registry._themes) == 1
        
        # Add another theme
        theme_dir2 = temp_themes_dir / "test_theme2"
        theme_dir2.mkdir()
        (theme_dir2 / "templates").mkdir()
        
        # Discovery without force refresh should not find new theme
        mock_theme_registry.discover_themes()
        assert len(mock_theme_registry._themes) == 1
        
        # Discovery with force refresh should find both themes
        mock_theme_registry.discover_themes(force_refresh=True)
        assert len(mock_theme_registry._themes) == 2

    def test_discover_themes_nonexistent_directory(self, mock_theme_registry, tmp_path, monkeypatch):
        """Test discovering themes when themes directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"
        monkeypatch.setattr(mock_theme_registry, "themes_dir", nonexistent_dir)
        
        # Should not raise exception
        mock_theme_registry.discover_themes()
        assert len(mock_theme_registry._themes) == 0

    def test_get_theme_template_dirs_no_active_theme(self, mock_theme_registry):
        """Test getting template dirs when no theme is active."""
        result = mock_theme_registry.get_theme_template_dirs()
        assert result == []

    def test_get_theme_template_dirs_invalid_theme(self, mock_theme_registry, temp_themes_dir, monkeypatch):
        """Test getting template dirs for invalid theme."""
        monkeypatch.setattr(mock_theme_registry, "themes_dir", temp_themes_dir)
        
        result = mock_theme_registry.get_theme_template_dirs("nonexistent")
        assert result == []

    @pytest.mark.django_db
    def test_get_active_theme_name(self, mock_theme_registry, valid_theme, monkeypatch):
        """Test getting active theme name."""
        monkeypatch.setattr(mock_theme_registry, "themes_dir", valid_theme.parent)
        mock_theme_registry.discover_themes()
        
        # No active theme initially
        assert mock_theme_registry.get_active_theme_name() is None
        
        # Mock Django settings to provide a theme
        with monkeypatch.context() as m:
            m.setattr("wagtail_feathers.themes.settings.WAGTAIL_FEATHERS_ACTIVE_THEME", "test_theme", raising=False)
            assert mock_theme_registry.get_active_theme_name() == "test_theme"


@pytest.mark.themes
class TestThemeValidationComprehensive:
    """Comprehensive tests for theme validation."""

    def test_validate_theme_missing_templates_dir(self, mock_theme_registry, temp_themes_dir, monkeypatch):
        """Test validation when templates directory is missing."""
        # Create theme without templates directory
        theme_dir = temp_themes_dir / "no_templates"
        theme_dir.mkdir()
        
        theme_json = {"name": "no_templates", "display_name": "No Templates"}
        with open(theme_dir / "theme.json", "w") as f:
            json.dump(theme_json, f)
        
        monkeypatch.setattr(mock_theme_registry, "themes_dir", temp_themes_dir)
        mock_theme_registry.discover_themes()
        
        # The theme won't be discovered because it's invalid, so validate non-existent theme
        issues = mock_theme_registry.validate_theme("no_templates")
        assert "not found" in issues[0]

    def test_validate_theme_invalid_json_file(self, mock_theme_registry, temp_themes_dir, monkeypatch):
        """Test validation with corrupted theme.json."""
        # Create theme with valid structure but invalid JSON
        theme_dir = temp_themes_dir / "bad_json"
        theme_dir.mkdir()
        (theme_dir / "templates").mkdir()
        (theme_dir / "templates" / "base.html").write_text("<html></html>")
        
        # Write invalid JSON
        with open(theme_dir / "theme.json", "w") as f:
            f.write("{ invalid: json, }")
        
        monkeypatch.setattr(mock_theme_registry, "themes_dir", temp_themes_dir)
        mock_theme_registry.discover_themes()
        
        # The theme won't be discovered because of invalid JSON, so validate non-existent theme
        issues = mock_theme_registry.validate_theme("bad_json")
        assert "not found" in issues[0]
