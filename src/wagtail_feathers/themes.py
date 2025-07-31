"""Theme Registry System for Wagtail Feathers.

This module provides a comprehensive theming system that auto-discovers themes
from the BASE_DIR/themes/ directory and manages theme metadata and registration.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from threading import local
from typing import Any, Dict, List, Optional

import django
from django.conf import settings
from django.contrib.staticfiles.finders import FileSystemFinder
from django.contrib.staticfiles.utils import matches_patterns
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.template import TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader
from django.utils.functional import cached_property

logger = logging.getLogger(__name__)



@dataclass
class ThemeInfo:
    """Data class representing theme metadata."""

    name: str
    path: Path
    display_name: str = ""
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    author_email: str = ""
    author_url: str = ""
    screenshot: str = ""
    preview_url: str = ""
    supports: List[str] = field(default_factory=list)
    requires: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default display_name if not provided."""
        if not self.display_name:
            self.display_name = self.name.replace("_", " ").replace("-", " ").title()

    @property
    def templates_dir(self) -> Path:
        """Return the templates directory for this theme."""
        return self.path / "templates"

    @property
    def static_dir(self) -> Path:
        """Return the static directory for this theme."""
        return self.path / "static"

    @property
    def is_valid(self) -> bool:
        """Check if theme has required directory structure."""
        return self.path.exists() and self.path.is_dir() and self.templates_dir.exists()


