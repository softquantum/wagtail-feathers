import pytest
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import override_settings
from wagtail.models import Page

from wagtail_feathers.models.taxonomy import (
    Category,
    CategoryCache,
    CategoryQuerySet,
    Classifier,
    ClassifierGroup,
    ClassifierQuerySet,
    PageCategory,
    PageClassifier,
    TaxonomyConstants,
    TaxonomyError,
    TreeIntegrityError,
)


@pytest.fixture
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def root_category(db):
    """Get or create the hidden root category."""
    return Category.get_or_create_hidden_root()


@pytest.fixture
def sample_category(root_category):
    """Create a sample category for testing."""
    return Category.add_root_category("Technology", slug="technology", icon="test-icon")


@pytest.fixture
def category_hierarchy(root_category):
    """Create a category hierarchy for testing."""
    parent = Category.add_root_category("Parent Category", live=True)
    child = parent.add_child_category("Child Category", live=True)
    grandchild = child.add_child_category("Grandchild Category", live=True)
    inactive_child = parent.add_child_category("Inactive Child", live=False)
    
    return {
        'parent': parent,
        'child': child,
        'grandchild': grandchild,
        'inactive_child': inactive_child
    }


@pytest.fixture
def classifier_groups(db):
    """Create classifier groups for testing."""
    subject_group = ClassifierGroup.objects.create(type="Subject", name="Technology")
    attribute_group = ClassifierGroup.objects.create(type="Attribute", name="Content Type")
    return {
        'subject': subject_group,
        'attribute': attribute_group
    }


@pytest.fixture
def classifiers(classifier_groups):
    """Create classifiers for testing."""
    ai_classifier = Classifier.objects.create(
        group=classifier_groups['subject'], 
        name="Artificial Intelligence"
    )
    ml_classifier = Classifier.objects.create(
        group=classifier_groups['subject'], 
        name="Machine Learning"
    )
    article_classifier = Classifier.objects.create(
        group=classifier_groups['attribute'], 
        name="Article"
    )
    
    return {
        'ai': ai_classifier,
        'ml': ml_classifier,
        'article': article_classifier
    }


@pytest.fixture(scope="session")
def test_page(django_db_blocker):
    """Create a test page."""
    from wagtail.models import Site, Locale
    
    with django_db_blocker.unblock():
        # Create default locale if it doesn't exist
        locale, created = Locale.objects.get_or_create(
            language_code='en',
            defaults={'language_code': 'en'}
        )
        
        # Get or create root page
        root_page = Page.objects.filter(depth=1).first()
        if not root_page:
            root_page = Page.add_root(instance=Page(title="Root", slug="root", locale=locale))
        
        # Check if home page already exists
        home_page = root_page.get_children().filter(slug="home").first()
        if not home_page:
            home_page = root_page.add_child(instance=Page(title="Home", slug="home", locale=locale))
        
        # Create or update the default site
        site, created = Site.objects.get_or_create(
            is_default_site=True,
            defaults={'hostname': 'localhost', 'port': 80, 'root_page': home_page}
        )
        if not created:
            site.root_page = home_page
            site.save()
        
        # Check if test page already exists
        test_page = home_page.get_children().filter(slug="test-page").first()
        if not test_page:
            test_page = home_page.add_child(instance=Page(title="Test Page", slug="test-page", locale=locale))
        
        return test_page


class TestTaxonomyConstants:
    """Test the TaxonomyConstants class."""
    
    def test_constants_values(self):
        assert TaxonomyConstants.ROOT_CATEGORY_NAME == "_root_category"
        assert TaxonomyConstants.DEFAULT_ICON == "heroicons-tag-outline"
        assert TaxonomyConstants.CACHE_TIMEOUT == 3600
        assert TaxonomyConstants.CACHE_VERSION == "v1"
        assert TaxonomyConstants.MAX_BREADCRUMB_LENGTH == 80


class TestTaxonomyExceptions:
    """Test taxonomy exception classes."""
    
    def test_taxonomy_error_inheritance(self):
        error = TaxonomyError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
    
    def test_tree_integrity_error_inheritance(self):
        error = TreeIntegrityError("Tree integrity error")
        assert isinstance(error, TaxonomyError)
        assert isinstance(error, Exception)
        assert str(error) == "Tree integrity error"


