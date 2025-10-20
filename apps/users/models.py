"""
User models for Python Learning Studio.
"""

from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from .validators import (
    SecureAvatarUpload,
    SecureIconUpload,
    SecureAchievementIconUpload,
    validate_image_file_size,
    validate_image_dimensions,
    validate_image_content,
    validate_mime_type,
)


class UserManager(DjangoUserManager):
    """
    Custom User manager that filters out soft-deleted users by default.

    Prevents soft-deleted users from appearing in queries unless explicitly requested.
    Implements GDPR "right to be forgotten" at database level.

    Related: Todo #024 - Implement Soft Delete Infrastructure
    """

    def get_queryset(self):
        """Return only non-deleted users by default."""
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        """Return all users including soft-deleted ones (admin use only)."""
        return super().get_queryset()

    def deleted_only(self):
        """Return only soft-deleted users (admin recovery use)."""
        return super().get_queryset().filter(is_deleted=True)


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.

    Implements soft delete to prevent CASCADE deletion of related objects.
    When deleted, user data is anonymized for GDPR compliance while preserving
    community content (forum posts, course reviews, etc.).

    Related: Todo #024 - Implement Soft Delete Infrastructure
    """
    email = models.EmailField(unique=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(
        upload_to=SecureAvatarUpload(),
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp']
            ),
            validate_image_file_size,
            validate_image_dimensions,
            validate_image_content,
            validate_mime_type,
        ],
        help_text='Profile picture (max 5 MB, JPG/PNG/GIF/WEBP, 50x50 to 2048x2048)'
    )
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    github_username = models.CharField(max_length=100, blank=True)
    linkedin_url = models.URLField(blank=True)

    # Learning preferences
    preferred_programming_languages = models.CharField(max_length=200, blank=True)
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        default='beginner'
    )
    learning_goals = models.TextField(max_length=1000, blank=True)

    # Profile settings
    is_mentor = models.BooleanField(default=False)
    accepts_mentees = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)

    # Soft delete fields
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Soft delete flag - user is hidden but data preserved'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text='Timestamp when user was soft deleted'
    )
    deletion_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text='Reason for account deletion (e.g., "user_request", "terms_violation")'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Custom manager
    objects = UserManager()

    class Meta:
        indexes = [
            # Soft delete filtering (most frequent query)
            models.Index(fields=['is_deleted'], name='user_is_deleted_idx'),
            # Recovery queries (admin searching deleted users)
            models.Index(fields=['is_deleted', 'deleted_at'], name='user_deleted_at_idx'),
            # Active users lookup
            models.Index(fields=['is_deleted', 'is_active'], name='user_active_idx'),
        ]

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('users:profile', kwargs={'username': self.username})

    def get_full_display_name(self):
        """Return full name if available, otherwise username."""
        return self.get_full_name() or self.username

    @property
    def total_achievements(self):
        """Return count of user achievements."""
        return self.achievements.count()

    @property
    def completion_rate(self):
        """Calculate course completion rate."""
        enrollments = self.enrollments.all()
        if not enrollments:
            return 0
        completed = enrollments.filter(completed=True).count()
        return int((completed / enrollments.count()) * 100)

    def soft_delete(self, reason='user_request'):
        """
        Soft delete user account (GDPR "right to be forgotten").

        Anonymizes personal data while preserving community contributions:
        - Forum posts remain but show "[Deleted User]"
        - Course reviews remain for other students
        - Enrollment history preserved for statistics
        - Personal data (email, name, bio) anonymized

        Idempotent - safe to call multiple times.

        Args:
            reason: Deletion reason (e.g., "user_request", "terms_violation")

        Related: Todo #024 - Implement Soft Delete Infrastructure
        """
        from django.db import transaction

        with transaction.atomic():
            # Use all_with_deleted() to prevent DoesNotExist if already deleted
            user = User.objects.all_with_deleted().select_for_update().get(pk=self.pk)

            # Idempotent check - skip if already deleted
            if user.is_deleted:
                return

            # Mark as deleted
            user.is_deleted = True
            user.deleted_at = timezone.now()
            user.deletion_reason = reason
            user.is_active = False  # Prevent login

            # Anonymize personal data
            user.anonymize_personal_data()

            user.save()

    def anonymize_personal_data(self):
        """
        Anonymize user's personal data for GDPR compliance.

        Removes PII while keeping username structure for foreign key integrity.
        Community content (posts, reviews) remains with "[Deleted User]" attribution.

        Fields anonymized:
        - Email: deleted_user_{id}@deleted.local
        - Name: [Deleted User]
        - Bio, location, website, social links: cleared
        - Avatar: deleted
        - Learning preferences: cleared
        """
        import uuid

        # Generate unique anonymous email (prevents unique constraint violations)
        self.email = f'deleted_user_{self.pk}@deleted.local'

        # Anonymize name
        self.first_name = '[Deleted'
        self.last_name = 'User]'

        # Clear personal information
        self.bio = ''
        self.location = ''
        self.website = ''
        self.github_username = ''
        self.linkedin_url = ''

        # Clear learning preferences
        self.preferred_programming_languages = ''
        self.learning_goals = ''

        # Delete avatar file
        if self.avatar:
            self.avatar.delete(save=False)
            self.avatar = None

        # Clear profile settings
        self.is_mentor = False
        self.accepts_mentees = False
        self.email_notifications = False

    def restore(self):
        """
        Restore soft-deleted user (admin recovery only).

        WARNING: Cannot restore anonymized data. Only un-deletes the account.
        User must re-enter personal information after restoration.

        Related: Todo #024 - Implement Soft Delete Infrastructure
        """
        from django.db import transaction

        if not self.is_deleted:
            return  # Already active

        with transaction.atomic():
            user = User.objects.all_with_deleted().select_for_update().get(pk=self.pk)
            user.is_deleted = False
            user.deleted_at = None
            user.is_active = True
            user.save()

    def hard_delete(self):
        """
        Permanently delete user and ALL related data.

        WARNING: This is irreversible and will CASCADE delete:
        - Forum posts, topics
        - Course enrollments, reviews
        - Exercise submissions
        - All related objects (90+ models)

        Only use when required by law (GDPR "right to erasure" after grace period).

        Related: Todo #024 - Implement Soft Delete Infrastructure
        """
        # Delete avatar file first
        if self.avatar:
            self.avatar.delete(save=False)

        # Bypass soft delete manager to permanently delete
        super(User, self).delete()

    def save(self, *args, **kwargs):
        """
        Delete old avatar when uploading new one.

        Uses select_for_update() to prevent race conditions when
        multiple requests attempt to update the same user concurrently.

        Handles soft-deleted users correctly using all_with_deleted().
        """
        from django.db import transaction

        old_avatar = None

        if self.pk:
            try:
                # Use all_with_deleted() to handle soft-deleted users
                with transaction.atomic():
                    old_instance = User.objects.all_with_deleted().select_for_update().get(pk=self.pk)
                    if old_instance.avatar and self.avatar != old_instance.avatar:
                        old_avatar = old_instance.avatar
            except User.DoesNotExist:
                pass

        # Save the new avatar
        super().save(*args, **kwargs)

        # Delete old file after successful save
        if old_avatar:
            old_avatar.delete(save=False)

    def delete(self, *args, **kwargs):
        """Delete avatar file when user deleted."""
        if self.avatar:
            self.avatar.delete(save=False)
        super().delete(*args, **kwargs)


class UserProfile(models.Model):
    """
    Extended profile information for users.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Programming skills
    programming_languages = models.ManyToManyField('ProgrammingLanguage', blank=True)
    skill_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        default='beginner'
    )
    
    # Learning statistics
    total_courses_completed = models.PositiveIntegerField(default=0)
    total_exercises_solved = models.PositiveIntegerField(default=0)
    total_study_hours = models.PositiveIntegerField(default=0)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    
    # Social features
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    
    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('private', 'Private'),
            ('friends', 'Friends Only'),
        ],
        default='public'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            # Composite indexes for common query patterns
            models.Index(
                fields=['skill_level', 'profile_visibility'],
                name='profile_skill_vis_idx'
            ),
            models.Index(
                fields=['profile_visibility', '-total_courses_completed'],
                name='profile_vis_courses_idx'
            ),
            models.Index(
                fields=['profile_visibility', '-total_exercises_solved'],
                name='profile_vis_exercises_idx'
            ),
            models.Index(
                fields=['-created_at'],
                name='profile_created_idx'
            ),
        ]

    def __str__(self):
        return f"{self.user.username}'s Profile"


