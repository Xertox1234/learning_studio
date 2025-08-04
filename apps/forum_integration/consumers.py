"""
WebSocket consumers for real-time forum functionality
"""

import json
import logging
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from .notification_service import NotificationService

logger = logging.getLogger(__name__)
User = get_user_model()


class BaseForumConsumer(AsyncWebsocketConsumer):
    """Base consumer with common functionality"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.user = None
        self.last_heartbeat = timezone.now()
        
    async def connect(self):
        """Handle WebSocket connection"""
        # Get user from scope
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # Join room group
        if self.room_group_name:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
        await self.accept()
        
        # Track user as online
        await self.update_user_presence(online=True)
        
        # Send initial data
        await self.send_initial_data()
        
        logger.info(f"User {self.user.username} connected to {self.room_group_name}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
        # Update user presence
        await self.update_user_presence(online=False)
        
        logger.info(f"User {self.user.username if self.user else 'Anonymous'} disconnected from {self.room_group_name}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Handle different message types
            if message_type == 'heartbeat':
                await self.handle_heartbeat(data)
            elif message_type == 'typing_start':
                await self.handle_typing_start(data)
            elif message_type == 'typing_stop':
                await self.handle_typing_stop(data)
            elif message_type == 'user_activity':
                await self.handle_user_activity(data)
            else:
                await self.handle_custom_message(data)
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def send_initial_data(self):
        """Send initial data when user connects"""
        pass  # Override in subclasses
    
    async def handle_custom_message(self, data):
        """Handle custom message types - override in subclasses"""
        pass
    
    async def handle_heartbeat(self, data):
        """Handle heartbeat messages"""
        self.last_heartbeat = timezone.now()
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_ack',
            'timestamp': self.last_heartbeat.isoformat()
        }))
    
    async def handle_typing_start(self, data):
        """Handle typing start notifications"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_notification',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': True,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def handle_typing_stop(self, data):
        """Handle typing stop notifications"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_notification',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': False,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def handle_user_activity(self, data):
        """Handle user activity updates"""
        # Track user activity in cache
        cache_key = f"user_activity_{self.user.id}"
        cache.set(cache_key, {
            'last_seen': timezone.now().isoformat(),
            'current_page': data.get('page'),
            'action': data.get('action')
        }, 300)  # 5 minutes
    
    async def update_user_presence(self, online=True):
        """Update user's online presence"""
        if not self.user:
            return
            
        cache_key = f"user_online_{self.user.id}"
        if online:
            cache.set(cache_key, {
                'user_id': self.user.id,
                'username': self.user.username,
                'last_seen': timezone.now().isoformat(),
                'room': self.room_group_name
            }, 300)  # 5 minutes
        else:
            cache.delete(cache_key)
    
    async def typing_notification(self, event):
        """Send typing notification to WebSocket"""
        if event['user_id'] != self.user.id:  # Don't send to the typing user
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing'],
                'timestamp': event['timestamp']
            }))


