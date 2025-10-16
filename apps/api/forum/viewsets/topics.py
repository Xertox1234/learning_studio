"""
Topic ViewSet for CRUD operations on forum topics.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from machina.apps.forum_conversation.models import Topic, Post
from ..serializers import (
    TopicListSerializer,
    TopicDetailSerializer,
    TopicCreateSerializer,
    PostListSerializer
)


class TopicViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing forum topics.

    list: Get all topics (paginated)
    create: Create a new topic
    retrieve: Get detailed information about a specific topic
    update: Update a topic (requires permission)
    destroy: Delete a topic (requires permission)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'pk'

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return TopicCreateSerializer
        elif self.action == 'retrieve':
            return TopicDetailSerializer
        return TopicListSerializer

    def get_queryset(self):
        """Get topics with optimized queries."""
        queryset = Topic.objects.filter(
            approved=True
        ).select_related(
            'forum',
            'poster',
            'poster__trust_level',
            'last_post',
            'last_post__poster'
        ).order_by('-last_post_on')

        # Filter by forum if specified
        forum_id = self.request.query_params.get('forum_id')
        if forum_id:
            queryset = queryset.filter(forum_id=forum_id)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create a new topic with first post."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        topic = serializer.save()

        # Return created topic with detail serializer
        detail_serializer = TopicDetailSerializer(topic, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update a topic (subject, type)."""
        topic = self.get_object()

        # Check permissions
        if not self._can_edit_topic(request.user, topic):
            return Response(
                {'error': 'You do not have permission to edit this topic.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update subject and type
        if 'subject' in request.data:
            topic.subject = request.data['subject']
        if 'type' in request.data:
            # Only moderators can change type
            if self._is_moderator(request.user):
                topic.type = request.data['type']

        topic.save()

        serializer = TopicDetailSerializer(topic, context={'request': request})
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Delete a topic."""
        topic = self.get_object()

        # Check permissions
        if not self._can_delete_topic(request.user, topic):
            return Response(
                {'error': 'You do not have permission to delete this topic.'},
                status=status.HTTP_403_FORBIDDEN
            )

        forum = topic.forum
        topic.delete()

        # Update forum trackers
        if forum:
            forum.update_trackers()
            forum.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """
        Get posts for a specific topic with pagination.

        Query params:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 20, max: 100)
        """
        topic = self.get_object()

        # Increment view count
        topic.views_count += 1
        topic.save(update_fields=['views_count'])

        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)

        # Get posts
        posts = Post.objects.filter(
            topic=topic,
            approved=True
        ).select_related(
            'poster',
            'poster__trust_level'
        ).order_by('created')

        # Calculate pagination
        start = (page - 1) * page_size
        end = start + page_size
        total_count = posts.count()

        page_posts = posts[start:end]

        # Serialize
        serializer = PostListSerializer(page_posts, many=True, context={'request': request})

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

    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        """Subscribe to topic notifications."""
        topic = self.get_object()

        if request.user in topic.subscribers.all():
            return Response({'message': 'Already subscribed'}, status=status.HTTP_200_OK)

        topic.subscribers.add(request.user)
        return Response({'message': 'Subscribed successfully'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'])
    def unsubscribe(self, request, pk=None):
        """Unsubscribe from topic notifications."""
        topic = self.get_object()

        if request.user not in topic.subscribers.all():
            return Response({'message': 'Not subscribed'}, status=status.HTTP_200_OK)

        topic.subscribers.remove(request.user)
        return Response({'message': 'Unsubscribed successfully'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        """Lock a topic (moderators only)."""
        topic = self.get_object()

        if not self._is_moderator(request.user):
            return Response(
                {'error': 'Only moderators can lock topics.'},
                status=status.HTTP_403_FORBIDDEN
            )

        topic.status = Topic.TOPIC_LOCKED
        topic.save()

        return Response({'message': 'Topic locked successfully'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def unlock(self, request, pk=None):
        """Unlock a topic (moderators only)."""
        topic = self.get_object()

        if not self._is_moderator(request.user):
            return Response(
                {'error': 'Only moderators can unlock topics.'},
                status=status.HTTP_403_FORBIDDEN
            )

        topic.status = Topic.TOPIC_UNLOCKED
        topic.save()

        return Response({'message': 'Topic unlocked successfully'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """Pin a topic (moderators only)."""
        topic = self.get_object()

        if not self._is_moderator(request.user):
            return Response(
                {'error': 'Only moderators can pin topics.'},
                status=status.HTTP_403_FORBIDDEN
            )

        pin_type = request.data.get('type', 'sticky')  # sticky or announce
        topic.type = Topic.TOPIC_ANNOUNCE if pin_type == 'announce' else Topic.TOPIC_STICKY
        topic.save()

        return Response({'message': f'Topic pinned as {pin_type}'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def unpin(self, request, pk=None):
        """Unpin a topic (moderators only)."""
        topic = self.get_object()

        if not self._is_moderator(request.user):
            return Response(
                {'error': 'Only moderators can unpin topics.'},
                status=status.HTTP_403_FORBIDDEN
            )

        topic.type = Topic.TOPIC_POST
        topic.save()

        return Response({'message': 'Topic unpinned successfully'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Move a topic to another forum (moderators only)."""
        topic = self.get_object()

        if not self._is_moderator(request.user):
            return Response(
                {'error': 'Only moderators can move topics.'},
                status=status.HTTP_403_FORBIDDEN
            )

        new_forum_id = request.data.get('forum_id')
        if not new_forum_id:
            return Response(
                {'error': 'forum_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from machina.apps.forum.models import Forum
        try:
            new_forum = Forum.objects.get(id=new_forum_id, type=Forum.FORUM_POST)
        except Forum.DoesNotExist:
            return Response(
                {'error': 'Forum not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        old_forum = topic.forum
        topic.forum = new_forum
        topic.save()

        # Update trackers for both forums
        if old_forum:
            old_forum.update_trackers()
            old_forum.save()
        new_forum.update_trackers()
        new_forum.save()

        return Response({
            'message': f'Topic moved to {new_forum.name}',
            'new_forum_id': new_forum.id,
        }, status=status.HTTP_200_OK)

    # Helper methods
    def _is_moderator(self, user):
        """Check if user is a moderator."""
        return user.is_staff or user.is_superuser or (
            hasattr(user, 'trust_level') and user.trust_level.level >= 3
        )

    def _can_edit_topic(self, user, topic):
        """Check if user can edit the topic."""
        return topic.poster == user or self._is_moderator(user)

    def _can_delete_topic(self, user, topic):
        """Check if user can delete the topic."""
        return topic.poster == user or self._is_moderator(user)
