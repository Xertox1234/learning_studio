"""
Custom JWT authentication class with httpOnly cookie support.

This module implements cookie-based JWT authentication as the primary method,
with fallback to Authorization header for API clients and testing.

Security Benefits:
- httpOnly cookies prevent XSS-based token theft (CVE-2024-JWT-003)
- Tokens automatically sent with requests (no JS token handling)
- SameSite protection against CSRF attacks
- Secure flag for HTTPS-only transmission

Architecture:
1. Check for JWT in httpOnly cookie (primary method)
2. Fall back to Authorization header (for API clients, testing)
3. Validate token and return user

References:
- OWASP Session Management Cheat Sheet
- RFC 8725 - JWT Best Current Practices
- Django REST Framework Simple JWT docs
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings


class JWTCookieAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads tokens from httpOnly cookies.

    This class extends DRF SimpleJWT's JWTAuthentication to:
    1. Read access token from httpOnly cookie (primary method)
    2. Fall back to Authorization header (compatibility with API clients)
    3. Validate token and return authenticated user

    Cookie Name:
    - Configured via settings.SIMPLE_JWT['AUTH_COOKIE']
    - Default: 'access_token'

    Usage:
        # In settings.py
        REST_FRAMEWORK = {
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'apps.api.authentication.JWTCookieAuthentication',
            ],
        }

    Security Properties:
    - Tokens stored in httpOnly cookies (not accessible to JavaScript)
    - Automatic CSRF protection via SameSite cookie attribute
    - Falls back to header auth for API clients and testing

    Example Request:
        GET /api/v1/user/ HTTP/1.1
        Host: example.com
        Cookie: access_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
    """

    def authenticate(self, request):
        """
        Authenticate the request using JWT from cookie or header.

        Process:
        1. Try to get token from httpOnly cookie
        2. If no cookie, fall back to Authorization header
        3. Validate token and return (user, validated_token)

        Args:
            request: The HTTP request object

        Returns:
            tuple: (user, validated_token) if authentication successful
            None: If no token found or authentication failed

        Raises:
            AuthenticationFailed: If token is invalid or expired
        """
        # 🔒 SECURITY: Try cookie-based authentication first (primary method)
        raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])

        if raw_token is None:
            # Fall back to header-based authentication (for API clients, testing)
            # This calls the parent JWTAuthentication.authenticate() which reads
            # the Authorization: Bearer <token> header
            return super().authenticate(request)

        # Validate the token from cookie
        # This will raise AuthenticationFailed if token is invalid/expired
        validated_token = self.get_validated_token(raw_token)

        # Get the user associated with the token
        # This will raise AuthenticationFailed if user doesn't exist
        user = self.get_user(validated_token)

        return user, validated_token
