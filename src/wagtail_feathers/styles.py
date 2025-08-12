from pathlib import Path


def get_tailwind_paths():
    """Return paths for Tailwind content scanning."""
    package_dir = Path(__file__).parent
    return [
        str(package_dir / "**" / "*.html"),
        str(package_dir / "**" / "*.py"),
    ]