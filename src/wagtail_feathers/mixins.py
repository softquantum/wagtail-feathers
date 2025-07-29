from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from wagtail.admin.panels import FieldPanel


class TimestampMixin(models.Model):
    """Mixin to add timestamp fields to models."""

    created_at = models.DateTimeField(_("Created at"), default=timezone.now, editable=False)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        abstract = True
