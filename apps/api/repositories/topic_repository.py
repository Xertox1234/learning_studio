"""
Topic repository for optimized topic data access.

This repository provides optimized queries for topic-related operations,
including posts, statistics, and moderation.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from django.db.models import Count, Prefetch, Q, F
from django.utils import timezone
from machina.apps.forum_conversation.models import Topic, Post

from .base import OptimizedRepository


class TopicRepository(OptimizedRepository):
    """
    Repository for Topic model with optimized queries.

    Handles topic retrieval, statistics, and related posts.
    """

    def __init__(self):
        """Initialize with Topic model."""
        super().__init__(Topic)

    def _get_select_related(self) -> List[str]:
        """
        Optimize topic queries with related data.

        Returns:
            List of fields to select_related
        """
        return ['poster', 'forum', 'last_post', 'last_post__poster']

    def _get_prefetch_related(self) -> List[str | Prefetch]:
        """
        Prefetch topic posts.

        Returns:
            List of Prefetch objects
        """
        return [
            Prefetch(
                'posts',
                queryset=self._get_optimized_posts_queryset()
            ),
        ]

    def _get_optimized_posts_queryset(self):
        """
        Get optimized posts queryset for prefetching.

        Returns:
            Optimized Post queryset
        """
        return (
            Post.objects
            .select_related('poster', 'poster__trust_level')
            .filter(approved=True)
            .order_by('created')
        )

    def get_by_slug(self, slug: str) -> Optional[Topic]:
        """
        Get topic by slug.

        Args:
            slug: Topic slug

        Returns:
            Topic instance or None
        """
        try:
            return self.get_optimized_queryset().get(slug=slug)
        except Topic.DoesNotExist:
            return None

    def get_with_posts(self, topic_id: int) -> Optional[Topic]:
        """
        Get topic with all posts optimized.

        This solves N+1 query problem by prefetching posts with their posters.

        Args:
            topic_id: Topic ID

        Returns:
            Topic with prefetched posts
        """
        try:
            return self.get_optimized_queryset().get(pk=topic_id)
        except Topic.DoesNotExist:
            return None

    def get_topics_for_forum(
        self,
        forum_id: int,
        page: int = 1,
        page_size: int = 20,
        include_pinned: bool = True
    ) -> dict:
        """
        Get paginated topics for a forum.

        Args:
            forum_id: Forum ID
            page: Page number
            page_size: Items per page
            include_pinned: Whether to include pinned topics

        Returns:
            Dict with results and pagination info
        """
        queryset = (
            self.get_optimized_queryset()
            .filter(forum_id=forum_id, approved=True)
        )

        if include_pinned:
            # Order: pinned first, then by last post
            queryset = queryset.order_by(
                F('type').desc(),  # Pinned/announce topics first
                '-last_post_on'
            )
        else:
            queryset = queryset.filter(type=Topic.TOPIC_POST).order_by('-last_post_on')

        return self._paginate_queryset(queryset, page, page_size)

    def count_approved(self) -> int:
        """
        Count approved topics.

        Returns:
            Number of approved topics
        """
        return self.count(approved=True)

    def get_recent_topics(self, limit: int = 10) -> List[Topic]:
        """
        Get recently created topics.

        Args:
            limit: Maximum number of topics

        Returns:
            List of recent topics
        """
        return list(
            self.get_optimized_queryset()
            .filter(approved=True)
            .order_by('-created')
            [:limit]
        )

    def get_active_topics(self, days: int = 7, limit: int = 10) -> List[Topic]:
        """
        Get topics with recent activity.

        Args:
            days: Number of days to look back
            limit: Maximum number of topics

        Returns:
            List of active topics
        """
        threshold = timezone.now() - timedelta(days=days)
        return list(
            self.get_optimized_queryset()
            .filter(
                approved=True,
                last_post_on__gte=threshold
            )
            .order_by('-last_post_on')
            [:limit]
        )

    def get_user_topics(self, user_id: int, limit: Optional[int] = None) -> List[Topic]:
        """
        Get topics created by user.

        Args:
            user_id: User ID
            limit: Optional limit

        Returns:
            List of user's topics
        """
        queryset = (
            self.get_optimized_queryset()
            .filter(poster_id=user_id, approved=True)
            .order_by('-created')
        )

        if limit:
            queryset = queryset[:limit]

        return list(queryset)

    def search_topics(self, query: str, forum_id: Optional[int] = None) -> List[Topic]:
        """
        Search topics by subject.

        Args:
            query: Search query
            forum_id: Optional forum to search within

        Returns:
            List of matching topics
        """
        queryset = (
            self.get_optimized_queryset()
            .filter(
                Q(subject__icontains=query),
                approved=True
            )
        )

        if forum_id:
            queryset = queryset.filter(forum_id=forum_id)

        return list(queryset.order_by('-last_post_on'))

    def get_pinned_topics(self, forum_id: int) -> List[Topic]:
        """
        Get pinned/announced topics for a forum.

        Args:
            forum_id: Forum ID

        Returns:
            List of pinned topics
        """
        return list(
            self.get_optimized_queryset()
            .filter(
                forum_id=forum_id,
                approved=True,
                type__in=[Topic.TOPIC_STICKY, Topic.TOPIC_ANNOUNCE]
            )
            .order_by(F('type').desc(), '-last_post_on')
        )

    def increment_views(self, topic_id: int) -> bool:
        """
        Increment topic view count.

        Args:
            topic_id: Topic ID

        Returns:
            True if updated
        """
        updated = Topic.objects.filter(pk=topic_id).update(
            views_count=F('views_count') + 1
        )
        return updated > 0

    def increment_post_count(self, topic_id: int) -> bool:
        """
        Increment topic post count.

        Args:
            topic_id: Topic ID

        Returns:
            True if updated
        """
        updated = Topic.objects.filter(pk=topic_id).update(
            posts_count=F('posts_count') + 1
        )
        return updated > 0

    def decrement_post_count(self, topic_id: int) -> bool:
        """
        Decrement topic post count.

        Args:
            topic_id: Topic ID

        Returns:
            True if updated
        """
        updated = Topic.objects.filter(pk=topic_id).update(
            posts_count=F('posts_count') - 1
        )
        return updated > 0

    def lock_topic(self, topic_id: int) -> bool:
        """
        Lock a topic (prevent new posts).

        Args:
            topic_id: Topic ID

        Returns:
            True if locked
        """
        return self.update(topic_id, status=Topic.TOPIC_LOCKED)

    def unlock_topic(self, topic_id: int) -> bool:
        """
        Unlock a topic.

        Args:
            topic_id: Topic ID

        Returns:
            True if unlocked
        """
        return self.update(topic_id, status=Topic.TOPIC_UNLOCKED)

    def pin_topic(self, topic_id: int) -> bool:
        """
        Pin a topic (sticky).

        Args:
            topic_id: Topic ID

        Returns:
            True if pinned
        """
        return self.update(topic_id, type=Topic.TOPIC_STICKY)

    def unpin_topic(self, topic_id: int) -> bool:
        """
        Unpin a topic.

        Args:
            topic_id: Topic ID

        Returns:
            True if unpinned
        """
        return self.update(topic_id, type=Topic.TOPIC_POST)

    def approve_topic(self, topic_id: int) -> bool:
        """
        Approve a topic.

        Args:
            topic_id: Topic ID

        Returns:
            True if approved
        """
        return self.update(topic_id, approved=True)

    def _paginate_queryset(self, queryset, page: int, page_size: int) -> dict:
        """
        Helper to paginate a queryset.

        Args:
            queryset: QuerySet to paginate
            page: Page number
            page_size: Items per page

        Returns:
            Dict with pagination info
        """
        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        results = list(queryset[start:end])

        return {
            'results': results,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size,
            'has_next': page * page_size < total,
            'has_prev': page > 1,
        }
