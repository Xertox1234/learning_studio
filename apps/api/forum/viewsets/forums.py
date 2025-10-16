"""
Forum ViewSet for listing and retrieving forums.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from django.db.models import Count, Q
from machina.apps.forum.models import Forum
from ..serializers import ForumListSerializer, ForumDetailSerializer


class ForumViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing forums.

    list: Get all forums organized by category
    retrieve: Get detailed information about a specific forum
    """
    permission_classes = [AllowAny]  # Allow anyone to view forums
    lookup_field = 'slug'

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ForumDetailSerializer
        return ForumListSerializer

    def get_queryset(self):
        """Get forums with optimized queries."""
        return Forum.objects.filter(
            type=Forum.FORUM_POST
        ).select_related(
            'parent'
        ).prefetch_related(
            'children'
        ).order_by('tree_id', 'lft')

    def list(self, request, *args, **kwargs):
        """
        Get forum list organized by categories.

        Returns forums grouped by their parent categories with statistics.
        """
        # Get all categories
        categories = Forum.objects.filter(type=Forum.FORUM_CAT).order_by('tree_id', 'lft')

        forums_data = []
        for category in categories:
            # Get child forums for this category
            child_forums = category.get_children().filter(type=Forum.FORUM_POST)

            if child_forums.exists():
                category_data = {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': str(category.description) if category.description else '',
                    'type': 'category',
                    'forums': ForumListSerializer(child_forums, many=True, context={'request': request}).data
                }
                forums_data.append(category_data)

        # Get overall forum statistics using DI container
        from apps.api.services.container import container
        stats_service = container.get_statistics_service()
        overall_stats = stats_service.get_forum_statistics()

        return Response({
            'categories': forums_data,
            'stats': {
                'total_topics': overall_stats['total_topics'],
                'total_posts': overall_stats['total_posts'],
                'total_users': overall_stats['total_users'],
                'online_users': overall_stats['online_users'],
            }
        })

    @action(detail=True, methods=['get'])
    def topics(self, request, slug=None):
        """
        Get topics for a specific forum with pagination.

        Query params:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 20, max: 100)
        - sort: Sort by (activity, created, title, views)
        - pinned: Show only pinned topics (true/false)
        """
        forum = self.get_object()
        from machina.apps.forum_conversation.models import Topic
        from ..serializers import TopicListSerializer

        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        sort_by = request.GET.get('sort', 'activity')
        pinned_only = request.GET.get('pinned', '').lower() == 'true'

        # Build queryset
        queryset = Topic.objects.filter(
            forum=forum,
            approved=True
        ).select_related(
            'poster',
            'poster__trust_level',
            'last_post',
            'last_post__poster'
        )

        # Filter pinned if requested
        if pinned_only:
            queryset = queryset.filter(type__in=[Topic.TOPIC_STICKY, Topic.TOPIC_ANNOUNCE])

        # Apply sorting
        if sort_by == 'created':
            queryset = queryset.order_by('-created')
        elif sort_by == 'title':
            queryset = queryset.order_by('subject')
        elif sort_by == 'views':
            queryset = queryset.order_by('-views_count')
        else:  # activity (default)
            queryset = queryset.order_by('-last_post_on')

        # Separate pinned topics from regular topics
        pinned_topics = queryset.filter(type__in=[Topic.TOPIC_STICKY, Topic.TOPIC_ANNOUNCE])
        regular_topics = queryset.filter(type=Topic.TOPIC_POST)

        # Calculate pagination
        start = (page - 1) * page_size
        end = start + page_size

        # Combine pinned + regular topics
        all_topics = list(pinned_topics) + list(regular_topics)
        total_count = len(all_topics)
        page_topics = all_topics[start:end]

        # Serialize
        serializer = TopicListSerializer(page_topics, many=True, context={'request': request})

        return Response({
            'results': serializer.data,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size,
                'has_next': end < total_count,
                'has_previous': page > 1,
            }
        })

    @action(detail=True, methods=['get'])
    def stats(self, request, slug=None):
        """Get detailed statistics for a forum."""
        forum = self.get_object()
        from apps.api.services.container import container

        stats_service = container.get_statistics_service()
        stats = stats_service.get_forum_specific_stats(forum.id)

        return Response({
            'forum_id': forum.id,
            'forum_name': forum.name,
            'topics_count': forum.direct_topics_count,
            'posts_count': forum.direct_posts_count,
            'weekly_posts': stats['weekly_posts'],
            'online_users': stats['online_users'],
            'trending': stats['trending'],
        })
