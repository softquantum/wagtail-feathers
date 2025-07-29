import hashlib
import itertools
import logging
import os
from xml.dom import minidom

from django import template
from django.contrib.staticfiles.finders import find
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.cache import cache
from django.utils.safestring import mark_safe

from wagtail_feathers.helpers import get_svg_icons

logger = logging.getLogger(__name__)
register = template.Library()


def _make_cache_key(*parts):
    """Generate a memcached-compatible cache key from the given parts."""
    key_string = "_".join(str(part) for part in parts if part)
    return hashlib.md5(key_string.encode()).hexdigest()


@register.inclusion_tag("wagtail_feathers/templatetags/_svg_icon.html", takes_context=False)
def svg_icon(name=None, filename=None, classname=None, title=None, wrapped=False):
    """Abstracts away the actual icon implementation.

    Usage:
        {% load svg_tags %}
        ...
        {% icon name="cogs" classname="icon--red" title="Settings" wrapped=True %}
        {% icon filename="branding/logo.svg" classname="icon--red" title="Settings" wrapped=True %}

    :param name: the icon name/id, required unless filename is given (string)
    :param filename: the icon's path relative to static directory (string)
    :param classname: defaults to 'icon' if not provided (string)
    :param title: accessible label intended for screen readers (string)
    :param wrapped: wrap icon in a <span class="icon-wrapper"> element (boolean)
    :return: Rendered template snippet (string)
    """
    svg_content = None
    cache_key = None

    if not name and not filename:
        raise ValueError("Either 'name' or 'filename' parameter must be provided")

    if name:
        cache_key = _make_cache_key("svg_icon", name, classname)
        svg_content = cache.get(cache_key)
        if not svg_content:
            # Get all registered icons from Wagtail
            all_icons = get_svg_icons()
            if all_icons.get(name):
                svg_content = all_icons.get(name)

                if classname:
                    doc = minidom.parseString(svg_content)
                    svg = doc.getElementsByTagName("svg")[0]
                    svg.setAttribute("class", classname)
                    svg_content = svg.toxml()

    elif filename:
        # TODO: check if this is a real filepath
        filepath = filename

        # Try to get the SVG content from cache first
        cache_key = _make_cache_key("svg_icon", filepath, classname)
        svg_content = cache.get(cache_key)

        if not svg_content:
            # Try to get the path directly from storage
            try:
                absolute_path = staticfiles_storage.path(filepath)
            except NotImplementedError:
                # Some storage backends don't implement path()
                absolute_path = None

            # If direct path doesn't work, try to find the file
            if not absolute_path or not os.path.exists(absolute_path):
                try:
                    found_path = find(filepath)
                    # Handle case where find() returns a list
                    if isinstance(found_path, list):
                        if found_path:
                            absolute_path = found_path[0]
                        else:
                            raise FileNotFoundError(f"No matches found for {filepath}")
                    else:
                        absolute_path = found_path
                    
                    if not absolute_path:
                        raise FileNotFoundError(f"Could not find {filepath}")
                except (FileNotFoundError, TypeError) as e:
                    logger.error(f"Could not find SVG file: {filepath} - {e}")
                    return {
                        "name": name,
                        "svg_content": None,
                        "classname": classname,
                        "title": title,
                        "wrapped": wrapped,
                    }

            with open(absolute_path, "r") as file:
                svg_content = file.read()

            if classname:
                doc = minidom.parseString(svg_content)
                svg = doc.getElementsByTagName("svg")[0]
                svg.setAttribute("class", classname)
                svg_content = svg.toxml()

    if svg_content and cache_key:
        cache.set(cache_key, svg_content, 14400)

    return {
        "name": name,
        "svg_content": mark_safe(svg_content) if svg_content else None,
        "classname": classname,
        "title": title,
        "wrapped": wrapped,
    }
