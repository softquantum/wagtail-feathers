import re

from django import template
from django.utils.safestring import mark_safe
from django.utils.text import slugify

register = template.Library()


@register.filter
def with_heading_ids(value):
    """Add IDs to headings in HTML content for TOC generation."""
    if not value:
        return value

    heading_re = r"<h([1-6])([^>]*)>(.+?)</h\1>"
    used_ids = set()

    def add_id_attribute(match):
        n = match.group(1)
        attributes = match.group(2)
        text_content = match.group(3)

        if not re.search(r'id=["\'][^"\']+["\']', attributes):
            base_id = slugify(text_content)
            id_attr = base_id
            counter = 2
            while id_attr in used_ids:
                id_attr = f"{base_id}-{counter}"
                counter += 1
            used_ids.add(id_attr)
            attributes += f' id="{id_attr}"'

        return f'<h{n}{attributes}>{text_content}</h{n}>'

    result = re.sub(heading_re, add_id_attribute, str(value))
    return mark_safe(result)
