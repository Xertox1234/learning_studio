"""
User repository for optimized user data access.

This repository provides optimized queries for user-related operations,
including trust levels, activity tracking, and authentication.
"""

from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Prefetch
from django.utils import timezone

from .base import OptimizedRepository


class UserRepository(OptimizedRepository):
    """
    Repository for User model with optimized queries.

    Handles user authentication, trust levels, and activity tracking.
    """

    def __init__(self):
        """Initialize with User model."""
        User = get_user_model()
        super().__init__(User)

    def _get_select_related(self) -> List[str]:
        """
        Optimize user queries with related data.

        Returns:
            List of fields to select_related
        """
        return ['trust_level']

    def _get_prefetch_related(self) -> List[str]:
        """
        Prefetch user's forum activity.

        Returns:
            List of fields to prefetch_related
        """
        return [
            'post_set',  # User's forum posts
            'topic_set',  # User's forum topics
        ]

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User's email address

        Returns:
            User instance or None
        """
        try:
            return self.get_optimized_queryset().get(email=email)
        except User.DoesNotExist:
            return None

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            User instance or None
        """
        try:
            return self.get_optimized_queryset().get(username=username)
        except User.DoesNotExist:
            return None

    def count_active_users(self) -> int:
        """
        Count active users.

        Returns:
            Number of active users
        """
        return self.count(is_active=True)

    def get_online_users(self, threshold_minutes: int = 15) -> List[User]:
        """
        Get users active within threshold.

        Args:
            threshold_minutes: Activity threshold in minutes

        Returns:
            List of online users
        """
        threshold = timezone.now() - timedelta(minutes=threshold_minutes)
        return list(
            self.get_optimized_queryset()
            .filter(
                is_active=True,
                last_login__gte=threshold
            )
            .order_by('-last_login')
        )

    def count_online_users(self, threshold_minutes: int = 15) -> int:
        """
        Count online users.

        Args:
            threshold_minutes: Activity threshold in minutes

        Returns:
            Number of online users
        """
        threshold = timezone.now() - timedelta(minutes=threshold_minutes)
        return self.count(
            is_active=True,
            last_login__gte=threshold
        )

    def get_latest_member(self) -> Optional[User]:
        """
        Get most recently joined active user.

        Returns:
            Latest user or None
        """
        return (
            self.filter(is_active=True)
            .order_by('-date_joined')
            .first()
        )

    def get_users_by_trust_level(self, level: int) -> List[User]:
        """
        Get users with specific trust level.

        Args:
            level: Trust level (0-4)

        Returns:
            List of users
        """
        return list(
            self.get_optimized_queryset()
            .filter(trust_level__level=level)
        )

    def get_moderators(self) -> List[User]:
        """
        Get users who can moderate (TL3+, staff, superuser).

        Returns:
            List of moderators
        """
        return list(
            self.get_optimized_queryset()
            .filter(
                Q(trust_level__level__gte=3) |
                Q(is_staff=True) |
                Q(is_superuser=True)
            )
            .distinct()
        )

    def search_users(self, query: str, limit: int = 20) -> List[User]:
        """
        Search users by username or email.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching users
        """
        return list(
            self.get_optimized_queryset()
            .filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
            .filter(is_active=True)
            .distinct()
            [:limit]
        )

    def get_users_with_post_count(self) -> List[User]:
        """
        Get users annotated with their post count.

        Returns:
            QuerySet with post_count annotation
        """
        return list(
            self.get_optimized_queryset()
            .annotate(post_count=Count('post'))
            .order_by('-post_count')
        )

    def get_active_users_since(self, since: datetime) -> List[User]:
        """
        Get users active since specified time.

        Args:
            since: Cutoff datetime

        Returns:
            List of active users
        """
        return list(
            self.get_optimized_queryset()
            .filter(
                is_active=True,
                last_login__gte=since
            )
            .order_by('-last_login')
        )

    def update_last_login(self, user_id: int) -> bool:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID

        Returns:
            True if updated
        """
        return self.update(user_id, last_login=timezone.now())

    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate a user account.

        Args:
            user_id: User ID

        Returns:
            True if deactivated
        """
        return self.update(user_id, is_active=False)

    def activate_user(self, user_id: int) -> bool:
        """
        Activate a user account.

        Args:
            user_id: User ID

        Returns:
            True if activated
        """
        return self.update(user_id, is_active=True)
