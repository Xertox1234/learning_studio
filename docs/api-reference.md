"""
API URL configuration for Python Learning Studio.
Provides REST API endpoints for all core functionality.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router for ViewSets
router = DefaultRouter()

# Learning Management API
router.register(r'categories', views.CategoryViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'lessons', views.LessonViewSet)
router.register(r'enrollments', views.CourseEnrollmentViewSet, basename='courseenrollment')
router.register(r'progress', views.UserProgressViewSet, basename='userprogress')
router.register(r'learning-paths', views.LearningPathViewSet)
router.register(r'reviews', views.CourseReviewViewSet, basename='coursereview')

# Exercise System API
router.register(r'programming-languages', views.ProgrammingLanguageViewSet)
router.register(r'exercise-types', views.ExerciseTypeViewSet)
router.register(r'exercises', views.ExerciseViewSet)
router.register(r'submissions', views.SubmissionViewSet, basename='submission')
router.register(r'test-cases', views.TestCaseViewSet)
router.register(r'exercise-progress', views.StudentProgressViewSet, basename='studentprogress')
router.register(r'hints', views.ExerciseHintViewSet)

# Community Features API
router.register(r'discussions', views.DiscussionViewSet)
router.register(r'discussion-replies', views.DiscussionReplyViewSet, basename='discussionreply')
router.register(r'study-groups', views.StudyGroupViewSet)
router.register(r'study-group-posts', views.StudyGroupPostViewSet, basename='studygrouppost')
router.register(r'peer-reviews', views.PeerReviewViewSet)
router.register(r'code-reviews', views.CodeReviewViewSet, basename='codereview')
router.register(r'learning-buddies', views.LearningBuddyViewSet, basename='learningbuddy')
router.register(r'learning-sessions', views.LearningSessionViewSet)
router.register(r'notifications', views.NotificationViewSet, basename='notification')

# User Management API
router.register(r'users', views.UserViewSet)
router.register(r'user-profiles', views.UserProfileViewSet)

app_name = 'api'

urlpatterns = [
    # API Root
    path('v1/', include(router.urls)),
    
    # Authentication endpoints
    path('auth/', include('rest_framework.urls')),
    
    # Custom API endpoints
    path('v1/code-execution/', views.CodeExecutionView.as_view(), name='code-execution'),
    path('v1/ai-assistance/', views.AIAssistanceView.as_view(), name='ai-assistance'),
    path('v1/exercise-evaluation/', views.ExerciseEvaluationView.as_view(), name='exercise-evaluation'),
    
    # Docker-based code execution endpoints
    path('v1/execute/', views.execute_code, name='execute-code'),
    path('v1/exercises/<int:exercise_id>/submit/', views.submit_exercise_code, name='submit-exercise-code'),
    path('v1/docker/status/', views.docker_status, name='docker-status'),
    
    # API Documentation (to be implemented)
    # path('docs/', include_docs_urls(title='Python Learning Studio API')),
]