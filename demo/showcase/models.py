from django import forms
from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, TabbedInterface
from wagtail.contrib.forms.models import AbstractFormField
from wagtail.fields import RichTextField, StreamField
from wagtail.images import get_image_model_string
from wagtail.models import Page

from wagtail_feathers.blocks import PageHeaderBlock, CommonContentBlock
from wagtail_feathers.models import WebBasePage, IndexPage, ItemPage, FormBasePage


class HomePage(WebBasePage):
    """Home page model."""

    template = "pages/home_page.html"

    parent_page_types = ["wagtailcore.Page"]
    max_count = 1
    show_in_menus_default = True

    class Meta:
        verbose_name = "Home Page"


class WebPage(WebBasePage):
    """Web page model.

    Gets from WebBasePage:
    - PageHeaderBlock with Hero content for page headers and landing areas
    - All CommonContentBlock capabilities (paragraphs, images, CTAs, cards, etc.)
    - Maintains all FeatherPage functionality (taxonomy, authorship, etc.)

    A generic web page that can be used for various purposes like
    About Us, What We Do, etc.
    """

    template = "pages/web_page.html"

    class Meta:
        verbose_name = "Web Page"
        ordering = ["-first_published_at"]


class ArticleIndexPage(IndexPage):
    """Article index page model.

    A landing page for articles, which can be used to list all articles
    or a specific set of articles.

    It inherits from the IndexPage and can have an introduction and featured image.
    It has a body field with a stream field for common content.
    """

    template = "pages/article_index_page.html"
    subpage_types = ["showcase.ArticlePage"]

    def get_items(self):
        """Get items to display on this index page with optimized queries.

        Overrides parent method to optimize SQL queries specifically for ArticlePage.
        Uses select_related for one-to-one/foreign key relationships and
        prefetch_related for many-to-many relationships.
        """
        return (
            self.get_children()
            .live()
            .select_related("articlepage__featured_image")
            .prefetch_related(
                "articlepage__tags", "articlepage__classifiers__classifier", "articlepage__authors__person"
            )
            .specific()
            .order_by("-first_published_at")
        )

    class Meta:
        verbose_name = "Article Index Page"


class ArticlePage(ItemPage):
    """Comprehensive article page demonstrating all ItemPage features."""
    
    template = "pages/article_page.html"
    
    # Article-specific fields
    excerpt = RichTextField(
        blank=True,
        help_text="Brief summary of the article (used in listings and meta descriptions)"
    )
    
    featured_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Featured image for the article"
    )
    
    # Custom content panels extending ItemPage
    content_panels = ItemPage.content_panels + [
        FieldPanel('excerpt'),
        FieldPanel('featured_image'),
    ]
    
    # Enhanced context for templates
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        # Add related articles based on categories
        if hasattr(self, 'categories') and self.categories.exists():
            related_articles = ArticlePage.objects.live().public().exclude(id=self.id).filter(
                categories__in=self.categories.all()
            ).distinct().order_by('-first_published_at')[:3]
            context['related_articles'] = related_articles
        
        return context
    
    class Meta:
        verbose_name = "Article Page"


class AuthorPage(WebBasePage):
    """Author profile page demonstrating Person model integration."""
    
    template = "pages/author_page.html"
    
    # Author profile information
    bio = RichTextField(
        blank=True,
        help_text="Author biography and background"
    )
    
    profile_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Author profile photo"
    )
    
    # Contact information
    email = models.EmailField(blank=True, help_text="Public contact email")
    website = models.URLField(blank=True, help_text="Personal website or portfolio")
    
    # Social media links (will be enhanced with Person model integration)
    twitter_handle = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Twitter handle (without @)"
    )
    linkedin_url = models.URLField(blank=True)
    
    # Author specialties
    specialties = RichTextField(
        blank=True,
        help_text="Areas of expertise and specialization"
    )
    
    content_panels = WebBasePage.content_panels + [
        MultiFieldPanel([
            FieldPanel('profile_image'),
            FieldPanel('bio'),
            FieldPanel('specialties'),
        ], heading="Profile Information"),
        
        MultiFieldPanel([
            FieldPanel('email'),
            FieldPanel('website'),
            FieldPanel('twitter_handle'),
            FieldPanel('linkedin_url'),
        ], heading="Contact & Social Media"),
    ]
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        # Get articles by this author (will be enhanced with PageAuthor relationships)
        author_articles = ArticlePage.objects.live().public().order_by('-first_published_at')[:10]
        context['author_articles'] = author_articles
        
        return context
    
    class Meta:
        verbose_name = "Author Page"


class FAQPage(WebBasePage):
    """FAQ page demonstrating FAQ system functionality."""
    
    template = "pages/faq_page.html"
    
    # FAQ-specific content
    introduction = RichTextField(
        blank=True,
        help_text="Introduction text for the FAQ page"
    )
    
    # FAQ categories to display (simplified for demo)
    show_search = models.BooleanField(
        default=True,
        help_text="Show search functionality on the FAQ page"
    )
    
    show_categories = models.BooleanField(
        default=True,
        help_text="Show category filtering on the FAQ page"
    )
    
    items_per_page = models.PositiveIntegerField(
        default=10,
        help_text="Number of FAQ items to show per page"
    )
    
    content_panels = WebBasePage.content_panels + [
        FieldPanel('introduction'),
        MultiFieldPanel([
            FieldPanel('show_search'),
            FieldPanel('show_categories'),
            FieldPanel('items_per_page'),
        ], heading="FAQ Settings"),
    ]
    
    class Meta:
        verbose_name = "FAQ Page"


class ContactPage(FormBasePage):
    """Contact page demonstrating FormBasePage with enhanced features."""
    
    # Office/contact information
    office_hours = RichTextField(
        blank=True,
        help_text="Business hours and availability"
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Contact phone number"
    )
    
    address = RichTextField(
        blank=True,
        help_text="Physical address"
    )
    
    map_embed = models.TextField(
        blank=True,
        help_text="Embed code for map (Google Maps, etc.)"
    )
    
    # Emergency contact information
    emergency_contact = RichTextField(
        blank=True,
        help_text="Emergency or after-hours contact information"
    )
    
    content_panels = FormBasePage.content_panels + [
        MultiFieldPanel([
            FieldPanel('office_hours'),
            FieldPanel('phone_number'),
            FieldPanel('address'),
            FieldPanel('map_embed'),
            FieldPanel('emergency_contact'),
        ], heading="Contact Information"),
    ]
    
    class Meta:
        verbose_name = "Contact Page"


class ContactFormField(AbstractFormField):
    """Form fields for the ContactPage."""
    
    page = ParentalKey(
        ContactPage,
        on_delete=models.CASCADE,
        related_name='form_fields'
    )