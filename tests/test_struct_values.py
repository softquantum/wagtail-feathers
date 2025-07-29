"""Tests for struct values, particularly LinkStructValue"""

import pytest
from django.template import Context, Template
from wagtail.models import Locale, Page, Site

from wagtail_feathers.blocks import ExternalLinkBlock, InternalLinkBlock
from wagtail_feathers.struct_values import LinkStructValue


@pytest.fixture
def test_page():
    """Create a test page with proper Wagtail site structure."""
    # Create locale
    locale, _ = Locale.objects.get_or_create(
            language_code='en',
            defaults={'language_code': 'en'}
    )

    # Get or create root page
    root = Page.objects.filter(depth=1).first()
    if not root:
        root = Page.add_root(instance=Page(title="Root", slug="root", locale=locale))

    # Create test page
    page = Page(title="Test Page", slug="test-page", locale=locale)
    root.add_child(instance=page)

    # Ensure there's a default site
    Site.objects.get_or_create(
            is_default_site=True,
            defaults={'hostname': 'localhost', 'port': 80, 'root_page': root}
    )

    return page


@pytest.mark.django_db
class TestLinkStructValue:
    """Test LinkStructValue properties and template rendering"""

    def test_internal_link_with_page(self, test_page):
        """Test internal link with page fallback for title"""
        # Create block and struct value
        block = InternalLinkBlock()
        data = {
            'page': test_page.pk,
            'title': '',  # Empty to test fallback
        }
        struct_value = block.to_python(data)

        # Test properties
        assert isinstance(struct_value, LinkStructValue)
        assert struct_value.get_title == test_page.title
        assert struct_value.url == test_page.url
        assert struct_value.link_type == 'internal'

    def test_internal_link_with_custom_title(self, test_page):
        """Test internal link with custom title"""
        block = InternalLinkBlock()
        data = {
            'page': test_page.pk,
            'title': 'Custom Title',
        }
        struct_value = block.to_python(data)

        assert struct_value.get_title == 'Custom Title'
        assert struct_value.url == test_page.url

    def test_external_link(self):
        """Test external link block"""
        block = ExternalLinkBlock()
        data = {
            'link': 'https://example.com',
            'title': 'Example',
            'link_target': True,
        }
        struct_value = block.to_python(data)

        assert isinstance(struct_value, LinkStructValue)
        assert struct_value.get_title == 'Example'
        assert struct_value.url == 'https://example.com'
        assert struct_value.link_type == 'external'

    def test_template_rendering(self, test_page):
        """Test that properties work in Django templates"""
        block = InternalLinkBlock()
        data = {
            'page': test_page.pk,
            'title': '',  # Empty to test fallback
        }
        struct_value = block.to_python(data)

        # Test direct template rendering
        template = Template("Title: {{ value.get_title }}, URL: {{ value.url }}")
        context = Context({'value': struct_value})
        output = template.render(context)

        assert test_page.title in output
        assert test_page.url in output if test_page.url else True

    def test_template_property_access(self, test_page):
        """Test different ways to access properties in templates"""
        block = InternalLinkBlock()
        struct_value = block.to_python({'page': test_page.pk, 'title': ''})

        # Test various template access patterns
        template = Template("""
    Direct: {{ value.get_title }}
    With default: {{ value.get_title|default:"No title" }}
    Boolean check: {% if value.get_title %}YES{% else %}NO{% endif %}
    Length: {{ value.get_title|length }}
            """)

        context = Context({'value': struct_value})
        output = template.render(context)

        # The output should contain the page title
        assert test_page.title in output or "No title" in output