class TopicConsumer(BaseForumConsumer):
    """WebSocket consumer for real-time topic updates"""
    
    async def connect(self):
        """Handle connection to a specific topic"""
        self.topic_id = self.scope['url_route']['kwargs']['topic_id']
        self.room_group_name = f'topic_{self.topic_id}'
        
        await super().connect()
    
    async def send_initial_data(self):
        """Send initial topic data"""
        topic_data = await self.get_topic_data()
        online_users = await self.get_online_users()
        
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'topic': topic_data,
            'online_users': online_users,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_topic_data(self):
        """Get topic information"""
        try:
            from machina.apps.forum_conversation.models import Topic
            topic = Topic.objects.select_related('forum', 'poster').get(id=self.topic_id)
            
            return {
                'id': topic.id,
                'subject': topic.subject,
                'posts_count': topic.posts_count,
                'views_count': getattr(topic, 'views_count', 0),
                'is_locked': topic.is_locked,
                'is_sticky': topic.is_sticky,
                'forum': {
                    'id': topic.forum.id,
                    'name': topic.forum.name
                }
            }
        except Exception as e:
            logger.error(f"Error getting topic data: {e}")
            return None
    
    async def get_online_users(self):
        """Get list of users currently viewing this topic"""
        online_users = []
        
        # Get all online users in this room
        cache_pattern = f"user_online_*"
        for key in cache._cache.keys():
            if key.startswith('user_online_'):
                user_data = cache.get(key)
                if user_data and user_data.get('room') == self.room_group_name:
                    online_users.append({
                        'id': user_data['user_id'],
                        'username': user_data['username'],
                        'last_seen': user_data['last_seen']
                    })
        
        return online_users
    
    # Group message handlers
    async def new_post(self, event):
        """Handle new post notifications"""
        await self.send(text_data=json.dumps({
            'type': 'new_post',
            'post': event['post'],
            'timestamp': event['timestamp']
        }))
    
    async def post_updated(self, event):
        """Handle post update notifications"""
        await self.send(text_data=json.dumps({
            'type': 'post_updated',
            'post': event['post'],
            'timestamp': event['timestamp']
        }))
    
    async def post_deleted(self, event):
        """Handle post deletion notifications"""
        await self.send(text_data=json.dumps({
            'type': 'post_deleted',
            'post_id': event['post_id'],
            'timestamp': event['timestamp']
        }))
    
    async def like_updated(self, event):
        """Handle like count updates"""
        await self.send(text_data=json.dumps({
            'type': 'like_updated',
            'post_id': event['post_id'],
            'likes_count': event['likes_count'],
            'user_liked': event.get('user_liked', False),
            'timestamp': event['timestamp']
        }))
    
    async def user_joined(self, event):
        """Handle user joining topic"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user': event['user'],
            'timestamp': event['timestamp']
        }))
    
    async def user_left(self, event):
        """Handle user leaving topic"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))


class ForumConsumer(BaseForumConsumer):
    """WebSocket consumer for forum-wide updates"""
    
    async def connect(self):
        """Handle connection to a forum"""
        self.forum_id = self.scope['url_route']['kwargs']['forum_id']
        self.room_group_name = f'forum_{self.forum_id}'
        
        await super().connect()
    
    async def send_initial_data(self):
        """Send initial forum data"""
        forum_data = await self.get_forum_data()
        recent_topics = await self.get_recent_topics()
        
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'forum': forum_data,
            'recent_topics': recent_topics,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_forum_data(self):
        """Get forum information"""
        try:
            from machina.apps.forum.models import Forum
            forum = Forum.objects.get(id=self.forum_id)
            
            return {
                'id': forum.id,
                'name': forum.name,
                'description': getattr(forum, 'description', ''),
                'topics_count': getattr(forum, 'topics_count', 0),
                'posts_count': getattr(forum, 'posts_count', 0)
            }
        except Exception as e:
            logger.error(f"Error getting forum data: {e}")
            return None
    
    @database_sync_to_async
    def get_recent_topics(self):
        """Get recent topics in this forum"""
        try:
            from machina.apps.forum_conversation.models import Topic
            topics = Topic.objects.filter(
                forum_id=self.forum_id,
                approved=True
            ).select_related('poster', 'last_post', 'last_post__poster').order_by('-last_post_on')[:10]
            
            return [{
                'id': topic.id,
                'subject': topic.subject,
                'posts_count': topic.posts_count,
                'views_count': getattr(topic, 'views_count', 0),
                'poster': {
                    'id': topic.poster.id if topic.poster else None,
                    'username': topic.poster.username if topic.poster else 'Unknown'
                },
                'last_post': {
                    'id': topic.last_post.id if topic.last_post else None,
                    'created': topic.last_post.created.isoformat() if topic.last_post else None,
                    'poster': {
                        'username': topic.last_post.poster.username if topic.last_post and topic.last_post.poster else 'Unknown'
                    }
                } if topic.last_post else None
            } for topic in topics]
        except Exception as e:
            logger.error(f"Error getting recent topics: {e}")
            return []
    
    # Group message handlers
    async def new_topic(self, event):
        """Handle new topic notifications"""
        await self.send(text_data=json.dumps({
            'type': 'new_topic',
            'topic': event['topic'],
            'timestamp': event['timestamp']
        }))
    
    async def topic_updated(self, event):
        """Handle topic update notifications"""
        await self.send(text_data=json.dumps({
            'type': 'topic_updated',
            'topic': event['topic'],
            'timestamp': event['timestamp']
        }))