class TestCategoryCache:
    """Test the CategoryCache utility class."""
    
    def test_make_key(self):
        key = CategoryCache.make_key("test_prefix", 123)
        expected = f"category_{TaxonomyConstants.CACHE_VERSION}_test_prefix_123"
        assert key == expected
    
    def test_get_descendants_key(self):
        key = CategoryCache.get_descendants_key(456)
        expected = f"category_{TaxonomyConstants.CACHE_VERSION}_descendants_456"
        assert key == expected
    
    def test_get_content_count_key(self):
        key = CategoryCache.get_content_count_key(789)
        expected = f"category_{TaxonomyConstants.CACHE_VERSION}_content_count_789"
        assert key == expected
    
    def test_invalidate_all(self, clear_cache):
        cache.set("test_key", "test_value")
        CategoryCache.invalidate_all()
        assert cache.get("test_key") is None


@pytest.mark.django_db
class TestCategoryModel:
    """Test the Category model."""
    
    def test_get_or_create_hidden_root(self):
        root = Category.get_or_create_hidden_root()
        assert root.name == TaxonomyConstants.ROOT_CATEGORY_NAME
        assert root.live is False
        assert root.is_hidden_root()
    
    def test_get_or_create_hidden_root_idempotent(self):
        root1 = Category.get_or_create_hidden_root()
        root2 = Category.get_or_create_hidden_root()
        assert root1.pk == root2.pk
    
    def test_create_category_auto_adds_to_root(self, root_category):
        category = Category(name="Test Category")
        category.save()
        assert category.get_parent() == root_category
        assert category.get_depth() == 2
    
    def test_create_root_category_method(self, root_category):
        category = Category.add_root_category("Root Level Category")
        assert category.get_parent() == root_category
        assert category.name == "Root Level Category"
    
    def test_add_child_category(self):
        parent = Category.add_root_category("Parent Category")
        child = parent.add_child_category("Child Category")
        assert child.get_parent() == parent
        assert child.name == "Child Category"
    
    def test_is_hidden_root(self, root_category):
        assert root_category.is_hidden_root()
        regular_category = Category.add_root_category("Regular Category")
        assert not regular_category.is_hidden_root()
    
    def test_is_visible(self, root_category):
        assert not root_category.is_visible()
        active_category = Category.add_root_category("Active Category", live=True)
        assert active_category.is_visible()
        inactive_category = Category.add_root_category("Inactive Category", live=False)
        assert not inactive_category.is_visible()
    
    def test_get_visible_children(self):
        parent = Category.add_root_category("Parent")
        active_child = parent.add_child_category("Active Child", live=True)
        inactive_child = parent.add_child_category("Inactive Child", live=False)
        
        visible_children = parent.get_visible_children()
        assert active_child in visible_children
        assert inactive_child not in visible_children
    
    def test_get_navigation_children(self):
        parent = Category.add_root_category("Parent")
        child1 = parent.add_child_category("Child 1", order_index=2)
        child2 = parent.add_child_category("Child 2", order_index=1)
        
        nav_children = list(parent.get_navigation_children())
        assert nav_children[0] == child2
        assert nav_children[1] == child1
    
    def test_get_breadcrumb_trail(self, category_hierarchy):
        grandchild = category_hierarchy['grandchild']
        trail = grandchild.get_breadcrumb_trail()
        assert len(trail) == 2
        assert trail[0] == category_hierarchy['parent']
        assert trail[1] == category_hierarchy['child']
    
    def test_get_depth_display(self, category_hierarchy):
        # Parent is a child of hidden root, so its display depth is 1
        assert category_hierarchy['parent'].get_depth_display() == 1
        assert category_hierarchy['child'].get_depth_display() == 2
        assert category_hierarchy['grandchild'].get_depth_display() == 3
    
    def test_full_name_property(self, category_hierarchy):
        parent = category_hierarchy['parent']
        child = category_hierarchy['child']
        grandchild = category_hierarchy['grandchild']
        
        assert parent.full_name == "Parent Category"
        assert child.full_name == "Parent Category Child Category"
        assert grandchild.full_name == "Parent Category Child Category Grandchild Category"
    
    def test_str_representation(self, category_hierarchy):
        parent = category_hierarchy['parent']
        child = category_hierarchy['child']
        
        assert str(parent) == "Parent Category"
        assert str(child) == "Parent Category :: Child Category"
    
    def test_str_representation_with_long_breadcrumb(self):
        parent = Category.add_root_category("A" * 30)
        child = parent.add_child_category("B" * 30)
        grandchild = child.add_child_category("C" * 30)
        
        result = str(grandchild)
        assert len(result) <= TaxonomyConstants.MAX_BREADCRUMB_LENGTH + 10
    
    def test_get_url_path(self):
        parent = Category.add_root_category("Technology", slug="technology")
        child = parent.add_child_category("AI", slug="ai")
        
        assert parent.get_url_path() == "technology"
        assert child.get_url_path() == "technology/ai"
    
    def test_move_to_parent(self):
        parent1 = Category.add_root_category("Parent 1")
        parent2 = Category.add_root_category("Parent 2")
        child = parent1.add_child_category("Child")
        
        # Store original parent for comparison
        assert child.get_parent() == parent1
        
        # Move the child to the new parent
        child.move_to_parent(parent2)
        
        # Get a fresh instance from database (refresh_from_db doesn't work with treebeard)
        child_fresh = Category.objects.get(pk=child.pk)
        
        assert child_fresh.get_parent().pk == parent2.pk
    
    def test_move_to_root(self, root_category):
        parent = Category.add_root_category("Parent")
        child = parent.add_child_category("Child")
        
        # Verify initial parent
        assert child.get_parent() == parent
        
        child.move_to_root()
        
        # Get a fresh instance from database (refresh_from_db doesn't work with treebeard)
        child_fresh = Category.objects.get(pk=child.pk)
        
        assert child_fresh.get_parent().pk == root_category.pk
    
    def test_cannot_move_hidden_root(self, root_category):
        parent = Category.add_root_category("Parent")
        with pytest.raises(ValueError, match="Cannot move hidden root category"):
            root_category.move_to_parent(parent)
    
    def test_cannot_delete_hidden_root(self, root_category):
        with pytest.raises(TreeIntegrityError, match="Cannot delete hidden root category"):
            root_category.delete()
    
    def test_clean_validation_root_category_live(self):
        root_category = Category(name=TaxonomyConstants.ROOT_CATEGORY_NAME, live=True)
        with pytest.raises(ValidationError):
            root_category.clean()
    
    def test_clean_validation_name_too_long(self):
        long_name = "x" * 101
        category = Category(name=long_name)
        with pytest.raises(ValidationError):
            category.clean()
    
    def test_cannot_create_multiple_hidden_roots(self, root_category):
        # Try to create another hidden root using regular save
        duplicate_root = Category(name=TaxonomyConstants.ROOT_CATEGORY_NAME, live=False)
        with pytest.raises(TreeIntegrityError, match="Hidden root category already exists"):
            duplicate_root.save()
    
    def test_get_visible_root_categories(self):
        active_root = Category.add_root_category("Active Root", live=True)
        inactive_root = Category.add_root_category("Inactive Root", live=False)
        
        visible_roots = Category.get_visible_root_categories()
        assert active_root in visible_roots
        assert inactive_root not in visible_roots
    
    def test_get_category_tree(self, root_category, category_hierarchy):
        tree = Category.get_category_tree()
        assert category_hierarchy['parent'] in tree
        assert category_hierarchy['child'] in tree
        assert root_category not in tree
    
    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    def test_cache_invalidation_on_save(self, clear_cache):
        category = Category.add_root_category("Test Category")
        cache_key = CategoryCache.get_descendants_key(category.pk)
        cache.set(cache_key, [1, 2, 3])
        
        category.save()
        assert cache.get(cache_key) is None
    
    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    def test_descendant_ids_caching(self, clear_cache):
        parent = Category.add_root_category("Parent")
        child1 = parent.add_child_category("Child 1")
        child2 = parent.add_child_category("Child 2")
        
        descendant_ids = parent.descendant_ids
        assert child1.pk in descendant_ids
        assert child2.pk in descendant_ids
        
        cached_ids = parent.descendant_ids
        assert descendant_ids == cached_ids
    
    def test_get_name_display(self, sample_category):
        display = sample_category.get_name_display()
        assert "Technology" in display
        assert "test-icon" in display


