"""
Django signals for tracking forum activity, trust level progression, and real-time updates
"""
import json
import logging
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from machina.apps.forum_conversation.models import Topic, Post
from .middleware import ForumActivityTracker
from .models import TrustLevel
from .review_queue_service import ReviewQueueService
from .gamification_service import GamificationService

User = get_user_model()
logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


def broadcast_to_channel(group_name, message_type, data):
    """Helper function to broadcast messages to WebSocket groups"""
    if not channel_layer:
        logger.warning("Channel layer not available for broadcasting")
        return
        
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': message_type,
                **data,
                'timestamp': timezone.now().isoformat()
            }
        )
        logger.debug(f"Broadcasted {message_type} to {group_name}")
    except Exception as e:
        logger.error(f"Error broadcasting to {group_name}: {e}")


@receiver(post_save, sender=User)
def create_trust_level_for_new_user(sender, instance, created, **kwargs):
    """
    Automatically create a TrustLevel instance for new users
    """
    if created:
        TrustLevel.objects.get_or_create(
            user=instance,
            defaults={
                'level': 0,
            }
        )
        
        # Add user to Authenticated Users group for forum permissions
        from django.contrib.auth.models import Group
        auth_group, _ = Group.objects.get_or_create(name='Authenticated Users')
        instance.groups.add(auth_group)
        
        # Initialize gamification for new user
        GamificationService.initialize_user(instance)


@receiver(post_save, sender=Post)
def track_post_creation(sender, instance, created, **kwargs):
    """
    Track when users create new posts and broadcast real-time updates
    """
    if created and instance.poster:
        ForumActivityTracker.track_post_created(instance.poster, instance)
        
        # Handle gamification for post creation
        GamificationService.handle_post_created(instance.poster, instance)
        
        # Check if post needs moderation review
        ReviewQueueService.check_new_post(instance)
        
        # Update forum trackers to show latest post
        if instance.topic and instance.topic.forum:
            instance.topic.forum.update_trackers()
            instance.topic.forum.save(update_fields=['last_post_id', 'last_post_on'])
        
        # Broadcast real-time updates
        try:
            created_time = instance.created.isoformat() if instance.created else timezone.now().isoformat()
        except (AttributeError, TypeError):
            created_time = timezone.now().isoformat()
            
        post_data = {
            'id': instance.id,
            'content': instance.content.raw if hasattr(instance.content, 'raw') else str(instance.content),
            'poster': {
                'id': instance.poster.id,
                'username': instance.poster.username
            },
            'created': created_time,
            'topic_id': instance.topic.id,
            'forum_id': instance.topic.forum.id
        }
        
        # Broadcast to topic-specific group
        topic_group = f'topic_{instance.topic.id}'
        broadcast_to_channel(topic_group, 'new_post', {'post': post_data})
        
        # Broadcast to forum-wide group
        forum_group = f'forum_{instance.topic.forum.id}'
        broadcast_to_channel(forum_group, 'new_post', {'post': post_data})
        
        # Broadcast to global activity feed
        broadcast_to_channel('forum_activity', 'activity_update', {
            'activity': {
                'type': 'new_post',
                'user': post_data['poster'],
                'topic': {
                    'id': instance.topic.id,
                    'subject': instance.topic.subject
                },
                'forum': {
                    'id': instance.topic.forum.id,
                    'name': instance.topic.forum.name
                }
            }
        })
        
        logger.info(f"New post created by {instance.poster} in topic {instance.topic.id}")
    
    elif not created and instance.poster:
        # Check if edited post needs review
        ReviewQueueService.check_edited_post(instance, instance.poster)
        
        # Handle post updates
        try:
            created_time = instance.created.isoformat() if instance.created else timezone.now().isoformat()
            updated_time = instance.updated.isoformat() if instance.updated else timezone.now().isoformat()
        except (AttributeError, TypeError):
            created_time = timezone.now().isoformat()
            updated_time = timezone.now().isoformat()
            
        post_data = {
            'id': instance.id,
            'content': instance.content.raw if hasattr(instance.content, 'raw') else str(instance.content),
            'poster': {
                'id': instance.poster.id,
                'username': instance.poster.username
            },
            'created': created_time,
            'updated': updated_time,
            'topic_id': instance.topic.id,
            'forum_id': instance.topic.forum.id
        }
        
        topic_group = f'topic_{instance.topic.id}'
        broadcast_to_channel(topic_group, 'post_updated', {'post': post_data})
        logger.info(f"Post {instance.id} updated by {instance.poster}")


