"""
Factory classes for generating sample taxonomy data.

Usage:
    from wagtail_feathers.factories import CategoryFactory, ClassifierGroupFactory, ClassifierFactory
    
    # Create sample categories
    CategoryFactory.create_sample_tree()
    
    # Create sample classifier groups and classifiers
    ClassifierFactory.create_sample_data()
"""

import factory
from django.utils.text import slugify

from .models.taxonomy import Category, ClassifierGroup, Classifier


class CategoryFactory(factory.django.DjangoModelFactory):
    """Factory for creating Category instances."""
    
    class Meta:
        model = Category
    
    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    icon = "heroicons-folder-outline"
    live = True
    aliases = ""
    order_index = factory.Sequence(lambda n: n)
    
    @classmethod
    def create_sample_tree(cls):
        """Create a comprehensive sample category tree."""
        
        # Ensure root category exists
        root = Category.get_or_create_hidden_root()
        
        # Technology branch
        tech = root.add_child_category(
            name="Technology",
            slug="technology",
            icon="heroicons-cpu-chip-outline",
            aliases="Tech, IT, Computing"
        )
        
        tech.add_child_category(
            name="Artificial Intelligence",
            slug="artificial-intelligence", 
            icon="heroicons-beaker-outline",
            aliases="AI, Machine Learning, ML"
        )
        
        tech.add_child_category(
            name="Web Development",
            slug="web-development",
            icon="heroicons-code-bracket-outline", 
            aliases="Frontend, Backend, Full Stack"
        )
        
        tech.add_child_category(
            name="Data Science",
            slug="data-science",
            icon="heroicons-chart-bar-outline",
            aliases="Analytics, Big Data, Statistics"
        )
        
        tech.add_child_category(
            name="Cybersecurity",
            slug="cybersecurity",
            icon="heroicons-shield-check-outline",
            aliases="InfoSec, Security, Privacy"
        )
        
        # Business branch
        business = root.add_child_category(
            name="Business",
            slug="business",
            icon="heroicons-building-office-outline",
            aliases="Finance, Marketing, Strategy"
        )
        
        business.add_child_category(
            name="Digital Marketing",
            slug="digital-marketing",
            icon="heroicons-megaphone-outline",
            aliases="SEO, SEM, Social Media"
        )
        
        business.add_child_category(
            name="Financial Planning",
            slug="financial-planning",
            icon="heroicons-currency-dollar-outline",
            aliases="Budgeting, Investment, Retirement"
        )
        
        business.add_child_category(
            name="Entrepreneurship",
            slug="entrepreneurship",
            icon="heroicons-rocket-launch-outline",
            aliases="Startups, Innovation, Ventures"
        )
        
        # Science branch
        science = root.add_child_category(
            name="Science",
            slug="science",
            icon="heroicons-beaker-outline",
            aliases="Research, Academia, Discovery"
        )
        
        science.add_child_category(
            name="Physics",
            slug="physics",
            icon="heroicons-light-bulb-outline",
            aliases="Quantum, Mechanics, Theory"
        )
        
        science.add_child_category(
            name="Biology",
            slug="biology",
            icon="heroicons-heart-outline",
            aliases="Life Sciences, Genetics, Ecology"
        )
        
        science.add_child_category(
            name="Chemistry",
            slug="chemistry",
            icon="heroicons-beaker-outline",
            aliases="Molecular, Organic, Inorganic"
        )
        
        # Arts & Culture branch
        arts = root.add_child_category(
            name="Arts & Culture",
            slug="arts-culture",
            icon="heroicons-paint-brush-outline",
            aliases="Creative, Design, Literature"
        )
        
        arts.add_child_category(
            name="Digital Design",
            slug="digital-design",
            icon="heroicons-photo-outline",
            aliases="UI, UX, Graphic Design"
        )
        
        arts.add_child_category(
            name="Writing",
            slug="writing",
            icon="heroicons-pencil-outline",
            aliases="Literature, Content, Copywriting"
        )
        
        # Education branch
        education = root.add_child_category(
            name="Education",
            slug="education",
            icon="heroicons-academic-cap-outline",
            aliases="Learning, Teaching, Academia"
        )
        
        education.add_child_category(
            name="Online Learning",
            slug="online-learning",
            icon="heroicons-computer-desktop-outline",
            aliases="E-learning, MOOCs, Digital Education"
        )
        
        education.add_child_category(
            name="Professional Development",
            slug="professional-development",
            icon="heroicons-arrow-trending-up-outline",
            aliases="Career, Skills, Training"
        )
        
        return {
            'technology': tech,
            'business': business,
            'science': science,
            'arts': arts,
            'education': education
        }