@pytest.mark.django_db
class TestCategoryQuerySet:
    """Test the CategoryQuerySet methods."""
    
    def test_active_filter(self, category_hierarchy):
        active_categories = Category.objects.active()
        assert category_hierarchy['parent'] in active_categories
        assert category_hierarchy['child'] in active_categories
        assert category_hierarchy['inactive_child'] not in active_categories
    
    def test_visible_filter(self, root_category, category_hierarchy):
        visible_categories = Category.objects.visible()
        assert category_hierarchy['parent'] in visible_categories
        assert category_hierarchy['inactive_child'] not in visible_categories
        assert root_category not in visible_categories
    
    def test_root_level_filter(self, category_hierarchy):
        root_level = Category.objects.root_level()
        assert category_hierarchy['parent'] in root_level
        assert category_hierarchy['child'] not in root_level
    
    def test_for_sitemap_filter(self, category_hierarchy):
        sitemap_categories = Category.objects.for_sitemap()
        assert category_hierarchy['parent'] in sitemap_categories
        assert category_hierarchy['grandchild'] not in sitemap_categories


@pytest.mark.django_db
class TestClassifierGroup:
    """Test the ClassifierGroup model."""
    
    def test_create_subject_group(self):
        group = ClassifierGroup.objects.create(type="Subject", name="Technology")
        assert group.type == "Subject"
        assert group.name == "Technology"
    
    def test_create_attribute_group(self):
        group = ClassifierGroup.objects.create(type="Attribute", name="Content Type")
        assert group.type == "Attribute"
        assert group.name == "Content Type"
    
    def test_str_representation(self):
        group = ClassifierGroup.objects.create(type="Subject", name="Technology")
        assert str(group) == "Technology (Subject)"
    
    def test_unique_constraint(self):
        ClassifierGroup.objects.create(type="Subject", name="Technology")
        with pytest.raises(IntegrityError):
            ClassifierGroup.objects.create(type="Subject", name="Technology")
    
    def test_classifiers_list_empty(self):
        group = ClassifierGroup.objects.create(type="Subject", name="Technology")
        assert group.classifiers_list() == ""
    
    def test_classifiers_list_with_items(self):
        group = ClassifierGroup.objects.create(type="Subject", name="Technology")
        for i in range(3):
            Classifier.objects.create(group=group, name=f"Classifier {i}")
        
        result = group.classifiers_list()
        assert "Classifier 0" in result
        assert "Classifier 1" in result
        assert "Classifier 2" in result
    
    def test_classifiers_list_with_many_items(self):
        group = ClassifierGroup.objects.create(type="Subject", name="Technology")
        for i in range(7):
            Classifier.objects.create(group=group, name=f"Classifier {i}")
        
        result = group.classifiers_list()
        assert "(+2 more)" in result
    
    def test_queryset_subjects_filter(self, classifier_groups):
        subjects = ClassifierGroup.objects.subjects()
        assert classifier_groups['subject'] in subjects
        assert classifier_groups['attribute'] not in subjects
    
    def test_queryset_attributes_filter(self, classifier_groups):
        attributes = ClassifierGroup.objects.attributes()
        assert classifier_groups['attribute'] in attributes
        assert classifier_groups['subject'] not in attributes


