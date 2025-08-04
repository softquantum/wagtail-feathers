from wagtail.admin.viewsets.chooser import ChooserViewSet
from django.utils.translation import gettext_lazy as _
from django import forms
from wagtail.admin.forms.choosers import BaseFilterForm
from wagtail.admin.views.generic import chooser as chooser_views

from wagtail_feathers.models import ClassifierGroup


class ClassifierFilterForm(BaseFilterForm):
    """Form for filtering Classifier objects."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from wagtail_feathers.models import ClassifierGroup

        groups = ClassifierGroup.objects.all().order_by("type", "name")

        self.fields["group"].choices = [("", _("All groups"))] + [
            (str(group.pk), f"{group.name} ({group.type[0]})") for group in groups
        ]

    group_type = forms.ChoiceField(
        choices=[
            ("", _("All")),
            ("Subject", _("Subject")),
            ("Attribute", _("Attribute")),
        ],
        required=False,
        label=_("Group Type"),
        widget=forms.RadioSelect(
            attrs={
                "data-controller": "w-submit",
                "data-action": "change->w-submit#submit",
                "class": "classifier-type-radio-options",
            }
        ),
    )

    group = forms.ChoiceField(
        choices=[],
        required=False,
        label=_("Group Name"),
        widget=forms.Select(
            attrs={
                "data-controller": "w-submit",
                "data-action": "change->w-submit#submit",
            }
        ),
    )

    def filter(self, objects):
        """Filter the queryset based on the form data.

        Make sure you do not set in the chooser url_filter_parameters and
        preserve_url_parameters with 'group' and 'group_type'.
        """
        objects = super().filter(objects)
        
        group_type = self.cleaned_data.get("group_type")
        group = self.cleaned_data.get("group")

        if group_type:
            objects = objects.filter(group__type=group_type)

        if group:
            objects = objects.filter(group=group)

        return objects


class ClassifierChooseView(chooser_views.ChooseView):
    """Custom chooser view for choosing Classifier objects."""

    filter_form_class = ClassifierFilterForm


class ClassifierChooseResultsView(chooser_views.ChooseResultsView):
    """Custom results view for viewing Classifier objects."""

    filter_form_class = ClassifierFilterForm


class ClassifierChooserViewSet(ChooserViewSet):

    model = "wagtail_feathers.Classifier"
    
    choose_view_class = ClassifierChooseView
    choose_results_view_class = ClassifierChooseResultsView
    icon = "tag"
    choose_one_text = _("Choose a classifier")
    choose_another_text = _("Choose another")
    edit_item_text = _("Edit")
    ordering = ["group__type", "group__name", "name"]

    def get_common_view_kwargs(self, **kwargs):
        return super().get_common_view_kwargs(
            ordering=self.ordering,
            **kwargs
        )


classifier_chooser_viewset = ClassifierChooserViewSet("classifier_chooser")