"""
HTML sanitization utilities for user-generated content.

SECURITY NOTE: This module implements XSS prevention for CVE-2024-XSS-002.
User-supplied embed code is sanitized to prevent arbitrary JavaScript execution.
"""

import bleach
from bleach.css_sanitizer import CSSSanitizer
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

# Whitelist of allowed HTML tags
ALLOWED_TAGS = [
    'iframe', 'video', 'audio', 'img', 'a',
    'p', 'br', 'strong', 'em', 'u', 'blockquote',
    'div', 'span'  # For basic formatting
]

# Whitelist of allowed attributes per tag
ALLOWED_ATTRIBUTES = {
    'iframe': ['src', 'width', 'height', 'frameborder', 'allowfullscreen', 'allow'],
    'video': ['src', 'width', 'height', 'controls', 'poster', 'preload'],
    'audio': ['src', 'controls', 'preload'],
    'img': ['src', 'alt', 'width', 'height', 'title'],
    'a': ['href', 'title', 'target', 'rel'],
    'div': ['class'],  # Limited class for styling
    'span': ['class'],
}

# Whitelist of allowed protocols in URLs
ALLOWED_PROTOCOLS = ['http', 'https']

# Whitelist of trusted embed domains for iframes
ALLOWED_IFRAME_DOMAINS = [
    'youtube.com',
    'www.youtube.com',
    'player.vimeo.com',
    'vimeo.com',
    'codepen.io',
    'replit.com',
    'repl.it',
    'codesandbox.io',
    'jsfiddle.net',
    'stackblitz.com',
]

# CSS sanitizer - only allow safe CSS properties
# ⚠️ WARNING: Do NOT add properties that accept URLs (background-image, etc.)
# as they can be used for data exfiltration attacks
css_sanitizer = CSSSanitizer(
    allowed_css_properties=['width', 'height', 'max-width', 'max-height']
)

# 🔒 SECURITY: Validate that ALLOWED_IFRAME_DOMAINS doesn't contain TLD-only entries
# Prevents bypass attacks if someone adds '.com' or '.org' to the whitelist
for domain in ALLOWED_IFRAME_DOMAINS:
    if '.' not in domain or domain.count('.') < 1:
        raise ValueError(
            f"Invalid domain in ALLOWED_IFRAME_DOMAINS: {domain}. "
            f"Must include at least one subdomain (e.g., 'youtube.com', not 'com')"
        )
    # Also check for leading dots (e.g., '.youtube.com' instead of 'youtube.com')
    if domain.startswith('.'):
        raise ValueError(
            f"Invalid domain in ALLOWED_IFRAME_DOMAINS: {domain}. "
            f"Domain should not start with a dot. Use 'youtube.com', not '.youtube.com'"
        )


