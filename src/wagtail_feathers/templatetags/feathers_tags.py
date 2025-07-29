import re

from bs4 import BeautifulSoup
from django import template

register = template.Library()


@register.filter
def unwrap_p_regex(value):
    """Remove opening <p> and closing </p> tags from richtext fields, leave inner HTML intact.

    Usage:
    {{ page.yourfield|richtext|unwrap_p|safe }}

    """
    return re.sub(
            r'^\s*<p[^>]*>(.*?)</p>\s*$',
            r'\1',
            value,
            flags=re.DOTALL | re.IGNORECASE
    )


@register.filter
def unwrap_p(value):
    """Remove only the outermost <p> tag

    Usage:
    {{ page.yourfield|richtext|unwrap_p|safe }}

    """
    soup = BeautifulSoup(value, "html.parser")
    if (
        len(soup.contents) == 1
        and getattr(soup.contents[0], "name", None) == "p"
    ):
        return soup.contents[0].decode_contents()
    return value


@register.filter
def placeholder_from_help(field):
    """
    Set the placeholder attribute from the field's help_text.

    Usage:
        {{ field|placeholder_from_help }}

    This allows themers to choose whether to use help_text as placeholders
    by applying this filter in templates.
    """
    if hasattr(field.field, 'help_text') and field.field.help_text:
        field.field.widget.attrs['placeholder'] = field.field.help_text
    return field


@register.filter
def placeholder(field, text):
    """
    Set a custom placeholder text for a field.

    Usage:
        {{ field|placeholder:"Enter your name" }}
    """
    field.field.widget.attrs['placeholder'] = text
    return field