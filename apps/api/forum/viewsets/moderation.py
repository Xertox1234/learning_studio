"""
Moderation ViewSet for reviewing and moderating content.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count
from apps.forum_integration.models import ReviewQueue, ModerationLog
from apps.api.services.container import container


class ModerationQueueViewSet(viewsets.ViewSet):
    """
    ViewSet for moderation queue operations.

    Requires TL3+ (Regular), staff, or superuser permissions.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Get moderation queue items.

        Query params:
        - status: pending, approved, rejected (default: pending)
        - content_type: posts, topics, users (optional)
        - priority: Filter by priority level (1-5)
        - page: Page number (default: 1)
        - page_size: Items per page (default: 20, max: 100)
        """
        # Check permissions
        if not self._can_moderate(request.user):
            return Response(
                {'error': 'You do not have permission to access the moderation queue.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get query parameters
        status_filter = request.query_params.get('status', 'pending')
        content_type = request.query_params.get('content_type')
        priority = request.query_params.get('priority')
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 100)

        # Build queryset
        queryset = ReviewQueue.objects.select_related(
            'content_type',
            'author',
            'author__trust_level',
            'reviewed_by',
            'reviewed_by__trust_level'
        ).order_by('-priority_score', '-created_at')

        # Apply filters
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if content_type:
            queryset = queryset.filter(content_type__model=content_type.rstrip('s'))  # posts -> post

        if priority:
            queryset = queryset.filter(priority_score=priority)

        # Pagination
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        items = queryset[start:end]

        # Serialize
        serialized_items = []
        for item in items:
            serialized_items.append({
                'id': item.id,
                'content_type': item.content_type.model,
                'object_id': item.object_id,
                'author': {
                    'id': item.author.id,
                    'username': item.author.username,
                    'trust_level': {
                        'level': item.author.trust_level.level if hasattr(item.author, 'trust_level') else 0,
                        'name': item.author.trust_level.level_name if hasattr(item.author, 'trust_level') else 'New User',
                    }
                },
                'reason': item.reason,
                'priority_score': item.priority_score,
                'flags_count': item.flags_count,
                'status': item.status,
                'created_at': item.created_at.isoformat(),
                'reviewed_at': item.reviewed_at.isoformat() if item.reviewed_at else None,
                'reviewed_by': {
                    'id': item.reviewed_by.id,
                    'username': item.reviewed_by.username,
                } if item.reviewed_by else None,
                'review_notes': item.review_notes,
                'content_preview': self._get_content_preview(item),
            })

        return Response({
            'results': serialized_items,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size,
                'has_next': end < total_count,
                'has_previous': page > 1,
            }
        })

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """
        Review a moderation queue item.

        Body params:
        - action: approve or reject (required)
        - notes: Review notes (optional)
        """
        # Check permissions
        if not self._can_moderate(request.user):
            return Response(
                {'error': 'You do not have permission to review content.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            item = ReviewQueue.objects.get(pk=pk)
        except ReviewQueue.DoesNotExist:
            return Response(
                {'error': 'Queue item not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        action = request.data.get('action')
        notes = request.data.get('notes', '')

        if action not in ['approve', 'reject']:
            return Response(
                {'error': 'Invalid action. Must be "approve" or "reject".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Perform review
        review_service = container.get_review_queue_service()
        success = review_service.review_item(
            item_id=item.id,
            reviewer=request.user,
            action=action,
            notes=notes
        )

        if success:
            return Response({
                'message': f'Content {action}d successfully.',
                'item_id': item.id,
                'action': action,
            })
        else:
            return Response(
                {'error': 'Failed to review item.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get moderation statistics."""
        # Check permissions
        if not self._can_moderate(request.user):
            return Response(
                {'error': 'You do not have permission to view moderation stats.'},
                status=status.HTTP_403_FORBIDDEN
            )

        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        # Get counts
        stats = {
            'pending': ReviewQueue.objects.filter(status='pending').count(),
            'approved': ReviewQueue.objects.filter(status='approved').count(),
            'rejected': ReviewQueue.objects.filter(status='rejected').count(),
            'today_count': ReviewQueue.objects.filter(
                created_at__date=today
            ).count(),
            'yesterday_count': ReviewQueue.objects.filter(
                created_at__date=yesterday
            ).count(),
            'by_content_type': {},
            'by_priority': {},
        }

        # By content type
        content_types = ReviewQueue.objects.values(
            'content_type__model'
        ).annotate(count=Count('id')).filter(status='pending')

        for ct in content_types:
            stats['by_content_type'][ct['content_type__model']] = ct['count']

        # By priority
        priorities = ReviewQueue.objects.values(
            'priority_score'
        ).annotate(count=Count('id')).filter(status='pending').order_by('-priority_score')

        for p in priorities:
            stats['by_priority'][p['priority_score']] = p['count']

        return Response(stats)

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get moderation analytics with trends.

        Query params:
        - days: Number of days to analyze (default: 7)
        """
        # Check permissions
        if not self._can_moderate(request.user):
            return Response(
                {'error': 'You do not have permission to view moderation analytics.'},
                status=status.HTTP_403_FORBIDDEN
            )

        from django.utils import timezone
        from datetime import timedelta

        days = int(request.query_params.get('days', 7))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Get reviews in timeframe
        reviews = ModerationLog.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).select_related('moderator')

        total_reviews = reviews.count()
        approved_count = reviews.filter(action_type='approve').count()
        rejected_count = reviews.filter(action_type='reject').count()

        approval_rate = (approved_count / total_reviews * 100) if total_reviews > 0 else 0

        # Get pending items
        pending_items = ReviewQueue.objects.filter(status='pending').count()

        # Calculate trends comparing to previous period
        previous_start_date = start_date - timedelta(days=days)
        previous_end_date = start_date

        previous_reviews = ModerationLog.objects.filter(
            timestamp__gte=previous_start_date,
            timestamp__lt=previous_end_date
        )
        previous_total = previous_reviews.count()
        previous_approved = previous_reviews.filter(action_type='approve').count()

        # Calculate percentage change
        review_trend = ((total_reviews - previous_total) / previous_total * 100) if previous_total > 0 else 0
        approval_trend = ((approved_count - previous_approved) / previous_approved * 100) if previous_approved > 0 else 0

        # Calculate average response time (time from creation to review)
        from django.db.models import Avg, F, ExpressionWrapper, fields

        avg_response_time_data = ReviewQueue.objects.filter(
            status__in=['approved', 'rejected'],
            resolved_at__isnull=False,
            created_at__isnull=False
        ).annotate(
            response_duration=ExpressionWrapper(
                F('resolved_at') - F('created_at'),
                output_field=fields.DurationField()
            )
        ).aggregate(avg_time=Avg('response_duration'))

        avg_response_seconds = None
        if avg_response_time_data['avg_time']:
            avg_response_seconds = avg_response_time_data['avg_time'].total_seconds()

        # Get top moderators (users with most moderation actions in the period)
        top_moderators_data = ModerationLog.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).values(
            'moderator__id',
            'moderator__username'
        ).annotate(
            action_count=Count('id')
        ).order_by('-action_count')[:5]

        top_moderators = [
            {
                'user_id': mod['moderator__id'],
                'username': mod['moderator__username'],
                'actions': mod['action_count']
            }
            for mod in top_moderators_data
        ]

        # Get daily activity breakdown
        from django.db.models.functions import TruncDate

        daily_activity_data = ModerationLog.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).annotate(
            day=TruncDate('timestamp')
        ).values('day').annotate(
            total_actions=Count('id'),
            approvals=Count('id', filter=Q(action_type='approve')),
            rejections=Count('id', filter=Q(action_type='reject'))
        ).order_by('day')

        daily_activity = [
            {
                'date': item['day'].isoformat(),
                'total_actions': item['total_actions'],
                'approvals': item['approvals'],
                'rejections': item['rejections']
            }
            for item in daily_activity_data
        ]

        return Response({
            'total_reviews': total_reviews,
            'approved': approved_count,
            'rejected': rejected_count,
            'approval_rate': round(approval_rate, 1),
            'pending_items': pending_items,
            'time_period': f'{days} days',
            'trends': {
                'reviews': {
                    'current': total_reviews,
                    'previous': previous_total,
                    'change_percent': round(review_trend, 1)
                },
                'approvals': {
                    'current': approved_count,
                    'previous': previous_approved,
                    'change_percent': round(approval_trend, 1)
                }
            },
            'avg_response_time_seconds': round(avg_response_seconds, 1) if avg_response_seconds else None,
            'top_moderators': top_moderators,
            'daily_activity': daily_activity,
        })

    # Helper methods
    def _can_moderate(self, user):
        """Check if user can access moderation features."""
        return user.is_staff or user.is_superuser or (
            hasattr(user, 'trust_level') and user.trust_level.level >= 3
        )

    def _get_content_preview(self, item):
        """Get preview text for the content being reviewed."""
        from django.contrib.contenttypes.models import ContentType
        from machina.apps.forum_conversation.models import Post, Topic

        content_type = item.content_type
        model_class = content_type.model_class()

        try:
            if model_class == Post:
                post = Post.objects.get(id=item.object_id)
                content = post.content.raw if hasattr(post.content, 'raw') else str(post.content)
                return content[:200] + ('...' if len(content) > 200 else '')
            elif model_class == Topic:
                topic = Topic.objects.get(id=item.object_id)
                return topic.subject
            else:
                return "N/A"
        except Exception:
            return "Content not available"
