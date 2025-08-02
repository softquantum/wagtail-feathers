""" Add ids to headings (from h1 to h6).

    This matches an h1/.../h6, using a regexp that is only guaranteed to work because
    we know that the source of the HTML code we'll be working with generates nice
    and predictable HTML code (and note the non-greedy "one or more" for the heading content).

    Usage:
    Import this module in your def ready() of one of your apps.

    Alternative:
    Use the filtertag {% page.body | with_heading_ids %} from tocbot_tags templatetags

"""

import re
from django.utils.text import slugify
from wagtail.fields import StreamValue

__original__html__ = StreamValue.__html__
heading_re = r"<h([1-6])([^>]*)>(.+?)</h\1>"


def with_heading_ids(self):
    """We don't actually change how StreamValue.__html__ works, we just replace
    it with a function that does "whatever it already did", plus a
    substitution pass that adds fragment ids and their associated link
    elements to any headings that might be in the streamfield content.
    """
    used_ids = set()

    def add_id_attribute(match):
        """Add IDs to headings in HTML content for TOC generation."""
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

        return f"<h{n}{attributes}>{text_content}</h{n}>"

    html = __original__html__(self)
    return re.sub(heading_re, add_id_attribute, html)


# Rebind the StreamValue's html serialization function such that
# the output is still entirely functional as far as wagtail
# can tell, except with headings enriched with fragment ids.
StreamValue.__html__ = with_heading_ids
