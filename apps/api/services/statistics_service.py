"""
Refactored Forum Statistics Service with Dependency Injection and Redis Caching.

This service provides optimized forum statistics using:
- Repository pattern for data access (eliminates N+1 queries)
- Redis caching for hot paths
- Dependency injection for testability
- Cache versioning for easy invalidation

Usage:
    from apps.api.services.container import container

    stats_service = container.get_statistics_service()
    overall_stats = stats_service.get_forum_statistics()
    forum_stats = stats_service.get_forum_specific_stats(forum_id=1)
"""

from datetime import timedelta
from typing import Dict, Any, Optional, List
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class ForumStatisticsService:
    """
    Service for calculating and caching forum statistics.

    Uses dependency injection for repositories and cache backend.
    All methods are cacheable with configurable TTLs.
    """

    # Cache timeouts (in seconds)
    CACHE_TIMEOUT_SHORT = 60        # 1 minute - for frequently changing data
    CACHE_TIMEOUT_MEDIUM = 300      # 5 minutes - for user stats
    CACHE_TIMEOUT_LONG = 900        # 15 minutes - for static data

    # Cache version for easy invalidation
    CACHE_VERSION = 'v1'

    # Online user threshold
    ONLINE_THRESHOLD_MINUTES = 15

    def __init__(
        self,
        user_repo,
        topic_repo,
        post_repo,
        forum_repo,
        cache
    ):
        """
        Initialize statistics service with dependencies.

        Args:
            user_repo: UserRepository instance
            topic_repo: TopicRepository instance
            post_repo: PostRepository instance
            forum_repo: ForumRepository instance
            cache: Django cache backend (Redis)
        """
        self.user_repo = user_repo
        self.topic_repo = topic_repo
        self.post_repo = post_repo
        self.forum_repo = forum_repo
        self.cache = cache

    # ========================================
    # Overall Forum Statistics
    # ========================================

    def get_forum_statistics(self) -> Dict[str, Any]:
        """
        Get overall forum statistics with caching.

        Returns cached stats if available, otherwise calculates and caches.
        Cache TTL: CACHE_TIMEOUT_SHORT (60s) for live data

        Returns:
            Dict with keys: total_topics, total_posts, total_users,
                           online_users, latest_member
        """
        cache_key = f'{self.CACHE_VERSION}:forum:stats:all'

        # Try cache first
        stats = self.cache.get(cache_key)
        if stats is not None:
            logger.debug(f"Cache HIT: {cache_key}")
            return stats

        logger.debug(f"Cache MISS: {cache_key}")

        # Calculate stats using repositories
        total_users = self.user_repo.count(is_active=True)
        total_topics = self.topic_repo.count_approved()
        total_posts = self.post_repo.count_approved()
        online_users = self._get_online_users_count()
        latest_member = self._get_latest_member()

        # Serialize latest_member to dict (can't cache model instances)
        latest_member_data = None
        if latest_member:
            latest_member_data = {
                'id': latest_member.id,
                'username': latest_member.username,
                'email': latest_member.email,
                'date_joined': latest_member.date_joined.isoformat() if latest_member.date_joined else None,
            }

        stats = {
            'total_topics': total_topics,
            'total_posts': total_posts,
            'total_users': total_users,
            'online_users': online_users,
            'latest_member': latest_member_data,
        }

        # Cache for short duration (live data changes frequently)
        self.cache.set(cache_key, stats, timeout=self.CACHE_TIMEOUT_SHORT)

        return stats

    def get_online_users_count(self) -> int:
        """
        Get count of users active in the last 15 minutes.

        This is a public wrapper for _get_online_users_count.
        Cached separately with short TTL.

        Returns:
            Number of online users
        """
        cache_key = f'{self.CACHE_VERSION}:forum:online_count'

        count = self.cache.get(cache_key)
        if count is not None:
            return count

        count = self._get_online_users_count()
        self.cache.set(cache_key, count, timeout=30)  # 30 second cache

        return count

    def get_online_users_list(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get list of recently active users.

        Args:
            limit: Maximum number of users to return

        Returns:
            List of user data dicts
        """
        cache_key = f'{self.CACHE_VERSION}:forum:online_users:{limit}'

        users_data = self.cache.get(cache_key)
        if users_data is not None:
            return users_data

        threshold_minutes = self.ONLINE_THRESHOLD_MINUTES
        users = self.user_repo.get_online_users(
            threshold_minutes=threshold_minutes
        )[:limit]

        # Serialize users to dicts (can't cache model instances)
        users_data = [
            {
                'id': user.id,
                'username': user.username,
                'last_login': user.last_login.isoformat() if user.last_login else None,
            }
            for user in users
        ]

        self.cache.set(cache_key, users_data, timeout=30)  # 30 second cache

        return users_data

    # ========================================
    # Forum-Specific Statistics
    # ========================================

    def get_forum_specific_stats(self, forum_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific forum with caching.

        Optimized to avoid N+1 queries using repository methods.

        Args:
            forum_id: Forum ID

        Returns:
            Dict with forum statistics
        """
        cache_key = f'{self.CACHE_VERSION}:forum:stats:{forum_id}'

        stats = self.cache.get(cache_key)
        if stats is not None:
            logger.debug(f"Cache HIT: {cache_key}")
            return stats

        logger.debug(f"Cache MISS: {cache_key}")

        forum = self.forum_repo.get_by_id(forum_id)
        if not forum:
            return {
                'topics_count': 0,
                'posts_count': 0,
                'weekly_posts': 0,
                'online_users': 0,
                'trending': False,
            }

        # Calculate weekly posts using optimized repository method
        week_ago = timezone.now() - timedelta(days=7)
        weekly_posts = self.post_repo.count_for_forum_since(
            forum_id=forum_id,
            since=week_ago
        )

        # Get online users for this forum
        # (users who posted recently in this forum)
        online_users = self._get_forum_online_users_count(forum_id)

        stats = {
            'topics_count': forum.direct_topics_count,
            'posts_count': forum.direct_posts_count,
            'weekly_posts': weekly_posts,
            'online_users': online_users,
            'trending': weekly_posts > 5,  # Forum is trending if >5 posts/week
        }

        # Cache for short duration (activity changes frequently)
        self.cache.set(cache_key, stats, timeout=self.CACHE_TIMEOUT_SHORT)

        return stats

    # ========================================
    # User Statistics
    # ========================================

    def get_user_forum_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get forum statistics for a specific user.

        Args:
            user_id: User ID

        Returns:
            Dict with user statistics
        """
        cache_key = f'{self.CACHE_VERSION}:forum:user_stats:{user_id}'

        stats = self.cache.get(cache_key)
        if stats is not None:
            logger.debug(f"Cache HIT: {cache_key}")
            return stats

        logger.debug(f"Cache MISS: {cache_key}")

        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {
                'topics_count': 0,
                'posts_count': 0,
                'last_post': None,
                'last_topic': None,
            }

        # Get user's topics and posts counts
        topics = self.topic_repo.get_user_topics(user_id, limit=1)
        posts = self.post_repo.get_user_posts(user_id, limit=1)

        # Serialize last post and topic (can't cache model instances)
        last_post_data = None
        if posts:
            last_post = posts[0]
            last_post_data = {
                'id': last_post.id,
                'subject': last_post.subject,
                'created': last_post.created.isoformat() if last_post.created else None,
            }

        last_topic_data = None
        if topics:
            last_topic = topics[0]
            last_topic_data = {
                'id': last_topic.id,
                'subject': last_topic.subject,
                'created': last_topic.created.isoformat() if last_topic.created else None,
            }

        stats = {
            'topics_count': self.topic_repo.count(poster_id=user_id, approved=True),
            'posts_count': self.post_repo.count(poster_id=user_id, approved=True),
            'last_post': last_post_data,
            'last_topic': last_topic_data,
        }

        # Cache user stats for medium duration
        self.cache.set(cache_key, stats, timeout=self.CACHE_TIMEOUT_MEDIUM)

        return stats

    # ========================================
    # Cache Invalidation
    # ========================================

    def invalidate_cache(self, forum_id: Optional[int] = None, user_id: Optional[int] = None):
        """
        Invalidate statistics caches.

        Args:
            forum_id: Optional forum ID to invalidate specific forum cache
            user_id: Optional user ID to invalidate specific user cache
        """
        if forum_id:
            # Invalidate specific forum cache
            cache_key = f'{self.CACHE_VERSION}:forum:stats:{forum_id}'
            self.cache.delete(cache_key)
            logger.debug(f"Invalidated cache: {cache_key}")

        if user_id:
            # Invalidate specific user cache
            cache_key = f'{self.CACHE_VERSION}:forum:user_stats:{user_id}'
            self.cache.delete(cache_key)
            logger.debug(f"Invalidated cache: {cache_key}")

        # Invalidate overall stats
        self.cache.delete(f'{self.CACHE_VERSION}:forum:stats:all')
        self.cache.delete(f'{self.CACHE_VERSION}:forum:online_count')

        logger.info("Forum statistics cache invalidated")

    def invalidate_all_caches(self):
        """
        Invalidate all statistics caches using pattern deletion.

        This is useful when you want to force refresh all stats.
        """
        # Delete all keys matching the pattern
        pattern = f'{self.CACHE_VERSION}:forum:*'

        try:
            # Redis-specific pattern deletion
            if hasattr(self.cache, 'delete_pattern'):
                deleted_count = self.cache.delete_pattern(pattern)
                logger.info(f"Invalidated {deleted_count} cache keys matching {pattern}")
            else:
                # Fallback: delete known keys
                self.invalidate_cache()
                logger.warning("Cache backend doesn't support pattern deletion, using fallback")
        except Exception as e:
            logger.error(f"Error invalidating caches: {e}")

    # ========================================
    # Private Helper Methods
    # ========================================

    def _get_online_users_count(self) -> int:
        """
        Internal method to get online users count.

        Returns:
            Number of online users
        """
        return len(self.user_repo.get_online_users(
            threshold_minutes=self.ONLINE_THRESHOLD_MINUTES
        ))

    def _get_latest_member(self) -> Optional[User]:
        """
        Get the most recently joined active user.

        Returns:
            User instance or None
        """
        users = self.user_repo.filter(is_active=True).order_by('-date_joined')[:1]
        return users[0] if users else None

    def _get_forum_online_users_count(self, forum_id: int) -> int:
        """
        Get count of users who posted recently in this forum.

        This is an approximation of "online in this forum".

        Args:
            forum_id: Forum ID

        Returns:
            Number of active users
        """
        # Get posts from last 15 minutes
        threshold = timezone.now() - timedelta(minutes=self.ONLINE_THRESHOLD_MINUTES)

        # Get recent posts in this forum
        from machina.apps.forum_conversation.models import Post
        recent_poster_ids = (
            Post.objects
            .filter(
                topic__forum_id=forum_id,
                created__gte=threshold,
                approved=True
            )
            .values_list('poster_id', flat=True)
            .distinct()
        )

        return len(list(recent_poster_ids))

    # ========================================
    # Analytics and Reporting
    # ========================================

    def get_activity_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get forum activity summary for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with activity metrics
        """
        cache_key = f'{self.CACHE_VERSION}:forum:activity:{days}d'

        summary = self.cache.get(cache_key)
        if summary is not None:
            return summary

        threshold = timezone.now() - timedelta(days=days)

        # Get recent topics and posts
        recent_topics = self.topic_repo.get_active_topics(days=days, limit=100)

        # Calculate metrics
        summary = {
            'period_days': days,
            'new_topics': self.topic_repo.count(created__gte=threshold, approved=True),
            'new_posts': self.post_repo.count(created__gte=threshold, approved=True),
            'active_topics_count': len(recent_topics),
            'new_users': self.user_repo.count(date_joined__gte=threshold, is_active=True),
        }

        # Cache for medium duration
        self.cache.set(cache_key, summary, timeout=self.CACHE_TIMEOUT_MEDIUM)

        return summary

    # ========================================
    # Platform-wide Statistics (for homepage)
    # ========================================

    def get_platform_statistics(self) -> Dict[str, Any]:
        """
        Get overall platform statistics for home page.

        Returns cached stats if available, otherwise calculates and caches.
        Cache TTL: CACHE_TIMEOUT_SHORT (60s) for reasonably fresh data

        Returns:
            Dict with keys: total_courses, total_exercises, total_users, success_rate
        """
        cache_key = f'{self.CACHE_VERSION}:platform:stats:all'

        # Try cache first
        stats = self.cache.get(cache_key)
        if stats is not None:
            logger.debug(f"Cache HIT: {cache_key}")
            return stats

        logger.debug(f"Cache MISS: {cache_key}")

        # Import models (lazy import to avoid circular dependencies)
        from apps.learning.models import Course, Exercise
        from apps.learning.exercise_models import Submission
        from django.db.models import Q

        # Calculate total users
        total_users = self.user_repo.count(is_active=True)

        # Calculate total published courses
        total_courses = Course.objects.filter(is_published=True).count()

        # Calculate total published exercises
        total_exercises = Exercise.objects.filter(is_published=True).count()

        # Calculate platform-wide success rate from exercise submissions
        total_submissions = Submission.objects.count()
        if total_submissions > 0:
            # Success criteria: status='passed' AND score >= 80
            successful_submissions = Submission.objects.filter(
                Q(status='passed') & Q(score__gte=80)
            ).count()
            success_rate = int((successful_submissions / total_submissions) * 100)
        else:
            success_rate = 0  # No submissions yet

        stats = {
            'total_users': total_users,
            'total_courses': total_courses,
            'total_exercises': total_exercises,
            'success_rate': success_rate,
        }

        # Cache for short duration (60 seconds)
        self.cache.set(cache_key, stats, timeout=self.CACHE_TIMEOUT_SHORT)

        return stats
