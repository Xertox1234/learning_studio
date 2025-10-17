# Move JWT Tokens to httpOnly Cookies

**Priority**: 🔴 P1 - CRITICAL
**Category**: Security
**Effort**: 8-12 hours
**Deadline**: Within 1 week

## Problem

Authentication and refresh tokens are stored in localStorage, making them accessible to any JavaScript code including XSS payloads. This creates a critical vulnerability where any XSS attack results in full account takeover.

## Location

`frontend/src/contexts/AuthContext.jsx:49,106,126`

## Current Code

```javascript
// Line 49
localStorage.setItem('authToken', newToken)
// Line 108
localStorage.setItem('refreshToken', refresh)
```

## Impact

- Any XSS vulnerability becomes full account takeover
- Tokens accessible to malicious browser extensions
- Tokens persist across browser sessions indefinitely
- No automatic expiration on browser close
- Vulnerable to malicious scripts on any page

## Solution

Switch to httpOnly cookies for token storage, which are:
- Not accessible to JavaScript (XSS-proof)
- Automatically sent with requests
- Can be configured to expire on browser close
- Support SameSite protection against CSRF

## Implementation Steps

### Step 1: Install django-cors-headers (if not already)

```bash
pip install django-cors-headers
```

### Step 2: Configure Django JWT to use cookies

```python
# learning_community/settings/base.py
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # Cookie-based token storage
    'AUTH_COOKIE': 'access_token',
    'AUTH_COOKIE_REFRESH': 'refresh_token',
    'AUTH_COOKIE_SECURE': True,  # HTTPS only in production
    'AUTH_COOKIE_HTTP_ONLY': True,  # Not accessible to JavaScript
    'AUTH_COOKIE_SAMESITE': 'Lax',  # CSRF protection
    'AUTH_COOKIE_PATH': '/',
    'AUTH_COOKIE_DOMAIN': None,  # Same domain only

    # Rotation settings
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,

    # Algorithm
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# For development (use False, for production use True)
SIMPLE_JWT['AUTH_COOKIE_SECURE'] = not DEBUG

# CORS configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://yourdomain.com",
]

CORS_ALLOW_CREDENTIALS = True  # Required for cookies

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://yourdomain.com",
]

# Session cookie settings (for CSRF)
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False  # CSRF token needs to be read by JS
```

### Step 3: Update JWT views to set cookies

```python
# apps/api/views/auth.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings

class CookieTokenObtainPairView(TokenObtainPairView):
    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')

            # Set access token cookie
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=access_token,
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
            )

            # Set refresh token cookie
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                value=refresh_token,
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
            )

            # Remove tokens from response body
            del response.data['access']
            del response.data['refresh']

        return super().finalize_response(request, response, *args, **kwargs)

class CookieTokenRefreshView(TokenRefreshView):
    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 200:
            access_token = response.data.get('access')

            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=access_token,
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
            )

            del response.data['access']

        return super().finalize_response(request, response, *args, **kwargs)
```

### Step 4: Create custom JWT authentication class

```python
# apps/api/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings

class JWTCookieAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Try to get token from cookie first
        raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])

        if raw_token is None:
            # Fall back to header (for API clients)
            return super().authenticate(request)

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
```

### Step 5: Update DRF settings

```python
# learning_community/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.api.authentication.JWTCookieAuthentication',  # Cookie-based JWT
    ],
    # ... other settings
}
```

### Step 6: Update API URLs

```python
# apps/api/urls.py
from apps.api.views.auth import CookieTokenObtainPairView, CookieTokenRefreshView

urlpatterns = [
    path('auth/login/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    # ... other URLs
]
```

### Step 7: Create logout endpoint

```python
# apps/api/views/auth.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

class LogoutView(APIView):
    def post(self, request):
        response = Response(
            {'detail': 'Successfully logged out'},
            status=status.HTTP_200_OK
        )

        # Delete cookies
        response.delete_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE'],
            path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
        )
        response.delete_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
            path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
        )

        return response
```

### Step 8: Update frontend to use credentials mode