class NotificationConsumer(BaseForumConsumer):
    """WebSocket consumer for user notifications and badge celebrations"""
    
    async def connect(self):
        """Handle connection for user notifications"""
        if not self.scope['user'].is_authenticated:
            await self.close()
            return
            
        self.user = self.scope['user']
        self.room_group_name = f'user_notifications_{self.user.id}'
        self.user_group_name = f'user_{self.user.id}'
        
        # Join both notification groups
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send pending notifications
        await self.send_pending_notifications()
        
        logger.debug(f"Notification WebSocket connected for user {self.user.username}")
    
    async def disconnect(self, close_code):
        """Leave notification groups when disconnecting."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        logger.debug(f"Notification WebSocket disconnected for user {getattr(self.user, 'username', 'unknown')}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            
            elif message_type == 'mark_notifications_read':
                await self.mark_notifications_read()
            
            elif message_type == 'request_pending':
                await self.send_pending_notifications()
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from WebSocket: {text_data}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    async def send_initial_data(self):
        """Send initial notification data"""
        unread_count = await self.get_unread_notifications_count()
        
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'unread_count': unread_count,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_unread_notifications_count(self):
        """Get count of unread notifications"""
        from .models import UserBadge
        return UserBadge.objects.filter(
            user=self.user,
            notification_sent=False
        ).count()
    
    @database_sync_to_async
    def get_pending_notifications(self):
        """Get pending notifications for the user."""
        return NotificationService.get_pending_notifications(self.user)
    
    @database_sync_to_async
    def mark_notifications_read(self):
        """Mark user's notifications as read."""
        from .models import UserBadge
        UserBadge.objects.filter(
            user=self.user,
            notification_sent=False
        ).update(notification_sent=True)
    
    async def send_pending_notifications(self):
        """Send any pending notifications to the client."""
        try:
            pending = await self.get_pending_notifications()
            
            for notification in pending:
                await self.send(text_data=json.dumps(notification))
            
            # Mark them as sent
            if pending:
                await self.mark_notifications_read()
                
        except Exception as e:
            logger.error(f"Error sending pending notifications: {e}")
    
    # Group message handlers
    async def notification(self, event):
        """Handle new notification"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification'],
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))
    
    async def notification_message(self, event):
        """Send notification message to WebSocket client."""
        await self.send(text_data=json.dumps(event))
    
    async def badge_earned(self, event):
        """Handle badge earned notifications."""
        await self.send(text_data=json.dumps({
            'type': 'badge_earned',
            **event
        }))
    
    async def achievement_unlocked(self, event):
        """Handle achievement unlocked notifications."""
        await self.send(text_data=json.dumps({
            'type': 'achievement_unlocked',
            **event
        }))
    
    async def milestone_reached(self, event):
        """Handle milestone notifications."""
        await self.send(text_data=json.dumps({
            'type': 'milestone_reached',
            **event
        }))
    
    async def leaderboard_update(self, event):
        """Handle leaderboard position updates."""
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_update',
            **event
        }))
    
    async def badge_progress(self, event):
        """Handle badge progress notifications."""
        await self.send(text_data=json.dumps({
            'type': 'badge_progress',
            **event
        }))


class ActivityConsumer(BaseForumConsumer):
    """WebSocket consumer for global forum activity"""
    
    async def connect(self):
        """Handle connection for global activity"""
        self.room_group_name = 'forum_activity'
        
        await super().connect()
    
    async def send_initial_data(self):
        """Send initial activity data"""
        recent_activity = await self.get_recent_activity()
        online_users_count = await self.get_online_users_count()
        
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'recent_activity': recent_activity,
            'online_users_count': online_users_count,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_recent_activity(self):
        """Get recent forum activity"""
        # This would typically query recent posts, topics, etc.
        return []
    
    async def get_online_users_count(self):
        """Get count of online users"""
        count = 0
        cache_pattern = "user_online_*"
        
        # Count all online users
        for key in cache._cache.keys():
            if key.startswith('user_online_'):
                if cache.get(key):
                    count += 1
        
        return count
    
    # Group message handlers
    async def activity_update(self, event):
        """Handle activity updates"""
        await self.send(text_data=json.dumps({
            'type': 'activity_update',
            'activity': event['activity'],
            'timestamp': event['timestamp']
        }))