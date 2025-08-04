"""
URL patterns for forum integration features
"""
from django.urls import path
from . import views
# from . import moderation_views, achievement_views  # Temporarily disabled

app_name = 'forum_integration'

urlpatterns = [
    # Trust Level System
    # path('trust-level/', views.trust_level_profile, name='trust_level_profile'),
    # path('api/track-reading-time/', views.track_reading_time, name='track_reading_time'),
    
    # Basic forum integration endpoints only for now
]