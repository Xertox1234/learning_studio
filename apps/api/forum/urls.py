"""
URL configuration for forum API ViewSets.
"""
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .viewsets import (
    ForumViewSet,
    TopicViewSet,
    PostViewSet,
    ModerationQueueViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'forums', ForumViewSet, basename='forum')
router.register(r'topics', TopicViewSet, basename='topic')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'moderation', ModerationQueueViewSet, basename='moderation')

app_name = 'forum_api'

urlpatterns = [
    path('', include(router.urls)),
]
