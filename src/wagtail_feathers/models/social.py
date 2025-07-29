from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.models import Orderable, TranslatableMixin

try:
    from wagtail_localize.fields import TranslatableField
    WAGTAIL_LOCALIZE_AVAILABLE = True
except ImportError:
    WAGTAIL_LOCALIZE_AVAILABLE = False


class SocialMediaSettings(TranslatableMixin, ClusterableModel):
    """Translatable social media settings separate from SiteSettings."""

    name = models.CharField(
            max_length=100,
            default="Social Media",
            help_text=_("Name for this social media configuration")
    )

    site = models.ForeignKey(
            'wagtailcore.Site',
            on_delete=models.CASCADE,
            help_text=_("Site this social media configuration belongs to")
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("site"),
        InlinePanel("social_media_links", label=_("Social Media Links")),
    ]

    # No translatable fields on the container itself - just the links
    if WAGTAIL_LOCALIZE_AVAILABLE:
        translatable_fields = []

    def __str__(self):
        return f"{self.name} ({self.site})"

    class Meta:
        verbose_name = _("Social Media Settings")
        verbose_name_plural = _("Social Media Settings")
        constraints = [
            models.UniqueConstraint(
                    fields=["translation_key", "locale"],
                    name="unique_socialmediasettings_translation_key_locale"
            )
        ]


class SocialMediaLink(TranslatableMixin, Orderable):
    """Represents a translatable social media link."""

    setting = ParentalKey("SocialMediaSettings", on_delete=models.CASCADE, related_name="social_media_links")
    name = models.CharField(max_length=100, help_text=_("Name of the social media platform"))
    url = models.URLField(help_text=_("URL to your social media profile"))
    handle = models.CharField(
            max_length=100, blank=True, help_text=_("Optional handle or ID if a URL is not available")
    )
    icon = models.CharField(max_length=50, blank=True, help_text=_("Icon to use"))

    panels = [
        FieldPanel("name"),
        FieldPanel("url"),
        FieldPanel("handle"),
        FieldPanel("icon"),
    ]

    # Translation configuration - only available with wagtail-localize
    if WAGTAIL_LOCALIZE_AVAILABLE:
        translatable_fields = [
            TranslatableField('name'),
            TranslatableField('handle'),
        ]

    def __str__(self):
        return f"{self.name}: {self.url}"

    class Meta:
        verbose_name = _("Social Media Link")
        verbose_name_plural = _("Social Media Links")
        constraints = [
            models.UniqueConstraint(
                    fields=["translation_key", "locale"],
                    name="unique_socialmedialink_translation_key_locale"
            )
        ]