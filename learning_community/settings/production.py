"""
Production settings for Python Learning Studio.
"""

import os
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Note: SECRET_KEY validation is handled in base.py
# It's required and must be set via environment variable

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'sslmode': 'prefer',
        },
    }
}

# Cache Configuration (Redis with optimizations)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://redis:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            # Note: HiredisParser is used automatically if hiredis is installed
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,  # Increased for better concurrency
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'PICKLE_VERSION': -1,  # Use latest pickle protocol
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',  # Compress large values
        },
        'KEY_PREFIX': 'learning_studio',  # Match development prefix
        'VERSION': 1,  # Increment to invalidate all caches on deployment
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF configuration
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# CORS configuration (production)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_HEADERS = [
    'Accept', 'Accept-Language', 'Content-Language', 'Content-Type',
    'Authorization', 'X-CSRFToken', 'X-Requested-With', 'Origin'
]
CORS_EXPOSE_HEADERS = ['Content-Type', 'Authorization']

# CSRF trusted origins for cross-origin POSTs (e.g., SPA)
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Content Security Policy (django-csp)
# Keep tight, allow SPA and CodeMirror assets. Extend via env if needed.
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", 'https://fonts.googleapis.com')
CSP_IMG_SRC = ("'self'", 'data:', 'blob:')
CSP_FONT_SRC = ("'self'", 'data:', 'https://fonts.gstatic.com')
CSP_CONNECT_SRC = ("'self'",) + tuple(CORS_ALLOWED_ORIGINS)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024*1024*50,  # 50 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
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
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@pythonlearning.studio')

# Environment-specific settings
ENVIRONMENT = 'production'

# Docker executor settings
DOCKER_EXECUTOR_ENABLED = config('DOCKER_EXECUTOR_ENABLED', default=True, cast=bool)
DOCKER_EXECUTOR_IMAGE = config('DOCKER_EXECUTOR_IMAGE', default='python-learning-studio-executor')
DOCKER_EXECUTOR_NETWORK = config('DOCKER_EXECUTOR_NETWORK', default='none')
DOCKER_EXECUTOR_MEMORY_LIMIT = config('DOCKER_EXECUTOR_MEMORY_LIMIT', default='256m')
DOCKER_EXECUTOR_CPU_LIMIT = config('DOCKER_EXECUTOR_CPU_LIMIT', default='0.5')
DOCKER_EXECUTOR_TIME_LIMIT = config('DOCKER_EXECUTOR_TIME_LIMIT', default=30, cast=int)

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)