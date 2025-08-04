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


class EnhancedClassifierInlinePanel(InlinePanel):
    """Enhanced InlinePanel for classifiers with Stimulus-based UI improvements."""
    
    class BoundPanel(InlinePanel.BoundPanel):
        template_name = "wagtail_feathers/admin/panels/enhanced_classifier_inline_panel.html"
        
        def get_context_data(self, parent_context):
            context = super().get_context_data(parent_context)
            
            # Add classifier data for enhanced UI
            if self.panel.relation_name == 'classifiers':
                # Custom ordering to show Subject before Attribute
                from django.db.models import Case, IntegerField, When

                from wagtail_feathers.models.taxonomy import Classifier, ClassifierGroup
                
                context.update({
                    'all_classifiers': Classifier.objects.select_related('group').order_by('group__type', 'group__name', 'sort_order'),
                    'classifier_groups': ClassifierGroup.objects.prefetch_related('classifiers').annotate(
                        type_order=Case(
                            When(type='Subject', then=0),
                            When(type='Attribute', then=1),
                            default=2,
                            output_field=IntegerField()
                        )
                    ).order_by('type_order', 'name'),
                    'is_classifier_panel': True,
                })
            
            return context
    
    def __init__(self, relation_name, **kwargs):
        # Only apply enhancements to classifier relations
        if relation_name == 'classifiers':
            kwargs.setdefault('label', 'Classifiers')
            kwargs.setdefault('help_text', 'Select classifiers to categorize this content. Use the search and grouping features for easier selection.')
        
        super().__init__(relation_name, **kwargs)
