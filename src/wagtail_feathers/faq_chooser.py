from wagtail.admin.viewsets.chooser import ChooserViewSet


class FAQChooserViewSet(ChooserViewSet):
    model = "wagtail_feathers.FAQ"
    icon = "help-circle"


faq_chooser_viewset = FAQChooserViewSet("faq_chooser")