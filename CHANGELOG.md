# Changelog

## v1.0.0rc3

### Breaking

- Bumped minimum Wagtail to **7.4 LTS** and Django to **5.2**. Wagtail 6.x is no longer supported. Django 6.x is supported (Python 3.12+).

### Improvements

- Per-site theming now resolves correctly at the template loader and static finder layer. New `wagtail_feathers.middleware.theme_site_middleware` (sync + async) binds the current request's Wagtail `Site` to a `contextvars.ContextVar` so themes resolve per-request. Public helpers `get_current_site`, `set_current_site`, and `use_site` are available from `wagtail_feathers.themes` for management commands, scripts, and tests. **Action required:** add `wagtail_feathers.middleware.theme_site_middleware` to `MIDDLEWARE`.
- `get_active_theme_info()` now accepts a `site` argument and is cached in Django's default cache (per-site key) instead of a process-wide `lru_cache`. Cache is invalidated automatically when `SiteSettings.active_theme` changes.
- New `wagtail_feathers.themes.ThemeAwareCachedLoader`: drop-in subclass of Django's `cached.Loader` that keys cache entries by `(site_id, template_name)`. Use it in place of `cached.Loader` if you wrap our template loader, otherwise stock caching would serve one site's theme template to another.
- Admin template-variant discovery (`FeatherBasePage.get_available_template_variants`, `FormBasePage.get_available_template_variants`) now unions variants across every installed theme via the new `ThemeRegistry.get_all_theme_template_dirs()`, so the editor exposes variants from all sites' themes, not just the default site's.

### Bug Fixes

- Fixed silent multi-site theming bug: `TemplateLoader.get_dirs()` and `ThemeAwareFileSystemFinder.get_theme_locations()` always resolved through the default site regardless of which site the request belonged to. They now read the current site from the new context variable populated by `theme_site_middleware`.

## v1.0.0rc2

### Improvements

- Rewrote viewsets `__init__.py` with lazy `__getattr__` pattern
- Refactored viewsets with `LocaleAwareMixin`
- Use `LocaleColumn` instead of `'locale'` in viewsets
- wagtail-localize now auto-discovers the FAQ `ChooserBlock` as a FK to a `TranslatableMixin` model
- Reading time feature now uses language-specific reading speeds to align with wagtail admin content metrics

### Bug Fixes

- Fixed navigation unique constraint to be localized
- Navigation slugs are now synchronized fields with wagtail-localize
- `FormBasePage` slug is now a sync field with wagtail-localize

### Internal

- Refactored test suite
- Updated theme integration tests
- Updated and added new migration files
