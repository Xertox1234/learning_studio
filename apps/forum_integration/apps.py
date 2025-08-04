from django.apps import AppConfig


class ForumIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.forum_integration'
    verbose_name = 'Forum Integration'
    
    def ready(self):
        """Import signals when the app is ready"""
        import apps.forum_integration.signals
        import apps.forum_integration.cache_signals
