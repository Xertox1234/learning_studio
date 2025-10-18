"""
Throttle classes for API rate limiting.

Provides specialized throttling for resource-intensive operations
like file uploads to prevent abuse and ensure fair usage.
"""

from rest_framework.throttling import UserRateThrottle


class FileUploadThrottle(UserRateThrottle):
    """
    Throttle for file upload endpoints.

    Restricts authenticated users to 10 file uploads per minute
    to prevent abuse, DoS attacks, and excessive storage consumption.

    **Security Benefits:**
    - Prevents rapid-fire upload attempts (brute force)
    - Limits storage consumption from malicious users
    - Reduces server load from file processing
    - Mitigates DoS attacks via upload endpoints

    **Usage:**
        class MyViewSet(viewsets.ModelViewSet):
            throttle_classes = [FileUploadThrottle]

            # Or for specific actions:
            @action(detail=False, methods=['post'],
                   throttle_classes=[FileUploadThrottle])
            def upload_file(self, request):
                pass

    **Configuration:**
    Set in REST_FRAMEWORK settings:
        'DEFAULT_THROTTLE_RATES': {
            'file_upload': '10/minute',  # Configurable rate
        }

    **References:**
    - CWE-400: Uncontrolled Resource Consumption
    - OWASP: https://owasp.org/www-community/attacks/Denial_of_Service
    """
    scope = 'file_upload'

    def get_cache_key(self, request, view):
        """
        Generate cache key for throttling.

        Uses user ID for authenticated users, IP for anonymous
        (though file uploads should require authentication).
        """
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
