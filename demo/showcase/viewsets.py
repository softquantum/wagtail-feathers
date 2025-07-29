from wagtail.admin.viewsets.pages import PageListingViewSet
from django.utils.translation import gettext_lazy as _
from .models import ArticlePage


class ArticlePageListingViewSet(PageListingViewSet):
    """Custom page listing for ArticlePages only."""
    model = ArticlePage
    menu_label = _("Articles")
    menu_icon = "doc-full"
    add_to_admin_menu = True
    menu_order = 200