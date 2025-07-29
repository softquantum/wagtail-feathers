"""
Custom form classes for Wagtail Feathers admin interface.
"""

from django import forms
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.contrib.forms.models import WagtailAdminFormPageForm


class TemplateVariantPageForm(WagtailAdminPageForm):
    """
    Custom admin form that provides dynamic template variant choices.
    
    This form automatically detects template variants for the page model
    and replaces the template_variant CharField with a ChoiceField containing
    the available variants.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Check if this model has template variant support
        model_class = self._meta.model
        if (hasattr(model_class, 'get_available_template_variants') and 
            'template_variant' in self.fields):
            
            # Get available variants for this model
            choices = [('', 'Default Template')]
            variants = model_class.get_available_template_variants()
            
            for variant in variants:
                # Convert variant name to human-readable format
                display_name = variant.replace('_', ' ').replace('-', ' ').title()
                choices.append((variant, display_name))
            
            # Only replace the field if we have variants
            if len(choices) > 1:
                # Get the original field to preserve its properties
                original_field = self.fields['template_variant']
                
                # Replace with a ChoiceField
                self.fields['template_variant'] = forms.ChoiceField(
                    choices=choices,
                    widget=forms.Select(choices=choices),
                    required=original_field.required,
                    label=original_field.label or 'Template Variant',
                    help_text=original_field.help_text or 'Select a template variant for this page.',
                    initial=original_field.initial
                )
                
# Form successfully configured with dynamic template variant choices


class TemplateVariantFormPageForm(WagtailAdminFormPageForm):
    """
    Custom admin form for form pages that provides dynamic template variant choices.
    
    This form extends WagtailAdminFormPageForm to maintain compatibility with 
    Wagtail's form builder functionality (AbstractEmailForm, FormMixin) while
    adding template variant support.
    
    Key features:
    - Inherits unique field name validation from WagtailAdminFormPageForm
    - Automatically detects template variants for the form page model
    - Replaces template_variant CharField with ChoiceField containing available variants
    - Maintains all form submission and email functionality
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply the same template variant logic as TemplateVariantPageForm
        model_class = self._meta.model
        if (hasattr(model_class, 'get_available_template_variants') and 
            'template_variant' in self.fields):
            
            # Get available variants for this model
            choices = [('', 'Default Template')]
            variants = model_class.get_available_template_variants()
            
            for variant in variants:
                # Convert variant name to human-readable format
                display_name = variant.replace('_', ' ').replace('-', ' ').title()
                choices.append((variant, display_name))
            
            # Only replace the field if we have variants
            if len(choices) > 1:
                # Get the original field to preserve its properties
                original_field = self.fields['template_variant']
                
                # Replace with a ChoiceField
                self.fields['template_variant'] = forms.ChoiceField(
                    choices=choices,
                    widget=forms.Select(choices=choices),
                    required=original_field.required,
                    label=original_field.label or 'Template Variant',
                    help_text=original_field.help_text or 'Select a template variant for this form page.',
                    initial=original_field.initial
                )
                
# Form successfully configured with dynamic template variant choices for form pages