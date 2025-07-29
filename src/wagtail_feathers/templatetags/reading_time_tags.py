"""
Template tags for reading time functionality in Wagtail Feathers.

Provides easy-to-use template tags for displaying reading time
in various formats across templates.
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def reading_time(page, format_type="default"):
    """
    Display reading time for a page.
    
    Usage:
        {% reading_time page %}
        {% reading_time page "short" %}
        {% reading_time page "long" %}
    
    Args:
        page: Page object with ReadingTimeMixin
        format_type: Display format ("default", "short", "long", "seo")
    
    Returns:
        str: Formatted reading time or empty string
    """
    if not page or not hasattr(page, 'reading_time_minutes'):
        return ""
    
    if not hasattr(page, 'get_reading_time_display'):
        return ""
    
    return page.get_reading_time_display(format_type)


@register.simple_tag
def reading_time_minutes(page):
    """
    Get raw reading time in minutes.
    
    Usage:
        {% reading_time_minutes page %}
    
    Returns:
        int: Reading time in minutes or None
    """
    if not page or not hasattr(page, 'reading_time_minutes'):
        return None
    
    return page.reading_time_minutes


@register.simple_tag
def word_count(page):
    """
    Get word count for a page.
    
    Usage:
        {% word_count page %}
    
    Returns:
        int: Total word count or 0
    """
    if not page or not hasattr(page, 'get_word_count'):
        return 0
    
    return page.get_word_count()


@register.inclusion_tag('wagtail_feathers/tags/reading_time_display.html')
def reading_time_badge(page, show_icon=True, css_class="reading-time-badge"):
    """
    Render a reading time badge with icon.
    
    Usage:
        {% reading_time_badge page %}
        {% reading_time_badge page show_icon=False %}
        {% reading_time_badge page css_class="custom-class" %}
    
    Args:
        page: Page object with ReadingTimeMixin
        show_icon: Whether to show clock icon
        css_class: CSS class for styling
    
    Returns:
        dict: Context for template rendering
    """
    return {
        'page': page,
        'reading_time': reading_time(page),
        'reading_time_minutes': reading_time_minutes(page),
        'show_icon': show_icon,
        'css_class': css_class,
    }


@register.filter
def has_reading_time(page):
    """
    Check if page has reading time calculated.
    
    Usage:
        {% if page|has_reading_time %}
            {% reading_time page %}
        {% endif %}
    
    Returns:
        bool: True if page has reading time
    """
    return (
        page and 
        hasattr(page, 'reading_time_minutes') and 
        page.reading_time_minutes and 
        page.reading_time_minutes > 0
    )


@register.filter
def reading_time_threshold(page, min_minutes=2):
    """
    Check if reading time meets minimum threshold.
    
    Usage:
        {% if page|reading_time_threshold:3 %}
            Long read: {% reading_time page %}
        {% endif %}
    
    Args:
        page: Page object
        min_minutes: Minimum minutes threshold
    
    Returns:
        bool: True if reading time >= threshold
    """
    if not has_reading_time(page):
        return False
    
    try:
        min_minutes = int(min_minutes)
    except (ValueError, TypeError):
        min_minutes = 2
    
    return page.reading_time_minutes >= min_minutes


@register.simple_tag
def reading_speed_info(page):
    """
    Get reading speed information for a page.
    
    Usage:
        {% reading_speed_info page %}
    
    Returns:
        dict: Reading speed information
    """
    if not page or not hasattr(page, 'words_per_minute'):
        return {}
    
    word_count_val = word_count(page)
    reading_time_val = reading_time_minutes(page)
    
    return {
        'words_per_minute': getattr(page, 'words_per_minute', 200),
        'word_count': word_count_val,
        'reading_time_minutes': reading_time_val,
        'auto_calculate': getattr(page, 'auto_calculate_reading_time', True),
    }


@register.simple_tag(takes_context=True)
def reading_time_schema(context, page):
    """
    Generate structured data for reading time.
    
    Usage:
        {% reading_time_schema page %}
    
    Returns:
        str: JSON-LD structured data or empty string
    """
    if not page or not hasattr(page, 'get_reading_time_for_seo'):
        return ""
    
    seo_data = page.get_reading_time_for_seo()
    if not seo_data:
        return ""
    
    # This would typically be integrated into the main structured data
    # but can be used standalone if needed
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "timeRequired": seo_data.get('duration_iso', ''),
    }
    
    import json
    return mark_safe(f'<script type="application/ld+json">{json.dumps(schema)}</script>')


@register.simple_tag
def reading_time_comparison(pages):
    """
    Compare reading times across multiple pages.
    
    Usage:
        {% reading_time_comparison page_list %}
    
    Returns:
        dict: Reading time statistics
    """
    if not pages:
        return {}
    
    reading_times = []
    for page in pages:
        if has_reading_time(page):
            reading_times.append(page.reading_time_minutes)
    
    if not reading_times:
        return {}
    
    return {
        'min_time': min(reading_times),
        'max_time': max(reading_times),
        'avg_time': round(sum(reading_times) / len(reading_times), 1),
        'total_pages': len(reading_times),
    }