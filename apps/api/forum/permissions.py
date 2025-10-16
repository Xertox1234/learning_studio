"""
Custom permissions for forum API endpoints.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsModeratorOrReadOnly(BasePermission):
    """
    Allow read-only access to all users, but write access only to moderators.
    Moderators are users with TL3+, staff, or superuser status.
    """

    def has_permission(self, request, view):
        """Check if user has permission for this request."""
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated

        return self._is_moderator(request.user)

    def _is_moderator(self, user):
        """Check if user is a moderator."""
        return user.is_staff or user.is_superuser or (
            hasattr(user, 'trust_level') and user.trust_level.level >= 3
        )


class IsOwnerOrModerator(BasePermission):
    """
    Allow access to content owners or moderators.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user has permission for this object."""
        # Read permissions are allowed to any authenticated user
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write permissions require ownership or moderator status
        is_owner = self._is_owner(request.user, obj)
        is_moderator = self._is_moderator(request.user)

        return is_owner or is_moderator

    def _is_owner(self, user, obj):
        """Check if user owns the object."""
        # Check for poster attribute (topics and posts)
        if hasattr(obj, 'poster'):
            return obj.poster == user

        # Check for author attribute (other models)
        if hasattr(obj, 'author'):
            return obj.author == user

        return False

    def _is_moderator(self, user):
        """Check if user is a moderator."""
        return user.is_staff or user.is_superuser or (
            hasattr(user, 'trust_level') and user.trust_level.level >= 3
        )


class CanPostToForum(BasePermission):
    """
    Check if user can post to a forum based on trust level and forum permissions.
    """

    def has_permission(self, request, view):
        """Check if user can create posts/topics."""
        if not request.user or not request.user.is_authenticated:
            return False

        # TL0 users can post but content goes to review queue
        # All other users can post freely
        return True


class CanModerate(BasePermission):
    """
    Permission class for moderation actions.
    Requires TL3+ (Regular), staff, or superuser status.
    """

    def has_permission(self, request, view):
        """Check if user can perform moderation actions."""
        if not request.user or not request.user.is_authenticated:
            return False

        return self._can_moderate(request.user)

    def _can_moderate(self, user):
        """Check if user has moderation permissions."""
        return user.is_staff or user.is_superuser or (
            hasattr(user, 'trust_level') and user.trust_level.level >= 3
        )


class CanLockTopic(BasePermission):
    """
    Permission to lock/unlock topics.
    Only moderators can lock topics.
    """

    def has_permission(self, request, view):
        """Check if user can lock topics."""
        if not request.user or not request.user.is_authenticated:
            return False

        return self._is_moderator(request.user)

    def _is_moderator(self, user):
        """Check if user is a moderator."""
        return user.is_staff or user.is_superuser or (
            hasattr(user, 'trust_level') and user.trust_level.level >= 3
        )


class CanPinTopic(BasePermission):
    """
    Permission to pin/unpin topics.
    Only moderators can pin topics.
    """

    def has_permission(self, request, view):
        """Check if user can pin topics."""
        if not request.user or not request.user.is_authenticated:
            return False

        return self._is_moderator(request.user)

    def _is_moderator(self, user):
        """Check if user is a moderator."""
        return user.is_staff or user.is_superuser or (
            hasattr(user, 'trust_level') and user.trust_level.level >= 3
        )


class CanMoveTopic(BasePermission):
    """
    Permission to move topics between forums.
    Only moderators can move topics.
    """

    def has_permission(self, request, view):
        """Check if user can move topics."""
        if not request.user or not request.user.is_authenticated:
            return False

        return self._is_moderator(request.user)

    def _is_moderator(self, user):
        """Check if user is a moderator."""
        return user.is_staff or user.is_superuser or (
            hasattr(user, 'trust_level') and user.trust_level.level >= 3
        )
