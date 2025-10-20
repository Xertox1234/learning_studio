"""
Community features ViewSets for discussions, study groups, and collaboration.
"""

from typing import Optional
from django.db.models import Q, QuerySet
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from apps.learning.models import (
    Discussion, DiscussionReply, StudyGroup, StudyGroupPost,
    PeerReview, CodeReview, LearningBuddy, LearningSession,
    Notification, StudyGroupMembership
)
from ..serializers import (
    DiscussionSerializer, DiscussionReplySerializer,
    StudyGroupSerializer, StudyGroupPostSerializer,
    PeerReviewSerializer, CodeReviewSerializer,
    LearningBuddySerializer, LearningSessionSerializer,
    NotificationSerializer
)
from ..permissions import IsOwnerOrReadOnly, IsOwnerOrAdmin
from ..mixins import RateLimitMixin


class DiscussionViewSet(RateLimitMixin, viewsets.ModelViewSet):
    """ViewSet for Discussion model."""
    queryset = Discussion.objects.all().order_by('-is_pinned', '-last_activity_at')
    serializer_class = DiscussionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self) -> QuerySet[Discussion]:
        queryset = super().get_queryset()

        # Filter by course, lesson, or exercise
        course: Optional[str] = self.request.query_params.get('course')
        if course:
            queryset = queryset.filter(course__slug=course)

        lesson: Optional[str] = self.request.query_params.get('lesson')
        if lesson:
            queryset = queryset.filter(lesson__slug=lesson)

        exercise: Optional[str] = self.request.query_params.get('exercise')
        if exercise:
            queryset = queryset.filter(exercise__slug=exercise)

        return queryset.select_related('author', 'course', 'lesson', 'exercise')

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'])
    def replies(self, request: Request, pk: Optional[int] = None) -> Response:
        """Get replies for this discussion."""
        discussion: Discussion = self.get_object()
        replies: QuerySet[DiscussionReply] = discussion.replies.filter(parent_reply__isnull=True).order_by('created_at')
        serializer: DiscussionReplySerializer = DiscussionReplySerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)


class DiscussionReplyViewSet(RateLimitMixin, viewsets.ModelViewSet):
    """ViewSet for DiscussionReply model."""
    serializer_class = DiscussionReplySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self) -> QuerySet[DiscussionReply]:
        return DiscussionReply.objects.all().select_related('author', 'discussion')

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(author=self.request.user)


class StudyGroupViewSet(viewsets.ModelViewSet):
    """ViewSet for StudyGroup model."""
    queryset = StudyGroup.objects.filter(is_active=True, is_public=True)
    serializer_class = StudyGroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def join(self, request: Request, pk: Optional[int] = None) -> Response:
        """Join study group."""
        study_group: StudyGroup = self.get_object()
        if study_group.is_full:
            return Response({'message': 'Study group is full'}, status=status.HTTP_400_BAD_REQUEST)

        membership, created = StudyGroupMembership.objects.get_or_create(
            user=request.user,
            study_group=study_group
        )
        if created:
            return Response({'message': 'Joined study group'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Already a member'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def leave(self, request: Request, pk: Optional[int] = None) -> Response:
        """Leave study group."""
        study_group: StudyGroup = self.get_object()
        try:
            membership: StudyGroupMembership = StudyGroupMembership.objects.get(
                user=request.user,
                study_group=study_group
            )
            membership.delete()
            return Response({'message': 'Left study group'}, status=status.HTTP_204_NO_CONTENT)
        except StudyGroupMembership.DoesNotExist:
            return Response({'message': 'Not a member'}, status=status.HTTP_404_NOT_FOUND)


class StudyGroupPostViewSet(viewsets.ModelViewSet):
    """ViewSet for StudyGroupPost model."""
    serializer_class = StudyGroupPostSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self) -> QuerySet[StudyGroupPost]:
        # Only show posts from groups user is a member of
        user_groups: QuerySet[StudyGroup] = StudyGroup.objects.filter(members=self.request.user)
        return StudyGroupPost.objects.filter(study_group__in=user_groups).order_by('-created_at')

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(author=self.request.user)


class PeerReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PeerReview model with object-level authorization.

    Security:
        - Users can only view/edit their own peer reviews
        - Staff can view/edit all peer reviews
        - Implements IDOR/BOLA prevention

    Permissions:
        - IsAuthenticated: Requires user to be logged in
        - IsOwnerOrAdmin: Checks ownership at object level
    """
    queryset = PeerReview.objects.all()  # For router introspection only
    serializer_class = PeerReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self) -> QuerySet[PeerReview]:
        """
        Filter queryset to only user's own peer reviews.
        Staff can see all peer reviews.

        Security: Prevents IDOR attacks by filtering at queryset level.
        """
        user = self.request.user

        if user.is_staff or user.is_superuser:
            # Staff can see all peer reviews
            return PeerReview.objects.all().order_by('-created_at')

        # Regular users can only see their own peer reviews
        return PeerReview.objects.filter(author=user).order_by('-created_at')

    def perform_create(self, serializer: Serializer) -> None:
        """
        Force ownership to authenticated user.

        Security: Prevents ownership hijacking
        """
        serializer.save(author=self.request.user)


class CodeReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CodeReview model with object-level authorization.

    Security:
        - Users can only view/edit their own code reviews
        - Staff can view/edit all code reviews
        - Implements IDOR/BOLA prevention

    Permissions:
        - IsAuthenticated: Requires user to be logged in
        - IsOwnerOrAdmin: Checks ownership at object level
    """
    queryset = CodeReview.objects.all()  # For router introspection only
    serializer_class = CodeReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self) -> QuerySet[CodeReview]:
        """
        Filter queryset to only user's own code reviews.
        Staff can see all code reviews.

        Security: Prevents IDOR attacks by filtering at queryset level.
        """
        user = self.request.user

        if user.is_staff or user.is_superuser:
            # Staff can see all code reviews
            return CodeReview.objects.all().select_related('reviewer', 'peer_review')

        # Regular users can only see their own code reviews
        return CodeReview.objects.filter(reviewer=user).select_related('reviewer', 'peer_review')

    def perform_create(self, serializer: Serializer) -> None:
        """
        Force ownership to authenticated user.

        Security: Prevents ownership hijacking
        """
        serializer.save(reviewer=self.request.user)


class LearningBuddyViewSet(viewsets.ModelViewSet):
    """ViewSet for LearningBuddy model."""
    serializer_class = LearningBuddySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self) -> QuerySet[LearningBuddy]:
        return LearningBuddy.objects.filter(
            Q(user1=self.request.user) | Q(user2=self.request.user),
            is_active=True
        )

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(user1=self.request.user)


class LearningSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for LearningSession model."""
    queryset = LearningSession.objects.filter(is_public=True).order_by('scheduled_at')
    serializer_class = LearningSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(organizer=self.request.user)


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for Notification model."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self) -> QuerySet[Notification]:
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request: Request, pk: Optional[int] = None) -> Response:
        """Mark notification as read."""
        notification: Notification = self.get_object()
        notification.mark_as_read()
        return Response({'message': 'Notification marked as read'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request: Request) -> Response:
        """Mark all notifications as read."""
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read'}, status=status.HTTP_200_OK)