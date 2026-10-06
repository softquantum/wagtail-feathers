from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from wagtail.models import Locale, Page, Site
from wagtail.rich_text import RichText

from showcase.models import ArticleIndexPage, ArticlePage, HomePage, WebPage
from wagtail_feathers.models import Category, Classifier, ClassifierGroup, PageCategory, PageClassifier

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up demo data for wagtail-feathers showcase'

    def handle(self, *args, **options):
        self.stdout.write('Setting up demo data...')
        
        # Create superuser if it doesn't exist
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Created superuser: admin/admin123'))
        
        # Get or create root page
        root_page = Page.objects.filter(depth=1).first()
        if not root_page:
            self.stdout.write(self.style.ERROR('No root page found'))
            return
            
        # Delete existing demo pages and Wagtail's default welcome page
        for home_page in HomePage.objects.all():
            home_page.delete()
        for page in Page.objects.filter(depth=2).exact_type(Page):
            page.delete()
        root_page.refresh_from_db()

        # Create home page
        home_page = HomePage(
            title='Wagtail Feathers Demo',
            slug='home',
            body=[
                ('paragraph_block', RichText(
                    '<p>Welcome to the Wagtail Feathers demo site! This showcases the features '
                    'and capabilities of the wagtail-feathers package.</p>'
                )),
            ],
        )
        root_page.add_child(instance=home_page)

        # Update site to point to home page
        site = Site.objects.filter(is_default_site=True).first() or Site(is_default_site=True, hostname='localhost')
        site.root_page = home_page
        site.site_name = 'Wagtail Feathers Demo'
        site.save()

        # Create a generic web page
        about_page = WebPage(
            title='About',
            slug='about',
            body=[
                ('paragraph_block', RichText('<p>A generic web page built on WebBasePage.</p>')),
            ],
        )
        home_page.add_child(instance=about_page)

        # Create taxonomy
        locale = Locale.get_default()
        Category.get_or_create_hidden_root()
        category = Category.objects.filter(slug='technology').first()
        if not category:
            category = Category.add_root_category('Technology', slug='technology')
            category.add_child_category('Wagtail')

        classifiers = []
        groups = [
            ('Subject', 'Topics', ['Theming', 'SEO', 'Getting started']),
            ('Attribute', 'Level', ['Beginner', 'Advanced']),
        ]
        for group_type, group_name, names in groups:
            group, _ = ClassifierGroup.objects.get_or_create(type=group_type, name=group_name, locale=locale)
            for name in names:
                classifier, _ = Classifier.objects.get_or_create(group=group, name=name, locale=locale)
                classifiers.append(classifier)

        # Create article index
        blog_index = ArticleIndexPage(
            title='Blog',
            slug='blog',
        )
        home_page.add_child(instance=blog_index)

        # Create sample articles
        articles = [
            {
                'title': 'Getting Started with Wagtail Feathers',
                'slug': 'getting-started',
                'body': '''<p>Wagtail Feathers provides a comprehensive foundation for your Wagtail CMS projects. This article demonstrates the reading time calculation feature and SEO optimization capabilities.</p>
                
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
                
                <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                
                <h2>Features Included</h2>
                <ul>
                    <li>SEO optimization with meta tags</li>
                    <li>Reading time calculation</li>
                    <li>Theme support</li>
                    <li>Navigation management</li>
                    <li>Taxonomy system</li>
                </ul>''',
            },
            {
                'title': 'Advanced Theme Customization',
                'slug': 'theme-customization',
                'body': '''<p>One of the powerful features of Wagtail Feathers is its theme system, which allows you to easily customize the appearance of your site.</p>
                
                <p>The theme system provides flexible template organization and styling capabilities. You can create custom themes or extend existing ones to match your brand requirements.</p>
                
                <h2>Theme Structure</h2>
                <p>Themes in Wagtail Feathers follow a structured approach:</p>
                
                <ol>
                    <li>Template organization</li>
                    <li>Static asset management</li>
                    <li>CSS and JavaScript bundling</li>
                    <li>Component-based architecture</li>
                </ol>
                
                <p>This approach ensures maintainable and scalable theme development while providing the flexibility needed for complex projects.</p>''',
            },
            {
                'title': 'SEO Best Practices with Wagtail Feathers',
                'slug': 'seo-best-practices',
                'body': '''<p>Search engine optimization is crucial for any website, and Wagtail Feathers makes it easy to implement SEO best practices.</p>
                
                <p>The SEO mixin provides automatic meta tag generation, Open Graph support, and Twitter Card integration. This ensures your content is properly optimized for search engines and social media sharing.</p>
                
                <h2>Key SEO Features</h2>
                <ul>
                    <li>Automatic meta description generation</li>
                    <li>Open Graph meta tags</li>
                    <li>Twitter Card support</li>
                    <li>Canonical URL management</li>
                    <li>Schema.org structured data</li>
                </ul>
                
                <p>These features work together to improve your site's search engine visibility and social media presence, helping you reach a wider audience.</p>''',
            }
        ]
        
        for article_data in articles:
            article = ArticlePage(
                title=article_data['title'],
                slug=article_data['slug'],
                publication_date=timezone.now().date(),
                body=[('paragraph_block', RichText(article_data['body']))],
            )
            article.categories = [PageCategory(category=category)]
            article.classifiers = [PageClassifier(classifier=classifiers[0])]
            blog_index.add_child(instance=article)
        
        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))
        self.stdout.write('You can now access the demo at http://localhost:8000')
        self.stdout.write('Admin interface: http://localhost:8000/admin (admin/admin123)')