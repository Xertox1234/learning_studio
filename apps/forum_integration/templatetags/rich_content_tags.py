from django import template
from django.utils.safestring import mark_safe
from ..models import RichForumPost

register = template.Library()


@register.simple_tag
def render_post_content(post):
    """
    Render post content, checking for rich content first, then falling back to simple content.
    """
    try:
        rich_post = post.rich_content
        if rich_post.has_content:
            # Render the StreamField content
            return mark_safe(rich_post.render_content())
    except RichForumPost.DoesNotExist:
        pass
    
    # Fall back to simple content
    return mark_safe(post.content.replace('\n', '<br>') if post.content else '')


@register.filter
def has_rich_content(post):
    """
    Check if a post has rich content.
    """
    try:
        return post.rich_content.has_content
    except RichForumPost.DoesNotExist:
        return False


@register.simple_tag
def get_content_type(post):
    """
    Get the content type for a post (rich or simple).
    """
    try:
        if post.rich_content.has_content:
            return 'rich'
    except RichForumPost.DoesNotExist:
        pass
    return 'simple'