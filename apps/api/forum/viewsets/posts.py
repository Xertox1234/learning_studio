"""
Post ViewSet for CRUD operations on forum posts.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from machina.apps.forum_conversation.models import Post
from ..serializers import (
    PostListSerializer,
    PostDetailSerializer,
    PostCreateSerializer,
    PostUpdateSerializer
)


class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing forum posts.

    list: Get all posts (paginated, usually filtered by topic)
    create: Create a new post (reply to topic)
    retrieve: Get detailed information about a specific post
    update: Update a post (requires permission)
    destroy: Delete a post (requires permission)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'pk'

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PostCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PostUpdateSerializer
        elif self.action == 'retrieve':
            return PostDetailSerializer
        return PostListSerializer

    def get_queryset(self):
        """Get posts with optimized queries."""
        queryset = Post.objects.filter(
            approved=True
        ).select_related(
            'topic',
            'topic__forum',
            'poster',
            'poster__trust_level'
        ).order_by('created')

        # Filter by topic if specified
        topic_id = self.request.query_params.get('topic_id')
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        # Filter by user if specified
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(poster_id=user_id)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create a new post."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        post = serializer.save()

        # Return created post with detail serializer
        detail_serializer = PostDetailSerializer(post, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update a post."""
        post = self.get_object()

        # Check permissions
        if not self._can_edit_post(request.user, post):
            return Response(
                {'error': 'You do not have permission to edit this post.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(post, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        post = serializer.save()

        # Return updated post with detail serializer
        detail_serializer = PostDetailSerializer(post, context={'request': request})
        return Response(detail_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Delete a post."""
        post = self.get_object()

        # Check permissions
        if not self._can_delete_post(request.user, post):
            return Response(
                {'error': 'You do not have permission to delete this post.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Cannot delete first post in topic (must delete entire topic)
        if post.position == 1:
            return Response(
                {'error': 'Cannot delete the first post. Delete the entire topic instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        topic = post.topic
        forum = topic.forum
        post.delete()

        # Update topic and forum trackers
        topic.update_trackers()
        topic.save()

        if forum:
            forum.update_trackers()
            forum.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def quote(self, request, pk=None):
        """Get post content formatted for quoting."""
        post = self.get_object()

        quote_content = f"> **{post.poster.username}** wrote:\n"
        # Split content into lines and prefix each with >
        content_lines = str(post.content).split('\n')
        for line in content_lines:
            quote_content += f"> {line}\n"

        quote_content += "\n"  # Add blank line after quote

        return Response({
            'quoted_content': quote_content,
            'original_post_id': post.id,
            'original_poster': post.poster.username,
        })

    # Helper methods
    def _is_moderator(self, user):
        """Check if user is a moderator."""
        return user.is_staff or user.is_superuser or (
            hasattr(user, 'trust_level') and user.trust_level.level >= 3
        )

    def _can_edit_post(self, user, post):
        """Check if user can edit the post."""
        return post.poster == user or self._is_moderator(user)

    def _can_delete_post(self, user, post):
        """Check if user can delete the post."""
        return post.poster == user or self._is_moderator(user)
