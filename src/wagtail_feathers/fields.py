"""
Custom form fields for Wagtail Feathers.
"""

from django import forms
from .widgets import TemplateVariantWidget


class TemplateVariantField(forms.ChoiceField):
    """
    A choice field that dynamically populates template variant choices.
    """
    
    def __init__(self, page_class=None, *args, **kwargs):
        # Don't pass choices to parent __init__ yet
        self.page_class = page_class
        kwargs['widget'] = TemplateVariantWidget(page_class=page_class)
        kwargs['choices'] = []  # Will be populated later
        kwargs['required'] = kwargs.get('required', False)
        super().__init__(*args, **kwargs)
        
    def _get_choices(self):
        """Dynamically get choices from widget."""
        if hasattr(self.widget, 'get_choices'):
            return self.widget.get_choices()
        return [('', 'Default Template')]
    
    def _set_choices(self, value):
        """Allow choices to be set but prefer dynamic choices."""
        self._choices = value
        
    choices = property(_get_choices, _set_choices)
    
    def widget_attrs(self, widget):
        """Pass page_class to widget if available."""
        attrs = super().widget_attrs(widget)
        if self.page_class and hasattr(widget, 'page_class'):
            widget.page_class = self.page_class
        return attrs