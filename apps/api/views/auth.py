"""
Custom JWT authentication views with httpOnly cookie support.

This module implements secure cookie-based JWT authentication to prevent
XSS-based token theft (CVE-2024-JWT-003).

Key Security Features:
- Tokens stored in httpOnly cookies (not accessible to JavaScript)
- SameSite cookie protection against CSRF attacks
- Secure flag for HTTPS-only transmission in production
- Tokens removed from response body (not exposed)
- Automatic cookie expiration matching token lifetime

References:
- OWASP Session Management Cheat Sheet
- RFC 8725 - JWT Best Current Practices
- todos/003-move-jwt-to-httponly-cookies.md
"""

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.contrib.auth import authenticate


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer that accepts email instead of username.

    The default TokenObtainPairSerializer expects 'username' field,
    but our application uses email for authentication. This serializer
    accepts 'email' and maps it to the username field for authentication.
    """

    username_field = 'email'

    def validate(self, attrs):
        """
        Validate and authenticate user with email.

        Args:
            attrs: Dictionary with 'email' and 'password'

        Returns:
            Dictionary with 'access' and 'refresh' tokens

        Raises:
            AuthenticationFailed: If credentials are invalid
        """
        # Map email to username for parent class
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Use Django's authenticate which handles email-based auth
            user = authenticate(
                request=self.context.get('request'),
                username=email,  # Our User model uses email as username
                password=password
            )

            if user:
                # Create tokens for authenticated user
                refresh = self.get_token(user)

                data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }

                return data

        # If authentication fails, call parent for proper error handling
        return super().validate(attrs)


class CookieTokenObtainPairView(TokenObtainPairView):
    """
    JWT token obtain view that sets httpOnly cookies.

    This view extends the standard TokenObtainPairView to:
    1. Accept email instead of username for authentication
    2. Set access and refresh tokens in httpOnly cookies
    3. Remove tokens from response body (security best practice)
    4. Apply cookie security settings from Django settings

    Security Properties:
    - httpOnly: Prevents JavaScript access (XSS protection)
    - Secure: HTTPS-only in production
    - SameSite: CSRF protection
    - Path: Cookie scope restriction
    """

    serializer_class = EmailTokenObtainPairSerializer

    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')

            if access_token:
                # Set access token cookie
                response.set_cookie(
                    key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                    value=access_token,
                    max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                    path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
                )

            if refresh_token:
                # Set refresh token cookie
                response.set_cookie(
                    key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                    value=refresh_token,
                    max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                    path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
                )

            # 🔒 SECURITY: Remove tokens from response body
            # Tokens should only exist in httpOnly cookies, not in JSON response
            if 'access' in response.data:
                del response.data['access']
            if 'refresh' in response.data:
                del response.data['refresh']

            # Add user data to response (for frontend)
            # Get user from the access token instead of request.user
            # (request.user is AnonymousUser before login completes)
            if access_token:
                from rest_framework_simplejwt.tokens import AccessToken
                try:
                    token = AccessToken(access_token)
                    user_id = token.get('user_id')
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    user = User.objects.get(id=user_id)
                    user_data = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                    }
                    response.data['user'] = user_data
                    response.data['success'] = True
                except (Exception,):
                    pass  # If we can't get user, just return without user data

        return super().finalize_response(request, response, *args, **kwargs)


class CookieTokenRefreshView(TokenRefreshView):
    """
    JWT token refresh view that sets httpOnly cookie for new access token.

    This view extends the standard TokenRefreshView to:
    1. Read refresh token from httpOnly cookie
    2. Set new access token in httpOnly cookie
    3. Remove new access token from response body

    The refresh token remains in its cookie and is rotated if
    ROTATE_REFRESH_TOKENS is enabled in settings.
    """

    def post(self, request, *args, **kwargs):
        """
        Override post to inject refresh token from cookie into request data.

        The TokenRefreshView expects 'refresh' in request.data, but we
        store it in an httpOnly cookie. This method reads the cookie
        and injects it into request.data before calling the parent.
        """
        # Read refresh token from httpOnly cookie
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])

        if refresh_token:
            # Inject refresh token into request data for parent class
            # We need to make request.data mutable
            if hasattr(request.data, '_mutable'):
                request.data._mutable = True
            request.data['refresh'] = refresh_token
            if hasattr(request.data, '_mutable'):
                request.data._mutable = False

        return super().post(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')  # May be present if rotation enabled

            if access_token:
                # Set new access token cookie
                response.set_cookie(
                    key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                    value=access_token,
                    max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                    path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
                )

            # If token rotation is enabled, update the refresh token cookie
            if refresh_token:
                response.set_cookie(
                    key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                    value=refresh_token,
                    max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                    path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
                )

            # 🔒 SECURITY: Remove tokens from response body
            if 'access' in response.data:
                del response.data['access']
            if 'refresh' in response.data:
                del response.data['refresh']

        return super().finalize_response(request, response, *args, **kwargs)


class LogoutView(APIView):
    """
    Logout endpoint that clears JWT cookies.

    This view handles logout by:
    1. Deleting both access and refresh token cookies
    2. Setting cookie values to empty string
    3. Setting max_age to 0 (immediate expiration)

    Note: This is a client-side logout. For server-side token revocation,
    enable token blacklisting in SIMPLE_JWT settings.
    """

    def post(self, request):
        response = Response(
            {'detail': 'Successfully logged out'},
            status=status.HTTP_200_OK
        )

        # Delete access token cookie
        response.delete_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE'],
            path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
        )

        # Delete refresh token cookie
        response.delete_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
            path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
        )

        return response
