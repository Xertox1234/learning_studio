"""
Development settings for Python Learning Studio.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Check if we're running tests
import sys
TESTING = 'test' in sys.argv

# Development-specific apps (exclude debug_toolbar during tests)
if not TESTING:
    INSTALLED_APPS += [
        'django_extensions',
        'debug_toolbar',
        # 'silk',  # Performance profiling - commented out temporarily
    ]

    # Debug Toolbar Middleware
    MIDDLEWARE += [
        # 'silk.middleware.SilkyMiddleware',  # Must be first for accurate profiling - commented out temporarily
        'debug_toolbar.middleware.DebugToolbarMiddleware',
        'apps.api.middleware.QueryLoggingMiddleware',
    ]

    # Debug Toolbar Configuration
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]
else:
    # During tests, only add django_extensions
    INSTALLED_APPS += [
        'django_extensions',
    ]

# Database for development (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache for development (Redis with fallback to local memory)
import os
import logging

logger = logging.getLogger(__name__)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')

# Try to use Redis, fallback to LocMemCache if not available
try:
    import redis
    redis_client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=1)
    redis_client.ping()

    # Redis is available - use it
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                # Note: HiredisParser is used automatically if hiredis is installed
                'CONNECTION_POOL_CLASS_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'PICKLE_VERSION': -1,  # Use latest pickle protocol
            },
            'KEY_PREFIX': 'learning_studio',
            'VERSION': 1,  # Increment to invalidate all caches
            'TIMEOUT': 300,  # 5 minutes default
        },
        # Fallback cache for when Redis is down
        'fallback': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'fallback-cache',
        }
    }
    logger.info("✓ Redis cache configured successfully")
except (ImportError, redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
    # Redis not available - use local memory cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
    logger.warning("⚠ Redis not available, using local memory cache")

# Override cache for testing to avoid Mock serialization issues
if TESTING:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache',
        }
    }

# Email backend for development (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging for development (more verbose)
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'

# Create logs directory if it doesn't exist
import os
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# CSRF settings for development (allow React dev server)
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Session configuration for development
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Static files configuration for development
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Disable some security features for development
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Development-specific environment variables
ENVIRONMENT = 'development'

# Query logging for development (helps identify N+1 queries and slow queries)
# Set to False if query logging is too verbose
QUERY_LOGGING_ENABLED = config('QUERY_LOGGING_ENABLED', default=False, cast=bool)

# Django Silk Configuration (Performance Profiling)
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_ANALYZE_QUERIES = True
SILKY_META = True
SILKY_INTERCEPT_PERCENT = 100  # Profile 100% of requests in development
SILKY_MAX_RECORDED_REQUESTS = 10000
SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = 10
# Authentication required to access silk
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True
SILKY_PERMISSIONS = lambda user: user.is_superuser