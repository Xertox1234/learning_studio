from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.api'
    verbose_name = 'API'

    def ready(self):
        """Import signal handlers to register cache invalidation."""
        # Import cache invalidation signals
        from apps.api.cache import invalidation

        # This ensures all @receiver decorators are executed
        invalidation.setup_cache_invalidation()
