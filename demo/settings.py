"""
Django settings for wagtail-feathers demo project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-demo-key-only-for-development-do-not-use-in-production"

# SECURITY WARNING: don"t run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Application definition
INSTALLED_APPS = [
    "wagtail_feathers",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "modelcluster",
    "taggit",
    "django_filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "wagtail.locales",
    "showcase",
    # added with wagtail_feathers
    "wagtailmarkdown",
    "wagtail.contrib.settings",
    "wagtail.contrib.table_block",
    "django_countries",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": False,  # Since we specify the loader sequence explicitly below, it is False
        "OPTIONS": {
            "loaders": [
                "wagtail_feathers.themes.TemplateLoader",
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",  # added by Wagtail Feathers
                "wagtail_feathers.context_processors.active_theme_info",  # added by Wagtail Feathers
            ],
        },
    },
]

WSGI_APPLICATION = "wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Wagtail settings
WAGTAIL_SITE_NAME = "Wagtail Feathers Demo"
WAGTAILADMIN_BASE_URL = "http://localhost:8000"

STATICFILES_FINDERS = [
    "wagtail_feathers.themes.ThemeAwareFileSystemFinder",
    # "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]


# Wagtail Feathers settings
# You can omit these settings if you want to use the default ones.

## Authorship default roles, modify as needed.
AUTHORSHIP_ROLES = [
    "Author",
    "Co-Author",
    "Contributor",
    "Reviewer",
]

## Theme System Settings
# This is set through the admin in Site Settings
# DO NOT USE UNLESS you want to override the admin Site Settings for dev purposes
# WAGTAIL_FEATHERS_ACTIVE_THEME = "minimal"  # e.g., "minimal"
WAGTAIL_FEATHERS_ACTIVE_THEME = "quantum"