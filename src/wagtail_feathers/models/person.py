from django import forms
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalManyToManyField
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable
from wagtail.search import index
from wagtail.images import get_image_model_string


class PersonGroup(Orderable):
    """Assign a Group to a Person."""

    name = models.CharField("name", unique=True, max_length=254)

    panels = [FieldPanel("name")]

    def __str__(self):
        return "{}".format(self.name)

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        ordering = ["name"]


class Person(index.Indexed, ClusterableModel):
    """Model representing a Person with a profile, typically used for authoring content.

    The `display_name` field accommodates names with titles such as Dr., Mr., Eng, etc.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="person_profile",
        help_text="Link to a system user account, if this person is a registered user.",
    )
    first_name = models.CharField(_("First name"), max_length=254)
    last_name = models.CharField(_("Last name"), max_length=254)
    email = models.EmailField(
        _("email address"),
        unique=True,
        error_messages={
            "unique": _("A person with that email already exists."),
        },
        blank=True,
    )
    display_name = models.CharField(_("Display name"), max_length=254, blank=True)
    bio = RichTextField(blank=True)
    groups = ParentalManyToManyField("wagtail_feathers.PersonGroup", blank=True, help_text="Select all that apply")

    image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("first_name"),
                        FieldPanel("last_name"),
                    ]
                ),
                FieldPanel("display_name"),
            ],
            _("Name"),
        ),
        FieldPanel("bio"),
        FieldPanel("image"),
        FieldPanel("email"),
        FieldPanel("user"),
        FieldPanel("groups", widget=forms.CheckboxSelectMultiple),
    ]

    search_fields = [
        index.SearchField("first_name"),
        index.SearchField("last_name"),
        index.SearchField("bio"),
        index.AutocompleteField("first_name"),
        index.AutocompleteField("last_name"),
    ]

    @property
    def thumb_image(self):
        try:
            return self.image.get_rendition("fill-50x50").img_tag()
        except (AttributeError, ValueError, Exception):
            return ""

    @property
    def user_email(self):
        return self.user.email if self.user and hasattr(self.user, "email") else ""

    def __str__(self):
        return f"{self.display_name}" or f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("People")
