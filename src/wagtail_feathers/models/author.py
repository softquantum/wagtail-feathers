from django import forms
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel
from wagtail.models import Orderable


def get_default_author_type():
    """Get the first AuthorType instance, or None if none exist.
    
    This function is designed to be called lazily, not during model definition.
    """
    try:
        first_type = AuthorType.objects.first()
        return first_type.pk if first_type else None
    except Exception:
        # Handle case where database isn't ready yet
        return None


class AuthorType(models.Model):
    """Model representing a role that an author can have."""

    name = models.CharField(_("Name"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("description"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Author Type")
        verbose_name_plural = _("Author Types")
        ordering = ["name"]


class AuthorTypeWidget(forms.RadioSelect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        widget_html = super().render(name, value, attrs, renderer)
        add_url = reverse("wagtailsnippets_wagtail_feathers_authortype:add")
        add_button_text = _("Add an Author Type")
        full_widget = format_html(
            '<div class="author-type-chooser-widget">'
            '<div class="author-type-radio-options">{}</div>'
            '<div class="author-type-add-button">'
            '<a href="{}" target="_blank" class="button button-small button-secondary">{}</a>'
            "</div>"
            "</div>",
            widget_html,
            add_url,
            add_button_text,
        )
        return full_widget


class BaseContentAuthor(models.Model):
    """Abstract base model for content authors."""

    person = models.ForeignKey(
        "wagtail_feathers.Person",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Person"),
    )
    type = models.ForeignKey(
        "wagtail_feathers.AuthorType",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Type"),
        null=True,
        blank=True,
        help_text=_("Select the author's role or type")
    )

    panels = [
        FieldPanel("person"),
        FieldPanel(
            "type",
            widget=AuthorTypeWidget,
            help_text=_("You can add an Author type, e.g. 'Author' or 'Co-Author' (Optional)."),
        ),
    ]

    class Meta:
        abstract = True


class PageAuthor(Orderable, BaseContentAuthor):
    """Model for associating authors with pages."""

    page = ParentalKey(
        "wagtail_feathers.FeatherBasePage",
        on_delete=models.CASCADE,
        related_name="authors",
    )

    panels = BaseContentAuthor.panels
