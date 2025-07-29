# Wagtail Feathers

A comprehensive Wagtail CMS extension providing foundational functionality for building sophisticated content management systems.

[![Python Version](https://img.shields.io/pypi/pyversions/wagtail-feathers.svg)](https://pypi.org/project/wagtail-feathers/)
[![Django Version](https://img.shields.io/badge/django-5.1%20%7C%205.2-blue.svg)](https://docs.djangoproject.com/en/5.2/)
[![Wagtail Version](https://img.shields.io/badge/wagtail-6.x%20%7C%207.x-orange.svg)](https://wagtail.org/)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-green.svg)](LICENSE)

> [!CAUTION]
> This package is a beta version which means it is **almost** stable and definitely lacks some documentation and tests
> The package is aimed at new installations

## Features

Wagtail Feathers provides a comprehensive set of reusable components and patterns:

### 🏗️ **Advanced Page Architecture**
- **FeatherBasePage**: Foundation for all custom pages with comprehensive SEO capabilities
- **Flexible Content Blocks**: Rich StreamField blocks for dynamic content composition
- **Page Relationships**: Built-in related page functionality and cross-references

### 📂 **Taxonomy & Classification**  
- **Hierarchical Categories**: Tree-structured content classification
- **Flexible Subjects**: Tagging and subject matter organization
- **Custom Attributes**: Extensible metadata and properties system
- **Admin Integration**: Beautiful select widgets and management interface

### 🧭 **Dynamic Navigation**
- **Multiple Menu Types**: Traditional hierarchical and StreamField-based navigation
- **Flexible Menu Items**: Support for both page links and external URLs

### 🔍 **SEO & Metadata**
- **Built on Wagtail SEO**: Extends Wagtail's built-in `seo_title` and `search_description` fields
- **Social Media Ready**: Open Graph and Twitter Card support with dedicated image field
- **Structured Data**: Automatic JSON-LD generation for articles, organizations, and more
- **Smart Fallbacks**: Intelligent content detection for missing SEO fields
- **Search Engine Control**: No-index/no-follow directives and robots meta tags
- **Reading Time**: Automatic reading time calculation with SEO integration

### 🎨 **Theme System**
- **Multi-Site Theming**: Different themes per site
- **Template Discovery**: Automatic theme-based template resolution
- **Asset Management**: Theme-specific CSS/JS handling
- **Configuration**: Site-wide settings and theme preferences


### 🌍 **Internationalization** (Optional)
- **Locale-Aware Ready**: Models ready for i18n when you need it
- **Simple Translation**: Use Wagtail's built-in translation features
- **Advanced Workflows**: Optional wagtail-localize integration (recommended)

### 👥 **Authorship & People**
- **Author Management**: Flexible author attribution system with AuthorType and PageAuthor models
- **People Directory**: Staff and contributor profiles with PersonGroup organization
- **Social Integration**: Social media links and profiles with SocialMediaSettings

### ❌ **Error Pages**
- **Custom Error Pages**: Configurable 404, and 500 error pages (TBC: 400, 403)
- **ErrorPage Model**: Editable error pages with custom messages and images

### ❓ **FAQ System**
- **FAQ Management**: Structured FAQ system with FAQCategory and FAQ models
- **Categorized Content**: Organize frequently asked questions by category

### 🔗 **Page Relationships**
- **Related Content**: RelatedPage, RelatedDocument, and RelatedExternalLink models
- **Cross-References**: Built-in page relationship functionality
- **Geographic Tagging**: PageCountry model for location-based content

## Installation

### Basic Installation (No i18n)
```bash
pip install wagtail-feathers
```

### With Advanced Translation Workflows
```bash
pip install wagtail-feathers[localize]
```

## Quick Start

1. **Add to Django Settings**:

**Basic Setup:**
```python
INSTALLED_APPS = [
    # ... your apps
    "wagtail_feathers",
    "wagtailmarkdown",
    "django_extensions",
    # ... other apps
]
```

**Theming**
```
# create a folder named "themes" at the 'BASE_DIR' of your project
...
@cached_property
def themes_dir(self) -> Path:
    """Get the themes directory from Django settings."""
    return getattr(settings, "BASE_DIR", Path.cwd()) / "themes"
...
```
Add all the themes you want, see the demo/themes folder for an example.  Adapt the json file accordingly.


**With Simple Translation:**
```python
INSTALLED_APPS = [
    # ... your apps
    "wagtail_feathers",
    "wagtail.contrib.simple_translation",  # Wagtail built-in
    # ... other apps
]
```

**With Advanced Translation:**
```python
INSTALLED_APPS = [
    # ... your apps
    "wagtail_feathers",
    "wagtail_localize",
    "wagtail_localize.locales",
    # ... other apps
]
```

2. **Run Migrations**:
```bash
python manage.py migrate
```

3. **Create Your First Page**:
```python
from wagtail_feathers.models import FeatherBasePage

class MyPage(FeatherBasePage):
    # Your custom fields here
    pass
```

## Advanced Usage

### Custom Page Models

```python
from wagtail_feathers.models import FeatherBasePage, ItemPage
from wagtail_feathers.blocks import CommonContentBlock
from wagtail.fields import StreamField

class ArticlePage(ItemPage):
    body = StreamField([
        ("content", CommonContentBlock()),
    ], use_json_field=True)
    
    content_panels = ItemPage.content_panels + [
        FieldPanel("body"),
    ]
```

### Taxonomy Integration

```python
from wagtail_feathers.models import Category, Classifier, ClassifierGroup

# Create categories
category = Category.objects.create(name="Technology", slug="tech")

# Create classifier groups and classifiers
group = ClassifierGroup.objects.create(name="Topics", max_selections=3)
classifier = Classifier.objects.create(
    name="AI & Machine Learning",
    slug="ai-ml",
    group=group
)
```

### Navigation Menus

```python
from wagtail_feathers.models import Menu, MenuItem, FlatMenu, NestedMenu

# Create a flat menu
flat_menu = FlatMenu.objects.create(name="Main Navigation")

# Create a nested menu
nested_menu = NestedMenu.objects.create(name="Footer Navigation")

# Create menu items
MenuItem.objects.create(
    menu=flat_menu,
    link_page=home_page,
    link_text="Home",
    sort_order=1
)
```

### Error Pages

```python
from wagtail_feathers.models import ErrorPage

# Create custom error pages
error_404 = ErrorPage.objects.create(
    title="404",
    error_code="404",
    heading="Page Not Found",
    message="<p>The page you are looking for does not exist.</p>"
)
```

### FAQ System

```python
from wagtail_feathers.models import FAQCategory, FAQ

# Create FAQ categories and items
category = FAQCategory.objects.create(
    title="General Questions",
    slug="general"
)

faq = FAQ.objects.create(
    question="How do I get started?",
    answer="<p>Follow our quick start guide...</p>",
    category=category
)
```

### SEO & Metadata

```python
from wagtail_feathers.models import FeatherBasePage
from wagtail_feathers.models.seo import SeoContentType, TwitterCardType

class ArticlePage(FeatherBasePage):
    # SEO fields are automatically available via SeoMixin
    pass

# In your templates - add to <head> section:
# {% load seo_tags %}
# {% include "wagtail_feathers/seo/meta.html" %}

# In your templates - add before </body>:
# {% include "wagtail_feathers/seo/structured_data.html" %}

# Programmatic SEO control:
page = ArticlePage.objects.get(pk=1)
page.seo_title = "Custom SEO Title"  # Uses Wagtail's built-in field
page.search_description = "Custom meta description for search engines"  # Uses Wagtail's built-in field
page.seo_content_type = SeoContentType.ARTICLE
page.twitter_card_type = TwitterCardType.SUMMARY_LARGE_IMAGE
page.save()
```

### Reading Time Features

All `ItemPage` models automatically include reading time calculation:

```python
from wagtail_feathers.models import ItemPage

class BlogPost(ItemPage):
    # Reading time is automatically calculated from:
    # - title, introduction, body content
    # - Configurable words-per-minute (default: 200 WPM)
    pass

# In templates:
# {% load reading_time_tags %}
# {% reading_time page %}  # "5 min read"
# {% reading_time page "long" %}  # "5 minutes read"  
# {% reading_time_badge page %}  # Badge with clock icon

# Custom reading time logic:
class TechnicalArticle(ItemPage):
    summary = RichTextField(blank=True)
    
    def get_additional_word_sources(self):
        """Include summary in word count."""
        words = 0
        if self.summary:
            words += self._count_text_words(str(self.summary))
        return words
    
    # Slower reading speed for technical content
    words_per_minute = 150

# Reading time extends SEO automatically:
# - Twitter Cards: "Reading time: 5 min read"
# - Structured Data: "timeRequired": "PT5M"
# - Meta tags: article:reading_time
```

### Extending SEO Features

The SEO functionality in wagtail_feathers is designed to be extensible. Here are several ways to enhance it:

#### 1. Adding Custom SEO Fields

```python
from wagtail_feathers.models import FeatherBasePage, SeoMixin
from wagtail.admin.panels import FieldPanel

class ArticlePage(FeatherBasePage):
    # Add your own SEO-related fields
    meta_keywords = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Comma-separated keywords (optional for modern SEO)"
    )
    
    facebook_app_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Facebook App ID for Open Graph"
    )
    
    # Extend the SEO panels
    seo_panels = SeoMixin.seo_panels + [
        FieldPanel("meta_keywords"),
        FieldPanel("facebook_app_id"),
    ]
    
    # Override SEO methods for custom behavior
    def get_seo_description(self):
        """Custom SEO description logic."""
        # Try your custom field first
        if hasattr(self, "excerpt") and self.excerpt:
            return self.excerpt[:160]
        
        # Fall back to parent implementation
        return super().get_seo_description()
```

#### 2. Custom Structured Data

```python
import json
from wagtail_feathers.models import SeoMixin

class ProductPage(FeatherBasePage):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.CharField(max_length=100)
    sku = models.CharField(max_length=50)
    
    def get_structured_data(self):
        """Override to add Product schema."""
        if self.seo_content_type == "product":
            site = self.get_site()
            base_url = site.root_url if site.root_url else f"https://{site.hostname}"
            
            schema = {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": self.get_seo_title(),
                "description": self.get_seo_description(),
                "sku": self.sku,
                "brand": {
                    "@type": "Brand",
                    "name": self.brand
                },
                "offers": {
                    "@type": "Offer",
                    "price": str(self.price),
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/InStock"
                }
            }
            
            # Add image if available
            if self.get_seo_image():
                schema["image"] = f"{base_url}{self.get_seo_image().file.url}"
                
            return json.dumps(schema, ensure_ascii=False)
        
        # Fall back to parent implementation
        return super().get_structured_data()
```

#### 3. SEO-Focused Page Types

```python
from wagtail_feathers.models import ItemPage
from wagtail_feathers.models.seo import SeoContentType, TwitterCardType

class SEOOptimizedArticle(ItemPage):
    """Article page optimized for SEO best practices."""
    
    # Set SEO defaults
    seo_content_type = SeoContentType.ARTICLE
    twitter_card_type = TwitterCardType.SUMMARY_LARGE_IMAGE
    
    # Additional SEO fields
    focus_keyword = models.CharField(
        max_length=100,
        blank=True,
        help_text="Primary keyword/phrase for this article"
    )
    
    reading_time = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Estimated reading time in minutes"
    )
    
    content_panels = ItemPage.content_panels + [
        FieldPanel("focus_keyword"),
        FieldPanel("reading_time"),
    ]
    
    def get_structured_data(self):
        """Enhanced article schema with reading time."""
        schema_str = super().get_structured_data()
        if schema_str and self.seo_content_type == SeoContentType.ARTICLE:
            schema = json.loads(schema_str)
            
            # Add reading time
            if self.reading_time:
                schema["timeRequired"] = f"PT{self.reading_time}M"
            
            # Add focus keyword as about
            if self.focus_keyword:
                schema["about"] = {
                    "@type": "Thing",
                    "name": self.focus_keyword
                }
                
            return json.dumps(schema, ensure_ascii=False)
        
        return schema_str
```

#### 4. Custom SEO Template Tags

```python
# In your app"s templatetags/custom_seo_tags.py
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def custom_meta_tags(page):
    """Add custom meta tags based on page type."""
    tags = []
    
    # Add article-specific tags
    if hasattr(page, "focus_keyword") and page.focus_keyword:
        tags.append(f"<meta name='keywords' content='{page.focus_keyword}'>")
    
    # Add Facebook App ID if available
    if hasattr(page, "facebook_app_id") and page.facebook_app_id:
        tags.append(f"<meta property='fb:app_id' content='{page.facebook_app_id}'>")
    
    # Add reading time for articles
    if hasattr(page, "reading_time") and page.reading_time:
        tags.append(f"<meta name='twitter:label1' content="Reading time">")
        tags.append(f"<meta name='twitter:data1' content='{page.reading_time} min read'>")
    
    return mark_safe("\n".join(tags))

# In your templates:
# {% load custom_seo_tags %}
# {% custom_meta_tags page %}
```

#### 5. SEO Analytics Integration

```python
class AnalyticsEnhancedPage(FeatherBasePage):
    """Page with SEO analytics tracking."""
    
    google_analytics_id = models.CharField(
        max_length=20,
        blank=True,
        help_text="Google Analytics tracking ID (e.g., GA-XXXXX-X)"
    )
    
    track_scroll_depth = models.BooleanField(
        default=False,
        help_text="Enable scroll depth tracking for SEO insights"
    )
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        # Add SEO tracking context
        context.update({
            "enable_seo_tracking": self.track_scroll_depth,
            "ga_tracking_id": self.google_analytics_id,
        })
        
        return context
```

#### 6. Multi-language SEO

```python
# If using wagtail-localize
from wagtail_feathers.models.seo import SeoMixin
from wagtail_localize.fields import TranslatableField

class MultilingualSEOPage(FeatherBasePage):
    """Page with enhanced multilingual SEO support."""
    
    # Additional translatable SEO fields
    local_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="Keywords in local language"
    )
    
    cultural_context = models.TextField(
        blank=True,
        help_text="Cultural context for this market"
    )
    
    # Add to translatable fields
    if SeoMixin.WAGTAIL_LOCALIZE_AVAILABLE:
        translatable_fields = SeoMixin.translatable_fields + [
            TranslatableField("local_keywords"),
            TranslatableField("cultural_context"),
        ]
    
    def get_seo_description(self):
        """Localized SEO description."""
        if self.cultural_context:
            return f"{super().get_seo_description()} {self.cultural_context}"[:160]
        return super().get_seo_description()
```

#### 7. Using Extension Points

The SeoMixin provides several extension points for easy customization:

```python
class BlogArticlePage(ItemPage):
    """Blog article with enhanced SEO using extension points."""
    
    author_twitter = models.CharField(max_length=50, blank=True)
    focus_keyword = models.CharField(max_length=100, blank=True)
    # Note: reading_time is automatically provided by ItemPage
    
    def get_custom_meta_tags(self):
        """Add custom meta tags."""
        tags = {}
        
        if self.focus_keyword:
            tags["keywords"] = self.focus_keyword
        
        # Reading time is automatically added via ReadingTimeMixin
        # but you can customize it here if needed
            
        return tags
    
    def get_custom_twitter_tags(self):
        """Add custom Twitter Card tags."""
        tags = {}
        
        if self.author_twitter:
            tags["twitter:creator"] = f"@{self.author_twitter}"
        
        # Reading time Twitter tags are automatically added via ReadingTimeMixin
        # Additional Twitter tags can be added here
            
        return tags
    
    def get_custom_og_tags(self):
        """Add custom Open Graph tags."""
        tags = {}
        
        if self.author_twitter:
            tags["article:author"] = f"https://twitter.com/{self.author_twitter}"
            
        return tags
    
    def get_sitemap_priority(self):
        """Higher priority for recent articles and longer reads."""
        from django.utils import timezone
        from datetime import timedelta
        
        base_priority = super().get_sitemap_priority()
        
        # Boost recent articles
        if hasattr(self, "publication_date"):
            recent_threshold = timezone.now().date() - timedelta(days=30)
            if self.publication_date >= recent_threshold:
                base_priority += 0.1
        
        # Boost longer articles (more comprehensive content)
        if self.reading_time_minutes and self.reading_time_minutes >= 10:
            base_priority += 0.1
                
        return min(1.0, base_priority)  # Cap at 1.0
```

These examples show how to build upon wagtail_feathers SEO foundation to create powerful, customized SEO solutions for specific use cases.

### People & Authors

```python
from wagtail_feathers.models import Person, PersonGroup, AuthorType, PageAuthor

# Create person groups and people
group = PersonGroup.objects.create(name="Editorial Team")
person = Person.objects.create(
    first_name="John",
    last_name="Doe",
    email="john@example.com"
)
person.groups.add(group)

# Create author types and assign to pages
author_type = AuthorType.objects.create(name="Writer")
PageAuthor.objects.create(
    page=my_page,
    person=person,
    author_type=author_type
)
```

## Requirements

- Python 3.11+
- Django 5.0+  
- Wagtail 5.2+

See `pyproject.toml` for complete dependency list.

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/softquantum/wagtail-feathers.git
cd wagtail-feathers

# Navigate to demo directory
cd demo

# Install demo dependencies (includes editable package install)
pip install -r requirements.txt

# Set up database and demo data
python manage.py migrate
python manage.py setup_demo_data

# Start the demo server
python manage.py runserver
```

```bash
# Run tests
pytest

# Run tests across multiple environments
tox
```

### Try the Demo Site

**Demo Access:**
- **Frontend:** http://localhost:8000
- **Admin:** http://localhost:8000/admin (admin/admin123)

The demo includes (WORK IN PROGRESS):
- Sample pages using wagtail-feathers features
- SEO optimization examples
- Reading time calculation
- Taxonomy and navigation examples
- Live package development (changes reflect immediately)

### Testing

The package includes some tests covering:
- Model functionality and relationships
- Template rendering and themes
- Navigation generation
- Taxonomy management
- Multi-site behavior

```bash
# Run all tests
pytest
```

### Code Quality

```bash
# Lint code
ruff check src/

# Format code  
ruff format src/

# Run via tox
tox -e lint
tox -e format
```

## Architecture

Wagtail Feathers follows a modular architecture:

```
wagtail_feathers/
├── models/           # Core model definitions
│   ├── base.py      # FeatherBasePage and foundation classes
│   ├── author.py    # AuthorType and PageAuthor models
│   ├── errors.py    # ErrorPage model
│   ├── faq.py       # FAQ and FAQCategory models  
│   ├── geographic.py # PageCountry model
│   ├── inline.py    # Related content models
│   ├── navigation.py # Menu and navigation models
│   ├── person.py    # Person and PersonGroup models
│   ├── settings.py  # SiteSettings model
│   ├── social.py    # Social media models
│   ├── specialized_pages.py # Specialized page types
│   ├── taxonomy.py  # Category and Classifier models
│   └── utils.py     # Model utilities
├── blocks.py        # StreamField content blocks
├── templatetags/    # Template tag libraries
├── viewsets/        # Wagtail admin viewsets
├── themes.py        # Theme system
└── management/      # Django management commands
```

## Key Models

Based on the migration, wagtail_feathers provides these core models:

- **Page Foundation**: `FeatherBasePage`, `FeatherBasePageTag`
- **Taxonomy**: `Category`, `Classifier`, `ClassifierGroup`, `PageCategory`, `PageClassifier`
- **Navigation**: `Menu`, `MenuItem`, `FlatMenu`, `NestedMenu`, `Footer`, `FooterNavigation`
- **People & Authors**: `Person`, `PersonGroup`, `AuthorType`, `PageAuthor`
- **Content Organization**: `FAQ`, `FAQCategory`, `ErrorPage`
- **Relationships**: `RelatedPage`, `RelatedDocument`, `RelatedExternalLink`
- **Geography**: `PageCountry`
- **Social**: `SocialMediaSettings`, `SocialMediaLink`
- **Settings**: `SiteSettings`

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License
[BSD-3-Clause](LICENSE)

## Credits & Attributions
- ✅ Wagtail Feathers is Developed by [Maxime Decooman](https://github.com/softquantum).
- ✅ Built on the excellent [Wagtail CMS](https://wagtail.org/) (License [BSD-3-Clause](https://github.com/wagtail/wagtail/blob/main/LICENSE))
- ✅ The icons prefixed "heroicons-" are sourced from version 2.2.0 of [Heroicons](https://github.com/tailwindlabs/heroicons), the beautiful hand-crafted SVG icons library, by the makers of Tailwind CSS (License [MIT](https://github.com/tailwindlabs/heroicons/blob/master/LICENSE)).