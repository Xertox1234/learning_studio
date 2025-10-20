"""
ReviewQueue repository for optimized moderation queue data access.

This repository provides optimized queries for moderation-related operations,
including queue management, analytics, and review workflows.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from django.db.models import Count, Q, Avg, F
from django.utils import timezone

from .base import OptimizedRepository


class ReviewQueueRepository(OptimizedRepository):
    """
    Repository for ReviewQueue model with optimized queries.

    Handles moderation queue, analytics, and review workflows.
    """

    def __init__(self):
        """Initialize with ReviewQueue model."""
        from apps.forum_integration.models import ReviewQueue
        super().__init__(ReviewQueue)

    def _get_select_related(self) -> List[str]:
        """
        Optimize review queue queries with related data.

        Returns:
            List of fields to select_related
        """
        return [
            'post',
            'post__poster',
            'post__poster__trust_level',
            'post__topic',
            'post__topic__forum',
            'topic',
            'topic__poster',
            'topic__poster__trust_level',
            'topic__forum',
            'reported_user',
            'reported_user__trust_level',
            'reporter',
            'assigned_moderator',
        ]

    def get_pending_queue(
        self,
        review_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get pending review items with pagination.

        Args:
            review_type: Optional filter by review type
            page: Page number
            page_size: Items per page

        Returns:
            Dict with results and pagination info
        """
        queryset = (
            self.get_optimized_queryset()
            .filter(status='pending')
            .order_by('-priority', '-score', '-created_at')
        )

        if review_type:
            queryset = queryset.filter(review_type=review_type)

        return self._paginate_queryset(queryset, page, page_size)

    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get moderation queue statistics.

        Returns:
            Dict with queue statistics
        """
        from apps.forum_integration.models import ReviewQueue

        total = self.count()
        pending = self.count(status='pending')
        approved = self.count(status='approved')
        rejected = self.count(status='rejected')

        # Get counts by review type
        type_counts = dict(
            ReviewQueue.objects
            .filter(status='pending')
            .values('review_type')
            .annotate(count=Count('id'))
            .values_list('review_type', 'count')
        )

        # Get average resolution time for resolved items
        resolved_items = ReviewQueue.objects.filter(
            status__in=['approved', 'rejected'],
            resolved_at__isnull=False
        )

        avg_resolution_time = None
        if resolved_items.exists():
            # Calculate average time difference
            from django.db.models import Avg, ExpressionWrapper, F, DurationField
            avg_resolution_time = resolved_items.aggregate(
                avg_time=Avg(
                    ExpressionWrapper(
                        F('resolved_at') - F('created_at'),
                        output_field=DurationField()
                    )
                )
            )['avg_time']

        return {
            'total': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'by_type': type_counts,
            'avg_resolution_time_seconds': (
                avg_resolution_time.total_seconds() if avg_resolution_time else None
            ),
        }

    def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get moderation analytics for specified period.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with analytics data
        """
        from apps.forum_integration.models import ReviewQueue
        from django.db.models.functions import TruncDate

        threshold = timezone.now() - timedelta(days=days)

        queryset = ReviewQueue.objects.filter(created_at__gte=threshold)

        total_reviewed = queryset.filter(status__in=['approved', 'rejected']).count()
        approved = queryset.filter(status='approved').count()
        rejected = queryset.filter(status='rejected').count()
        pending = queryset.filter(status='pending').count()

        # Group by date (using safe TruncDate instead of .extra())
        by_date = dict(
            queryset
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .values_list('date', 'count')
        )

        # Group by review type
        by_type = dict(
            queryset
            .values('review_type')
            .annotate(count=Count('id'))
            .values_list('review_type', 'count')
        )

        # Group by status
        by_status = dict(
            queryset
            .values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )

        return {
            'period_days': days,
            'total_items': queryset.count(),
            'total_reviewed': total_reviewed,
            'approved': approved,
            'rejected': rejected,
            'pending': pending,
            'approval_rate': (approved / total_reviewed * 100) if total_reviewed > 0 else 0,
            'by_date': by_date,
            'by_type': by_type,
            'by_status': by_status,
        }

    def get_items_by_user(
        self,
        user_id: int,
        status: Optional[str] = None
    ) -> List:
        """
        Get review items for a specific user.

        Args:
            user_id: User ID
            status: Optional status filter

        Returns:
            List of review items
        """
        queryset = (
            self.get_optimized_queryset()
            .filter(
                Q(post__poster_id=user_id) |
                Q(topic__poster_id=user_id) |
                Q(reported_user_id=user_id)
            )
        )

        if status:
            queryset = queryset.filter(status=status)

        return list(queryset.order_by('-created_at'))

    def get_high_priority_items(self, limit: int = 10) -> List:
        """
        Get highest priority items needing review.

        Args:
            limit: Maximum items to return

        Returns:
            List of high-priority items
        """
        return list(
            self.get_optimized_queryset()
            .filter(status='pending')
            .order_by('-priority', '-score', '-created_at')
            [:limit]
        )

    def approve_item(
        self,
        item_id: int,
        moderator_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """
        Approve a review item.

        Args:
            item_id: ReviewQueue ID
            moderator_id: Moderator user ID
            reason: Optional approval reason

        Returns:
            True if approved
        """
        return self.update(
            item_id,
            status='approved',
            assigned_moderator_id=moderator_id,
            resolved_at=timezone.now(),
            moderator_notes=reason or ''
        )

    def reject_item(
        self,
        item_id: int,
        moderator_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """
        Reject a review item.

        Args:
            item_id: ReviewQueue ID
            moderator_id: Moderator user ID
            reason: Optional rejection reason

        Returns:
            True if rejected
        """
        return self.update(
            item_id,
            status='rejected',
            assigned_moderator_id=moderator_id,
            resolved_at=timezone.now(),
            moderator_notes=reason or ''
        )

    def escalate_item(self, item_id: int, new_priority: int = 1) -> bool:
        """
        Escalate item priority.

        Args:
            item_id: ReviewQueue ID
            new_priority: New priority level

        Returns:
            True if escalated
        """
        return self.update(item_id, priority=new_priority)

    def add_note(self, item_id: int, note: str) -> bool:
        """
        Add moderator note to item.

        Args:
            item_id: ReviewQueue ID
            note: Note content

        Returns:
            True if updated
        """
        item = self.get_by_id(item_id)
        if not item:
            return False

        existing_notes = item.moderator_notes or ''
        updated_notes = f"{existing_notes}\n{note}".strip()

        return self.update(item_id, moderator_notes=updated_notes)

    def cleanup_old_items(self, days: int = 30) -> int:
        """
        Delete resolved items older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of items deleted
        """
        threshold = timezone.now() - timedelta(days=days)
        return self.delete_many(
            status__in=['approved', 'rejected'],
            resolved_at__lt=threshold
        )

    def _paginate_queryset(self, queryset, page: int, page_size: int) -> Dict[str, Any]:
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
