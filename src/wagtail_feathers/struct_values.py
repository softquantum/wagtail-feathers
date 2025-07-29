from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _
from wagtail import blocks


class LinkStructValue(blocks.StructValue):
    """Custom class that extends the default StructValue class.

    It extends Wagtail's StructValue to provide convenient methods for handling different
    types of links: internal pages, documents, and external links.
    """

    @property
    def url(self) -> str:
        if link := self.get("link"):
            return link

        if page := self.get("page"):
            return page.url

        if document := self.get("document"):
            return document.url

        return ""

    @property
    def get_title(self) -> str:
        """Returns the title of the link.

        If the title is provided, it will be returned.
        If not, the title of the linked page or document will be returned or the link URL.
        If neither is available, a default title "Read more" will be returned.
        """
        if title := self.get("title"):
            return title

        if page := self.get("page"):
            page = page.specific
            return page.title

        if document := self.get("document"):
            return document.title

        if link := self.get("link"):
            return link

        return _("Read more")

    @property
    def link_type(self) -> str:
        if self.get("page"):
            return "internal"
        if self.get("document"):
            return "document"
        return "external"

    @property
    def file_size(self) -> str:
        if document := self.get("document"):
            return filesizeformat(document.file.size)
        return ""

    @property
    def extension_type(self) -> str:
        if document := self.get("document"):
            return document.file_extension.upper()
        return ""
