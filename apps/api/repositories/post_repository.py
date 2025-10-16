"""
Post repository for optimized post data access.

This repository provides optimized queries for post-related operations,
including content, moderation, and statistics.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from django.db.models import Count, Q, F
from django.utils import timezone
from machina.apps.forum_conversation.models import Post

from .base import OptimizedRepository


class PostRepository(OptimizedRepository):
    """
    Repository for Post model with optimized queries.

    Handles post retrieval, moderation, and statistics.
    """

    def __init__(self):
        """Initialize with Post model."""
        super().__init__(Post)

    def _get_select_related(self) -> List[str]:
        """
        Optimize post queries with related data.

        Returns:
            List of fields to select_related
        """
        return ['poster', 'poster__trust_level', 'topic', 'topic__forum']

    def get_posts_for_topic(
        self,
        topic_id: int,
        page: int = 1,
        page_size: int = 20,
        approved_only: bool = True
    ) -> dict:
        """
        Get paginated posts for a topic.

        Args:
            topic_id: Topic ID
            page: Page number
            page_size: Items per page
            approved_only: Only return approved posts

        Returns:
            Dict with results and pagination info
        """
        queryset = (
            self.get_optimized_queryset()
            .filter(topic_id=topic_id)
            .order_by('created')
        )

        if approved_only:
            queryset = queryset.filter(approved=True)

        return self._paginate_queryset(queryset, page, page_size)

    def count_approved(self) -> int:
        """
        Count approved posts.

        Returns:
            Number of approved posts
        """
        return self.count(approved=True)

    def count_for_forum_since(self, forum_id: int, since: datetime) -> int:
        """
        Count posts for forum since specific time.

        Optimized query without N+1 problem.

        Args:
            forum_id: Forum ID
            since: Cutoff datetime

        Returns:
            Number of posts
        """
        return Post.objects.filter(
            topic__forum_id=forum_id,
            approved=True,
            created__gte=since
        ).count()

    def get_recent_posts(self, limit: int = 10, approved_only: bool = True) -> List[Post]:
        """
        Get recently created posts.

        Args:
            limit: Maximum number of posts
            approved_only: Only return approved posts

        Returns:
            List of recent posts
        """
        queryset = self.get_optimized_queryset().order_by('-created')

        if approved_only:
            queryset = queryset.filter(approved=True)

        return list(queryset[:limit])

    def get_user_posts(
        self,
        user_id: int,
        limit: Optional[int] = None,
        approved_only: bool = True
    ) -> List[Post]:
        """
        Get posts by user.

        Args:
            user_id: User ID
            limit: Optional limit
            approved_only: Only return approved posts

        Returns:
            List of user's posts
        """
        queryset = (
            self.get_optimized_queryset()
            .filter(poster_id=user_id)
            .order_by('-created')
        )

        if approved_only:
            queryset = queryset.filter(approved=True)

        if limit:
            queryset = queryset[:limit]

        return list(queryset)

    def search_posts(self, query: str, limit: int = 50) -> List[Post]:
        """
        Search posts by content.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching posts
        """
        return list(
            self.get_optimized_queryset()
            .filter(
                Q(content__icontains=query),
                approved=True
            )
            .order_by('-created')
            [:limit]
        )

    def get_posts_needing_approval(self) -> List[Post]:
        """
        Get posts pending approval.

        Returns:
            List of unapproved posts
        """
        return list(
            self.get_optimized_queryset()
            .filter(approved=False)
            .order_by('-created')
        )

    def get_duplicate_candidates(self, content: str, days: int = 7) -> List[Post]:
        """
        Find posts with similar content (duplicate detection).

        Args:
            content: Post content to match
            days: Number of days to look back

        Returns:
            List of potentially duplicate posts
        """
        threshold = timezone.now() - timedelta(days=days)
        content_stripped = content.strip()

        return list(
            self.get_optimized_queryset()
            .filter(
                created__gte=threshold,
                approved=True
            )
            .exclude(content='')
            .order_by('-created')
            [:100]  # Limit for performance
        )

    def approve_post(self, post_id: int) -> bool:
        """
        Approve a post.

        Args:
            post_id: Post ID

        Returns:
            True if approved
        """
        return self.update(post_id, approved=True)

    def reject_post(self, post_id: int) -> bool:
        """
        Reject a post (mark as not approved).

        Args:
            post_id: Post ID

        Returns:
            True if rejected
        """
        return self.update(post_id, approved=False)

    def update_content(self, post_id: int, content: str) -> bool:
        """
        Update post content.

        Args:
            post_id: Post ID
            content: New content

        Returns:
            True if updated
        """
        return self.update(
            post_id,
            content=content,
            updated=timezone.now()
        )

    def mark_as_edited(self, post_id: int) -> bool:
        """
        Update post's edited timestamp.

        Args:
            post_id: Post ID

        Returns:
            True if updated
        """
        return self.update(post_id, updated=timezone.now())

    def get_last_post_for_topic(self, topic_id: int) -> Optional[Post]:
        """
        Get most recent post in a topic.

        Args:
            topic_id: Topic ID

        Returns:
            Last post or None
        """
        return (
            self.filter(topic_id=topic_id, approved=True)
            .order_by('-created')
            .first()
        )

    def get_first_post_for_topic(self, topic_id: int) -> Optional[Post]:
        """
        Get first post in a topic (topic content).

        Args:
            topic_id: Topic ID

        Returns:
            First post or None
        """
        return (
            self.filter(topic_id=topic_id, approved=True)
            .order_by('created')
            .first()
        )

    def count_user_posts_in_period(
        self,
        user_id: int,
        hours: int = 24
    ) -> int:
        """
        Count posts by user in recent period.

        Useful for spam detection.

        Args:
            user_id: User ID
            hours: Time period in hours

        Returns:
            Number of posts
        """
        threshold = timezone.now() - timedelta(hours=hours)
        return self.count(
            poster_id=user_id,
            created__gte=threshold
        )

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
