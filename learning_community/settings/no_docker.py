"""
Development settings without Docker for network troubleshooting.
"""

from .development_minimal import *

# Disable Docker-related functionality
DOCKER_EXECUTOR_ENABLED = False

# Remove apps that depend on Docker
INSTALLED_APPS = [app for app in INSTALLED_APPS if 'code_execution' not in app]

# Minimal middleware with required allauth middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Simple URL config without Docker dependencies
ROOT_URLCONF = 'learning_community.urls'