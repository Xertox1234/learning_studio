"""
Serializers for user models.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Achievement, UserAchievement

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_superuser', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'bio', 'location', 'birth_date', 'github_username',
            'linkedin_profile', 'twitter_username', 'personal_website',
            'preferred_language', 'timezone', 'learning_goals',
            'skill_level', 'coding_experience_years', 'motivation',
            'daily_coding_time', 'preferred_learning_style',
            'profile_picture', 'is_public', 'receive_notifications',
            'email_frequency', 'total_points', 'current_streak',
            'longest_streak', 'last_activity_date', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'total_points', 'current_streak', 'longest_streak',
            'last_activity_date', 'created_at', 'updated_at'
        ]

class AchievementSerializer(serializers.ModelSerializer):
    """Serializer for Achievement model."""
    
    class Meta:
        model = Achievement
        fields = [
            'id', 'name', 'description', 'icon', 'category',
            'difficulty', 'points_reward', 'requirements',
            'is_active', 'created_at'
        ]

class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer for UserAchievement model."""
    
    achievement = AchievementSerializer(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = [
            'id', 'user', 'achievement', 'earned_at', 'progress_data'
        ]