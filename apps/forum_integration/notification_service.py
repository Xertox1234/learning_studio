"""
Badge notification and celebration service for real-time achievement alerts.
"""

import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import UserBadge, Badge, UserPoints, Achievement, ForumUserAchievement

User = get_user_model()
logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


class NotificationService:
    """
    Service for handling badge notifications, celebrations, and real-time alerts.
    """
    
    @classmethod
    def notify_badge_earned(cls, user_badge):
        """
        Send real-time notification when a user earns a badge.
        """
        badge = user_badge.badge
        user = user_badge.user
        
        # Prepare notification data
        notification_data = {
            'type': 'badge_earned',
            'badge': {
                'id': badge.id,
                'name': badge.name,
                'description': badge.description,
                'icon': badge.icon,
                'color': badge.color,
                'rarity': badge.rarity,
                'rarity_display': badge.get_rarity_display(),
                'points_awarded': badge.points_awarded,
                'category': badge.category.name,
            },
            'earned_at': user_badge.earned_at.isoformat(),
            'celebration_type': cls._get_celebration_type(badge),
        }
        
        # Send to user's personal notification channel
        cls._send_user_notification(user.id, notification_data)
        
        # Broadcast to public activity feed for legendary badges
        if badge.rarity in ['epic', 'legendary']:
            cls._broadcast_achievement(user, badge)
        
        # Mark notification as sent
        user_badge.notification_sent = True
        user_badge.save(update_fields=['notification_sent'])
        
        logger.info(f"Badge notification sent: {user.username} earned {badge.name}")
    
    @classmethod
    def notify_achievement_unlocked(cls, user_achievement):
        """
        Send notification for special achievements.
        """
        achievement = user_achievement.achievement
        user = user_achievement.user
        
        notification_data = {
            'type': 'achievement_unlocked',
            'achievement': {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'color': achievement.color,
                'points_reward': achievement.points_reward,
                'achievement_type': achievement.achievement_type,
            },
            'earned_at': user_achievement.earned_at.isoformat(),
            'celebration_type': 'fireworks',
        }
        
        cls._send_user_notification(user.id, notification_data)
        cls._broadcast_achievement(user, achievement, is_achievement=True)
        
        logger.info(f"Achievement notification sent: {user.username} unlocked {achievement.name}")
    
    @classmethod
    def notify_milestone_reached(cls, user, milestone_type, value):
        """
        Notify user of milestone achievements (e.g., 1000 points, 100 day streak).
        """
        milestone_configs = {
            'points': {
                'milestones': [100, 500, 1000, 5000, 10000, 25000, 50000, 100000],
                'icon': 'bi-star-fill',
                'color': '#ffd700',
                'title': 'Points Milestone',
            },
            'streak': {
                'milestones': [7, 30, 60, 90, 180, 365],
                'icon': 'bi-calendar-check',
                'color': '#28a745',
                'title': 'Streak Milestone',
            },
            'badges': {
                'milestones': [5, 10, 25, 50, 100],
                'icon': 'bi-award',
                'color': '#007bff',
                'title': 'Badge Collection Milestone',
            },
            'posts': {
                'milestones': [10, 50, 100, 500, 1000, 5000],
                'icon': 'bi-chat-dots',
                'color': '#17a2b8',
                'title': 'Post Milestone',
            },
        }
        
        config = milestone_configs.get(milestone_type)
        if not config or value not in config['milestones']:
            return
        
        notification_data = {
            'type': 'milestone_reached',
            'milestone': {
                'type': milestone_type,
                'value': value,
                'title': config['title'],
                'icon': config['icon'],
                'color': config['color'],
                'message': f"You've reached {value} {milestone_type}!",
            },
            'celebration_type': 'confetti' if value >= 1000 else 'sparkle',
        }
        
        cls._send_user_notification(user.id, notification_data)
        logger.info(f"Milestone notification sent: {user.username} reached {value} {milestone_type}")
    
    @classmethod
    def notify_leaderboard_change(cls, user, new_rank, old_rank, timeframe='global'):
        """
        Notify user when they move up in the leaderboard.
        """
        if new_rank >= old_rank:  # Only notify on improvement
            return
        
        # Special notifications for top positions
        special_messages = {
            1: "🥇 You're now #1 on the leaderboard!",
            2: "🥈 You've reached 2nd place!",
            3: "🥉 You've made it to 3rd place!",
        }
        
        notification_data = {
            'type': 'leaderboard_update',
            'leaderboard': {
                'timeframe': timeframe,
                'old_rank': old_rank,
                'new_rank': new_rank,
                'message': special_messages.get(new_rank, f"You've climbed to #{new_rank}!"),
                'icon': 'bi-graph-up-arrow',
                'color': '#28a745',
            },
            'celebration_type': 'bounce' if new_rank <= 10 else None,
        }
        
        cls._send_user_notification(user.id, notification_data)
        
        # Broadcast to activity feed for top 3
        if new_rank <= 3:
            cls._broadcast_leaderboard_achievement(user, new_rank, timeframe)
    
    @classmethod
    def check_and_notify_progress(cls, user, badge):
        """
        Check if user is close to earning a badge and send progress notification.
        """
        if UserBadge.objects.filter(user=user, badge=badge).exists():
            return
        
        progress = badge.calculate_progress(user)
        percentage = (progress / badge.condition_value * 100) if badge.condition_value > 0 else 0
        
        # Notify at 50%, 75%, and 90% progress
        thresholds = [50, 75, 90]
        for threshold in thresholds:
            if percentage >= threshold and percentage < threshold + 5:
                notification_data = {
                    'type': 'badge_progress',
                    'badge': {
                        'id': badge.id,
                        'name': badge.name,
                        'icon': badge.icon,
                        'progress': progress,
                        'required': badge.condition_value,
                        'percentage': int(percentage),
                        'threshold': threshold,
                    },
                    'message': f"You're {int(percentage)}% of the way to earning {badge.name}!",
                }
                
                cls._send_user_notification(user.id, notification_data)
                break
    
    @classmethod
    def _send_user_notification(cls, user_id, notification_data):
        """
        Send notification to user's personal channel.
        """
        if not channel_layer:
            logger.warning("Channel layer not available for notifications")
            return
        
        try:
            # Add timestamp
            notification_data['timestamp'] = timezone.now().isoformat()
            
            # Send to user's notification channel
            async_to_sync(channel_layer.group_send)(
                f'user_notifications_{user_id}',
                {
                    'type': 'notification_message',
                    **notification_data
                }
            )
            
            # Also send to user's active session channel
            async_to_sync(channel_layer.group_send)(
                f'user_{user_id}',
                {
                    'type': 'notification_message',
                    **notification_data
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
    
    @classmethod
    def _broadcast_achievement(cls, user, badge_or_achievement, is_achievement=False):
        """
        Broadcast major achievements to public activity feed.
        """
        if not channel_layer:
            return
        
        try:
            if is_achievement:
                activity_data = {
                    'type': 'public_achievement',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                    },
                    'achievement': {
                        'name': badge_or_achievement.name,
                        'description': badge_or_achievement.description,
                        'icon': badge_or_achievement.icon,
                        'color': badge_or_achievement.color,
                    },
                    'message': f"{user.username} unlocked {badge_or_achievement.name}!",
                }
            else:
                activity_data = {
                    'type': 'public_badge',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                    },
                    'badge': {
                        'name': badge_or_achievement.name,
                        'rarity': badge_or_achievement.get_rarity_display(),
                        'icon': badge_or_achievement.icon,
                        'color': badge_or_achievement.color,
                    },
                    'message': f"{user.username} earned the {badge_or_achievement.get_rarity_display()} badge: {badge_or_achievement.name}!",
                }
            
            async_to_sync(channel_layer.group_send)(
                'forum_activity',
                {
                    'type': 'activity_update',
                    'activity': activity_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error broadcasting achievement: {e}")
    
    @classmethod
    def _broadcast_leaderboard_achievement(cls, user, rank, timeframe):
        """
        Broadcast leaderboard achievements to activity feed.
        """
        if not channel_layer:
            return
        
        rank_emojis = {1: '🥇', 2: '🥈', 3: '🥉'}
        
        try:
            activity_data = {
                'type': 'leaderboard_achievement',
                'user': {
                    'id': user.id,
                    'username': user.username,
                },
                'rank': rank,
                'emoji': rank_emojis.get(rank, '🏆'),
                'timeframe': timeframe,
                'message': f"{rank_emojis.get(rank, '🏆')} {user.username} is now #{rank} on the {timeframe} leaderboard!",
            }
            
            async_to_sync(channel_layer.group_send)(
                'forum_activity',
                {
                    'type': 'activity_update',
                    'activity': activity_data,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error broadcasting leaderboard achievement: {e}")
    
    @classmethod
    def _get_celebration_type(cls, badge):
        """
        Determine celebration animation based on badge rarity.
        """
        celebrations = {
            'common': 'sparkle',
            'uncommon': 'bounce',
            'rare': 'confetti',
            'epic': 'fireworks',
            'legendary': 'epic_celebration',
        }
        return celebrations.get(badge.rarity, 'sparkle')
    
    @classmethod
    def get_pending_notifications(cls, user):
        """
        Get all pending notifications for a user.
        """
        # Get unnotified badges
        pending_badges = UserBadge.objects.filter(
            user=user,
            notification_sent=False
        ).select_related('badge', 'badge__category')
        
        notifications = []
        for user_badge in pending_badges:
            notifications.append({
                'type': 'badge_earned',
                'badge': {
                    'id': user_badge.badge.id,
                    'name': user_badge.badge.name,
                    'description': user_badge.badge.description,
                    'icon': user_badge.badge.icon,
                    'color': user_badge.badge.color,
                    'rarity': user_badge.badge.rarity,
                    'rarity_display': user_badge.badge.get_rarity_display(),
                    'points_awarded': user_badge.badge.points_awarded,
                },
                'earned_at': user_badge.earned_at.isoformat(),
            })
        
        return notifications