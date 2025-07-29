from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from wagtail_feathers.models import Category


class Command(BaseCommand):
    help = "Manage category tree structure and hidden root"

    def add_arguments(self, parser):
        parser.add_argument(
            "action", choices=["init", "repair", "stats", "create-root", "list"], help="Action to perform"
        )
        parser.add_argument("--name", type=str, help="Name for new root category")
        parser.add_argument("--slug", type=str, help="Slug for new root category")
        parser.add_argument("--icon", type=str, help="Icon for new root category")
        parser.add_argument("--force", action="store_true", help="Force action without confirmation")

    def handle(self, *args, **options):
        action = options["action"]

        if action == "init":
            self.init_hidden_root()
        elif action == "repair":
            self.repair_tree()
        elif action == "stats":
            self.show_stats()
        elif action == "create-root":
            self.create_root_category(options)
        elif action == "list":
            self.list_categories()

    def init_hidden_root(self):
        """Initialize or ensure hidden root exists."""
        self.stdout.write("Initializing category tree...")

        try:
            with transaction.atomic():
                root = Category.get_or_create_hidden_root()
                if root:
                    self.stdout.write(
                        self.style.SUCCESS(f"Hidden root category initialized: {root.name} (ID: {root.id})")
                    )
                else:
                    self.stdout.write(self.style.WARNING("Hidden root already exists"))
        except Exception as e:
            raise CommandError(f"Failed to initialize hidden root: {e}")

    def repair_tree(self):
        """Repair tree structure and fix any orphaned categories."""
        self.stdout.write("Repairing category tree...")

        try:
            with transaction.atomic():
                # Ensure hidden root exists
                hidden_root = Category.get_or_create_hidden_root()

                # Find orphaned categories (those without proper tree structure)
                orphaned = []
                for category in Category.objects.exclude(name=Category.ROOT_CATEGORY):
                    try:
                        # Check if category has proper tree structure
                        category.get_depth()
                        category.get_ancestors()
                    except Exception:
                        orphaned.append(category)

                # Move orphaned categories under hidden root
                if orphaned:
                    self.stdout.write(f"Found {len(orphaned)} orphaned categories")
                    for category in orphaned:
                        self.stdout.write(f"  Moving {category.name} to root level")
                        category.move(hidden_root, pos="sorted-child")

                # Rebuild tree
                Category.fix_tree()

                self.stdout.write(
                    self.style.SUCCESS(f"Tree repair completed. Fixed {len(orphaned)} orphaned categories.")
                )

        except Exception as e:
            raise CommandError(f"Failed to repair tree: {e}")

    def show_stats(self):
        """Show category tree statistics."""
        self.stdout.write("Category Tree Statistics:")
        self.stdout.write("=" * 40)

        # Hidden root info
        try:
            hidden_root = Category.get_or_create_hidden_root()
            self.stdout.write(f"Hidden Root: {hidden_root.name} (ID: {hidden_root.id})")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Hidden root error: {e}"))
            return

        # Visible categories
        visible_categories = Category.get_category_tree()
        total_visible = visible_categories.count()

        # Root categories
        root_categories = Category.get_visible_root_categories()
        total_roots = root_categories.count()

        # Depth analysis
        if visible_categories:
            depths = [cat.get_depth_display() for cat in visible_categories]
            max_depth = max(depths) if depths else 0
            depth_counts = {}
            for depth in depths:
                depth_counts[depth] = depth_counts.get(depth, 0) + 1
        else:
            max_depth = 0
            depth_counts = {}

        self.stdout.write(f"Total visible categories: {total_visible}")
        self.stdout.write(f"Root level categories: {total_roots}")
        self.stdout.write(f"Maximum depth: {max_depth}")

        if depth_counts:
            self.stdout.write("\nCategories by depth:")
            for depth in sorted(depth_counts.keys()):
                self.stdout.write(f"  Level {depth}: {depth_counts[depth]} categories")

        # Live vs disabled
        live_count = visible_categories.filter(live=True).count()
        disabled_count = visible_categories.filter(live=False).count()

        self.stdout.write(f"\nLive categories: {live_count}")
        self.stdout.write(f"Disabled categories: {disabled_count}")

    def create_root_category(self, options):
        """Create a new root-level category."""
        name = options.get("name")
        if not name:
            raise CommandError("--name is required for create-root action")

        slug = options.get("slug", "")
        icon = options.get("icon", "")

        try:
            with transaction.atomic():
                category = Category.add_root_category(name=name, slug=slug, icon=icon, live=True)

                self.stdout.write(self.style.SUCCESS(f"Created root category: {category.name} (ID: {category.id})"))

        except Exception as e:
            raise CommandError(f"Failed to create root category: {e}")

    def list_categories(self):
        """List all categories in tree order."""
        self.stdout.write("Category Tree:")
        self.stdout.write("=" * 40)

        try:
            # Show hidden root
            hidden_root = Category.get_or_create_hidden_root()
            self.stdout.write(f"[Hidden Root] {hidden_root.name}")

            # Show visible tree
            categories = Category.get_category_tree()

            if not categories:
                self.stdout.write("  (no visible categories)")
                return

            for category in categories:
                depth = category.get_depth_display()
                indent = "  " + ("  " * depth)
                status = "✓" if category.live else "✗"
                icon = f" [{category.icon}]" if category.icon else ""

                self.stdout.write(f"{indent}{status} {category.name} (ID: {category.id}){icon}")

        except Exception as e:
            raise CommandError(f"Failed to list categories: {e}")
