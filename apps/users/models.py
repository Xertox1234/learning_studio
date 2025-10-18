"""
User models for Python Learning Studio.
"""

from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from .validators import (
    SecureAvatarUpload,
    SecureIconUpload,
    SecureAchievementIconUpload,
    validate_image_file_size,
    validate_image_dimensions,
    validate_image_content,
    validate_mime_type,
)


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
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
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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

    def save(self, *args, **kwargs):
        """
        Delete old avatar when uploading new one.

        Uses select_for_update() to prevent race conditions when
        multiple requests attempt to update the same user concurrently.
        """
        from django.db import transaction

        old_avatar = None

        if self.pk:
            try:
                # Lock the row to prevent concurrent modifications
                with transaction.atomic():
                    old_instance = User.objects.select_for_update().get(pk=self.pk)
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
