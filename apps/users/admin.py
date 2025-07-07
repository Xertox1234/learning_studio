"""
Admin configuration for User models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import (
    User, UserProfile, ProgrammingLanguage, 
    Achievement, UserAchievement, UserFollow
)


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin."""
    inlines = (UserProfileInline,)
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'experience_level', 'is_mentor', 'date_joined'
    ]
    list_filter = [
        'experience_level', 'is_mentor', 'accepts_mentees',
        'email_notifications', 'date_joined'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': ('bio', 'avatar', 'location', 'website', 'github_username', 'linkedin_url')
        }),
        ('Learning Preferences', {
            'fields': ('preferred_programming_languages', 'experience_level', 'learning_goals')
        }),
        ('Community Settings', {
            'fields': ('is_mentor', 'accepts_mentees', 'email_notifications')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('email', 'experience_level')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile."""
    list_display = [
        'user', 'skill_level', 'total_courses_completed',
        'total_exercises_solved', 'current_streak'
    ]
    list_filter = ['skill_level', 'profile_visibility']
    search_fields = ['user__username', 'user__email']
    filter_horizontal = ['programming_languages']
    readonly_fields = [
        'followers_count', 'following_count', 'created_at', 'updated_at'
    ]


@admin.register(ProgrammingLanguage)
class ProgrammingLanguageAdmin(admin.ModelAdmin):
    """Admin for ProgrammingLanguage."""
    list_display = ['name', 'popularity_rank', 'difficulty_level', 'created_at']
    list_filter = ['difficulty_level']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['popularity_rank', 'name']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """Admin for Achievement."""
    list_display = ['name', 'achievement_type', 'required_count', 'is_hidden']
    list_filter = ['achievement_type', 'is_hidden']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    """Admin for UserAchievement."""
    list_display = ['user', 'achievement', 'earned_at']
    list_filter = ['achievement__achievement_type', 'earned_at']
    search_fields = ['user__username', 'achievement__name']
    date_hierarchy = 'earned_at'


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    """Admin for UserFollow."""
    list_display = ['follower', 'following', 'created_at']
    search_fields = ['follower__username', 'following__username']
    date_hierarchy = 'created_at'