@pytest.mark.django_db
class TestClassifier:
    """Test the Classifier model."""
    
    def test_create_classifier(self, classifier_groups):
        classifier = Classifier.objects.create(group=classifier_groups['subject'], name="AI")
        assert classifier.group == classifier_groups['subject']
        assert classifier.name == "AI"
        assert classifier.slug == "ai"
    
    def test_str_representation(self, classifiers):
        expected = "Technology – Artificial Intelligence (Subject)"
        assert str(classifiers['ai']) == expected
    
    def test_unique_constraint(self, classifier_groups):
        Classifier.objects.create(group=classifier_groups['subject'], name="AI")
        with pytest.raises(IntegrityError):
            Classifier.objects.create(group=classifier_groups['subject'], name="AI")
    
    def test_auto_slug_generation(self, classifier_groups):
        classifier = Classifier.objects.create(
            group=classifier_groups['subject'], 
            name="Machine Learning"
        )
        assert classifier.slug == "machine-learning"
    
    def test_queryset_subjects_filter(self, classifiers):
        subjects = Classifier.objects.subjects()
        assert classifiers['ai'] in subjects
        assert classifiers['ml'] in subjects
        assert classifiers['article'] not in subjects
    
    def test_queryset_attributes_filter(self, classifiers):
        attributes = Classifier.objects.attributes()
        assert classifiers['article'] in attributes
        assert classifiers['ai'] not in attributes
    
    def test_for_autocomplete(self, classifiers):
        results = Classifier.objects.for_autocomplete("Artificial")
        assert classifiers['ai'] in results
        assert classifiers['article'] not in results


