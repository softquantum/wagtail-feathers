from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.images import get_image_model_string
from wagtail.models import Page

from wagtail_feathers.models import CustomWagtailPage

"""
Error Page
===========
"""

class ErrorPage(CustomWagtailPage):
    """A custom error page that can be edited in the admin."""

    subpage_types = []

    error_code = models.CharField(
            max_length=3,
            choices=[
                ("400", _("400 - Bad Request")),
                ("403", _("403 - Permission Denied")),
                ("404", _("404 - Page Not Found")),
                ("500", _("500 - Internal Server Error")),
            ],
            unique=True,
    )

    show_in_menus = False

    image = models.ForeignKey(
            get_image_model_string(),
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name="+",
    )

    heading = models.CharField(
            max_length=255,
            default=_("Oops! Something went wrong")
    )

    message = RichTextField(
            help_text=_("Custom message to display on the error page"),
            blank=True,
    )

    content_panels = Page.content_panels[1:] + [
        FieldPanel("title", read_only=True, help_text=_("The error code will be used as the page title.")),
        FieldPanel("error_code"),
        FieldPanel("heading"),
        FieldPanel("image"),
        FieldPanel("message"),
    ]

    promote_panels = []


    class Meta:
        verbose_name = "Error Page"
        verbose_name_plural = "Error Pages"

    @classmethod
    def get_error_page(cls, error_code):
        try:
            return cls.objects.filter(error_code=error_code, live=True).first()
        except cls.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.error_code} Error Page"

    def save(self, *args, **kwargs):
        self.title = self.error_code
        self.slug = f"error-{self.error_code}"
        super().save(*args, **kwargs)



