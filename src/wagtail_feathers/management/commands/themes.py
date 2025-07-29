"""
Management commands for theme operations.

Provides commands to list, validate, and manage themes in the Wagtail Feathers system.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from wagtail_feathers.themes import theme_registry


class Command(BaseCommand):
    """Theme management command."""

    help = "Manage Wagtail Feathers themes"

    def add_arguments(self, parser):
        """Add command arguments."""
        subparsers = parser.add_subparsers(dest="action", help="Theme actions")

        list_parser = subparsers.add_parser("list", help="List all available themes")
        list_parser.add_argument("--detailed", "-d", action="store_true", help="Show detailed theme information")

        info_parser = subparsers.add_parser("info", help="Show detailed information about a specific theme")
        info_parser.add_argument("theme_name", help="Name of the theme to show info for")

        validate_parser = subparsers.add_parser("validate", help="Validate themes")
        validate_parser.add_argument(
            "theme_name", nargs="?", help="Name of specific theme to validate (validates all if not specified)"
        )

        activate_parser = subparsers.add_parser("activate", help="Set active theme")
        activate_parser.add_argument("theme_name", help="Name of the theme to activate")

        subparsers.add_parser("current", help="Show currently active theme")

    def handle(self, *args, **options):
        """Handle the command."""
        action = options.get("action")

        if not action:
            self.print_help("manage.py", "themes")
            return

        # Force theme discovery
        theme_registry.discover_themes(force_refresh=True)

        if action == "list":
            self.handle_list(options)
        elif action == "info":
            self.handle_info(options)
        elif action == "validate":
            self.handle_validate(options)
        elif action == "activate":
            self.handle_activate(options)
        elif action == "current":
            self.handle_current(options)
        else:
            raise CommandError(f"Unknown action: {action}")

    def handle_list(self, options):
        """Handle the list action."""
        themes = theme_registry.get_all_themes()
        detailed = options.get("detailed", False)

        if not themes:
            self.stdout.write(self.style.WARNING("No themes found."))
            return

        self.stdout.write(f"\nFound {len(themes)} theme(s):\n")

        for name, theme in themes.items():
            if detailed:
                self.stdout.write(f"📦 {theme.display_name} ({name})")
                self.stdout.write(f"   Description: {theme.description}")
                self.stdout.write(f"   Version: {theme.version}")
                self.stdout.write(f"   Author: {theme.author}")
                self.stdout.write(f"   Path: {theme.path}")
                self.stdout.write(f"   Valid: {'✅' if theme.is_valid else '❌'}")
                self.stdout.write("")
            else:
                status = "✅" if theme.is_valid else "❌"
                active = "🟢" if theme_registry.get_active_theme_name() == name else "⚪"
                self.stdout.write(f"  {active} {status} {theme.display_name} ({name})")

    def handle_info(self, options):
        """Handle the info action."""
        theme_name = options["theme_name"]
        theme = theme_registry.get_theme(theme_name)

        if not theme:
            raise CommandError(f"Theme '{theme_name}' not found.")

        self.stdout.write(f"\n📦 Theme Information: {theme.display_name}\n")
        self.stdout.write(f"Name: {theme.name}")
        self.stdout.write(f"Display Name: {theme.display_name}")
        self.stdout.write(f"Description: {theme.description}")
        self.stdout.write(f"Version: {theme.version}")
        self.stdout.write(f"Author: {theme.author}")
        if theme.author_email:
            self.stdout.write(f"Author Email: {theme.author_email}")
        if theme.author_url:
            self.stdout.write(f"Author URL: {theme.author_url}")
        self.stdout.write(f"Path: {theme.path}")
        self.stdout.write(f"Templates Directory: {theme.templates_dir}")
        self.stdout.write(f"Static Directory: {theme.static_dir}")
        self.stdout.write(f"Valid: {'✅ Yes' if theme.is_valid else '❌ No'}")

        if theme.supports:
            self.stdout.write(f"Supports: {', '.join(theme.supports)}")

        if theme.requires:
            self.stdout.write("Requirements:")
            for req, version in theme.requires.items():
                self.stdout.write(f"  - {req}: {version}")

        # Show active status
        active_theme_name = theme_registry.get_active_theme_name()
        if active_theme_name == theme_name:
            self.stdout.write(self.style.SUCCESS("\n🟢 This theme is currently ACTIVE"))
        else:
            self.stdout.write("\n⚪ This theme is not active")
            if active_theme_name:
                self.stdout.write(f"   Active theme: {active_theme_name}")
            else:
                self.stdout.write("   No theme is currently active")

    def handle_validate(self, options):
        """Handle the validate action."""
        theme_name = options.get("theme_name")

        if theme_name:
            # Validate specific theme
            if not theme_registry.theme_exists(theme_name):
                raise CommandError(f"Theme '{theme_name}' not found.")

            issues = theme_registry.validate_theme(theme_name)

            if not issues:
                self.stdout.write(self.style.SUCCESS(f"✅ Theme '{theme_name}' is valid."))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Theme '{theme_name}' has issues:"))
                for issue in issues:
                    self.stdout.write(f"  - {issue}")
        else:
            # Validate all themes
            themes = theme_registry.get_all_themes()

            if not themes:
                self.stdout.write(self.style.WARNING("No themes found to validate."))
                return

            valid_count = 0
            invalid_count = 0

            self.stdout.write(f"\nValidating {len(themes)} theme(s):\n")

            for name, theme in themes.items():
                issues = theme_registry.validate_theme(name)

                if not issues:
                    self.stdout.write(f"✅ {name}: Valid")
                    valid_count += 1
                else:
                    self.stdout.write(f"❌ {name}: Invalid")
                    for issue in issues:
                        self.stdout.write(f"   - {issue}")
                    invalid_count += 1

            self.stdout.write("\nValidation Summary:")
            self.stdout.write(f"  Valid themes: {valid_count}")
            self.stdout.write(f"  Invalid themes: {invalid_count}")

    def handle_activate(self, options):
        """Handle the activate action."""
        theme_name = options["theme_name"]

        if not theme_registry.theme_exists(theme_name):
            raise CommandError(f"Theme '{theme_name}' not found.")

        # Validate theme first
        issues = theme_registry.validate_theme(theme_name)
        if issues:
            self.stdout.write(self.style.WARNING(f"⚠️  Theme '{theme_name}' has validation issues:"))
            for issue in issues:
                self.stdout.write(f"  - {issue}")

            response = input("\nDo you want to activate this theme anyway? (y/N): ")
            if response.lower() not in ["y", "yes"]:
                self.stdout.write("Theme activation cancelled.")
                return

        # Check if Django settings will override
        django_theme = getattr(settings, "WAGTAIL_FEATHERS_ACTIVE_THEME", None)
        if django_theme:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  Note: WAGTAIL_FEATHERS_ACTIVE_THEME is set to '{django_theme}' in Django settings.\n"
                    "This will override the database setting. Remove it from settings to use database themes."
                )
            )
        
        # Set and persist to database
        if theme_registry.set_active_theme(theme_name):
            self.stdout.write(self.style.SUCCESS(f"🟢 Theme '{theme_name}' activated and saved to database!"))
            if django_theme:
                self.stdout.write(
                    self.style.WARNING("⚠️  Theme saved to database but Django settings will take precedence.")
                )
        else:
            # Fallback to runtime-only activation
            theme_registry._cache_active_theme(theme_name)
            self.stdout.write(self.style.SUCCESS(f"🟢 Theme '{theme_name}' activated (runtime only)!"))
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  Could not save to database. Theme will not persist across server restarts."
                )
            )

    def handle_current(self, options):
        """Handle the current action."""
        active_theme = theme_registry.get_active_theme()
        
        # Determine source of active theme
        django_theme = getattr(settings, "WAGTAIL_FEATHERS_ACTIVE_THEME", None)
        db_theme = theme_registry._get_theme_from_database()

        if active_theme:
            self.stdout.write(f"\n🟢 Currently active theme: {active_theme.display_name} ({active_theme.name})")
            self.stdout.write(f"Version: {active_theme.version}")
            self.stdout.write(f"Path: {active_theme.path}")
            
            # Show source
            if django_theme and django_theme == active_theme.name:
                self.stdout.write(f"Source: Django settings (WAGTAIL_FEATHERS_ACTIVE_THEME)")
            elif db_theme and db_theme == active_theme.name:
                self.stdout.write(f"Source: Database (Site settings)")
            else:
                self.stdout.write(f"Source: Runtime")
        else:
            # Show what's configured but not active
            if django_theme:
                if theme_registry.theme_exists(django_theme):
                    self.stdout.write(f"\n⚪ Theme '{django_theme}' configured in Django settings but not loading")
                else:
                    self.stdout.write(f"\n❌ Theme '{django_theme}' configured in Django settings but not found!")
            elif db_theme and db_theme != "":
                if theme_registry.theme_exists(db_theme):
                    self.stdout.write(f"\n⚪ Theme '{db_theme}' configured in database but not loading")
                else:
                    self.stdout.write(f"\n❌ Theme '{db_theme}' configured in database but not found!")
            elif db_theme == "":
                self.stdout.write("\n🚫 No theme active (explicitly disabled in database)")
            else:
                self.stdout.write("\n⚪ No active theme set")
