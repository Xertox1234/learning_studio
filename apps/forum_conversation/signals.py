"""
Signal handlers for caching usernames in Post and Topic models.

These signals ensure that usernames are cached before saving, so they can
be displayed even after a user deletes their account.
"""

from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Topic, Post


@receiver(pre_save, sender=Topic)
def cache_topic_poster_username(sender, instance, **kwargs):
    """
    Cache poster username before saving Topic.

    This ensures the username is preserved for display even if the user
    deletes their account later.

    Flow:
    1. If poster FK exists and poster_username is empty → cache username
    2. If poster FK is NULL and poster_username exists → preserve cached value
    3. If both NULL → leave empty (anonymous topic)
    """
    if instance.poster and not instance.poster_username:
        # Cache the username from the poster
        instance.poster_username = instance.poster.username
    # If poster is None but poster_username exists, preserve it (deleted user)


@receiver(pre_save, sender=Post)
def cache_post_poster_username(sender, instance, **kwargs):
    """
    Cache poster username before saving Post.

    Uses the inherited 'username' field from AbstractPost for caching.

    Flow:
    1. If poster FK exists and username is empty → cache username
    2. If poster FK is NULL and username exists → preserve cached value
    3. If both NULL → leave empty (will use anonymous_key if set)
    """
    if instance.poster and not instance.username:
        # Cache the username from the poster
        instance.username = instance.poster.username
    # If poster is None but username exists, preserve it (deleted user)