class ThemeRegistry:
    """Central registry for managing theme discovery, registration, and access.

    Automatically discovers themes from BASE_DIR/themes/ directory by scanning
    for theme.json metadata files and validates theme structure.
    """

    def __init__(self):
        self._themes: Dict[str, ThemeInfo] = {}
        self._active_theme: Optional[str] = None
        self._discovered = False

    @cached_property
    def themes_dir(self) -> Path:
        """Get the themes directory from Django settings."""
        return getattr(settings, "BASE_DIR", Path.cwd()) / "themes"

    def discover_themes(self, force_refresh: bool = False) -> None:
        """Discover all themes in the themes directory.

        Args:
            force_refresh: If True, clear cache and rediscover all themes

        """
        if self._discovered and not force_refresh:
            return

        self._themes.clear()

        if not self.themes_dir.exists():
            logger.warning(f"Themes directory does not exist: {self.themes_dir}")
            return

        for theme_dir in self.themes_dir.iterdir():
            if not theme_dir.is_dir():
                continue

            theme_json_path = theme_dir / "theme.json"
            if not theme_json_path.exists():
                # Still register themes without theme.json for backward compatibility
                theme_info = ThemeInfo(
                    name=theme_dir.name, path=theme_dir, description=f"Theme discovered at {theme_dir}"
                )
            else:
                try:
                    theme_info = self._load_theme_metadata(theme_dir, theme_json_path)
                except Exception as e:
                    logger.error(f"Failed to load theme {theme_dir.name}: {e}")
                    continue

            if theme_info.is_valid:
                self._themes[theme_info.name] = theme_info
                logger.debug(f"Registered theme: {theme_info.name}")
            else:
                logger.warning(f"Invalid theme structure: {theme_dir}")

        self._discovered = True
        logger.info(f"Discovered {len(self._themes)} themes")

    @staticmethod
    def _load_theme_metadata(theme_dir: Path, theme_json_path: Path) -> ThemeInfo:
        """Load theme metadata from theme.json file."""
        with open(theme_json_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        return ThemeInfo(
            name=metadata.get("name", theme_dir.name),
            path=theme_dir,
            display_name=metadata.get("display_name", ""),
            description=metadata.get("description", ""),
            version=metadata.get("version", "1.0.0"),
            author=metadata.get("author", ""),
            author_email=metadata.get("author_email", ""),
            author_url=metadata.get("author_url", ""),
            screenshot=metadata.get("screenshot", ""),
            preview_url=metadata.get("preview_url", ""),
            supports=metadata.get("supports", []),
            requires=metadata.get("requires", {}),
            metadata=metadata,
        )

    def get_theme(self, name: str) -> Optional[ThemeInfo]:
        """Get a theme by name."""
        self.discover_themes()
        return self._themes.get(name)

    def get_all_themes(self) -> Dict[str, ThemeInfo]:
        """Get all registered themes."""
        self.discover_themes()
        return self._themes.copy()

    def theme_exists(self, name: str) -> bool:
        """Check if a theme exists."""
        self.discover_themes()
        return name in self._themes

    def _cache_active_theme(self, name: Optional[str]) -> None:
        """Internal method to cache active theme in memory for performance.
        
        This is used internally by get_active_theme() to cache themes resolved
        from Django settings or database to avoid repeated lookups.
        """
        if name is not None and not self.theme_exists(name):
            raise ImproperlyConfigured(f"Theme '{name}' does not exist")
        self._active_theme = name

    def get_active_theme(self, site=None) -> Optional[ThemeInfo]:
        """Get the currently active theme for a specific site.
        
        Args:
            site: Wagtail Site instance to get theme for. If None, uses default site.
            
        Returns:
            ThemeInfo for the active theme, or None if no theme is active.
        """
        # 1. Check Django settings first (highest priority - overrides all sites)
        django_theme = getattr(settings, "WAGTAIL_FEATHERS_ACTIVE_THEME", None)
        if django_theme:
            return self.get_theme(django_theme)
        
        # 2. Check database settings for specific site
        db_theme = self._get_theme_from_database(site)
        if db_theme and db_theme != "":  # Handle "no theme" (empty string)
            return self.get_theme(db_theme)
        
        # 3. No theme
        return None

    def _get_theme_from_database(self, site=None) -> Optional[str]:
        """Get the active theme name from database settings for a specific site."""
        try:
            from wagtail.models import Site

            from wagtail_feathers.models.settings import SiteSettings
            
            # Use provided site or fallback to default site
            target_site = site
            if not target_site:
                # Use instance-level caching for default site to avoid repeated queries
                cache_key = '_default_site_cache'
                if hasattr(self, cache_key):
                    target_site = getattr(self, cache_key)
                else:
                    # Fallback to default site
                    target_site = Site.objects.filter(is_default_site=True).first()
                    if not target_site:
                        # Final fallback to any site
                        target_site = Site.objects.first()
                    # Cache the result
                    setattr(self, cache_key, target_site)
            
            if target_site:
                # Use instance-level caching for SiteSettings to avoid repeated queries
                settings_cache_key = f'_site_settings_cache_{target_site.id}'
                if hasattr(self, settings_cache_key):
                    site_settings = getattr(self, settings_cache_key)
                else:
                    site_settings = SiteSettings.for_site(target_site)
                    # Cache the result
                    setattr(self, settings_cache_key, site_settings)
                return site_settings.active_theme
        except Exception as e:
            logger.debug(f"Could not get theme from database: {e}")
        
        return None

    def set_active_theme(self, name: Optional[str], site=None) -> bool:
        """Set the active theme and persist it to the database.
        
        This is the main public method for changing themes. It validates the theme,
        saves it to the database, and clears caches to ensure the change takes effect.
        
        Args:
            name: Theme name to set as active, or empty string/None for no theme
            site: Specific site to set theme for, or None to use default site
            
        Returns:
            True if successfully set and persisted, False otherwise
        """
        try:
            from wagtail.models import Site

            from wagtail_feathers.models.settings import SiteSettings
            
            # Use provided site or fallback to default site
            target_site = site
            if not target_site:
                # Fallback to default site
                target_site = Site.objects.filter(is_default_site=True).first()
                if not target_site:
                    # Final fallback to any site
                    target_site = Site.objects.first()
            
            if not target_site:
                logger.error("No site found in database")
                return False
            
            # Validate theme exists if provided (empty string means "no theme")
            if name and not self.theme_exists(name):
                logger.error(f"Theme '{name}' does not exist")
                return False
                
            site_settings = SiteSettings.for_site(target_site)
            site_settings.active_theme = name or ""  # Ensure empty string for None
            site_settings.save()
            
            # Clear all caches to force re-resolution
            self._clear_theme_caches()
            
            logger.info(f"Theme '{name or 'disabled'}' persisted to database for site {target_site.hostname}")
            return True
        except Exception as e:
            logger.error(f"Failed to persist active theme: {e}")
            return False

    def _clear_theme_caches(self) -> None:
        """Clear all theme-related caches to force re-resolution."""
        # Clear runtime theme cache
        self._active_theme = None
        
        # Clear site cache
        if hasattr(self, '_default_site_cache'):
            delattr(self, '_default_site_cache')
        
        # Clear site settings cache
        attrs_to_remove = [attr for attr in dir(self) if attr.startswith('_site_settings_cache_')]
        for attr in attrs_to_remove:
            delattr(self, attr)
        
        # Clear template context cache
        get_active_theme_info.cache_clear()
        
        # Clear Django's template cache if possible
        try:
            from django.template import engines
            from django.template.loader import get_template
            
            # Clear template cache for all engines
            for engine in engines.all():
                if hasattr(engine.engine, '_template_loaders'):
                    # Clear cached loaders
                    engine.engine._template_loaders = None
                if hasattr(engine.engine, 'template_loaders'):
                    # Clear loader caches
                    for loader in engine.engine.template_loaders:
                        if hasattr(loader, 'get_template_cache'):
                            loader.get_template_cache.clear()
                        if hasattr(loader, '_cached_loaders'):
                            loader._cached_loaders = []
        except Exception as e:
            # If cache clearing fails, log but don't break the theme change
            logger.debug(f"Could not clear Django template cache: {e}")

    def get_active_theme_name(self, site=None) -> Optional[str]:
        """Get the name of the currently active theme for a specific site."""
        theme = self.get_active_theme(site)
        return theme.name if theme else None

    def validate_theme(self, name: str) -> List[str]:
        """Validate a theme and return list of issues.

        Returns:
            List of validation error messages (empty if valid)

        """
        theme = self.get_theme(name)
        if not theme:
            return [f"Theme '{name}' not found"]

        issues = []

        # Check required directories
        if not theme.templates_dir.exists():
            issues.append(f"Missing templates directory: {theme.templates_dir}")

        # Check for base template
        base_template = theme.templates_dir / "base.html"
        if not base_template.exists():
            issues.append("Missing base.html template")

        # Check theme.json if it exists
        theme_json = theme.path / "theme.json"
        if theme_json.exists():
            try:
                with open(theme_json, "r") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                issues.append(f"Invalid theme.json: {e}")

        return issues

    def get_theme_template_dirs(self, theme_name: Optional[str] = None, site=None) -> List[Path]:
        """Get template directories for a theme.

        Args:
            theme_name: Theme name, or None to use active theme
            site: Site to get theme for, or None to use default site

        Returns:
            List of template directory paths

        """
        if theme_name is None:
            active_theme = self.get_active_theme(site)
            if not active_theme:
                return []
            theme_name = active_theme.name

        if not theme_name:
            return []

        theme = self.get_theme(theme_name)
        if not theme or not theme.templates_dir.exists():
            return []

        return [theme.templates_dir]


# Global theme registry instance
theme_registry = ThemeRegistry()


class TemplateLoader(BaseLoader):
    """Custom template loader that searches theme templates first, then falls back to defaults.

    This loader enables theme-aware template resolution by checking the active theme's
    templates directory before falling back to the default app templates.
    """

    def __init__(self, engine, dirs=None):
        super().__init__(engine)
        self.dirs = dirs or []
        # Cache the filesystem and app_directories loaders
        self._cached_loaders = None

    def get_dirs(self):
        """Get template directories including theme directories."""
        dirs = []

        # Add active theme template directories first
        theme_dirs = theme_registry.get_theme_template_dirs()
        dirs.extend(str(d) for d in theme_dirs)

        # Add configured template directories
        dirs.extend(self.dirs)

        return dirs

    @staticmethod
    def get_contents(origin):
        """Read template file contents."""
        try:
            with open(origin.name, encoding="utf-8") as fp:
                return fp.read()
        except FileNotFoundError as e:
            raise TemplateDoesNotExist(origin) from e

    def get_template_sources(self, template_name):
        """Generate possible template file paths."""
        for template_dir in self.get_dirs():
            template_path = Path(template_dir) / template_name
            yield Origin(
                name=str(template_path),
                template_name=template_name,
                loader=self,
            )

    def get_fallback_loaders(self):
        """Get fallback loaders for when theme templates are not found."""
        if self._cached_loaders is None:
            from django.template.loaders.filesystem import Loader as FilesystemLoader
            from django.template.loaders.app_directories import Loader as AppDirectoriesLoader
            
            self._cached_loaders = [
                FilesystemLoader(self.engine, self.engine.dirs),
                AppDirectoriesLoader(self.engine)
            ]
        return self._cached_loaders

    def get_template(self, template_name, skip=None):
        """Load a template by name, checking theme dirs first then falling back."""
        # First try to find in theme directories
        tried = []
        for origin in self.get_template_sources(template_name):
            if skip is not None and origin.name in skip:
                tried.append((origin, 'Skipped'))
                continue
            
            try:
                contents = self.get_contents(origin)
            except TemplateDoesNotExist:
                tried.append((origin, 'Source does not exist'))
                continue
            else:
                if django.VERSION >= (5, 2):
                    # Django 5.2+: from_string no longer accepts origin parameter
                    template = self.engine.from_string(contents)
                    template.origin = origin  # Set origin manually for compatibility
                    return template
                else:
                    return self.engine.from_string(contents, origin=origin, name=template_name)

        # If not found in theme dirs, try fallback loaders
        for loader in self.get_fallback_loaders():
            try:
                return loader.get_template(template_name, skip=skip)
            except TemplateDoesNotExist:
                continue
        
        # If we get here, template was not found anywhere
        raise TemplateDoesNotExist(template_name, tried=tried)


class Origin:
    """Template origin information for theme loader."""

    def __init__(self, name, template_name, loader):
        self.name = name
        self.template_name = template_name
        self.loader = loader


# Utility functions for theme context
@lru_cache(maxsize=1)
def get_active_theme_info() -> Optional[Dict[str, Any]]:
    """Get active theme information for template context.

    Returns:
        Dictionary with theme info or None if no active theme

    """
    theme = theme_registry.get_active_theme()
    if not theme:
        return None

    return {
        "name": theme.name,
        "display_name": theme.display_name,
        "description": theme.description,
        "version": theme.version,
        "author": theme.author,
        "static_url": f"/static/themes/{theme.name}/",
    }


def get_theme_variants(component_type: str) -> List[tuple]:
    """Get available theme variants for a component type.

    This function will be used by blocks to provide theme variant choices.
    For now, returns default variants - can be extended to read from theme metadata.

    Args:
        component_type: Type of component (e.g., "button", "card", "header")

    Returns:
        List of (value, label) tuples for variant choices

    """
    default_variants = [
        ("default", "Default"),
        ("primary", "Primary"),
        ("secondary", "Secondary"),
    ]

    # Don't access database during initialization - return defaults
    # This method is called during block __init__ which happens during Django startup
    # TODO: Confirm if other way to achieve this
    try:
        # Only try to get theme info if Django apps are ready
        from django.apps import apps
        if not apps.ready:
            return default_variants
            
        active_theme = theme_registry.get_active_theme()
        if active_theme and "variants" in active_theme.metadata:
            component_variants = active_theme.metadata["variants"].get(component_type, [])
            if component_variants:
                return [(v["value"], v["label"]) for v in component_variants]
    except Exception:
        # If anything goes wrong (database not ready, etc.), fall back to defaults
        pass

    return default_variants


class ThemeAwareFileSystemFinder(FileSystemFinder):
    """Custom static file finder that prioritizes files from the active theme.
    
    This finder extends Django's FileSystemFinder to search for static files
    in the active theme's static directory first, then falls back to other 
    configured static directories.
    """
    
    def __init__(self, app_names=None, *args, **kwargs):
        """Initialize the finder with theme-aware locations."""
        # Get the standard locations first
        super().__init__(app_names, *args, **kwargs)
        
        # We'll dynamically add theme locations in find() method
        # since the active theme can change at runtime
        
    def get_theme_locations(self):
        """Get static file locations for the active theme."""
        locations = []
        
        try:
            active_theme = theme_registry.get_active_theme()
            if active_theme and active_theme.static_dir.exists():
                # Add theme static directory
                theme_static_path = str(active_theme.static_dir)
                theme_prefix = f"themes/{active_theme.name}"
                locations.append((theme_prefix, theme_static_path))
        except Exception as e:
            logger.debug(f"Could not get theme locations: {e}")
            
        return locations
    
    def find(self, path, all=False, find_all=None):
        """Find static files, checking active theme first."""
        # Handle both parameter names for compatibility
        find_all_matches = all or find_all
        matches = []
        
        
        # First check if this path is in the active theme
        theme_locations = self.get_theme_locations()
        for prefix, root in theme_locations:
            if path.startswith(prefix + '/'):
                # Remove theme prefix to get actual file path within theme
                theme_relative_path = path[len(prefix) + 1:]
                theme_storage = FileSystemStorage(location=root)
                if theme_storage.exists(theme_relative_path):
                    matched_path = theme_storage.path(theme_relative_path)
                    if not find_all_matches:
                        return matched_path
                    matches.append(matched_path)
        
        # Also check for files without theme prefix in active theme
        # This allows templates to use {% static 'css/main.css' %} and find
        # the theme-specific version
        for prefix, root in theme_locations:
            theme_storage = FileSystemStorage(location=root)
            if theme_storage.exists(path):
                matched_path = theme_storage.path(path)
                if not find_all_matches:
                    return matched_path
                matches.append(matched_path)
        
        # Fall back to standard finder behavior
        standard_result = super().find(path, find_all=find_all_matches)
        if standard_result:
            if find_all_matches:
                if isinstance(standard_result, list):
                    matches.extend(standard_result)
                else:
                    matches.append(standard_result)
            else:
                return standard_result
        
        # Follow Django's built-in finder pattern:
        # - When find_all=False and we have matches, return first match immediately
        # - Otherwise return matches list (empty if no matches)
        if not find_all_matches and matches:
            return matches[0]
        return matches
    
    def list(self, ignore_patterns):
        """List all static files, including theme files."""
        # Start with standard files
        for path, storage in super().list(ignore_patterns):
            yield path, storage
            
        # Add theme files
        theme_locations = self.get_theme_locations()
        for prefix, root in theme_locations:
            theme_storage = FileSystemStorage(location=root)
            if theme_storage.exists(''):
                # Walk through all files recursively
                for dirpath, dirnames, filenames in os.walk(root):
                    # Get relative path from root
                    relative_dir = os.path.relpath(dirpath, root)
                    if relative_dir == '.':
                        relative_dir = ''
                    
                    for filename in filenames:
                        # Construct the full relative path
                        if relative_dir:
                            file_path = os.path.join(relative_dir, filename)
                        else:
                            file_path = filename
                        
                        # Check against ignore patterns
                        if not matches_patterns(file_path, ignore_patterns):
                            # Yield with theme prefix
                            yield file_path, theme_storage
