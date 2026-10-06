# wagtail-feathers

Reusable Wagtail package (`src/wagtail_feathers`). Supports Wagtail 7.3+ and 8.x on Django 5.2–6.1, Python 3.12+. Custom base page models (`WAGTAIL_PAGE_MODEL`) are deliberately unsupported; `check_default_page_model()` rejects them at startup.

## Testing

- Full matrix: `tox` (Python 3.12–3.14 × Django 5.2/6.0/6.1 × Wagtail 7.3/7.4/8.0). Takes ~15 minutes.
- Quick checks: the tox envs live in `.tox/` and can be used directly, e.g.
  `.tox/py313-django52-wagtail80/bin/python -m pytest --no-migrations tests/test_admin_smoke.py`
  (pytest config in `pyproject.toml` puts `src` and `.` on the path and uses `tests.settings`).
- `tests/testapp` holds concrete page models for the admin smoke tests; it has migrations, so plain `pytest` (with migrations) also works.
- Migration drift: `PYTHONPATH=src:. DJANGO_SETTINGS_MODULE=tests.settings .tox/<env>/bin/python -m django makemigrations wagtail_feathers --check --dry-run`. Run it on the lowest and highest Wagtail env when StreamField blocks change.

## Demo site

- `demo/` runs the package against the `quantum` theme. From `demo/`: `python manage.py migrate && python manage.py setup_demo_data && python manage.py runserver`.
- `setup_demo_data` is re-runnable and creates a superuser, pages, categories and classifiers, which is what you need for a browsable admin (classifier chooser, category listing buttons, block form layouts).
- To test against a specific Wagtail version without touching `demo/db.sqlite3`, point `DATABASES` at a scratch copy via a settings module that does `from settings import *`, and run `manage.py` with a `.tox/<env>/bin/python`.

## Conventions

- Block template variants are `<template>--<variant>.html` siblings discovered from theme template dirs at startup; restart the server after adding one.
- The Wagtail Feathers admin menu lives under Settings (`add_to_settings_menu = True`).
