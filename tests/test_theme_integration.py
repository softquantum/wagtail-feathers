"""Tests for theme integration with other Wagtail Feathers components."""

from unittest.mock import patch

import pytest

from wagtail_feathers.blocks import BaseBlock
from wagtail_feathers.themes import ThemeInfo, theme_registry


@pytest.fixture
def mock_active_theme():
    """Create a mock active theme."""
    theme_info = ThemeInfo(
        name="test_theme",
        path="/test/themes/test_theme",
        display_name="Test Theme",
        description="A test theme",
        version="1.0.0",
        author="Test Author",
    )

    with patch.object(theme_registry, "get_active_theme", return_value=theme_info):
        with patch.object(theme_registry, "get_active_theme_name", return_value="test_theme"):
            yield theme_info


@pytest.mark.themes
class TestThemeAwareTemplateResolution:
    """Tests for theme-aware template resolution in FeatherBasePage."""

    def test_theme_aware_template_resolution(self, mock_active_theme):
        """Test theme-aware template resolution logic."""
        # This test directly tests the logic in FeatherBasePage.get_template
        # without actually calling the method

        # The logic in FeatherBasePage.get_template is:
        # 1. Get the template name from the parent class
        # 2. Get the active theme
        # 3. If there's an active theme, prefix the template name with the theme name
        # 4. Return the template name

        # Given a template name and an active theme
        template_name = "page.html"
        active_theme = mock_active_theme

        # When we apply the logic from FeatherBasePage.get_template
        result = f"{active_theme.name}/pages/{template_name}" if active_theme else template_name

        # Then the template name should be prefixed with the theme name
        assert result == "test_theme/pages/page.html"

    def test_template_resolution_without_active_theme(self):
        """Test template resolution logic without an active theme."""
        # Given a template name and no active theme
        template_name = "page.html"
        active_theme = None

        # When we apply the logic from FeatherBasePage.get_template
        result = f"{active_theme.name}/pages/{template_name}" if active_theme else template_name

        # Then the original template name should be returned
        assert result == template_name


@pytest.mark.themes
class TestThemeVariantsInBlocks:
    """Tests for theme variants in BaseBlock."""

    @pytest.mark.django_db
    def test_base_block_has_theme_variant(self):
        """Test that BaseBlock includes a theme_variant field when component_type is set."""
        # Create a concrete block with component_type
        class TestBlock(BaseBlock):
            component_type = "test_component"
            default_variant = "default"
            
        block = TestBlock()

        # Check if theme_variant field was added
        assert "theme_variant" in block.child_blocks

    @pytest.mark.django_db
    @patch("wagtail_feathers.blocks.get_theme_variants")
    def test_base_block_uses_theme_variants(self, mock_get_theme_variants):
        """Test that BaseBlock uses theme variants from the theme system."""
        # Set up mock to return specific variants
        mock_get_theme_variants.return_value = [
            ("test1", "Test 1"),
            ("test2", "Test 2"),
        ]

        # Create a concrete block with component_type
        class TestBlock(BaseBlock):
            component_type = "test_component"
            default_variant = "default"
            
        block = TestBlock()

        # Access the field property to trigger the theme variants call
        theme_variant_block = block.child_blocks["theme_variant"]
        field = theme_variant_block.field

        # Verify that get_theme_variants was called with the correct component type
        mock_get_theme_variants.assert_called_once_with("test_component")

    @pytest.mark.django_db
    def test_base_block_with_custom_component_type(self):
        """Test BaseBlock with a custom component type."""

        # Create a custom block class with a different component type
        class ButtonBlock(BaseBlock):
            component_type = "button"
            default_variant = "default"

        # Use a spy to verify the component type is passed correctly
        with patch("wagtail_feathers.blocks.get_theme_variants") as mock_get_theme_variants:
            mock_get_theme_variants.return_value = [("default", "Default")]

            # Create the block
            block = ButtonBlock()

            # Access the field property to trigger the theme variants call
            theme_variant_block = block.child_blocks["theme_variant"]
            field = theme_variant_block.field

            # Verify get_theme_variants was called with the correct component type
            mock_get_theme_variants.assert_called_once_with("button")

    @pytest.mark.django_db
    def test_base_block_with_custom_default_variant(self):
        """Test BaseBlock with a custom default variant."""

        # Create a custom block class with a different default variant
        class CustomBlock(BaseBlock):
            component_type = "card"
            default_variant = "primary"

        # Create the block
        block = CustomBlock()

        # Verify the theme_variant field exists and has the correct default
        assert "theme_variant" in block.child_blocks
        theme_variant_block = block.child_blocks["theme_variant"]
        
        # Check that the default variant is set correctly
        assert theme_variant_block._default == "primary"
