"""
User models for Python Learning Studio.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    """
    email = models.EmailField(unique=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
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
    icon = models.ImageField(upload_to='language_icons/', blank=True, null=True)
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


class Achievement(models.Model):
    """
    Achievements that users can earn.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    icon = models.ImageField(upload_to='achievement_icons/', blank=True, null=True)
    
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
