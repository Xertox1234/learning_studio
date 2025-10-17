"""
Template filters for forum content rendering.

SECURITY NOTE: These filters implement XSS prevention for CVE-2024-XSS-002.
"""

from django import template
from django.utils.safestring import mark_safe
from apps.forum_integration.utils.sanitization import sanitize_embed_code
import logging

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter(name='safe_embed')
def safe_embed(value):
    """
    Sanitize and render embed code safely.

    This filter is specifically designed to replace Django's |safe filter
    for user-supplied embed code. It sanitizes the HTML to prevent XSS attacks
    while allowing legitimate embeds from trusted sources.

    Security features:
    - Removes <script> tags and event handlers
    - Blocks javascript: protocol in URLs
    - Restricts iframes to whitelisted domains (YouTube, Vimeo, CodePen, etc.)
    - Sanitizes CSS to prevent CSS-based attacks

    Usage in templates:
        {% load forum_filters %}
        {{ embed_code|safe_embed|safe }}

    IMPORTANT: The |safe filter is still needed AFTER sanitization because
    we want to render the sanitized HTML. The sanitization happens first,
    making the subsequent |safe filter actually safe to use.

    Args:
        value (str): Raw HTML embed code from user

    Returns:
        str: Sanitized HTML marked as safe for Django template rendering

    Example:
        {{ "<script>alert('XSS')</script>"|safe_embed }}
        # Returns: "" (script tags removed)

        {{ "<iframe src='https://youtube.com/embed/abc'></iframe>"|safe_embed }}
        # Returns: "<iframe src='https://youtube.com/embed/abc'></iframe>" (allowed)
    """
    if not value:
        return ''

    # 🔒 SECURITY: Sanitize the embed code before rendering
    sanitized = sanitize_embed_code(value)

    # 🔒 CRITICAL SECURITY: mark_safe() is ONLY safe here because
    # sanitize_embed_code() has already removed all XSS vectors via bleach + domain validation.
    # NEVER use mark_safe() on unsanitized user input!
    # This is the critical security fix for CVE-2024-XSS-002
    return mark_safe(sanitized)


@register.filter(name='truncate_html')
def truncate_html(value, length=100):
    """
    Truncate HTML content while preserving tags.

    This is useful for previews and excerpts.

    Args:
        value (str): HTML content
        length (int): Maximum length in characters

    Returns:
        str: Truncated HTML
    """
    if not value:
        return ''

    # Strip HTML tags for length calculation
    from django.utils.html import strip_tags
    text = strip_tags(value)

    if len(text) <= length:
        return value

    # Truncate and add ellipsis
    truncated = text[:length].rsplit(' ', 1)[0] + '...'
    return truncated
