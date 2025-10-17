"""
Tests for cookie-based JWT authentication (CVE-2024-JWT-003).

This test module verifies that JWT tokens are properly stored in httpOnly cookies
and that authentication works correctly without exposing tokens to JavaScript.

Security Requirements Tested:
- Tokens stored in httpOnly cookies (not localStorage)
- Tokens not exposed in response body
- Cookie security flags set correctly (httpOnly, Secure, SameSite)
- Token refresh works from cookies
- Logout properly clears cookies
- Authentication works with cookies

References:
- CVE-2024-JWT-003
- todos/003-move-jwt-to-httponly-cookies.md
- OWASP Session Management Cheat Sheet
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
import json

User = get_user_model()


class CookieAuthenticationTests(TestCase):
    """
    Test suite for cookie-based JWT authentication.
    """

    def setUp(self):
        """Set up test client and test user."""
        self.client = APIClient()
        self.email = 'test@example.com'
        self.password = 'testpass123'
        self.username = 'testuser'

        # Create test user
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password
        )

    def test_login_sets_httponly_cookies(self):
        """
        🔒 SECURITY TEST: Ensure login sets httpOnly cookies.

        Verifies that:
        - Login returns 200 OK
        - access_token cookie is set
        - refresh_token cookie is set
        - Both cookies have httponly=True flag
        """
        response = self.client.post('/api/v1/auth/login/', {
            'email': self.email,
            'password': self.password,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check cookies are set
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

        # Check httpOnly flag (security critical)
        access_cookie = response.cookies['access_token']
        refresh_cookie = response.cookies['refresh_token']

        self.assertTrue(access_cookie['httponly'], "Access token must be httpOnly")
        self.assertTrue(refresh_cookie['httponly'], "Refresh token must be httpOnly")

    def test_login_tokens_not_in_response_body(self):
        """
        🔒 SECURITY TEST: Ensure tokens are not exposed in response body.

        Verifies that:
        - Tokens are NOT in JSON response (only in cookies)
        - Response contains user data
        """
        response = self.client.post('/api/v1/auth/login/', {
            'email': self.email,
            'password': self.password,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        # 🔒 SECURITY: Tokens should NOT be in response body
        self.assertNotIn('access', data)
        self.assertNotIn('refresh', data)
        self.assertNotIn('token', data)

        # Should contain user data
        self.assertIn('user', data)

    def test_login_cookie_security_flags(self):
        """
        🔒 SECURITY TEST: Verify cookie security flags.

        Verifies that:
        - SameSite is set to 'Lax' (CSRF protection)
        - Secure flag matches DEBUG setting
        - Path is set to '/'
        """
        response = self.client.post('/api/v1/auth/login/', {
            'email': self.email,
            'password': self.password,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        access_cookie = response.cookies['access_token']
        refresh_cookie = response.cookies['refresh_token']

        # Check SameSite (CSRF protection)
        self.assertEqual(access_cookie['samesite'], 'Lax')
        self.assertEqual(refresh_cookie['samesite'], 'Lax')

        # Check Secure flag (HTTPS only in production)
        # Note: In test environment, secure flag may be empty string instead of False
        expected_secure = not settings.DEBUG
        access_secure = access_cookie.get('secure', False)
        refresh_secure = refresh_cookie.get('secure', False)

        # Handle both False and empty string as equivalent to False in tests
        if expected_secure:
            self.assertTrue(access_secure, "Access cookie should be secure in production")
            self.assertTrue(refresh_secure, "Refresh cookie should be secure in production")
        else:
            # In development, secure can be False or empty string
            self.assertIn(access_secure, [False, ''], "Access cookie should not be secure in development")
            self.assertIn(refresh_secure, [False, ''], "Refresh cookie should not be secure in development")

        # Check path
        self.assertEqual(access_cookie['path'], '/')
        self.assertEqual(refresh_cookie['path'], '/')

    def test_authenticated_request_with_cookie(self):
        """
        🔒 SECURITY TEST: Ensure cookie-based authentication works.

        Verifies that:
        - Login sets cookies
        - Subsequent request with cookies is authenticated
        - User endpoint returns correct user data
        """
        # Login to get cookies
        login_response = self.client.post('/api/v1/auth/login/', {
            'email': self.email,
            'password': self.password,
        })

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Extract cookies from login response
        access_token = login_response.cookies.get('access_token').value

        # Make authenticated request (cookies sent automatically by test client)
        user_response = self.client.get(
            '/api/v1/auth/user/',
            HTTP_COOKIE=f'access_token={access_token}'
        )

        self.assertEqual(user_response.status_code, status.HTTP_200_OK)
        data = user_response.json()
        self.assertTrue(data.get('authenticated'))
        self.assertEqual(data['user']['email'], self.email)

    def test_register_sets_httponly_cookies(self):
        """
        🔒 SECURITY TEST: Ensure registration sets httpOnly cookies.

        Verifies that:
        - Registration returns 200 OK
        - Cookies are set with httpOnly flag
        - Tokens not in response body
        """
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
        }, format='json')

        # If registration fails, print the error for debugging
        if response.status_code != status.HTTP_200_OK:
            print(f"Registration failed with status {response.status_code}: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check cookies are set
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

        # Check httpOnly flag
        self.assertTrue(response.cookies['access_token']['httponly'])
        self.assertTrue(response.cookies['refresh_token']['httponly'])

        # Check tokens not in body
        data = response.json()
        self.assertNotIn('access', data)
        self.assertNotIn('refresh', data)
        self.assertNotIn('token', data)

    def test_logout_deletes_cookies(self):
        """
        🔒 SECURITY TEST: Ensure logout removes cookies.

        Verifies that:
        - Login sets cookies
        - Logout endpoint clears cookies
        - Cookie values are set to empty string
        """
        # Login first
        login_response = self.client.post('/api/v1/auth/login/', {
            'email': self.email,
            'password': self.password,
        })

        access_token = login_response.cookies.get('access_token').value

        # Logout
        logout_response = self.client.post(
            '/api/v1/auth/logout/',
            HTTP_COOKIE=f'access_token={access_token}'
        )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # Check cookies are deleted (set to empty string with max_age=0)
        self.assertEqual(logout_response.cookies['access_token'].value, '')
        self.assertEqual(logout_response.cookies['refresh_token'].value, '')

    def test_token_refresh_from_cookie(self):
        """
        🔒 SECURITY TEST: Ensure token refresh works from cookies.

        Verifies that:
        - Login sets refresh token cookie
        - Refresh endpoint reads from cookie (not request body)
        - New access token is set in cookie
        - Tokens not in response body
        """
        # Login to get cookies
        login_response = self.client.post('/api/v1/auth/login/', {
            'email': self.email,
            'password': self.password,
        })

        refresh_token = login_response.cookies.get('refresh_token').value

        # Refresh token (send refresh token in cookie)
        refresh_response = self.client.post(
            '/api/v1/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={refresh_token}'
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)

        # Check new access token is set in cookie
        self.assertIn('access_token', refresh_response.cookies)

        # Check tokens not in response body
        data = refresh_response.json()
        self.assertNotIn('access', data)
        self.assertNotIn('refresh', data)

    def test_invalid_credentials(self):
        """Test that invalid credentials are rejected."""
        response = self.client.post('/api/v1/auth/login/', {
            'email': self.email,
            'password': 'wrongpassword',
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access_token', response.cookies)

    def test_authentication_without_cookie_fails(self):
        """
        Test that protected endpoints require authentication cookie.

        Verifies that:
        - Request without cookie is rejected
        - Returns 401 Unauthorized
        """
        response = self.client.get('/api/v1/auth/user/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cookie_expiration_time(self):
        """
        Test that cookie expiration times match token lifetimes.

        Verifies that:
        - Access token cookie max_age matches ACCESS_TOKEN_LIFETIME
        - Refresh token cookie max_age matches REFRESH_TOKEN_LIFETIME
        """
        response = self.client.post('/api/v1/auth/login/', {
            'email': self.email,
            'password': self.password,
        })

        access_cookie = response.cookies['access_token']
        refresh_cookie = response.cookies['refresh_token']

        expected_access_max_age = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
        expected_refresh_max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())

        self.assertEqual(access_cookie['max-age'], expected_access_max_age)
        self.assertEqual(refresh_cookie['max-age'], expected_refresh_max_age)


class CookieAuthenticationIntegrationTests(TestCase):
    """
    Integration tests for complete authentication flows.
    """

    def setUp(self):
        """Set up test client and test user."""
        self.client = APIClient()
        self.email = 'test@example.com'
        self.password = 'testpass123'

        self.user = User.objects.create_user(
            username='testuser',
            email=self.email,
            password=self.password
        )

    def test_complete_auth_flow(self):
        """
        Test complete authentication flow: login → authenticated request → logout.

        Verifies that:
        - Login works and sets cookies
        - Authenticated request succeeds
        - Logout clears cookies
        - Request after logout fails
        """
        # Step 1: Login
        login_response = self.client.post('/api/v1/auth/login/', {
            'email': self.email,
            'password': self.password,
        })

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.cookies.get('access_token').value

        # Step 2: Make authenticated request
        user_response = self.client.get(
            '/api/v1/auth/user/',
            HTTP_COOKIE=f'access_token={access_token}'
        )

        self.assertEqual(user_response.status_code, status.HTTP_200_OK)

        # Step 3: Logout
        logout_response = self.client.post(
            '/api/v1/auth/logout/',
            HTTP_COOKIE=f'access_token={access_token}'
        )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # Step 4: Try authenticated request after logout (should fail)
        after_logout_response = self.client.get('/api/v1/auth/user/')

        self.assertEqual(after_logout_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_and_authenticate_flow(self):
        """
        Test registration and immediate authentication.

        Verifies that:
        - Registration succeeds and sets cookies
        - Can immediately access protected endpoints
        """
        # Register new user
        register_response = self.client.post('/api/v1/auth/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
        })

        self.assertEqual(register_response.status_code, status.HTTP_200_OK)
        access_token = register_response.cookies.get('access_token').value

        # Immediately access protected endpoint
        user_response = self.client.get(
            '/api/v1/auth/user/',
            HTTP_COOKIE=f'access_token={access_token}'
        )

        self.assertEqual(user_response.status_code, status.HTTP_200_OK)
        data = user_response.json()
        self.assertEqual(data['user']['email'], 'new@example.com')
