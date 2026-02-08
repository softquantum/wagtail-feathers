from wagtail.snippets.views.snippets import SnippetViewSet

from wagtail_feathers.models import FAQ, FAQItem


class FAQViewSet(SnippetViewSet):
    """Admin viewset for managing FAQ Categories."""
    
    model = FAQ
    menu_icon = "help-circle"
    menu_label = "FAQs"
    # list_display = ["name", "slug"]
    search_fields = ["name", "description"]


class FAQItemViewSet(SnippetViewSet):
    """Admin viewset for managing individual FAQ items."""
    
    model = FAQItem
    menu_icon = "help"
    menu_label = "FAQ Items"
    # list_display = ["question", "category", "live"]
    list_filter = ["category", "live"]
    search_fields = ["question", "answer"]