# Changelog

## v1.0.0rc1

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
