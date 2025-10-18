"""
Utility functions for API serialization.
"""
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def serialize_tags(taggable_obj):
    """
    Serialize tags from a ClusterTaggableManager.
    
    Args:
        taggable_obj: Model instance with tags attribute
        
    Returns:
        List of tag dictionaries with id, name, and slug
    """
    if not hasattr(taggable_obj, 'tags'):
        return []
    
    try:
        return [
            {
                'id': tag.id,
                'name': tag.name,
                'slug': tag.slug
            }
            for tag in taggable_obj.tags.all()
        ]
    except Exception as e:
        logger.warning(f"Error serializing tags: {str(e)}")
        return []


def get_image_url(image, rendition='fill-800x450'):
    """
    Get URL for a Wagtail image with optional rendition.
    
    Args:
        image: Wagtail Image instance or None
        rendition: Rendition spec (e.g., 'fill-800x450', 'width-500')
        
    Returns:
        Dictionary with image URLs and metadata, or None if no image
    """
    if not image:
        return None
    
    try:
        # Get rendition
        rendition_obj = image.get_rendition(rendition)
        
        # Build full URL
        base_url = settings.WAGTAILADMIN_BASE_URL.rstrip('/')
        
        return {
            'url': f"{base_url}{rendition_obj.url}",
            'width': rendition_obj.width,
            'height': rendition_obj.height,
            'alt': image.title,
            'original': {
                'url': f"{base_url}{image.file.url}",
                'width': image.width,
                'height': image.height
            }
        }
    except Exception as e:
        logger.warning(f"Error getting image rendition: {str(e)}")
        # Return original image URL as fallback
        try:
            base_url = settings.WAGTAILADMIN_BASE_URL.rstrip('/')
            return {
                'url': f"{base_url}{image.file.url}",
                'width': image.width,
                'height': image.height,
                'alt': image.title
            }
        except Exception:
            return None


def get_featured_image_url(obj):
    """
    Get featured image URL from object.
    
    Args:
        obj: Model instance with featured_image attribute
        
    Returns:
        Image data dictionary or None
    """
    if not hasattr(obj, 'featured_image') or not obj.featured_image:
        return None
    
    return get_image_url(obj.featured_image, rendition='fill-800x450')


def get_image_renditions(image, renditions=None):
    """
    Get multiple renditions of an image for responsive design.
    
    Args:
        image: Wagtail Image instance
        renditions: Dict of {name: spec} or None for defaults
        
    Returns:
        Dictionary with multiple rendition URLs
    """
    if not image:
        return None
    
    if renditions is None:
        renditions = {
            'thumbnail': 'fill-200x200',
            'small': 'fill-400x300',
            'medium': 'fill-800x450',
            'large': 'width-1200',
        }
    
    result = {
        'alt': image.title,
        'renditions': {}
    }
    
    base_url = settings.WAGTAILADMIN_BASE_URL.rstrip('/')
    
    for name, spec in renditions.items():
        try:
            rendition = image.get_rendition(spec)
            result['renditions'][name] = {
                'url': f"{base_url}{rendition.url}",
                'width': rendition.width,
                'height': rendition.height
            }
        except Exception as e:
            logger.warning(f"Error getting {name} rendition: {str(e)}")
            continue
    
    # Add original
    try:
        result['renditions']['original'] = {
            'url': f"{base_url}{image.file.url}",
            'width': image.width,
            'height': image.height
        }
    except Exception:
        pass
    
    return result if result['renditions'] else None
