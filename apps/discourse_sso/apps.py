"""
Discourse SSO app configuration.
"""

from django.apps import AppConfig


class DiscourseSsoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.discourse_sso'
    verbose_name = 'Discourse SSO Integration'