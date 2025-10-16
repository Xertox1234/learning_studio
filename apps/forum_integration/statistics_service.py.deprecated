"""
Centralized forum statistics service for consistent stats across the platform
"""
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.cache import cache
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post

User = get_user_model()


class ForumStatisticsService:
    """Service for calculating and caching forum statistics"""
    
    CACHE_TIMEOUT = 60  # Cache for 1 minute
    ONLINE_THRESHOLD_MINUTES = 15  # Users active in last 15 minutes
    
    @classmethod
    def get_online_users_count(cls):
        """Get count of users active in the last 15 minutes - LIVE (no cache)"""
        online_threshold = timezone.now() - timedelta(minutes=cls.ONLINE_THRESHOLD_MINUTES)
        return User.objects.filter(
            is_active=True,
            last_login__gte=online_threshold
        ).count()
    
    @classmethod
    def get_online_users_list(cls, limit=5):
        """Get list of recently active users - LIVE (no cache)"""
        online_threshold = timezone.now() - timedelta(minutes=cls.ONLINE_THRESHOLD_MINUTES)
        return list(User.objects.filter(
            is_active=True,
            last_login__gte=online_threshold
        ).order_by('-last_login')[:limit])
    
    @classmethod
    def get_forum_statistics(cls):
        """Get overall forum statistics - Mixed live and cached data"""
        cache_key = 'forum:static_stats'
        static_stats = cache.get(cache_key)
        
        if static_stats is None:
            # Cache only truly static data that doesn't change often
            static_stats = {
                'total_users': User.objects.filter(is_active=True).count(),
                'latest_member': User.objects.filter(is_active=True).order_by('-date_joined').first()
            }
            cache.set(cache_key, static_stats, cls.CACHE_TIMEOUT * 5)  # Cache longer for static data
        
        # Always get live data for topics, posts, and online users
        return {
            'total_topics': Topic.objects.filter(approved=True).count(),
            'total_posts': Post.objects.filter(approved=True).count(),
            'total_users': static_stats['total_users'],
            'online_users': cls.get_online_users_count(),
            'latest_member': static_stats['latest_member']
        }
    
    @classmethod
    def get_forum_specific_stats(cls, forum_id):
        """Get statistics for a specific forum - LIVE data for activity"""
        try:
            forum = Forum.objects.get(id=forum_id)
            
            # Always calculate live activity data
            week_ago = timezone.now() - timedelta(days=7)
            weekly_posts = Post.objects.filter(
                topic__forum=forum,
                approved=True,
                created__gte=week_ago
            ).count()
            
            # Calculate online users for this forum (users who posted recently)
            online_threshold = timezone.now() - timedelta(minutes=cls.ONLINE_THRESHOLD_MINUTES)
            forum_online_users = User.objects.filter(
                is_active=True,
                post__topic__forum=forum,
                post__created__gte=online_threshold
            ).distinct().count()
            
            return {
                'topics_count': forum.direct_topics_count,  # This comes from tracker fields
                'posts_count': forum.direct_posts_count,   # This comes from tracker fields
                'weekly_posts': weekly_posts,              # Live data
                'online_users': forum_online_users,        # Live data
                'trending': weekly_posts > 5               # Live calculation
            }
        except Forum.DoesNotExist:
            return {
                'topics_count': 0,
                'posts_count': 0,
                'weekly_posts': 0,
                'online_users': 0,
                'trending': False
            }
    
    @classmethod
    def invalidate_cache(cls, forum_id=None):
        """Invalidate statistics cache - only static data is cached now"""
        # Only invalidate the static stats cache (users and latest member)
        cache.delete('forum:static_stats')
        
        # Note: Most data is now live, so less cache invalidation needed
    
    @classmethod
    def get_user_forum_stats(cls, user):
        """Get forum statistics for a specific user"""
        cache_key = f'forum:user_stats:{user.id}'
        stats = cache.get(cache_key)
        
        if stats is None:
            stats = {
                'topics_count': Topic.objects.filter(poster=user, approved=True).count(),
                'posts_count': Post.objects.filter(poster=user, approved=True).count(),
                'last_post': Post.objects.filter(poster=user, approved=True).order_by('-created').first(),
                'last_topic': Topic.objects.filter(poster=user, approved=True).order_by('-created').first(),
            }
            cache.set(cache_key, stats, cls.CACHE_TIMEOUT * 5)  # Cache user stats for 5 minutes
        
        return stats


# Create a singleton instance
forum_stats_service = ForumStatisticsService()