@receiver(post_save, sender=Topic)
def track_topic_creation(sender, instance, created, **kwargs):
    """
    Track when users create new topics and broadcast real-time updates
    """
    if created and instance.poster:
        ForumActivityTracker.track_topic_created(instance.poster, instance)
        
        # Handle gamification for topic creation
        GamificationService.handle_topic_created(instance.poster, instance)
        
        # Check if topic needs moderation review
        ReviewQueueService.check_new_topic(instance)
        
        # Update forum trackers to show latest topic
        if instance.forum:
            instance.forum.update_trackers()
            instance.forum.save(update_fields=['last_post_id', 'last_post_on'])
        
        # Broadcast real-time updates
        try:
            created_time = instance.created.isoformat() if instance.created else timezone.now().isoformat()
        except (AttributeError, TypeError):
            created_time = timezone.now().isoformat()
            
        topic_data = {
            'id': instance.id,
            'subject': instance.subject,
            'posts_count': instance.posts_count,
            'views_count': getattr(instance, 'views_count', 0),
            'is_locked': instance.is_locked,
            'is_sticky': instance.is_sticky,
            'poster': {
                'id': instance.poster.id,
                'username': instance.poster.username
            },
            'created': created_time,
            'forum_id': instance.forum.id
        }
        
        # Broadcast to forum-wide group
        forum_group = f'forum_{instance.forum.id}'
        broadcast_to_channel(forum_group, 'new_topic', {'topic': topic_data})
        
        # Broadcast to global activity feed
        broadcast_to_channel('forum_activity', 'activity_update', {
            'activity': {
                'type': 'new_topic',
                'user': topic_data['poster'],
                'topic': topic_data,
                'forum': {
                    'id': instance.forum.id,
                    'name': instance.forum.name
                }
            }
        })
        
        logger.info(f"New topic '{instance.subject}' created by {instance.poster} in forum {instance.forum.id}")
    
    elif not created and instance.poster:
        # Handle topic updates
        try:
            created_time = instance.created.isoformat() if instance.created else timezone.now().isoformat()
        except (AttributeError, TypeError):
            created_time = timezone.now().isoformat()
            
        topic_data = {
            'id': instance.id,
            'subject': instance.subject,
            'posts_count': instance.posts_count,
            'views_count': getattr(instance, 'views_count', 0),
            'is_locked': instance.is_locked,
            'is_sticky': instance.is_sticky,
            'poster': {
                'id': instance.poster.id,
                'username': instance.poster.username
            },
            'created': created_time,
            'forum_id': instance.forum.id
        }
        
        # Broadcast to forum and topic groups
        forum_group = f'forum_{instance.forum.id}'
        topic_group = f'topic_{instance.id}'
        broadcast_to_channel(forum_group, 'topic_updated', {'topic': topic_data})
        broadcast_to_channel(topic_group, 'topic_updated', {'topic': topic_data})
        logger.info(f"Topic {instance.id} updated")


# Note: For tracking likes, views, and reading time, we'll need to integrate
# with django-machina's existing systems or create custom views.
# These signals handle the basic post/topic creation tracking.


@receiver(pre_delete, sender=Post)
def broadcast_post_deletion(sender, instance, **kwargs):
    """
    Broadcast post deletion before it's removed from database
    """
    if instance.topic and instance.topic.id:
        topic_group = f'topic_{instance.topic.id}'
        broadcast_to_channel(topic_group, 'post_deleted', {
            'post_id': instance.id,
            'topic_id': instance.topic.id
        })
        logger.info(f"Post {instance.id} deleted from topic {instance.topic.id}")


