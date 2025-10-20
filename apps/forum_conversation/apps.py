"""
AppConfig for custom forum_conversation app.

Overrides django-machina's forum_conversation app to customize Post and Topic models.
"""

from machina.apps.forum_conversation.apps import ForumConversationAppConfig as BaseForumConversationAppConfig


class ForumConversationAppConfig(BaseForumConversationAppConfig):
    """
    Custom forum_conversation app configuration.

    This overrides django-machina's forum_conversation app to change CASCADE to SET_NULL
    for User foreign keys in Post and Topic models.
    """
    name = 'apps.forum_conversation'
    label = 'forum_conversation'  # Same label as machina app - enables model swapping
    verbose_name = 'Forum Conversation (Custom)'

    def ready(self):
        """Import signal handlers when app is ready."""
        super().ready()
        # Import signals to register handlers
        from . import signals  # noqa: F401
