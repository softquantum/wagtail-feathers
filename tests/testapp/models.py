from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.contrib.forms.models import AbstractFormField

from wagtail_feathers.models import FormBasePage, ItemPage, WebBasePage


class ArticlePage(ItemPage):
    template = "pages/article_page.html"


class StandardPage(WebBasePage):
    template = "pages/standard_page.html"


class ContactPage(FormBasePage):
    pass


class ContactFormField(AbstractFormField):
    page = ParentalKey(ContactPage, on_delete=models.CASCADE, related_name="form_fields")