class ProgrammingLanguage(models.Model):
    """
    Programming languages that users can be proficient in.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(
        upload_to=SecureIconUpload(),
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp']
            ),
            validate_image_file_size,
            validate_image_dimensions,
            validate_image_content,
            validate_mime_type,
        ],
        help_text='Language icon (max 5 MB, JPG/PNG/GIF/WEBP)'
    )
    official_website = models.URLField(blank=True)
    
    # Popularity and difficulty
    popularity_rank = models.PositiveIntegerField(default=1)
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner Friendly'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='intermediate'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['popularity_rank', 'name']
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Delete old icon when uploading new one.

        Uses select_for_update() to prevent race conditions when
        multiple requests attempt to update the same language concurrently.
        """
        from django.db import transaction

        old_icon = None

        if self.pk:
            try:
                # Lock the row to prevent concurrent modifications
                with transaction.atomic():
                    old_instance = ProgrammingLanguage.objects.select_for_update().get(pk=self.pk)
                    if old_instance.icon and self.icon != old_instance.icon:
                        old_icon = old_instance.icon
            except ProgrammingLanguage.DoesNotExist:
                pass

        # Save the new icon
        super().save(*args, **kwargs)

        # Delete old file after successful save
        if old_icon:
            old_icon.delete(save=False)

    def delete(self, *args, **kwargs):
        """Delete icon file when language deleted."""
        if self.icon:
            self.icon.delete(save=False)
        super().delete(*args, **kwargs)