@receiver(post_delete, sender=Post)
def handle_post_deletion(sender, instance, **kwargs):
    """
    Handle post deletion by updating user metrics
    Note: In a production system, you might want to keep the metrics
    and just mark posts as deleted rather than decrementing counts
    """
    if instance.poster:
        try:
            trust_level = TrustLevel.objects.get(user=instance.poster)
            if trust_level.posts_created > 0:
                trust_level.posts_created -= 1
                trust_level.save(update_fields=['posts_created'])
        except TrustLevel.DoesNotExist:
            pass


@receiver(post_delete, sender=Topic)
def handle_topic_deletion(sender, instance, **kwargs):
    """
    Handle topic deletion by updating user metrics
    """
    if instance.poster:
        try:
            trust_level = TrustLevel.objects.get(user=instance.poster)
            if trust_level.topics_created > 0:
                trust_level.topics_created -= 1
                trust_level.save(update_fields=['topics_created'])
        except TrustLevel.DoesNotExist:
            pass


@receiver(post_save, sender=TrustLevel)
def handle_trust_level_promotion(sender, instance, created, **kwargs):
    """
    Handle trust level promotions and award points/badges
    """
    if not created and instance.pk:
        # Get the previous level from database
        try:
            old_instance = TrustLevel.objects.get(pk=instance.pk)
            if hasattr(old_instance, '_state') and old_instance._state.db:
                # This is an update, check if level changed
                old_level = TrustLevel.objects.filter(pk=instance.pk).values_list('level', flat=True).first()
                if old_level is not None and old_level < instance.level:
                    # Trust level was promoted
                    GamificationService.handle_trust_level_promotion(instance.user, instance.level)
                    logger.info(f"Trust level promotion: {instance.user.username} -> TL{instance.level}")
        except TrustLevel.DoesNotExist:
            pass


# Helper functions for real-time broadcasting

def broadcast_like_update(post_id, likes_count, user_id=None, user_liked=False):
    """
    Broadcast like count updates for a post
    This function can be called from views when likes are added/removed
    """
    try:
        post = Post.objects.select_related('topic', 'topic__forum').get(id=post_id)
        
        # Handle gamification for likes
        if user_id and user_liked:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                GamificationService.handle_like_given(user, post)
            except User.DoesNotExist:
                pass
        
        # Broadcast to topic-specific group
        topic_group = f'topic_{post.topic.id}'
        broadcast_to_channel(topic_group, 'like_updated', {
            'post_id': post_id,
            'likes_count': likes_count,
            'user_liked': user_liked
        })
        
        logger.info(f"Like count updated for post {post_id}: {likes_count} likes")
        
    except Post.DoesNotExist:
        logger.error(f"Cannot broadcast like update: Post {post_id} not found")


def broadcast_user_presence(user_id, username, room_group, is_joining=True):
    """
    Broadcast user presence updates (joining/leaving rooms)
    This can be called from WebSocket consumers
    """
    presence_data = {
        'user': {
            'id': user_id,
            'username': username
        }
    }
    
    if is_joining:
        broadcast_to_channel(room_group, 'user_joined', presence_data)
        logger.debug(f"User {username} joined {room_group}")
    else:
        broadcast_to_channel(room_group, 'user_left', {
            'user_id': user_id
        })
        logger.debug(f"User {username} left {room_group}")


def broadcast_notification(user_id, notification_data):
    """
    Broadcast notifications to specific users
    """
    user_group = f'user_notifications_{user_id}'
    broadcast_to_channel(user_group, 'notification', {
        'notification': notification_data
    })
    
    logger.debug(f"Notification sent to user {user_id}")


def broadcast_custom_activity(activity_type, user_data, additional_data=None):
    """
    Broadcast custom activity to the global activity feed
    Useful for activities that don't have direct model signals
    """
    activity_data = {
        'activity': {
            'type': activity_type,
            'user': user_data,
            **(additional_data or {})
        }
    }
    
    broadcast_to_channel('forum_activity', 'activity_update', activity_data)
    logger.info(f"Custom activity broadcasted: {activity_type}")


def handle_daily_visit(user):
    """
    Handle daily visit tracking and gamification.
    Call this from middleware or views when a user visits the forum.
    """
    GamificationService.handle_daily_visit(user)
    logger.debug(f"Daily visit processed for {user.username}")