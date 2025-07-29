from io import BytesIO

from django.contrib.staticfiles.finders import find
from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile
from django.db import models
from django.forms import Select
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.images import get_image_model, get_image_model_string
from willow.image import Image as WillowImage


class ThemeChoiceWidget(Select):
    """Custom widget that dynamically loads theme choices."""

    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs, choices)
        self.choices = self.get_theme_choices()

    def get_theme_choices(self):
        """Get available theme choices."""
        try:
            from wagtail_feathers.themes import theme_registry

            theme_registry.discover_themes(force_refresh=True)
            themes = theme_registry.get_all_themes()

            choices = [("", _("No theme (use default)"))]
            for name, theme in themes.items():
                if theme.is_valid:
                    choices.append((name, theme.display_name))
            return choices
        except Exception:
            # Fallback if themes can't be loaded
            return [("", _("No theme (use default)"))]


@register_setting(icon="site")
class SiteSettings(BaseSiteSetting):
    """Settings for the site."""

    title_suffix = models.CharField(
        verbose_name="Title suffix",
        max_length=255,
        help_text="The suffix for the title meta tag e.g. ' | Feathers Library'",
        default="Feathers Library",
    )

    placeholder_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Choose the image you wish to be displayed as a placeholder image.",
    )

    active_theme = models.CharField(
        verbose_name="Active theme",
        max_length=100,
        blank=True,
        default="",
        help_text="Select the active theme for this site",
    )

    words_per_minute = models.PositiveIntegerField(
        verbose_name="Words per minute",
        default=200,
        help_text="Average reading speed for reading time calculation. Default: 200 WPM (average adult reading speed)",
    )

    panels = [
        FieldPanel("title_suffix"),
        FieldPanel("active_theme", widget=ThemeChoiceWidget),
        FieldPanel("words_per_minute"),
        FieldPanel("placeholder_image"),
    ]

    def _set_default_placeholder_image(self):
        """Ensure placeholder image exists and is set."""
        if self.placeholder_image:
            return

        absolute_path = find("images/placeholder-image.webp")
        if not absolute_path:
            raise ValidationError("Placeholder image file not found in static files.")

        try:
            from django.db import transaction

            with transaction.atomic():
                with open(absolute_path, "rb") as f:
                    image_bytes = f.read()

                img_file = ImageFile(BytesIO(image_bytes), name="placeholder-image.webp")
                im = WillowImage.open(img_file)
                width, height = im.get_size()

                ImageModel = get_image_model()
                new_default_image = ImageModel(title="Placeholder Image", file=img_file, width=width, height=height)
                new_default_image.save()
                new_default_image.tags.add("placeholder")

                self.placeholder_image = new_default_image
        except Exception as e:
            raise ValidationError(f"Failed to create placeholder image: {str(e)}") from e

    def get_placeholder_image(self):
        """Get the placeholder image."""
        self._set_default_placeholder_image()
        return self.placeholder_image

    def clean(self):
        """Validate the selected theme."""
        super().clean()
        if self.active_theme and self.active_theme != "":
            try:
                from wagtail_feathers.themes import theme_registry

                if not theme_registry.theme_exists(self.active_theme):
                    raise ValidationError(
                        {
                            "active_theme": _('The selected theme "{}" does not exist or is not valid.').format(
                                self.active_theme
                            )
                        }
                    )
            except Exception as e:
                raise ValidationError({"active_theme": _("Error validating theme: {}").format(str(e))})

    def save(self, *args, **kwargs):
        """Save the settings and clear theme caches."""
        old_active_theme = None
        if self.pk:
            try:
                old_active_theme = SiteSettings.objects.get(pk=self.pk).active_theme
            except SiteSettings.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if old_active_theme != self.active_theme:
            try:
                from wagtail_feathers.themes import theme_registry
                theme_registry._clear_theme_caches()
            except Exception:
                pass
