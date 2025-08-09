from django import forms
from wagtail.admin.panels import FieldPanel, InlinePanel, PageChooserPanel
from wagtail.models import Page


class CurrentLocalePageChooserPanel(PageChooserPanel):
    """A custom PageChooserPanel that filters pages by the current locale."""

    def get_form_class(self):
        form_class = super().get_form_class()

        class LocaleFilteredForm(form_class):
            def __init__(self, *args, instance=None, parent_page=None, **kwargs):
                super().__init__(*args, instance=instance, **kwargs)

                current_locale = None
                if parent_page and hasattr(parent_page, "locale"):
                    current_locale = parent_page.locale
                elif instance and hasattr(instance, "page") and instance.page:
                    current_locale = getattr(instance.page, "locale", None)

                if current_locale and "linked_page" in self.fields:
                    self.fields["linked_page"].queryset = Page.objects.filter(locale=current_locale).live().public()

        return LocaleFilteredForm
