"""
Custom Post and Topic models with SET_NULL for user deletion.

This module overrides django-machina's Post and Topic models to change
on_delete=CASCADE to on_delete=SET_NULL for the poster foreign key.

This preserves forum content when users delete their accounts (GDPR compliance).
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from machina.apps.forum_conversation.abstract_models import AbstractTopic, AbstractPost


class Topic(AbstractTopic):
    """
    Custom Topic model with SET_NULL for poster preservation.

    Changes from AbstractTopic:
    - poster: on_delete=CASCADE → on_delete=SET_NULL
    - Add poster_username field to cache username for display after deletion

    GDPR Compliance:
    When a user deletes their account, their topics are preserved with:
    - poster FK set to NULL
    - poster_username contains cached username for display
    """

    # Override poster field to change CASCADE to SET_NULL
    poster = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,  # ✅ Changed from CASCADE
        verbose_name=_('Poster'),
        help_text=_('User who created this topic (NULL if user deleted)')
    )

    # Add cached username field for display after user deletion
    poster_username = models.CharField(
        max_length=155,
        blank=True,
        null=True,
        verbose_name=_('Poster Username (cached)'),
        help_text=_('Cached username for display when poster is deleted')
    )

    class Meta(AbstractTopic.Meta):
        abstract = False
        app_label = 'forum_conversation'


class Post(AbstractPost):
    """
    Custom Post model with SET_NULL for poster preservation.

    Changes from AbstractPost:
    - poster: on_delete=CASCADE → on_delete=SET_NULL
    - username field (inherited) already handles caching

    GDPR Compliance:
    When a user deletes their account, their posts are preserved with:
    - poster FK set to NULL
    - username field (inherited) contains cached username for display

    Note: AbstractPost already has a 'username' field (max_length=155)
    that we use for caching. No additional field needed.
    """

    # Override poster field to change CASCADE to SET_NULL
    poster = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='posts',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,  # ✅ Changed from CASCADE
        verbose_name=_('Poster'),
        help_text=_('User who created this post (NULL if user deleted)')
    )

    class Meta(AbstractPost.Meta):
        abstract = False
        app_label = 'forum_conversation'


# CRITICAL: Import machina models AFTER custom models
# This ensures our custom models are loaded instead of the defaults
from machina.apps.forum_conversation.models import *  # noqa: F401, F403, E402
