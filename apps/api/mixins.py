"""
Common mixins and utilities for API views.
"""

from django.conf import settings
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.response import Response


def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_or_ip(request):
    """Get user ID if authenticated, otherwise use IP address for rate limiting."""
    if request.user.is_authenticated:
        return f"user_{request.user.id}"
    return f"ip_{get_client_ip(request)}"


class RateLimitMixin:
    """
    Mixin to add rate limiting to ViewSets.
    Apply different rate limits based on action type.
    """
    
    @method_decorator(ratelimit(
        key=get_user_or_ip, 
        rate=settings.RATE_LIMIT_SETTINGS['API_CALLS'], 
        method=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], 
        block=True
    ))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


def ratelimited(request, exception):
    """
    Custom view for handling rate limit exceeded responses.
    Returns a user-friendly error message and appropriate HTTP status.
    """
    return Response({
        'error': 'Rate limit exceeded',
        'message': 'You have made too many requests. Please wait before trying again.',
        'retry_after': '60 seconds'
    }, status=status.HTTP_429_TOO_MANY_REQUESTS)