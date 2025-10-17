"""
Forum repository for optimized forum data access.

This repository provides optimized queries for forum-related operations,
including hierarchical forum structures and statistics.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from django.db.models import Count, Prefetch, Q
from django.utils import timezone
from machina.apps.forum.models import Forum

from .base import OptimizedRepository


class ForumRepository(OptimizedRepository):
    """
    Repository for Forum model with optimized queries.

    Handles forum hierarchy, statistics, and related data.
    """

    def __init__(self):
        """Initialize with Forum model."""
        super().__init__(Forum)

    def _get_select_related(self) -> List[str]:
        """
        Optimize forum queries with parent relationship.

        Returns:
            List of fields to select_related
        """
        return ['parent']

    def _get_prefetch_related(self) -> List[str]:
        """
        Prefetch forum topics and posts.

        Returns:
            List of fields to prefetch_related
        """
        return [
            Prefetch(
                'topics',
                queryset=self._get_optimized_topics_queryset()
            ),
        ]

    def _get_optimized_topics_queryset(self):
        """
        Get optimized topics queryset for prefetching.

        Returns:
            Optimized Topic queryset
        """
        from machina.apps.forum_conversation.models import Topic
        return (
            Topic.objects
            .select_related('poster', 'forum')
            .filter(approved=True)
            .order_by('-last_post_on')
        )

    def get_by_slug(self, slug: str) -> Optional[Forum]:
        """
        Get forum by slug.

        Args:
            slug: Forum slug

        Returns:
            Forum instance or None
        """
        try:
            return self.get_optimized_queryset().get(slug=slug)
        except Forum.DoesNotExist:
            return None

    def get_with_stats(self, forum_id: int) -> Optional[Forum]:
        """
        Get forum with optimized statistics.

        This method solves N+1 query problems by prefetching
        all related data in a single optimized query.

        Args:
            forum_id: Forum ID

        Returns:
            Forum with prefetched statistics
        """
        try:
            return (
                self.get_optimized_queryset()
                .annotate(
                    topics_count_annotated=Count('topics', filter=Q(topics__approved=True)),
                )
                .get(pk=forum_id)
            )
        except Forum.DoesNotExist:
            return None

    def get_root_forums(self) -> List[Forum]:
        """
        Get top-level forums (no parent).

        Returns:
            List of root forums
        """
        return list(
            self.get_optimized_queryset()
            .filter(parent__isnull=True)
            .order_by('display_order', 'name')
        )

    def get_child_forums(self, parent_id: int) -> List[Forum]:
        """
        Get child forums of a parent.

        Args:
            parent_id: Parent forum ID

        Returns:
            List of child forums
        """
        return list(
            self.get_optimized_queryset()
            .filter(parent_id=parent_id)
            .order_by('display_order', 'name')
        )

    def get_forums_by_category(self, category_id: int) -> List[Forum]:
        """
        Get forums within a category.

        Args:
            category_id: Category forum ID

        Returns:
            List of forums in category
        """
        return list(
            self.get_optimized_queryset()
            .filter(parent_id=category_id, type=Forum.FORUM_POST)
            .order_by('display_order', 'name')
        )

    def get_all_forums_with_hierarchy(self) -> List[Forum]:
        """
        Get all forums organized by hierarchy.

        Returns:
            List of forums with parent-child relationships optimized
        """
        return list(
            self.get_optimized_queryset()
            .order_by('tree_id', 'lft')  # MPTT ordering
        )

    def get_forums_for_user(self, user) -> List[Forum]:
        """
        Get forums visible to user (based on permissions).

        Args:
            user: User instance

        Returns:
            List of visible forums
        """
        # Staff and superusers can see all forums
        if user.is_staff or user.is_superuser:
            return self.get_all_forums_with_hierarchy()

        # Filter forums by permissions using machina's permission handler
        from machina.core.loading import get_class

        PermissionHandler = get_class('forum_permission.handler', 'PermissionHandler')
        perm_handler = PermissionHandler()

        all_forums = self.get_all_forums_with_hierarchy()
        accessible_forums = [
            forum for forum in all_forums
            if perm_handler.can_read_forum(forum, user)
        ]

        return accessible_forums

    def search_forums(self, query: str) -> List[Forum]:
        """
        Search forums by name or description.

        Args:
            query: Search query

        Returns:
            List of matching forums
        """
        return list(
            self.get_optimized_queryset()
            .filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )
            .filter(type=Forum.FORUM_POST)  # Only actual forums, not categories
            .order_by('name')
        )

    def get_forums_with_recent_activity(self, days: int = 7) -> List[Forum]:
        """
        Get forums with recent activity.

        Args:
            days: Number of days to look back

        Returns:
            List of active forums
        """
        threshold = timezone.now() - timedelta(days=days)
        return list(
            self.get_optimized_queryset()
            .filter(
                topics__last_post_on__gte=threshold,
                type=Forum.FORUM_POST
            )
            .distinct()
            .order_by('-topics__last_post_on')
        )

    def get_forum_ancestors(self, forum_id: int) -> List[Forum]:
        """
        Get all ancestor forums (breadcrumb path).

        Args:
            forum_id: Forum ID

        Returns:
            List of ancestor forums in order
        """
        forum = self.get_by_id(forum_id)
        if not forum:
            return []

        # Use MPTT get_ancestors()
        return list(forum.get_ancestors())

    def increment_topic_count(self, forum_id: int) -> bool:
        """
        Increment forum's topic count.

        Args:
            forum_id: Forum ID

        Returns:
            True if updated
        """
        from django.db.models import F
        updated = Forum.objects.filter(pk=forum_id).update(
            direct_topics_count=F('direct_topics_count') + 1
        )
        return updated > 0

    def decrement_topic_count(self, forum_id: int) -> bool:
        """
        Decrement forum's topic count.

        Args:
            forum_id: Forum ID

        Returns:
            True if updated
        """
        from django.db.models import F
        updated = Forum.objects.filter(pk=forum_id).update(
            direct_topics_count=F('direct_topics_count') - 1
        )
        return updated > 0

    def increment_post_count(self, forum_id: int) -> bool:
        """
        Increment forum's post count.

        Args:
            forum_id: Forum ID

        Returns:
            True if updated
        """
        from django.db.models import F
        updated = Forum.objects.filter(pk=forum_id).update(
            direct_posts_count=F('direct_posts_count') + 1
        )
        return updated > 0

    def decrement_post_count(self, forum_id: int) -> bool:
        """
        Decrement forum's post count.

        Args:
            forum_id: Forum ID

        Returns:
            True if updated
        """
        from django.db.models import F
        updated = Forum.objects.filter(pk=forum_id).update(
            direct_posts_count=F('direct_posts_count') - 1
        )
        return updated > 0
