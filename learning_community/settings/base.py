"""
Base Django settings for Python Learning Studio.
This file contains settings common to all environments.
"""

import os
import logging
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY is REQUIRED and must be set via environment variable
# Generate a secure key with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = config('SECRET_KEY', default='')

# Validate SECRET_KEY
INSECURE_SECRET_KEYS = [
    'django-insecure-y4xd$t)8(&zs6%2a186=wnscue&d@4h0s6(vw3+ovv_idptyl=',
    'your-super-secret-key-here',
    'your-super-secret-key-here-REPLACE-THIS',
    'REPLACE_WITH_GENERATED_KEY',
    '',
]

if not SECRET_KEY or SECRET_KEY in INSECURE_SECRET_KEYS:
    error_message = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║  SECURITY ERROR: SECRET_KEY not configured or insecure           ║
    ╚══════════════════════════════════════════════════════════════════╝

    The SECRET_KEY environment variable is required and must be set to
    a secure, random value. This key is used for:
    - Cryptographic signing of session cookies
    - JWT token generation and validation
    - Password reset tokens
    - CSRF protection

    🔐 To generate a secure SECRET_KEY, run:

        python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

    Then add it to your .env file:

        SECRET_KEY=<generated-key-here>

    ⚠️  NEVER commit the SECRET_KEY to version control!
    ⚠️  Use different keys for development and production!
    """
    raise ValueError(error_message)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

THIRD_PARTY_APPS = [
    # Wagtail CMS
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',
    'modelcluster',
    'taggit',
    
    # Wagtail AI
    'wagtail_ai',
    
    # Real-time WebSocket support
    'channels',
    
    # Authentication
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    # API
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    
    # Security
    'corsheaders',
    'csp',
    
    # Forum dependencies
    'mptt',
    'haystack',
    'widget_tweaks',
    
    # Django-machina apps
    'machina',
    'machina.apps.forum',
    'machina.apps.forum_conversation',
    'machina.apps.forum_conversation.forum_attachments',
    'machina.apps.forum_conversation.forum_polls',
    'machina.apps.forum_feeds',
    'machina.apps.forum_member',
    'machina.apps.forum_moderation',
    'machina.apps.forum_permission',
    'machina.apps.forum_search',
    'machina.apps.forum_tracking',
]

LOCAL_APPS = [
    'apps.users',
    'apps.learning',
    'apps.exercises',
    'apps.community',
    'apps.api',
    'apps.blog',
    'apps.forum_integration',
    'apps.frontend',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'machina.apps.forum_permission.middleware.ForumPermissionMiddleware',
    'apps.forum_integration.middleware.TrustLevelTrackingMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
]

ROOT_URLCONF = 'learning_community.urls'

from machina import MACHINA_MAIN_TEMPLATE_DIR

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # Your custom templates FIRST
            MACHINA_MAIN_TEMPLATE_DIR,  # Machina templates as fallback
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'wagtail.contrib.settings.context_processors.settings',
                'machina.core.context_processors.metadata',
                'apps.forum_integration.context_processors.forum_stats',
            ],
        },
    },
]

WSGI_APPLICATION = 'learning_community.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
    }
}

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Site ID for Django Sites framework
SITE_ID = 1

# Django Allauth Configuration
AUTHENTICATION_BACKENDS = [
    'apps.users.backends.EmailOrUsernameModelBackend',  # Our custom backend first
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Updated Allauth settings (new format)
ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = config('ACCOUNT_EMAIL_VERIFICATION', default='mandatory')
ACCOUNT_EMAIL_REQUIRED = True

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@pythonlearning.studio')

# Login/Logout URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 🔒 SECURITY: Cookie-based JWT authentication (CVE-2024-JWT-003)
        # Primary: Read JWT from httpOnly cookie (XSS-proof)
        # Fallback: Read JWT from Authorization header (API clients, testing)
        'apps.api.authentication.JWTCookieAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.api.pagination.StandardResultsSetPagination',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    # Token lifetimes
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # Short-lived access tokens
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # Weekly refresh tokens
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
    
    # Token rotation and blacklisting
    'ROTATE_REFRESH_TOKENS': True,                   # Generate new refresh token on refresh
    'BLACKLIST_AFTER_ROTATION': True,               # Blacklist old refresh tokens
    'UPDATE_LAST_LOGIN': True,                       # Update user's last_login field

    # 🔒 SECURITY: httpOnly Cookie Storage (CVE-2024-JWT-003)
    # Tokens stored in httpOnly cookies are NOT accessible to JavaScript,
    # preventing XSS-based token theft
    'AUTH_COOKIE': 'access_token',                   # Cookie name for access token
    'AUTH_COOKIE_REFRESH': 'refresh_token',         # Cookie name for refresh token
    'AUTH_COOKIE_SECURE': not DEBUG,                # HTTPS only in production
    'AUTH_COOKIE_HTTP_ONLY': True,                  # Not accessible to JavaScript
    'AUTH_COOKIE_SAMESITE': 'Lax',                  # CSRF protection
    'AUTH_COOKIE_PATH': '/',                         # Available for all paths
    'AUTH_COOKIE_DOMAIN': None,                      # Same domain only

    # Signing settings
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JSON_ENCODER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    
    # Token structure
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    # Token classes
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    # Claims
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    
    # Token validation
    'TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainPairSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSerializer',
    'TOKEN_VERIFY_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenVerifySerializer',
    'TOKEN_BLACKLIST_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenBlacklistSerializer',
    'SLIDING_TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer',
    'SLIDING_TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer',
}

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Python Learning Studio API',
    'DESCRIPTION': 'API for Python Learning Studio - AI-powered programming education platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Wagtail Settings
WAGTAIL_SITE_NAME = 'Python Learning Studio'
WAGTAILADMIN_BASE_URL = config('WAGTAILADMIN_BASE_URL', default='http://localhost:8000')

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Security Settings (base level)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Code Execution Security
# 🔒 CRITICAL SECURITY SETTING: Require Docker for all code execution
# This prevents the dangerous exec() fallback (CVE-2024-EXEC-001)
CODE_EXECUTION_REQUIRE_DOCKER = config('CODE_EXECUTION_REQUIRE_DOCKER', default=True, cast=bool)

# Session Configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS only in production

# CSRF Protection for Cookie-Based Authentication
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not DEBUG  # HTTPS only in production
CSRF_COOKIE_HTTPONLY = False  # CSRF token needs to be read by JavaScript for API calls
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:3001',
]

# Cache Configuration (will be overridden in environment-specific settings)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Rate Limiting Configuration
RATELIMIT_ENABLE = config('RATELIMIT_ENABLE', default=True, cast=bool)
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_VIEW = 'apps.api.views.ratelimited'

# Rate limiting settings
RATE_LIMIT_SETTINGS = {
    'LOGIN_ATTEMPTS': config('RATE_LIMIT_LOGIN', default='5/m', cast=str),  # 5 attempts per minute
    'REGISTRATION_ATTEMPTS': config('RATE_LIMIT_REGISTER', default='3/m', cast=str),  # 3 attempts per minute
    'API_CALLS': config('RATE_LIMIT_API', default='100/m', cast=str),  # 100 API calls per minute
    'FORUM_POSTS': config('RATE_LIMIT_FORUM_POSTS', default='10/m', cast=str),  # 10 posts per minute
    'CODE_EXECUTION': config('RATE_LIMIT_CODE_EXEC', default='20/m', cast=str),  # 20 code executions per minute
    'AI_REQUESTS': config('RATE_LIMIT_AI', default='30/h', cast=str),  # 30 AI requests per hour
}

# Email Configuration (will be overridden in environment-specific settings)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# OpenAI API Key for AI features
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')

# Wagtail AI Configuration
WAGTAIL_AI = {
    "BACKENDS": {
        "default": {
            "CLASS": "wagtail_ai.ai.openai.OpenAIBackend",
            "CONFIG": {
                "MODEL_ID": "gpt-4",
                "TOKEN_LIMIT": 2000,
            },
        },
        "vision": {
            "CLASS": "wagtail_ai.ai.openai.OpenAIBackend", 
            "CONFIG": {
                "MODEL_ID": "gpt-4-vision-preview",
                "TOKEN_LIMIT": 300,
            },
        },
    },
    "TEXT_COMPLETION_BACKEND": "default",
    "IMAGE_DESCRIPTION_BACKEND": "vision",
    "IMAGE_DESCRIPTION_PROMPT": "Generate a concise, educational alt-text description for this programming-related image.",
}

# Django-Machina Configuration

# Anonymous (non-authenticated) users can only read
MACHINA_DEFAULT_ANONYMOUS_USER_FORUM_PERMISSIONS = [
    'can_see_forum',
    'can_read_forum',
]

# Authenticated users get full permissions
MACHINA_DEFAULT_AUTHENTICATED_USER_FORUM_PERMISSIONS = [
    'can_see_forum',
    'can_read_forum',
    'can_start_new_topics',
    'can_reply_to_topics',
    'can_edit_own_posts',
    'can_post_without_approval',
    'can_create_polls',
    'can_vote_in_polls',
    'can_download_file',
]


# Forum markup settings
MACHINA_MARKUP_LANGUAGE = None  # Disable markup for now, can enable later
MACHINA_MARKUP_WIDGET = None  # Disable markup widget to avoid circular imports

# Forum attachment settings
MACHINA_ATTACHMENT_CACHE_NAME = 'default'
MACHINA_ATTACHMENT_FILE_UPLOAD_TO = 'machina/attachments/%Y/%m/%d/'

# Custom machina template settings
MACHINA_BASE_TEMPLATE_NAME = 'base/base.html'
MACHINA_FORUM_NAME = 'Python Learning Studio Forum'

# Haystack configuration for forum search (using simple backend for compatibility)
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}

# Django Channels Configuration for Real-time Updates
ASGI_APPLICATION = 'learning_community.asgi.application'

# Channel Layers (Redis backend for production, in-memory for development)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(config('REDIS_HOST', default='127.0.0.1'), config('REDIS_PORT', default=6379, cast=int))],
            'capacity': 1500,  # Maximum messages to store
            'expiry': 60,      # Message expiry in seconds
        },
    },
}

# WebSocket settings
WEBSOCKET_ACCEPT_ALL = config('WEBSOCKET_ACCEPT_ALL', default=True, cast=bool)
WEBSOCKET_HEARTBEAT_INTERVAL = config('WEBSOCKET_HEARTBEAT_INTERVAL', default=30, cast=int)
WEBSOCKET_MESSAGE_MAX_SIZE = config('WEBSOCKET_MESSAGE_MAX_SIZE', default=64 * 1024, cast=int)  # 64KB

# Sentry Error Tracking and Performance Monitoring
SENTRY_DSN = config('SENTRY_DSN', default='')
SENTRY_TRACES_SAMPLE_RATE = config('SENTRY_TRACES_SAMPLE_RATE', default=0.1, cast=float)
SENTRY_PROFILES_SAMPLE_RATE = config('SENTRY_PROFILES_SAMPLE_RATE', default=0.1, cast=float)

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
                cache_spans=True,
            ),
            RedisIntegration(),
            CeleryIntegration(
                monitor_beat_tasks=True,
                propagate_traces=True,
            ),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            ),
        ],

        # Performance monitoring
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,

        # Send default PII (Personally Identifiable Information)
        send_default_pii=False,

        # Environment
        environment=config('ENVIRONMENT', default='development'),

        # Release tracking
        release=config('SENTRY_RELEASE', default=None),

        # Error handling
        attach_stacktrace=True,
        max_breadcrumbs=50,

        # Before send hook to filter sensitive data
        before_send=lambda event, hint: event if not DEBUG else None,
    )

