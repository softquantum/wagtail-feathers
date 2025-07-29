"""
Management command to create sample taxonomy data.

Usage:
    python manage.py create_sample_taxonomy
    python manage.py create_sample_taxonomy --fixtures-only
    python manage.py create_sample_taxonomy --factories-only
    python manage.py create_sample_taxonomy --clear-existing
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import transaction

from wagtail_feathers.models.taxonomy import Category, ClassifierGroup, Classifier


class Command(BaseCommand):
    help = 'Create sample taxonomy data (Categories and Classifiers)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fixtures-only',
            action='store_true',
            help='Load only from fixtures (JSON file)',
        )
        parser.add_argument(
            '--factories-only', 
            action='store_true',
            help='Create only using factories (Python code)',
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing taxonomy data before creating new data',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating it',
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No data will be created')
            )

        try:
            with transaction.atomic():
                if options['clear_existing']:
                    self._clear_existing_data(options['dry_run'])

                if options['fixtures_only']:
                    self._load_fixtures(options['dry_run'])
                elif options['factories_only']:
                    self._create_with_factories(options['dry_run'])
                else:
                    # Default: try factories first, fallback to fixtures
                    try:
                        self._create_with_factories(options['dry_run'])
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'Factory creation failed: {e}')
                        )
                        self.stdout.write('Falling back to fixtures...')
                        self._load_fixtures(options['dry_run'])

                if options['dry_run']:
                    # Rollback the transaction in dry run mode
                    raise CommandError("Dry run completed - rolling back changes")

        except CommandError:
            if options['dry_run']:
                self.stdout.write(
                    self.style.SUCCESS('Dry run completed successfully')
                )
            else:
                raise
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating sample data: {e}')
            )
            raise

        self._show_summary()

    def _clear_existing_data(self, dry_run=False):
        """Clear existing taxonomy data."""
        self.stdout.write('Clearing existing taxonomy data...')
        
        if not dry_run:
            # Clear classifiers first (due to foreign key constraints)
            classifier_count = Classifier.objects.count()
            group_count = ClassifierGroup.objects.count()
            
            Classifier.objects.all().delete()
            ClassifierGroup.objects.all().delete()
            
            # Clear categories (but preserve root)
            category_count = Category.objects.filter(live=True).count()
            Category.objects.filter(live=True).delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Cleared {classifier_count} classifiers, '
                    f'{group_count} classifier groups, and '
                    f'{category_count} categories'
                )
            )
        else:
            classifier_count = Classifier.objects.count()
            group_count = ClassifierGroup.objects.count()
            category_count = Category.objects.filter(live=True).count()
            
            self.stdout.write(
                self.style.WARNING(
                    f'Would clear {classifier_count} classifiers, '
                    f'{group_count} classifier groups, and '
                    f'{category_count} categories'
                )
            )

    def _load_fixtures(self, dry_run=False):
        """Load sample data from fixtures."""
        self.stdout.write('Loading sample data from fixtures...')
        
        if not dry_run:
            try:
                call_command('loaddata', 'wagtail_feathers/fixtures/sample_taxonomy.json')
                self.stdout.write(
                    self.style.SUCCESS('Successfully loaded fixture data')
                )
            except Exception as e:
                raise CommandError(f'Failed to load fixtures: {e}')
        else:
            self.stdout.write(
                self.style.WARNING('Would load sample_taxonomy.json fixture')
            )

    def _create_with_factories(self, dry_run=False):
        """Create sample data using factories."""
        self.stdout.write('Creating sample data using factories...')
        
        if not dry_run:
            try:
                from wagtail_feathers.factories import create_all_sample_data
                
                result = create_all_sample_data()
                
                self.stdout.write(
                    self.style.SUCCESS('Successfully created sample data using factories')
                )
                
                # Show what was created
                categories = result['categories']
                classifiers = result['classifiers']
                
                self.stdout.write(f'Created {len(categories)} category trees')
                self.stdout.write(
                    f'Created {len(classifiers["subject_groups"]) + len(classifiers["attribute_groups"])} '
                    f'classifier groups'
                )
                
            except ImportError:
                raise CommandError(
                    'Factory Boy not available. Install with: pip install factory-boy'
                )
            except Exception as e:
                raise CommandError(f'Failed to create data with factories: {e}')
        else:
            self.stdout.write(
                self.style.WARNING('Would create sample data using factories')
            )

    def _show_summary(self):
        """Show summary of created data."""
        category_count = Category.objects.filter(live=True).count()
        group_count = ClassifierGroup.objects.count()
        classifier_count = Classifier.objects.count()
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('TAXONOMY DATA SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Categories: {category_count}')
        self.stdout.write(f'Classifier Groups: {group_count}')
        self.stdout.write(f'Classifiers: {classifier_count}')
        self.stdout.write('='*50)
        
        if category_count > 0:
            self.stdout.write('\nCategory Tree Structure:')
            self._show_category_tree()
        
        if group_count > 0:
            self.stdout.write('\nClassifier Groups:')
            self._show_classifier_groups()

    def _show_category_tree(self):
        """Display the category tree structure."""
        try:
            root = Category.get_or_create_hidden_root()
            for child in root.get_children():
                self._print_category_branch(child, 0)
        except Exception:
            self.stdout.write('  (Unable to display tree structure)')

    def _print_category_branch(self, category, level):
        """Recursively print category branch."""
        indent = '  ' * level
        icon = f' {category.icon}' if category.icon else ''
        self.stdout.write(f'{indent}├── {category.name}{icon}')
        
        for child in category.get_children():
            self._print_category_branch(child, level + 1)

    def _show_classifier_groups(self):
        """Display classifier groups and their counts."""
        for group in ClassifierGroup.objects.all().order_by('type', 'name'):
            classifier_count = group.classifiers.count()
            self.stdout.write(
                f'  {group.type}: {group.name} ({classifier_count} classifiers)'
            )