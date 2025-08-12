from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Display file paths for Tailwind CSS content scanning configuration"

    def handle(self, *args, **options):
        app_dir = Path(__file__).parent.parent.parent

        source_path = f'@source "{app_dir}/templates/**/*.{{py,html}}"'

        self.stdout.write(source_path)
