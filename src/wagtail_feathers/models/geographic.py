from django.db import models
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel
from wagtail.models import Orderable


class CountryGroup(models.Model):
    """User-defined groups of countries for easy selection."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("Name for this country group (e.g., 'ACP Countries', 'EU Countries', 'West Africa')")
    )
    description = models.TextField(
        blank=True,
        help_text=_("Optional description of this country group")
    )
    countries = CountryField(
        multiple=True,
        blank=True,
        help_text=_("Select countries that belong to this group")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this group is available for selection")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        FieldPanel("name"),
        FieldPanel("description"),
        FieldPanel("countries", widget=CheckboxSelectMultiple),
        FieldPanel("is_active"),
    ]
    
    class Meta:
        verbose_name = _("Country Group")
        verbose_name_plural = _("Country Groups")
        ordering = ["name"]
    
    def __str__(self):
        return self.name
    
    def get_country_codes(self):
        """Return list of country codes in this group."""
        return [str(country) for country in self.countries]
    
    def get_country_names(self):
        """Return list of country names in this group."""
        return [country.name for country in self.countries]
    
    def country_count(self):
        """Return number of countries in this group."""
        return len(self.countries)


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