@pytest.mark.django_db
class TestPageCategoryAndClassifier:
    """Test the PageCategory and PageClassifier models."""
    
    def test_create_page_category(self, test_page, sample_category):
        page_category = PageCategory.objects.create(page=test_page, category=sample_category)
        assert page_category.page == test_page
        assert page_category.category == sample_category
    
    def test_create_page_classifier(self, test_page, classifiers):
        page_classifier = PageClassifier.objects.create(
            page=test_page, 
            classifier=classifiers['ai']
        )
        assert page_classifier.page == test_page
        assert page_classifier.classifier == classifiers['ai']
    
    def test_page_category_unique_constraint(self, test_page, sample_category):
        PageCategory.objects.create(page=test_page, category=sample_category)
        with pytest.raises(IntegrityError):
            PageCategory.objects.create(page=test_page, category=sample_category)
    
    def test_page_classifier_unique_constraint(self, test_page, classifiers):
        PageClassifier.objects.create(page=test_page, classifier=classifiers['ai'])
        with pytest.raises(IntegrityError):
            PageClassifier.objects.create(page=test_page, classifier=classifiers['ai'])
    
    def test_page_relationships(self, test_page, sample_category, classifiers):
        PageCategory.objects.create(page=test_page, category=sample_category)
        PageClassifier.objects.create(page=test_page, classifier=classifiers['ai'])
        
        assert test_page.categories.count() == 1
        assert test_page.classifiers.count() == 1
        assert sample_category.pages.count() == 1
        assert classifiers['ai'].pages.count() == 1


@pytest.mark.django_db
class TestTaxonomyIntegration:
    """Integration tests for the taxonomy system."""
    
    def test_complex_taxonomy_relationships(self, test_page, category_hierarchy, classifiers):
        # Create a second page as a sibling of test_page
        page2 = test_page.get_parent().add_child(
            instance=Page(title="Page 2", slug="page-2")
        )
        
        PageCategory.objects.create(page=test_page, category=category_hierarchy['parent'])
        PageCategory.objects.create(page=page2, category=category_hierarchy['child'])
        PageClassifier.objects.create(page=test_page, classifier=classifiers['ml'])
        PageClassifier.objects.create(page=page2, classifier=classifiers['ml'])
        
        assert test_page.categories.count() == 1
        assert page2.categories.count() == 1
        assert category_hierarchy['parent'].pages.count() == 1
        assert category_hierarchy['child'].pages.count() == 1
        assert classifiers['ml'].pages.count() == 2
    
    def test_category_hierarchy_queries(self, category_hierarchy):
        parent = category_hierarchy['parent']
        child = category_hierarchy['child']
        grandchild = category_hierarchy['grandchild']
        
        descendants = parent.get_visible_descendants()
        assert child in descendants
        assert grandchild in descendants
        
        ancestors = grandchild.get_breadcrumb_trail()
        assert parent in ancestors
        assert child in ancestors
    
    def test_category_tree_operations(self, root_category):
        # Create fresh categories for this test to avoid interference
        original_parent = Category.add_root_category("Original Parent")
        new_parent = Category.add_root_category("New Parent")
        child = original_parent.add_child_category("Test Child")
        original_child_pk = child.pk
        
        # Test moving to a new parent
        child.move_to_parent(new_parent)
        
        # Get a fresh instance from database (refresh_from_db doesn't work with treebeard)
        child_fresh = Category.objects.get(pk=original_child_pk)
        assert child_fresh.get_parent().pk == new_parent.pk
        
        # Test moving to root
        child_fresh.move_to_root()
        
        # Get another fresh instance after second move
        child_fresh2 = Category.objects.get(pk=original_child_pk)
        assert child_fresh2.get_parent().pk == root_category.pk
    
    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    def test_category_caching_integration(self, clear_cache, category_hierarchy):
        parent = category_hierarchy['parent']
        child = category_hierarchy['child']
        
        descendant_ids = parent.descendant_ids
        assert child.pk in descendant_ids
        
        new_child = parent.add_child_category("New Child")
        del parent.descendant_ids
        updated_descendant_ids = parent.descendant_ids
        assert new_child.pk in updated_descendant_ids
