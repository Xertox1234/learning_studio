"""
WebSocket URL routing for real-time forum features
"""

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # Forum topic real-time updates
    path('ws/forum/topic/<int:topic_id>/', consumers.TopicConsumer.as_asgi()),
    
    # Forum-wide real-time updates
    path('ws/forum/<int:forum_id>/', consumers.ForumConsumer.as_asgi()),
    
    # User presence and notifications
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
    path('ws/notifications/<int:user_id>/', consumers.NotificationConsumer.as_asgi()),
    
    # Global forum activity
    path('ws/forum/activity/', consumers.ActivityConsumer.as_asgi()),
]