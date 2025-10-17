"""
User-related ViewSets for managing user profiles and authentication.
"""

from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.models import UserProfile
from ..serializers import UserSerializer, UserProfileSerializer
from ..permissions import IsOwnerOrReadOnly, IsOwnerOrAdmin

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for User model - read-only public profiles."""
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get or update current user profile."""
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserProfile model with object-level authorization.

    Security:
        - Users can only view/edit their own profile
        - Staff can view/edit all profiles
        - Implements IDOR/BOLA prevention via queryset filtering and permissions

    Permissions:
        - IsAuthenticated: Requires user to be logged in
        - IsOwnerOrAdmin: Checks ownership at object level
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """
        Filter queryset to only user's own profile.
        Staff can see all profiles.

        Security: Prevents IDOR attacks by filtering at queryset level.
        This ensures users cannot enumerate or access other users' profiles.
        """
        user = self.request.user

        if user.is_staff or user.is_superuser:
            # Admins see all profiles
            return UserProfile.objects.all()

        # Regular users can only see their own profile
        return UserProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        """
        Force ownership to authenticated user.

        Security: Prevents ownership hijacking by forcing user=request.user
        """
        serializer.save(user=self.request.user)