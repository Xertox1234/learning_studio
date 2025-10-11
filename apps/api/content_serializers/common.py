from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.conf import settings
from django.http import HttpRequest

import bleach

try:
    from wagtail.images.models import Image
except Exception:  # pragma: no cover - allow imports to resolve in docs/static checks
    Image = None  # type: ignore


# Editor-safe RichText sanitization (CodeMirror-friendly)
ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    'p', 'br', 'pre', 'code', 'blockquote', 'hr',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'strong', 'em', 'span', 'img', 'iframe',
]

ALLOWED_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    'a': ['href', 'title', 'rel', 'target'],
    'span': ['class'],
    'p': ['class'],
    'code': ['class'],
    'pre': ['class'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    # Allow safe iframes (actual origin restrictions are enforced by CSP)
    'iframe': ['src', 'width', 'height', 'allow', 'allowfullscreen', 'frameborder'],
}

ALLOWED_PROTOCOLS = list(bleach.sanitizer.ALLOWED_PROTOCOLS) + ['data']


def sanitize_rich_text(html: Optional[str]) -> str:
    """Sanitize RichText/HTML using a safe allowlist. Keeps code/pre tags.
    Do NOT use this for code-bearing fields or templates.
    """
    if not html:
        return ''
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=False,
    )


def absolute_media_url(request: HttpRequest, url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    # Build absolute URL for frontend clients and CDNs
    try:
        return request.build_absolute_uri(url)
    except Exception:
        return url


def serialize_image(image: Any, request: HttpRequest) -> Optional[Dict[str, Any]]:
    """Return image info with standard renditions and absolute URLs.
    Safe to call with None.
    """
    if not image:
        return None
    try:
        # Standard renditions
        rendition_specs = {
            'thumb': 'fill-400x300',
            'medium': 'fill-800x600',
            'large': 'fill-1600x900',
        }
        renditions: Dict[str, Dict[str, Any]] = {}
        for key, spec in rendition_specs.items():
            try:
                r = image.get_rendition(spec)
                renditions[key] = {
                    'url': absolute_media_url(request, r.url),
                    'width': getattr(r, 'width', None),
                    'height': getattr(r, 'height', None),
                }
            except Exception:
                continue
        return {
            'id': getattr(image, 'id', None),
            'title': getattr(image, 'title', ''),
            'original': absolute_media_url(request, getattr(image, 'file', None).url if getattr(image, 'file', None) else None),
            'renditions': renditions,
        }
    except Exception:
        return None
