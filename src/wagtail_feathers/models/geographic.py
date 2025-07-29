from django.db import models
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel
from wagtail.models import Orderable


class PageCountry(Orderable):
    """Countries associated with a page."""

    page = ParentalKey("wagtailcore.Page", on_delete=models.CASCADE, related_name="countries")
    countries = CountryField(blank=True, default=list, verbose_name=_("Countries"))

    panels = [
        FieldPanel("countries"),
    ]

    def __str__(self):
        if self.countries:
            country_names = [str(country.name) for country in self.countries]
            return ", ".join(country_names)
        return _("No countries selected")

    class Meta:
        verbose_name = _("Page Countries")
        verbose_name_plural = _("Page Countries")