```javascript
// frontend/src/contexts/AuthContext.jsx

// Remove all localStorage token logic
// DELETE these lines:
// localStorage.setItem('authToken', newToken)
// localStorage.setItem('refreshToken', refresh)
// localStorage.getItem('authToken')
// localStorage.removeItem('authToken')

// Update fetch calls to include credentials
const login = async (email, password) => {
    try {
        const response = await fetch('/api/v1/auth/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',  // ← IMPORTANT: Send cookies
            body: JSON.stringify({ email, password }),
        })

        if (response.ok) {
            const data = await response.json()
            // Tokens are now in httpOnly cookies
            // No need to store in localStorage
            setUser(data.user)
            setIsAuthenticated(true)
        }
    } catch (error) {
        console.error('Login failed', error)
    }
}

const logout = async () => {
    try {
        await fetch('/api/v1/auth/logout/', {
            method: 'POST',
            credentials: 'include',  // ← IMPORTANT: Send cookies
        })
    } finally {
        setUser(null)
        setIsAuthenticated(false)
    }
}

// Token refresh (automatic)
const refreshToken = async () => {
    try {
        const response = await fetch('/api/v1/auth/refresh/', {
            method: 'POST',
            credentials: 'include',  // ← IMPORTANT: Send cookies
        })

        if (response.ok) {
            // New access token set in cookie automatically
            return true
        }
    } catch (error) {
        console.error('Token refresh failed', error)
        return false
    }
}
```

### Step 9: Update all API calls to include credentials

```javascript
// frontend/src/lib/api.js (or wherever you make API calls)

export const apiClient = {
    async get(url) {
        const response = await fetch(url, {
            method: 'GET',
            credentials: 'include',  // ← Add to all requests
        })
        return response.json()
    },

    async post(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',  // ← Add to all requests
            body: JSON.stringify(data),
        })
        return response.json()
    },

    // ... other methods
}
```

### Step 10: Add CSRF token handling for mutation requests

```javascript
// frontend/src/lib/csrf.js

export function getCsrfToken() {
    const name = 'csrftoken'
    const cookies = document.cookie.split(';')

    for (let cookie of cookies) {
        cookie = cookie.trim()
        if (cookie.startsWith(name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1))
        }
    }
    return null
}

// Update API client
export const apiClient = {
    async post(url, data) {
        const csrfToken = getCsrfToken()

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,  // ← Add CSRF token
            },
            credentials: 'include',
            body: JSON.stringify(data),
        })
        return response.json()
    },
    // ... similar for PUT, PATCH, DELETE
}
```

## Testing

```python
# tests/test_jwt_cookies.py

class JWTCookieAuthTests(TestCase):
    def test_login_sets_httponly_cookies(self):
        """Ensure login sets httpOnly cookies"""
        response = self.client.post('/api/v1/auth/login/', {
            'email': 'test@test.com',
            'password': 'password123',
        })

        self.assertEqual(response.status_code, 200)

        # Check cookies are set
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

        # Check httpOnly flag
        access_cookie = response.cookies['access_token']
        self.assertTrue(access_cookie['httponly'])

    def test_tokens_not_in_response_body(self):
        """Ensure tokens are not exposed in response body"""
        response = self.client.post('/api/v1/auth/login/', {
            'email': 'test@test.com',
            'password': 'password123',
        })

        data = response.json()
        self.assertNotIn('access', data)
        self.assertNotIn('refresh', data)

    def test_authenticated_request_with_cookie(self):
        """Ensure cookie-based authentication works"""
        # Login
        self.client.post('/api/v1/auth/login/', {
            'email': 'test@test.com',
            'password': 'password123',
        })

        # Make authenticated request (cookies sent automatically)
        response = self.client.get('/api/v1/auth/user/')
        self.assertEqual(response.status_code, 200)

    def test_logout_deletes_cookies(self):
        """Ensure logout removes cookies"""
        # Login
        self.client.post('/api/v1/auth/login/', {
            'email': 'test@test.com',
            'password': 'password123',
        })

        # Logout
        response = self.client.post('/api/v1/auth/logout/')

        # Cookies should be deleted
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')
```

## Verification

- [ ] Django JWT configured for cookies
- [ ] Custom cookie auth views created
- [ ] Logout endpoint implemented
- [ ] Frontend updated to use credentials mode
- [ ] All localStorage token logic removed
- [ ] CSRF token handling added
- [ ] Tests pass
- [ ] Manual login/logout testing works
- [ ] Browser DevTools shows httpOnly cookies
- [ ] Tokens not accessible via JavaScript console

## Manual Testing Checklist

1. Login → Check DevTools Application tab → Cookies should have httpOnly flag
2. Try `console.log(document.cookie)` → Should NOT show tokens
3. Navigate to protected route → Should work automatically
4. Logout → Cookies should be deleted
5. Try accessing protected route after logout → Should fail

## Migration Notes

This is a breaking change for existing users. Consider:

1. **Gradual Migration**: Support both localStorage and cookies temporarily
2. **User Communication**: Notify users they'll be logged out
3. **Session Migration**: Provide migration script to move existing sessions

## References

- OWASP: Session Management Cheat Sheet
- JWT Best Practices: https://datatracker.ietf.org/doc/html/rfc8725
- Django CORS: https://pypi.org/project/django-cors-headers/
- Comprehensive Security Audit 2025, Finding #3
