"""
Minimal development settings for initial setup.
"""

from .base import *

# Include core apps for testing
LOCAL_APPS = [
    'apps.users',
    'apps.blog',
    'apps.learning',
    'apps.api',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Override for development
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'testserver']

# Database for development (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Development-specific environment variables
ENVIRONMENT = 'development'