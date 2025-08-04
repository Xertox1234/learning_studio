"""
Gamification service for managing badges, points, and achievements.
"""

import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import (
    Badge, UserBadge, UserPoints, PointHistory, 
    Achievement, ForumUserAchievement, TrustLevel
)
from .notification_service import NotificationService
from machina.apps.forum_conversation.models import Post, Topic

User = get_user_model()
logger = logging.getLogger(__name__)


class GamificationService:
    """
    Service class for handling all gamification mechanics including
    badges, points, achievements, and streaks.
    """
    
    # Point values for different actions
    POINT_VALUES = {
        'first_post': 25,
        'create_post': 5,
        'create_topic': 10,
        'receive_like': 3,
        'give_like': 1,
        'daily_visit': 2,
        'reading_milestone': 5,
        'trust_level_up': 50,
        'badge_earned': 10,  # Base value, actual badge points may override
        'helpful_post': 15,
        'moderation_action': 8,
        'consecutive_days': 5,
    }
    
    @classmethod
    def initialize_user(cls, user):
        """
        Initialize gamification data for a new user.
        """
        # Create UserPoints if it doesn't exist
        user_points, created = UserPoints.objects.get_or_create(
            user=user,
            defaults={
                'total_points': 0,
                'monthly_points': 0,
                'weekly_points': 0,
                'current_streak': 0,
                'longest_streak': 0,
            }
        )
        
        if created:
            logger.info(f"Initialized gamification for user {user.username}")
        
        return user_points
    
    @classmethod
    def award_points(cls, user, action, amount=None, context=None):
        """
        Award points to a user for a specific action.
        """
        if amount is None:
            amount = cls.POINT_VALUES.get(action, 5)
        
        user_points = cls.initialize_user(user)
        user_points.add_points(amount, reason=f"Action: {action}")
        
        # Check for new badges after points are awarded
        newly_earned = cls.check_and_award_badges(user)
        
        # Check for milestone notifications
        try:
            user_points = user.points
            cls._check_points_milestone(user, user_points.total_points)
        except UserPoints.DoesNotExist:
            pass
        
        logger.info(f"Awarded {amount} points to {user.username} for {action}")
        return amount
    
    @classmethod
    def handle_post_created(cls, user, post):
        """
        Handle gamification when a user creates a post.
        """
        with transaction.atomic():
            # Award points for post creation
            is_first_post = not Post.objects.filter(poster=user).exclude(id=post.id).exists()
            
            if is_first_post:
                cls.award_points(user, 'first_post', context={'post_id': post.id})
            else:
                cls.award_points(user, 'create_post', context={'post_id': post.id})
            
            # Update activity streak
            user_points = cls.initialize_user(user)
            user_points.update_streak()
            
            # Check for badges
            cls.check_and_award_badges(user)
    
    @classmethod
    def handle_topic_created(cls, user, topic):
        """
        Handle gamification when a user creates a topic.
        """
        with transaction.atomic():
            # Award points for topic creation
            cls.award_points(user, 'create_topic', context={'topic_id': topic.id})
            
            # Update activity streak
            user_points = cls.initialize_user(user)
            user_points.update_streak()
            
            # Check for badges
            cls.check_and_award_badges(user)
    
    @classmethod
    def handle_like_given(cls, user, target_post):
        """
        Handle gamification when a user gives a like.
        """
        with transaction.atomic():
            # Award points to the liker
            cls.award_points(user, 'give_like', context={'post_id': target_post.id})
            
            # Award points to the post author
            if target_post.poster and target_post.poster != user:
                cls.award_points(
                    target_post.poster, 
                    'receive_like', 
                    context={'post_id': target_post.id, 'from_user': user.id}
                )
            
            # Check for badges for both users
            cls.check_and_award_badges(user)
            if target_post.poster and target_post.poster != user:
                cls.check_and_award_badges(target_post.poster)
    
    @classmethod
    def handle_daily_visit(cls, user):
        """
        Handle gamification for daily visits.
        """
        user_points = cls.initialize_user(user)
        today = timezone.now().date()
        
        # Only award once per day
        if user_points.last_activity_date != today:
            user_points.update_streak()
            cls.award_points(user, 'daily_visit')
            
            # Bonus points for streaks
            if user_points.current_streak % 7 == 0:  # Weekly streak bonus
                bonus = user_points.current_streak // 7 * 5
                cls.award_points(user, 'consecutive_days', amount=bonus)
            
            # Check for streak milestones
            cls._check_streak_milestone(user, user_points.current_streak)
    
    @classmethod
    def handle_trust_level_promotion(cls, user, new_level):
        """
        Handle gamification when user's trust level increases.
        """
        # Award points for trust level promotion
        points = cls.POINT_VALUES['trust_level_up'] * new_level
        cls.award_points(user, 'trust_level_up', amount=points)
        
        # Check for trust level badges
        cls.check_and_award_badges(user)
    
    @classmethod
    def check_and_award_badges(cls, user):
        """
        Check all badges and award any that the user has newly earned.
        """
        # Get all active badges the user hasn't earned yet
        earned_badge_ids = UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
        available_badges = Badge.objects.filter(
            is_active=True
        ).exclude(id__in=earned_badge_ids)
        
        newly_earned = []
        
        for badge in available_badges:
            if badge.check_condition(user):
                # Award the badge
                user_badge = UserBadge.objects.create(
                    user=user,
                    badge=badge,
                )
                
                # Send notification for badge earned
                NotificationService.notify_badge_earned(user_badge)
                
                # Award badge points (but don't trigger recursive badge checks)
                user_points = cls.initialize_user(user)
                user_points.add_points(badge.points_awarded, reason=f"Badge earned: {badge.name}")
                
                newly_earned.append(user_badge)
                logger.info(f"Awarded badge '{badge.name}' to {user.username}")
            else:
                # Check if user is close to earning this badge
                NotificationService.check_and_notify_progress(user, badge)
        
        return newly_earned
    
    @classmethod
    def check_achievements(cls, user):
        """
        Check for complex achievements that the user might have earned.
        """
        # Get achievements the user hasn't earned
        earned_achievement_ids = ForumUserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        available_achievements = Achievement.objects.filter(
            is_active=True
        ).exclude(id__in=earned_achievement_ids)
        
        newly_earned = []
        
        for achievement in available_achievements:
            if cls.check_achievement_condition(user, achievement):
                user_achievement = ForumUserAchievement.objects.create(
                    user=user,
                    achievement=achievement
                )
                
                # Send notification for achievement
                NotificationService.notify_achievement_unlocked(user_achievement)
                
                # Award points (don't trigger recursive checks)
                user_points = cls.initialize_user(user)
                user_points.add_points(achievement.points_reward, reason=f"Achievement: {achievement.name}")
                
                # Award any associated badges
                for badge in achievement.badges_granted.all():
                    if not UserBadge.objects.filter(user=user, badge=badge).exists():
                        user_badge = UserBadge.objects.create(user=user, badge=badge)
                        NotificationService.notify_badge_earned(user_badge)
                
                newly_earned.append(user_achievement)
                logger.info(f"Awarded achievement '{achievement.name}' to {user.username}")
        
        return newly_earned
    
    @classmethod
    def check_achievement_condition(cls, user, achievement):
        """
        Check if user meets complex achievement requirements.
        """
        requirements = achievement.requirements
        
        # Example requirement checking (extend as needed)
        if 'min_trust_level' in requirements:
            try:
                if user.trust_level.level < requirements['min_trust_level']:
                    return False
            except TrustLevel.DoesNotExist:
                return False
        
        if 'min_badges' in requirements:
            badge_count = UserBadge.objects.filter(user=user).count()
            if badge_count < requirements['min_badges']:
                return False
        
        if 'min_points' in requirements:
            try:
                if user.points.total_points < requirements['min_points']:
                    return False
            except UserPoints.DoesNotExist:
                return False
        
        if 'min_streak' in requirements:
            try:
                if user.points.current_streak < requirements['min_streak']:
                    return False
            except UserPoints.DoesNotExist:
                return False
        
        # Add more complex requirements as needed
        return True
    
    @classmethod
    def get_user_stats(cls, user):
        """
        Get comprehensive gamification stats for a user.
        """
        try:
            user_points = user.points
        except UserPoints.DoesNotExist:
            user_points = cls.initialize_user(user)
        
        try:
            trust_level = user.trust_level
        except TrustLevel.DoesNotExist:
            trust_level = None
        
        badges = UserBadge.objects.filter(user=user).select_related('badge', 'badge__category')
        achievements = ForumUserAchievement.objects.filter(user=user).select_related('achievement')
        
        # Calculate badge stats by rarity
        badge_stats = {}
        for badge in badges:
            rarity = badge.badge.rarity
            badge_stats[rarity] = badge_stats.get(rarity, 0) + 1
        
        return {
            'points': {
                'total': user_points.total_points,
                'monthly': user_points.monthly_points,
                'weekly': user_points.weekly_points,
                'rank': user_points.global_rank,
            },
            'streaks': {
                'current': user_points.current_streak,
                'longest': user_points.longest_streak,
                'last_activity': user_points.last_activity_date,
            },
            'badges': {
                'total': badges.count(),
                'by_rarity': badge_stats,
                'recent': badges[:5],  # 5 most recent
            },
            'achievements': {
                'total': achievements.count(),
                'recent': achievements[:3],  # 3 most recent
            },
            'trust_level': {
                'level': trust_level.level if trust_level else 0,
                'name': trust_level.get_level_display() if trust_level else 'New User',
            }
        }
    
    @classmethod
    def get_leaderboard(cls, timeframe='all_time', limit=10):
        """
        Get leaderboard data for specified timeframe.
        """
        if timeframe == 'monthly':
            queryset = UserPoints.objects.filter(
                monthly_points__gt=0
            ).order_by('-monthly_points')
        elif timeframe == 'weekly':
            queryset = UserPoints.objects.filter(
                weekly_points__gt=0
            ).order_by('-weekly_points')
        else:  # all_time
            queryset = UserPoints.objects.filter(
                total_points__gt=0
            ).order_by('-total_points')
        
        return queryset.select_related('user')[:limit]
    
    @classmethod
    def update_leaderboard_ranks(cls):
        """
        Update cached leaderboard ranks for all users.
        """
        # Update global ranks
        for rank, user_points in enumerate(
            UserPoints.objects.order_by('-total_points'), 1
        ):
            user_points.global_rank = rank
            user_points.save(update_fields=['global_rank'])
        
        # Update monthly ranks
        for rank, user_points in enumerate(
            UserPoints.objects.filter(monthly_points__gt=0).order_by('-monthly_points'), 1
        ):
            user_points.monthly_rank = rank
            user_points.save(update_fields=['monthly_rank'])
    
    @classmethod
    def reset_weekly_points(cls):
        """
        Reset weekly points for all users (run weekly via cron).
        """
        UserPoints.objects.all().update(weekly_points=0)
        logger.info("Reset weekly points for all users")
    
    @classmethod
    def reset_monthly_points(cls):
        """
        Reset monthly points for all users (run monthly via cron).
        """
        UserPoints.objects.all().update(monthly_points=0, monthly_rank=None)
        logger.info("Reset monthly points for all users")
    
    @classmethod
    def create_default_badges(cls):
        """
        Create default badge set for the forum.
        """
        from .models import BadgeCategory
        
        # Create categories
        categories = {
            'participation': BadgeCategory.objects.get_or_create(
                name='Participation',
                defaults={
                    'description': 'Badges for active participation in the community',
                    'icon': 'bi-chat-dots',
                    'color': '#198754',
                    'sort_order': 1
                }
            )[0],
            'quality': BadgeCategory.objects.get_or_create(
                name='Quality',
                defaults={
                    'description': 'Badges for high-quality contributions',
                    'icon': 'bi-star',
                    'color': '#fd7e14',
                    'sort_order': 2
                }
            )[0],
            'dedication': BadgeCategory.objects.get_or_create(
                name='Dedication',
                defaults={
                    'description': 'Badges for long-term commitment',
                    'icon': 'bi-calendar-check',
                    'color': '#6f42c1',
                    'sort_order': 3
                }
            )[0],
            'moderation': BadgeCategory.objects.get_or_create(
                name='Moderation',
                defaults={
                    'description': 'Badges for community moderation',
                    'icon': 'bi-shield-check',
                    'color': '#dc3545',
                    'sort_order': 4
                }
            )[0],
            'special': BadgeCategory.objects.get_or_create(
                name='Special',
                defaults={
                    'description': 'Special and rare badges',
                    'icon': 'bi-gem',
                    'color': '#ffd700',
                    'sort_order': 5
                }
            )[0],
        }
        
        # Default badges to create
        default_badges = [
            # Participation badges
            {
                'name': 'First Post',
                'description': 'Created your first forum post',
                'category': categories['participation'],
                'condition_type': 'first_post',
                'condition_value': 1,
                'rarity': 'common',
                'points_awarded': 25,
                'icon': 'bi-pencil-square',
            },
            {
                'name': 'Conversationalist',
                'description': 'Created 10 forum posts',
                'category': categories['participation'],
                'condition_type': 'posts_created',
                'condition_value': 10,
                'rarity': 'common',
                'points_awarded': 15,
                'icon': 'bi-chat',
            },
            {
                'name': 'Active Poster',
                'description': 'Created 50 forum posts',
                'category': categories['participation'],
                'condition_type': 'posts_created',
                'condition_value': 50,
                'rarity': 'uncommon',
                'points_awarded': 25,
                'icon': 'bi-chat-fill',
            },
            {
                'name': 'Topic Starter',
                'description': 'Started 5 new topics',
                'category': categories['participation'],
                'condition_type': 'topics_created',
                'condition_value': 5,
                'rarity': 'common',
                'points_awarded': 20,
                'icon': 'bi-plus-circle',
            },
            
            # Quality badges
            {
                'name': 'Nice Reply',
                'description': 'Received 10 likes on your posts',
                'category': categories['quality'],
                'condition_type': 'likes_received',
                'condition_value': 10,
                'rarity': 'uncommon',
                'points_awarded': 30,
                'icon': 'bi-hand-thumbs-up',
            },
            {
                'name': 'Great Answer',
                'description': 'Received 50 likes on your posts',
                'category': categories['quality'],
                'condition_type': 'likes_received',
                'condition_value': 50,
                'rarity': 'rare',
                'points_awarded': 50,
                'icon': 'bi-star-fill',
            },
            {
                'name': 'Supporter',
                'description': 'Gave 25 likes to other posts',
                'category': categories['quality'],
                'condition_type': 'likes_given',
                'condition_value': 25,
                'rarity': 'common',
                'points_awarded': 15,
                'icon': 'bi-heart',
            },
            
            # Dedication badges
            {
                'name': 'Regular Visitor',
                'description': 'Visited the forum for 7 days',
                'category': categories['dedication'],
                'condition_type': 'days_visited',
                'condition_value': 7,
                'rarity': 'common',
                'points_awarded': 20,
                'icon': 'bi-calendar',
            },
            {
                'name': 'Dedicated Member',
                'description': 'Visited the forum for 30 days',
                'category': categories['dedication'],
                'condition_type': 'days_visited',
                'condition_value': 30,
                'rarity': 'uncommon',
                'points_awarded': 40,
                'icon': 'bi-calendar-check',
            },
            {
                'name': 'Bookworm',
                'description': 'Spent 10 hours reading forum content',
                'category': categories['dedication'],
                'condition_type': 'reading_time',
                'condition_value': 10,
                'rarity': 'uncommon',
                'points_awarded': 35,
                'icon': 'bi-book',
            },
            
            # Trust level badges
            {
                'name': 'Trusted Member',
                'description': 'Reached Trust Level 2',
                'category': categories['special'],
                'condition_type': 'trust_level',
                'condition_value': 2,
                'rarity': 'rare',
                'points_awarded': 75,
                'icon': 'bi-shield',
            },
            {
                'name': 'Community Leader',
                'description': 'Reached Trust Level 3',
                'category': categories['special'],
                'condition_type': 'trust_level',
                'condition_value': 3,
                'rarity': 'epic',
                'points_awarded': 100,
                'icon': 'bi-star',
            },
            
            # Moderation badges
            {
                'name': 'Helper',
                'description': 'Performed 10 moderation actions',
                'category': categories['moderation'],
                'condition_type': 'moderation_actions',
                'condition_value': 10,
                'rarity': 'rare',
                'points_awarded': 50,
                'icon': 'bi-person-check',
            },
        ]
        
        created_count = 0
        for badge_data in default_badges:
            badge, created = Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            if created:
                created_count += 1
        
        logger.info(f"Created {created_count} default badges")
        return created_count
    
    @classmethod
    def _check_points_milestone(cls, user, total_points):
        """Check and notify for points milestones."""
        milestones = [100, 500, 1000, 5000, 10000, 25000, 50000, 100000]
        for milestone in milestones:
            if total_points >= milestone:
                # Check if we just reached this milestone (within recent points)
                recent_history = PointHistory.objects.filter(user=user).order_by('-timestamp')[:5]
                for entry in recent_history:
                    if entry.new_total - entry.points_change < milestone <= entry.new_total:
                        NotificationService.notify_milestone_reached(user, 'points', milestone)
                        break
    
    @classmethod
    def _check_streak_milestone(cls, user, current_streak):
        """Check and notify for streak milestones."""
        milestones = [7, 30, 60, 90, 180, 365]
        if current_streak in milestones:
            NotificationService.notify_milestone_reached(user, 'streak', current_streak)
    
    @classmethod
    def _check_badge_collection_milestone(cls, user, badge_count):
        """Check and notify for badge collection milestones."""
        milestones = [5, 10, 25, 50, 100]
        if badge_count in milestones:
            NotificationService.notify_milestone_reached(user, 'badges', badge_count)