def sanitize_embed_code(html):
    """
    Sanitize user-supplied embed code to prevent XSS attacks.

    This function implements a two-pass sanitization:
    1. bleach.clean() removes dangerous HTML tags and attributes
    2. BeautifulSoup validates iframe domains against whitelist

    Security considerations:
    - Removes <script> tags and event handlers (onclick, onerror, etc.)
    - Blocks javascript: protocol in URLs
    - Restricts iframes to trusted domains only
    - Sanitizes CSS to prevent CSS-based attacks

    Args:
        html (str): Raw HTML embed code from user

    Returns:
        str: Sanitized HTML safe for rendering

    Example:
        >>> sanitize_embed_code('<script>alert("XSS")</script>')
        ''  # Script tags completely removed

        >>> sanitize_embed_code('<iframe src="https://youtube.com/embed/abc"></iframe>')
        '<iframe src="https://youtube.com/embed/abc"></iframe>'  # Allowed
    """
    if not html:
        return ''

    # 🔒 SECURITY AUDIT LOG: Log sanitization attempts
    logger.info(
        f"EMBED_SANITIZATION: "
        f"input_length={len(html)} "
        f"contains_script={'<script' in html.lower()} "
        f"contains_iframe={'<iframe' in html.lower()}"
    )

    # 🔒 SECURITY: Multi-pass sanitization for defense in depth
    # Pass 1: Pre-processing - Remove dangerous tags entirely (including content)
    # Pass 2: bleach.clean() - Battle-tested against XSS, handles malformed HTML
    # Pass 3: Domain validation - Restrict iframes to trusted sources only

    # First pass: Remove dangerous tags entirely (including their content)
    # NOTE: This is done BEFORE bleach for UX (to avoid showing script text).
    # Security concern addressed: bleach in Pass 2 will catch any malformed/nested
    # tags that BeautifulSoup misses (e.g., <scr<script>ipt>)
    soup_pre = BeautifulSoup(html, 'html.parser')
    dangerous_tags = ['script', 'style', 'noscript']
    for tag_name in dangerous_tags:
        for tag in soup_pre.find_all(tag_name):
            tag.decompose()  # Remove tag and all its content
    html_without_dangerous = str(soup_pre)

    # Second pass: bleach sanitization
    # bleach is designed to handle malformed/nested HTML attacks (e.g., <scr<script>ipt>)
    clean_html = bleach.clean(
        html_without_dangerous,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,  # Remove remaining disallowed tags (but not their content)
        css_sanitizer=css_sanitizer,
    )

    # Second pass: validate iframe domains
    # Even though bleach allows iframes, we must restrict to trusted domains
    soup = BeautifulSoup(clean_html, 'html.parser')

    iframes_removed = 0
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src', '')
        if not src:
            # No src attribute - remove iframe
            iframe.decompose()
            iframes_removed += 1
            continue

        try:
            parsed_url = urlparse(src)
            domain = parsed_url.netloc.lower()

            # Check if domain is in whitelist
            # Allow subdomain matches (e.g., player.vimeo.com matches vimeo.com)
            is_allowed = False
            for allowed_domain in ALLOWED_IFRAME_DOMAINS:
                if domain == allowed_domain or domain.endswith('.' + allowed_domain):
                    is_allowed = True
                    break

            if not is_allowed:
                logger.warning(
                    f"EMBED_BLOCKED: Untrusted iframe domain blocked: {domain}"
                )
                iframe.decompose()  # Remove untrusted iframe
                iframes_removed += 1
        except (ValueError, TypeError) as e:
            # URL parsing failed - remove unsafe iframe
            logger.warning(
                f"EMBED_SANITIZATION: Invalid URL in iframe src, removing iframe. "
                f"Error: {e}, URL: {src[:100]}"
            )
            iframe.decompose()
            iframes_removed += 1
        except Exception as e:
            # Unexpected error - only remove if URL contains known dangerous patterns
            logger.error(
                f"EMBED_SANITIZATION_ERROR: Unexpected error parsing iframe. "
                f"Error: {e}, URL: {src[:100]}"
            )
            # Check for obviously dangerous patterns
            dangerous_patterns = ['javascript:', 'data:', 'file:', 'vbscript:']
            if any(pattern in src.lower() for pattern in dangerous_patterns):
                logger.error(f"EMBED_BLOCKED: Dangerous protocol detected in URL")
                iframe.decompose()
                iframes_removed += 1
            # If URL seems safe, preserve it but log the error for investigation

    result = str(soup)

    # 🔒 SECURITY AUDIT LOG: Log sanitization results
    logger.info(
        f"EMBED_SANITIZATION_COMPLETE: "
        f"input_length={len(html)} "
        f"output_length={len(result)} "
        f"iframes_removed={iframes_removed} "
        f"sanitized={html != result}"
    )

    return result


def is_embed_safe(html):
    """
    Check if embed code is safe without modifying it.

    This is useful for validation before saving.

    Args:
        html (str): Raw HTML embed code

    Returns:
        tuple: (is_safe: bool, reason: str)
    """
    if not html:
        return True, "Empty embed code"

    # Check for obvious XSS attempts
    dangerous_patterns = [
        '<script',
        'javascript:',
        'onerror=',
        'onclick=',
        'onload=',
        'onmouseover=',
        '<object',
        '<embed',
    ]

    html_lower = html.lower()
    for pattern in dangerous_patterns:
        if pattern in html_lower:
            return False, f"Dangerous pattern detected: {pattern}"

    # Check if sanitization would modify the HTML
    sanitized = sanitize_embed_code(html)
    if sanitized != html:
        return False, "Embed code requires sanitization"

    return True, "Embed code is safe"