class ClassifierGroupFactory(factory.django.DjangoModelFactory):
    """Factory for creating ClassifierGroup instances."""
    
    class Meta:
        model = ClassifierGroup
    
    type = factory.Iterator(["Subject", "Attribute"])
    name = factory.Sequence(lambda n: f"Group {n}")


class ClassifierFactory(factory.django.DjangoModelFactory):
    """Factory for creating Classifier instances."""
    
    class Meta:
        model = Classifier
    
    group = factory.SubFactory(ClassifierGroupFactory)
    name = factory.Sequence(lambda n: f"Classifier {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    sort_order = factory.Sequence(lambda n: n)
    
    @classmethod
    def create_sample_data(cls):
        """Create comprehensive sample classifier data."""
        
        # Subject-based classifier groups
        content_topics = ClassifierGroup.objects.create(
            type="Subject",
            name="Content Topics"
        )
        
        academic_disciplines = ClassifierGroup.objects.create(
            type="Subject", 
            name="Academic Disciplines"
        )
        
        industry_sectors = ClassifierGroup.objects.create(
            type="Subject",
            name="Industry Sectors"
        )
        
        # Attribute-based classifier groups
        difficulty_level = ClassifierGroup.objects.create(
            type="Attribute",
            name="Content Difficulty"
        )
        
        content_format = ClassifierGroup.objects.create(
            type="Attribute",
            name="Content Format"
        )
        
        target_audience = ClassifierGroup.objects.create(
            type="Attribute",
            name="Target Audience"
        )
        
        content_length = ClassifierGroup.objects.create(
            type="Attribute",
            name="Content Length"
        )
        
        # Content Topics (Subject)
        topics = [
            "Software Development", "Machine Learning", "Cybersecurity",
            "Cloud Computing", "DevOps", "Mobile Development",
            "Blockchain", "IoT", "Quantum Computing", "Robotics"
        ]
        
        for i, topic in enumerate(topics, 1):
            Classifier.objects.create(
                group=content_topics,
                name=topic,
                slug=slugify(topic),
                sort_order=i
            )
        
        # Academic Disciplines (Subject)
        disciplines = [
            "Computer Science", "Mathematics", "Physics", "Engineering",
            "Economics", "Psychology", "Philosophy", "Biology",
            "Chemistry", "Statistics"
        ]
        
        for i, discipline in enumerate(disciplines, 1):
            Classifier.objects.create(
                group=academic_disciplines,
                name=discipline,
                slug=slugify(discipline),
                sort_order=i
            )
        
        # Industry Sectors (Subject)
        sectors = [
            "Healthcare", "Finance", "Education", "Manufacturing",
            "Retail", "Transportation", "Energy", "Entertainment",
            "Government", "Non-Profit"
        ]
        
        for i, sector in enumerate(sectors, 1):
            Classifier.objects.create(
                group=industry_sectors,
                name=sector,
                slug=slugify(sector),
                sort_order=i
            )
        
        # Content Difficulty (Attribute)
        difficulties = ["Beginner", "Intermediate", "Advanced", "Expert"]
        
        for i, difficulty in enumerate(difficulties, 1):
            Classifier.objects.create(
                group=difficulty_level,
                name=difficulty,
                slug=slugify(difficulty),
                sort_order=i
            )
        
        # Content Format (Attribute)
        formats = [
            "Tutorial", "Article", "Guide", "Reference", "Case Study",
            "Research Paper", "Interview", "News", "Opinion", "Review"
        ]
        
        for i, format_type in enumerate(formats, 1):
            Classifier.objects.create(
                group=content_format,
                name=format_type,
                slug=slugify(format_type),
                sort_order=i
            )
        
        # Target Audience (Attribute)
        audiences = [
            "Students", "Professionals", "Researchers", "Educators",
            "General Public", "Developers", "Managers", "Executives",
            "Beginners", "Experts"
        ]
        
        for i, audience in enumerate(audiences, 1):
            Classifier.objects.create(
                group=target_audience,
                name=audience,
                slug=slugify(audience),
                sort_order=i
            )
        
        # Content Length (Attribute)
        lengths = ["Quick Read (< 5 min)", "Short (5-15 min)", 
                  "Medium (15-30 min)", "Long (30+ min)", "Deep Dive (1+ hour)"]
        
        for i, length in enumerate(lengths, 1):
            Classifier.objects.create(
                group=content_length,
                name=length,
                slug=slugify(length),
                sort_order=i
            )
        
        return {
            'subject_groups': [content_topics, academic_disciplines, industry_sectors],
            'attribute_groups': [difficulty_level, content_format, target_audience, content_length]
        }


def create_all_sample_data():
    """Create all sample taxonomy data at once."""
    categories = CategoryFactory.create_sample_tree()
    classifiers = ClassifierFactory.create_sample_data()
    
    return {
        'categories': categories,
        'classifiers': classifiers
    }