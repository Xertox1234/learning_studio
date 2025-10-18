"""
User-related ViewSets for managing user profiles and authentication.
"""

from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.users.models import UserProfile
from ..serializers import UserSerializer, UserProfileSerializer
from ..permissions import IsOwnerOrReadOnly, IsOwnerOrAdmin
from ..throttle import FileUploadThrottle

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for User model - read-only public profiles.

    Security Features:
    - File upload support with MultiPartParser for avatar uploads
    - Comprehensive validation at serializer level
    - JSON parser for non-file updates
    """
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Get or update current user profile.

        Supports:
        - GET: Retrieve current user profile
        - PATCH: Update user profile (including avatar upload)

        Security:
        - Avatar uploads validated for extension, MIME type, size, dimensions
        - File paths generated with UUID (no user input)
        - Old avatars deleted automatically on update
        """
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser],
        throttle_classes=[FileUploadThrottle]
    )
    def upload_avatar(self, request):
        """
        Dedicated endpoint for avatar uploads.

        POST /api/v1/users/upload_avatar/

        Security:
        - Requires authentication
        - Rate limited to 10 uploads per minute (CWE-400 prevention)
        - Comprehensive validation via UserSerializer.validate_avatar()
        - UUID-based filenames prevent path traversal
        - Old avatars deleted automatically

        Request:
            multipart/form-data with 'avatar' field

        Response:
            200: {avatar_url: "https://example.com/media/avatars/user_123/uuid.jpg"}
            400: {avatar: ["Error message"]}
            429: {"detail": "Request was throttled. Expected available in X seconds."}
        """
        user = request.user

        if 'avatar' not in request.data:
            return Response(
                {'avatar': ['No avatar file provided']},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(user, data={'avatar': request.data['avatar']}, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                'avatar_url': serializer.data.get('avatar_url'),
                'message': 'Avatar uploaded successfully'
            })

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
    queryset = UserProfile.objects.all()  # For router introspection only
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