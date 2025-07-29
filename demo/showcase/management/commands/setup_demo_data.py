from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from wagtail.models import Site, Page
from showcase.models import HomePage, BlogIndexPage, ArticlePage

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
            
        # Delete existing demo pages
        HomePage.objects.all().delete()
        
        # Create home page
        home_page = HomePage(
            title='Wagtail Feathers Demo',
            slug='home',
            intro='<p>Welcome to the Wagtail Feathers demo site! This showcases the features and capabilities of the wagtail-feathers package.</p>'
        )
        root_page.add_child(instance=home_page)
        
        # Update site to point to home page
        site = Site.objects.get(is_default_site=True)
        site.root_page = home_page
        site.site_name = 'Wagtail Feathers Demo'
        site.save()
        
        # Create blog index
        blog_index = BlogIndexPage(
            title='Blog',
            slug='blog',
            intro='<p>Demo articles showcasing wagtail-feathers features like SEO optimization and reading time calculation.</p>'
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
                body=article_data['body']
            )
            blog_index.add_child(instance=article)
        
        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))
        self.stdout.write('You can now access the demo at http://localhost:8000')
        self.stdout.write('Admin interface: http://localhost:8000/admin (admin/admin123)')