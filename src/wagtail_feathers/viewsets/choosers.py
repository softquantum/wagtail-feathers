from wagtail.admin.viewsets.chooser import ChooserViewSet
from django.utils.translation import gettext_lazy as _
from django import forms
from django.http import JsonResponse
from django.urls import path
from wagtail.admin.forms.choosers import BaseFilterForm, SearchFilterMixin, LocaleFilterMixin, CollectionFilterMixin
from wagtail.admin.views.generic.chooser import (
    ChooseViewMixin,
    CreationFormMixin,
    ChooseResultsViewMixin,
    BaseChooseView
)
from wagtail.models import CollectionMember, Locale
from wagtail.search.index import class_is_indexed

from wagtail_feathers.models import ClassifierGroup


class ClassifierFilterMixin(forms.Form):
    """Mixin for filtering Classifier objects by group type and group."""

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
                "data-chooser-modal-search-filter": True,
                "class": "classifier-type-radio-options",
                "data-classifier-chooser-target": "groupType",
                "data-action": "change->classifier-chooser#groupTypeChanged",
            }
        ),
    )

    group = forms.ChoiceField(
        choices=[],
        required=False,
        label=_("Group Name"),
        widget=forms.Select(
            attrs={
                "data-chooser-modal-search-filter": True,
                "data-classifier-chooser-target": "groupSelect",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        groups = ClassifierGroup.objects.all().order_by("type", "name")

        self.fields["group"].choices = [("", _("All groups"))] + [
            (str(group.pk), f"{group.name} ({group.type[0]})") for group in groups
        ]

    def filter(self, objects):
        """Filter the results based on classifiers."""
        objects = super().filter(objects)
        group_type = self.cleaned_data.get("group_type")
        group = self.cleaned_data.get("group")

        if group_type:
            objects = objects.filter(group__type=group_type)

        if group:
            objects = objects.filter(group=group)

        return objects


class ClassifierBaseChooseView(BaseChooseView):
    """Custom chooser view for choosing Classifier objects."""

    template_name = "wagtail_feathers/admin/generic/chooser/classifier_chooser.html"

    def get_filter_form_class(self):
        if self.filter_form_class:
            return self.filter_form_class
        else:
            bases = [ClassifierFilterMixin, BaseFilterForm]

            if self.model_class:
                if class_is_indexed(self.model_class):
                    bases.insert(0, SearchFilterMixin)
                if issubclass(self.model_class, CollectionMember):
                    bases.insert(0, CollectionFilterMixin)

                if self.i18n_enabled:
                    bases.insert(0, LocaleFilterMixin)

            return type(
                "FilterForm",
                tuple(bases),
                {},
            )


class ClassifierChooseView(ChooseViewMixin, CreationFormMixin, ClassifierBaseChooseView):
    pass


class ClassifierChooseResultsView(ChooseResultsViewMixin, CreationFormMixin, ClassifierBaseChooseView):
    pass


class ClassifierChooserViewSet(ChooserViewSet):

    model = "wagtail_feathers.Classifier"
    choose_view_class = ClassifierChooseView
    choose_results_view_class = ClassifierChooseResultsView
    preserve_url_parameters = ["multiple", "group_type", "group", "locale"]
    icon = "tag"
    per_page = 10
    ordering = ["group__type", "group__name", "name"]

    def get_common_view_kwargs(self, **kwargs):
        return super().get_common_view_kwargs(
            ordering=self.ordering,
            **kwargs
        )

    def filter_groups(self, request):
        """AJAX endpoint to get filtered group choices based on group_type and locale."""
        group_type = request.GET.get('group_type', '')
        locale = request.GET.get('locale', '')
        
        # Start with all groups
        groups = ClassifierGroup.objects.all()
        
        # Filter by group_type if specified
        if group_type:
            groups = groups.filter(type=group_type)
        
        # Filter by locale if specified
        if locale:
            groups = groups.filter(locale__language_code=locale)
        
        # Order the results
        groups = groups.order_by('type', 'name')
        
        choices = [{'id': '', 'name': str(_('All groups'))}]
        choices.extend([
            {'id': str(group.pk), 'name': f"{group.name} ({group.type[0]})"}
            for group in groups
        ])
        
        return JsonResponse(choices, safe=False)

    def get_urlpatterns(self):
        urlpatterns = super().get_urlpatterns()
        urlpatterns += [
            path('filter_groups/', self.filter_groups, name='filter_groups'),
        ]
        return urlpatterns


classifier_chooser_viewset = ClassifierChooserViewSet("classifier_chooser")
