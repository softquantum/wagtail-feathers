"""Regression tests for FeatherPage.related_pages.

Locks in the contract that `page.related_pages` returns the *target* pages
curated by editors via the `page_related_pages` InlinePanel, in the editor-
specified order — not the owning page itself.
"""

import pytest
from wagtail.models import Page

from wagtail_feathers.models import RelatedPage


@pytest.fixture
def root(db):
    return Page.objects.get(depth=1)


@pytest.fixture
def pages(root):
    """A small tree: owner + 3 candidate target pages."""
    owner = Page(title="Owner", slug="owner")
    root.add_child(instance=owner)

    target_a = Page(title="Target A", slug="target-a")
    root.add_child(instance=target_a)
    target_b = Page(title="Target B", slug="target-b")
    root.add_child(instance=target_b)
    target_c = Page(title="Target C", slug="target-c")
    root.add_child(instance=target_c)

    for p in (owner, target_a, target_b, target_c):
        p.save_revision().publish()

    return owner, target_a, target_b, target_c


def _related_pages(owner):
    """Invoke the production `FeatherPage.related_pages` cached_property
    body against any Page-like instance.

    `FeatherPage` is abstract so we can't instantiate it; instead we pull
    the underlying function out of the cached_property descriptor and call
    it bound to a vanilla `wagtailcore.Page`. This exercises the exact
    line at `base.py:274` (the `item.url_id` we just fixed), so the test
    fails immediately if the bug is reintroduced.
    """
    from wagtail_feathers.models.base import FeatherPage

    fn = FeatherPage.related_pages.func  # cached_property → underlying callable
    return fn(owner)


def test_related_pages_returns_targets_not_owner(pages):
    owner, a, b, c = pages
    RelatedPage.objects.create(page=owner, url=a)
    RelatedPage.objects.create(page=owner, url=b)

    result = list(_related_pages(owner))

    assert owner not in result, (
        "Owner page leaked into result — regression of the page_id/url_id bug "
        "(the cached_property used to read item.page_id, which returns the "
        "owner pk, instead of item.url_id which returns the target pk)."
    )
    assert {p.pk for p in result} == {a.pk, b.pk}


def test_related_pages_preserves_editor_order(pages):
    owner, a, b, c = pages
    # Editor inserts in C, A, B order — sort_order on Orderable encodes intent.
    RelatedPage.objects.create(page=owner, url=c, sort_order=0)
    RelatedPage.objects.create(page=owner, url=a, sort_order=1)
    RelatedPage.objects.create(page=owner, url=b, sort_order=2)

    result = list(_related_pages(owner))

    assert [p.pk for p in result] == [c.pk, a.pk, b.pk]


def test_related_pages_empty_when_no_relations(pages):
    owner, *_ = pages
    assert list(_related_pages(owner)) == []


def test_related_pages_excludes_unpublished_targets(pages):
    owner, a, b, _c = pages
    b.unpublish()
    RelatedPage.objects.create(page=owner, url=a)
    RelatedPage.objects.create(page=owner, url=b)

    result = list(_related_pages(owner))

    assert [p.pk for p in result] == [a.pk]


def test_related_pages_url_id_attname_matches_field(db):
    """Sanity check that Django's auto-generated `url_id` is the correct
    accessor for the FK column. If wagtail_feathers ever renames `url`,
    this test pins the contract that the property's expression must match."""
    field = RelatedPage._meta.get_field("url")
    assert field.attname == "url_id"
    page_field = RelatedPage._meta.get_field("page")
    assert page_field.attname == "page_id"
    assert field.attname != page_field.attname, (
        "page and url FKs must have distinct attnames — the bug existed because "
        "they were both Page FKs and the wrong attname was used."
    )