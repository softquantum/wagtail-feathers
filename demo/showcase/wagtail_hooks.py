from wagtail import hooks
from .viewsets import ArticlePageListingViewSet


@hooks.register("register_admin_viewset")
def register_article_viewset():
    return ArticlePageListingViewSet("articles")