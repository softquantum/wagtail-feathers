# Development Guide for Wagtail Feathers

## Setup Development Environment

### 1. Clone and Install
```bash
git clone https://github.com/softquantum/wagtail-feathers.git
cd wagtail-feathers

# Install in development mode with all dev dependencies
pip install -e ".[dev]"
```

### 2. Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=wagtail_feathers --cov-report=html

# Run specific test files
pytest src/wagtail_feathers/tests/test_themes.py
```

### 3. Use Tox for Multi-Environment Testing
```bash
# Run tests across all supported Python/Django/Wagtail combinations
tox

# Run only linting
tox -e lint

# Run only formatting
tox -e format

# Run coverage
tox -e coverage
```

## Package Management with Flit

### Building the Package
```bash
# Install flit if not already installed
pip install flit

# Build the package
flit build

# Check what files will be included
flit build --check
```

### Publishing to PyPI
```bash
# Publish to Test PyPI first
flit publish --repository testpypi

# Publish to PyPI
flit publish
```

### Installing from Local Build
```bash
# Install in development mode
flit install --symlink

# Install normally
flit install
```

## Code Quality

### Linting and Formatting
```bash
# Check code style
ruff check src/

# Fix auto-fixable issues
ruff check --fix src/

# Format code
ruff format src/

# Check formatting without applying
ruff format --check src/
```

### Pre-commit Hooks (Optional)
```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
EOF

# Install hooks
pre-commit install
```

## Testing Strategy

### Test Structure
- `src/wagtail_feathers/tests/` contains all tests
- Tests are organized by functionality (themes, models, etc.)
- Uses pytest with Django integration
- Includes factories for test data generation

### Writing Tests
```python
import pytest
from wagtail_feathers.models import FeatherBasePage

@pytest.mark.django_db
def test_feather_base_page_creation():
    page = FeatherBasePage(title="Test Page")
    assert page.title == "Test Page"
```

### Test Settings
The package includes a dedicated test settings file at:
`src/wagtail_feathers/tests/settings.py`

This provides a minimal Django/Wagtail setup for testing.

## Version Management

Version is managed in `src/wagtail_feathers/__init__.py`:

```python
__version__ = "0.1.0"
```

Flit automatically reads this for package metadata.

## Documentation

### Updating README
The main README.md should be kept up-to-date with:
- Feature descriptions
- Installation instructions  
- Usage examples
- API documentation

### Docstrings
Follow Google-style docstrings:

```python
def my_function(param1: str, param2: int) -> bool:
    """Short description of the function.

    Longer description if needed.

    Args:
        param1: Description of parameter 1.
        param2: Description of parameter 2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When parameter is invalid.
    """
    pass
```

## Release Process

1. **Update Version**: Increment version in `__init__.py`
2. **Update Changelog**: Document changes in README or CHANGELOG
3. **Run Tests**: Ensure all tests pass across environments
4. **Build Package**: `flit build`
5. **Test Install**: Install and test in clean environment
6. **Publish**: `flit publish` (to testpypi first, then pypi)
7. **Tag Release**: Create git tag for the version
8. **Update Documentation**: Ensure docs reflect new version

## Contributing

When contributing:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Follow code style guidelines
6. Update documentation as needed
7. Submit a pull request

## Local Development Tips

### Working with the Parent Project
When developing wagtail_feathers within the project:

```bash
# Link local development version
pip uninstall wagtail-feathers
pip install -e /path/to/wagtail_feathers

# Or use pip's editable install
pip install -e ../wagtail_feathers
```

### Database Migrations
For testing database changes:

```bash
# Create test migrations
python -m pytest src/wagtail_feathers/tests/ --create-db

# Or run with Django management command
DJANGO_SETTINGS_MODULE=wagtail_feathers.tests.settings python -m django makemigrations wagtail_feathers
```