class Achievement(models.Model):
    """
    Achievements that users can earn.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    icon = models.ImageField(
        upload_to=SecureAchievementIconUpload(),
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp']
            ),
            validate_image_file_size,
            validate_image_dimensions,
            validate_image_content,
            validate_mime_type,
        ],
        help_text='Achievement icon (max 5 MB, JPG/PNG/GIF/WEBP)'
    )

    
    # Achievement criteria
    achievement_type = models.CharField(
        max_length=20,
        choices=[
            ('course', 'Course Completion'),
            ('exercise', 'Exercise Solving'),
            ('streak', 'Learning Streak'),
            ('social', 'Social Interaction'),
            ('contribution', 'Community Contribution'),
        ]
    )
    
    # Requirements
    required_count = models.PositiveIntegerField(default=1)
    is_hidden = models.BooleanField(default=False)  # Hidden until earned
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Delete old icon when uploading new one.

        Uses select_for_update() to prevent race conditions when
        multiple requests attempt to update the same achievement concurrently.
        """
        from django.db import transaction

        old_icon = None

        if self.pk:
            try:
                # Lock the row to prevent concurrent modifications
                with transaction.atomic():
                    old_instance = Achievement.objects.select_for_update().get(pk=self.pk)
                    if old_instance.icon and self.icon != old_instance.icon:
                        old_icon = old_instance.icon
            except Achievement.DoesNotExist:
                pass

        # Save the new icon
        super().save(*args, **kwargs)

        # Delete old file after successful save
        if old_icon:
            old_icon.delete(save=False)

    def delete(self, *args, **kwargs):
        """Delete icon file when achievement deleted."""
        if self.icon:
            self.icon.delete(save=False)
        super().delete(*args, **kwargs)


class UserAchievement(models.Model):
    """
    Junction table for user achievements with timestamps.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class UserFollow(models.Model):
    """
    User following system for social features.
    """
    follower = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='following'
    )
    following = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


# Signal handlers for profile creation
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)
