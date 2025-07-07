"""
Discourse SSO models for tracking user synchronization.
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class DiscourseUser(models.Model):
    """
    Model to track the relationship between Django users and Discourse users.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='discourse_profile'
    )
    discourse_user_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Discourse user ID"
    )
    discourse_username = models.CharField(
        max_length=255,
        help_text="Username in Discourse"
    )
    last_sync = models.DateTimeField(
        auto_now=True,
        help_text="Last synchronization timestamp"
    )
    sync_enabled = models.BooleanField(
        default=True,
        help_text="Whether user sync is enabled"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Discourse User"
        verbose_name_plural = "Discourse Users"
        indexes = [
            models.Index(fields=['discourse_user_id']),
            models.Index(fields=['discourse_username']),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.discourse_username}"


class DiscourseGroupMapping(models.Model):
    """
    Model to map Django groups to Discourse groups.
    """
    django_group = models.OneToOneField(
        'auth.Group',
        on_delete=models.CASCADE,
        related_name='discourse_mapping'
    )
    discourse_group_name = models.CharField(
        max_length=255,
        help_text="Discourse group name"
    )
    auto_sync = models.BooleanField(
        default=True,
        help_text="Automatically sync group membership"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Discourse Group Mapping"
        verbose_name_plural = "Discourse Group Mappings"

    def __str__(self):
        return f"{self.django_group.name} → {self.discourse_group_name}"


class DiscourseSsoLog(models.Model):
    """
    Model to log SSO authentication attempts for debugging and monitoring.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='discourse_sso_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(
        max_length=50,
        choices=[
            ('login', 'SSO Login'),
            ('register', 'SSO Registration'),
            ('sync', 'User Sync'),
            ('error', 'SSO Error'),
        ]
    )
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    nonce = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Discourse SSO Log"
        verbose_name_plural = "Discourse SSO Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} - {self.action} at {self.timestamp}"