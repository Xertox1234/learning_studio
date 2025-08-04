"""
Signal handlers for invalidating forum statistics cache
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from machina.apps.forum_conversation.models import Topic, Post
from django.contrib.auth import get_user_model
from .statistics_service import forum_stats_service

User = get_user_model()


@receiver(post_save, sender=Topic)
def invalidate_stats_on_topic_save(sender, instance, created, **kwargs):
    """Topics and posts are now live data - no cache invalidation needed for forum activity"""
    pass  # Live data - no cache to invalidate


@receiver(post_delete, sender=Topic)
def invalidate_stats_on_topic_delete(sender, instance, **kwargs):
    """Topics and posts are now live data - no cache invalidation needed for forum activity"""
    pass  # Live data - no cache to invalidate


@receiver(post_save, sender=Post)
def invalidate_stats_on_post_save(sender, instance, created, **kwargs):
    """Topics and posts are now live data - no cache invalidation needed for forum activity"""
    pass  # Live data - no cache to invalidate


@receiver(post_delete, sender=Post)
def invalidate_stats_on_post_delete(sender, instance, **kwargs):
    """Topics and posts are now live data - no cache invalidation needed for forum activity"""
    pass  # Live data - no cache to invalidate


@receiver(post_save, sender=User)
def invalidate_stats_on_user_save(sender, instance, created, **kwargs):
    """Invalidate statistics cache when a user is created or updated"""
    if created or instance.is_active != getattr(instance, '_original_is_active', True):
        forum_stats_service.invalidate_cache()
        
    # Store original is_active state for next time
    instance._original_is_active = instance.is_active


@receiver(post_delete, sender=User)
def invalidate_stats_on_user_delete(sender, instance, **kwargs):
    """Invalidate statistics cache when a user is deleted"""
    forum_stats_service.invalidate_cache()