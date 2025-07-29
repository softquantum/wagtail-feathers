import random
from django import template
from wagtail.images import get_image_model
from wagtail.models import Collection

register = template.Library()

@register.simple_tag(takes_context=True)
def get_placeholder_image(context):
    """Get a random image from the Placeholders collection with request-level caching."""
    ImageModel = get_image_model()
    request = context.get('request')
    if not request:
        # Fallback to non-cached version if no request context
        try:
            placeholders_collection = Collection.objects.get(name="Placeholders")
            placeholder_images = ImageModel.objects.filter(
                collection=placeholders_collection
            )
            if placeholder_images.exists():
                image_ids = list(placeholder_images.values_list('id', flat=True))
                random_id = random.choice(image_ids)
                return ImageModel.objects.get(id=random_id)
            return None
        except Collection.DoesNotExist:
            return None
    
    # Check if placeholder image is already cached in the request
    cache_key = '_placeholder_image_cache'
    if hasattr(request, cache_key):
        return getattr(request, cache_key)
    
    # Get placeholder image and cache it
    placeholder_image = None
    try:
        placeholders_collection = Collection.objects.get(name="Placeholders")
        placeholder_images = ImageModel.objects.filter(
            collection=placeholders_collection
        )
        if placeholder_images.exists():
            # Get all placeholder images and select one randomly
            image_ids = list(placeholder_images.values_list('id', flat=True))
            random_id = random.choice(image_ids)
            placeholder_image = ImageModel.objects.get(id=random_id)
    except Collection.DoesNotExist:
        placeholder_image = None
    
    # Cache the result in the request object
    setattr(request, cache_key, placeholder_image)
    return placeholder_image