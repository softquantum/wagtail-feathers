from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel
from wagtail.models import Orderable
from wagtail.documents import get_document_model_string


class RelatedLink(models.Model):
    """Abstract base model for related links."""

    title = models.CharField(max_length=255, blank=True)

    @property
    def url(self):
        raise NotImplementedError("Subclasses of RelatedLink must implement the url property or field.")

    @property
    def get_title(self):
        """Return the title based on what is available."""
        return self.title or (getattr(self.url, "title", None) or self.url if self.url else None) or _("External Link")

    panels = [FieldPanel("title", help_text="This title will be used instead of the object related title")]

    class Meta:
        abstract = True


class RelatedPage(Orderable, RelatedLink):
    """Model for related Pages."""

    page = ParentalKey("wagtailcore.Page", on_delete=models.CASCADE, related_name="page_related_pages")
    url = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Internal page",
    )

    panels = RelatedLink.panels + [
        FieldPanel("url"),
    ]
    # def get_panels(self):
    #     """Avoid circular import by using wagtail_feathers.panels."""
    #     from wagtail_feathers.panels import CurrentLocalePageChooserPanel
    #
    #     return RelatedLink.panels + [
    #         CurrentLocalePageChooserPanel("url", ["wagtailcore.Page"], help_text="Select a page"),
    #     ]


class RelatedDocument(Orderable, RelatedLink):
    """Model for related Documents."""

    page = ParentalKey("wagtailcore.Page", on_delete=models.CASCADE, related_name="related_documents")
    url = models.ForeignKey(
        get_document_model_string(),
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Document download",
    )
    panels = RelatedLink.panels + [
        FieldPanel("url"),
    ]


class RelatedExternalLink(Orderable, RelatedLink):
    """Model for related external links."""

    page = ParentalKey("wagtailcore.Page", on_delete=models.CASCADE, related_name="related_links")
    title = models.CharField(max_length=255, blank=False)
    url = models.URLField("url", blank=True)

    panels = RelatedLink.panels + [
        FieldPanel("url"),
    ]
