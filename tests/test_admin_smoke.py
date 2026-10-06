import pytest
from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.urls import reverse
from wagtail.models import Locale, Page, Site
from wagtail.models import get_page_models as wagtail_get_page_models
from wagtail.snippets.models import get_snippet_models

from tests.testapp.models import ArticlePage, ContactPage, StandardPage
from wagtail_feathers.models import Category, ErrorPage, FeatherBasePage, get_page_models
from wagtail_feathers.models.utils import check_default_page_model


@pytest.fixture
def root_page(db):
    Locale.objects.get_or_create(language_code="en")
    root = Page.get_first_root_node() or Page.add_root(title="Root", slug="root")
    Site.objects.get_or_create(
        is_default_site=True,
        defaults={"hostname": "localhost", "root_page": root, "site_name": "Test"},
    )
    return root


@pytest.fixture
def admin_user_client(root_page, client, django_user_model):
    user = django_user_model.objects.create_superuser("admin", "admin@example.com", "password")
    client.force_login(user)
    return client


class TestAdminSmoke:
    def test_admin_home(self, admin_user_client):
        response = admin_user_client.get(reverse("wagtailadmin_home"))
        assert response.status_code == 200

    def test_category_listing_buttons(self, admin_user_client):
        Category.get_or_create_hidden_root()
        category = Category.add_root_category("Technology", slug="technology")

        response = admin_user_client.get(reverse("wagtailsnippets_wagtail_feathers_category:list"))

        assert response.status_code == 200
        content = response.content.decode()
        assert reverse("wagtailsnippets_wagtail_feathers_category:add_child", args=[category.pk]) in content
        assert reverse("wagtailsnippets_wagtail_feathers_category:move", args=[category.pk]) in content

    @pytest.mark.parametrize("model", get_snippet_models(), ids=lambda m: m._meta.label)
    def test_snippet_listings(self, admin_user_client, model):
        response = admin_user_client.get(reverse(model.snippet_viewset.get_url_name("list")))

        assert response.status_code == 200

    def test_classifier_group_listing_has_type_filter(self, admin_user_client):
        from wagtail_feathers.models import ClassifierGroup

        response = admin_user_client.get(reverse(ClassifierGroup.snippet_viewset.get_url_name("list")))

        assert response.status_code == 200
        assert 'name="type"' in response.content.decode()

    def test_classifier_chooser(self, admin_user_client):
        response = admin_user_client.get(reverse("classifier_chooser:choose"))

        assert response.status_code == 200
        assert reverse("classifier_chooser:filter_groups") in response.json()["html"]

    def test_classifier_chooser_filter_groups(self, admin_user_client):
        response = admin_user_client.get(reverse("classifier_chooser:filter_groups"))

        assert response.status_code == 200
        assert response.json()[0]["id"] == ""

    @pytest.mark.parametrize("model", [ArticlePage, StandardPage, ContactPage, ErrorPage])
    def test_page_add_view(self, admin_user_client, root_page, model):
        url = reverse(
            "wagtailadmin_pages:add",
            args=[model._meta.app_label, model._meta.model_name, root_page.pk],
        )
        response = admin_user_client.get(url)
        assert response.status_code == 200

    @pytest.mark.parametrize("model", [ArticlePage, StandardPage, ContactPage])
    def test_page_edit_view(self, admin_user_client, root_page, model):
        page = root_page.add_child(instance=model(title="A page", slug="a-page"))

        response = admin_user_client.get(reverse("wagtailadmin_pages:edit", args=[page.pk]))

        assert response.status_code == 200

    def test_error_page_edit_view(self, admin_user_client, root_page):
        page = root_page.add_child(instance=ErrorPage(error_code="404"))

        response = admin_user_client.get(reverse("wagtailadmin_pages:edit", args=[page.pk]))

        assert response.status_code == 200


class TestPageModelClasses:
    def test_system_checks_pass(self, db):
        errors = [e for e in checks.run_checks() if e.level >= checks.ERROR]
        assert errors == []

    def test_page_models_registered_with_wagtail(self):
        registered = wagtail_get_page_models()
        for model in (FeatherBasePage, ErrorPage, ArticlePage, StandardPage, ContactPage):
            assert model in registered

    def test_creatable_flags(self):
        assert FeatherBasePage.is_creatable is False
        assert ArticlePage.is_creatable is True
        assert StandardPage.is_creatable is True

    def test_feather_page_models_registry(self):
        registered = get_page_models()
        assert ArticlePage in registered
        assert StandardPage in registered
        assert FeatherBasePage not in registered

    def test_edit_handler_tabs(self):
        handler = ArticlePage.get_edit_handler()
        headings = [str(child.heading) for child in handler.children]
        assert headings[0] == "Content"
        assert "Taxonomy" in headings
        assert "Promote" in headings
        assert headings[-1] == "Settings"

    def test_item_page_manager(self, root_page):
        root_page.add_child(instance=ArticlePage(title="Article", slug="article"))

        article = ArticlePage.objects.get(slug="article")

        assert article.specific_class is ArticlePage
        assert Page.objects.get(pk=article.pk).specific == article


class TestDefaultPageModelGuard:
    def test_default_setting(self):
        check_default_page_model()

    @override_settings(WAGTAIL_PAGE_MODEL="wagtailcore.page")
    def test_explicit_default(self):
        check_default_page_model()

    @override_settings(WAGTAIL_PAGE_MODEL="basepage.BasePage")
    def test_custom_page_model(self):
        with pytest.raises(ImproperlyConfigured, match="WAGTAIL_PAGE_MODEL"):
            check_default_page_model()
