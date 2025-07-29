"""
Template tags for SEO functionality in Wagtail Feathers.

Provides utilities for rendering SEO metadata, structured data,
and social media tags in templates.
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def seo_meta_tags(context, page=None):
    """
    Generate complete SEO meta tags for a page.
    
    Usage:
        {% seo_meta_tags %}
        {% seo_meta_tags page %}
    """
    if page is None:
        page = context.get('page')
    
    if not page or not hasattr(page, 'get_seo_title'):
        return ''
    
    request = context.get('request')
    
    # Build meta tags
    meta_tags = []
    
    # Basic meta tags
    meta_tags.append(f'<title>{page.get_seo_title()}</title>')
    meta_tags.append(f'<meta name="description" content="{page.get_seo_description()}">')
    meta_tags.append(f'<meta name="robots" content="{page.get_robots_content()}">')
    
    # Canonical URL
    canonical_url = page.get_canonical_url()
    if canonical_url:
        meta_tags.append(f'<link rel="canonical" href="{canonical_url}">')
    
    # Open Graph tags
    meta_tags.append(f'<meta property="og:type" content="{page.seo_content_type}">')
    meta_tags.append(f'<meta property="og:title" content="{page.get_seo_title()}">')
    meta_tags.append(f'<meta property="og:description" content="{page.get_seo_description()}">')
    
    if canonical_url:
        meta_tags.append(f'<meta property="og:url" content="{canonical_url}">')
    
    # Open Graph image
    seo_image = page.get_seo_image()
    if seo_image and request:
        try:
            from wagtail.images import get_image_model
            from wagtail.images.templatetags.wagtailimages_tags import ImageNode
            
            # Get resized image
            rendition = seo_image.get_rendition('fill-1200x630')
            image_url = request.build_absolute_uri(rendition.url)
            
            meta_tags.append(f'<meta property="og:image" content="{image_url}">')
            meta_tags.append(f'<meta property="og:image:width" content="{rendition.width}">')
            meta_tags.append(f'<meta property="og:image:height" content="{rendition.height}">')
            meta_tags.append(f'<meta property="og:image:alt" content="{seo_image.title or page.get_seo_title()}">')
        except:
            # Fallback to original image URL
            if hasattr(seo_image, 'file') and seo_image.file:
                image_url = request.build_absolute_uri(seo_image.file.url)
                meta_tags.append(f'<meta property="og:image" content="{image_url}">')
    
    # Site name
    if hasattr(page, 'get_site') and page.get_site():
        meta_tags.append(f'<meta property="og:site_name" content="{page.get_site().site_name}">')
    
    # Twitter Card tags
    meta_tags.append(f'<meta name="twitter:card" content="{page.twitter_card_type}">')
    meta_tags.append(f'<meta name="twitter:title" content="{page.get_seo_title()}">')
    meta_tags.append(f'<meta name="twitter:description" content="{page.get_seo_description()}">')
    
    # Twitter image (reuse Open Graph image logic)
    if seo_image and request:
        try:
            if page.twitter_card_type == 'summary_large_image':
                rendition = seo_image.get_rendition('fill-1200x630')
            else:
                rendition = seo_image.get_rendition('fill-400x400')
            
            image_url = request.build_absolute_uri(rendition.url)
            meta_tags.append(f'<meta name="twitter:image" content="{image_url}">')
            meta_tags.append(f'<meta name="twitter:image:alt" content="{seo_image.title or page.get_seo_title()}">')
        except:
            pass
    
    # Add custom meta tags
    if hasattr(page, 'get_custom_meta_tags'):
        custom_meta = page.get_custom_meta_tags()
        for name, content in custom_meta.items():
            meta_tags.append(f'<meta name="{name}" content="{content}">')
    
    # Add custom Open Graph tags
    if hasattr(page, 'get_custom_og_tags'):
        custom_og = page.get_custom_og_tags()
        for property_name, content in custom_og.items():
            meta_tags.append(f'<meta property="{property_name}" content="{content}">')
    
    # Add custom Twitter tags
    if hasattr(page, 'get_custom_twitter_tags'):
        custom_twitter = page.get_custom_twitter_tags()
        for name, content in custom_twitter.items():
            meta_tags.append(f'<meta name="{name}" content="{content}">')
    
    return mark_safe('\n'.join(meta_tags))


@register.simple_tag
def structured_data(page):
    """
    Generate JSON-LD structured data for a page.
    
    Usage:
        {% structured_data page %}
    """
    if not page or not hasattr(page, 'get_structured_data'):
        return ''
    
    data = page.get_structured_data()
    if data:
        return mark_safe(f'<script type="application/ld+json">\n{data}\n</script>')
    
    return ''


@register.simple_tag
def seo_title(page):
    """
    Get the SEO title for a page.
    
    Usage:
        {% seo_title page %}
    """
    if page and hasattr(page, 'get_seo_title'):
        return page.get_seo_title()
    return ''


@register.simple_tag 
def seo_description(page):
    """
    Get the SEO description for a page.
    
    Usage:
        {% seo_description page %}
    """
    if page and hasattr(page, 'get_seo_description'):
        return page.get_seo_description()
    return ''


@register.simple_tag
def canonical_url(page):
    """
    Get the canonical URL for a page.
    
    Usage:
        {% canonical_url page %}
    """
    if page and hasattr(page, 'get_canonical_url'):
        return page.get_canonical_url()
    return ''


@register.filter
def seo_image_url(image, spec='fill-1200x630'):
    """
    Get a resized image URL for SEO purposes.
    
    Usage:
        {{ page.get_seo_image|seo_image_url:"fill-400x400" }}
    """
    if not image:
        return ''
    
    try:
        rendition = image.get_rendition(spec)
        return rendition.url
    except:
        # Fallback to original image
        if hasattr(image, 'file') and image.file:
            return image.file.url
        return ''


@register.inclusion_tag('wagtail_feathers/seo/meta.html', takes_context=True)
def include_seo_meta(context, page=None):
    """
    Include SEO meta tags template with context.
    
    Usage:
        {% include_seo_meta %}
        {% include_seo_meta page %}
    """
    if page is None:
        page = context.get('page')
    
    return {
        'page': page,
        'request': context.get('request'),
    }


@register.inclusion_tag('wagtail_feathers/seo/structured_data.html', takes_context=True)
def include_structured_data(context, page=None):
    """
    Include structured data template with context.
    
    Usage:
        {% include_structured_data %}
        {% include_structured_data page %}
    """
    if page is None:
        page = context.get('page')
    
    return {
        'page': page,
        'request': context.get('request'),
    }