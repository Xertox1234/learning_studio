"""
API URL configuration for Python Learning Studio.
Provides REST API endpoints for all core functionality.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  # Keep for backward compatibility during migration
from . import auth_views
from . import forum_api
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework import permissions

# Import from new modular structure
from .viewsets import (
    user, learning, exercises, community
)
from .views import code_execution, wagtail, integrated_content

# API Router for ViewSets
router = DefaultRouter()

# User Management API
router.register(r'users', user.UserViewSet)
router.register(r'user-profiles', user.UserProfileViewSet)

# Learning Management API
router.register(r'categories', learning.CategoryViewSet)
router.register(r'courses', learning.CourseViewSet)
router.register(r'lessons', learning.LessonViewSet)
router.register(r'enrollments', learning.CourseEnrollmentViewSet, basename='courseenrollment')
router.register(r'progress', learning.UserProgressViewSet, basename='userprogress')
router.register(r'learning-paths', learning.LearningPathViewSet)
router.register(r'reviews', learning.CourseReviewViewSet, basename='coursereview')

# Exercise System API
router.register(r'programming-languages', exercises.ProgrammingLanguageViewSet)
router.register(r'exercise-types', exercises.ExerciseTypeViewSet)
router.register(r'exercises', exercises.ExerciseViewSet)
router.register(r'submissions', exercises.SubmissionViewSet, basename='submission')
router.register(r'test-cases', exercises.TestCaseViewSet)
router.register(r'exercise-progress', exercises.StudentProgressViewSet, basename='studentprogress')
router.register(r'hints', exercises.ExerciseHintViewSet)

# Community Features API
router.register(r'discussions', community.DiscussionViewSet)
router.register(r'discussion-replies', community.DiscussionReplyViewSet, basename='discussionreply')
router.register(r'study-groups', community.StudyGroupViewSet)
router.register(r'study-group-posts', community.StudyGroupPostViewSet, basename='studygrouppost')
router.register(r'peer-reviews', community.PeerReviewViewSet)
router.register(r'code-reviews', community.CodeReviewViewSet, basename='codereview')
router.register(r'learning-buddies', community.LearningBuddyViewSet, basename='learningbuddy')
router.register(r'learning-sessions', community.LearningSessionViewSet)
router.register(r'notifications', community.NotificationViewSet, basename='notification')

app_name = 'api'

urlpatterns = [
    # API Root
    path('v1/', include(router.urls)),
    
    # Authentication endpoints for React frontend
    path('v1/auth/user/', auth_views.current_user, name='current-user'),
    path('v1/auth/login/', auth_views.login, name='auth-login'),
    path('v1/auth/register/', auth_views.register, name='auth-register'),
    path('v1/auth/logout/', auth_views.logout, name='auth-logout'),
    path('v1/auth/status/', auth_views.auth_status, name='auth-status'),
    
    # DRF Authentication (for browsable API)
    path('auth/', include('rest_framework.urls')),
    
    # Custom API endpoints
    path('v1/code-execution/', code_execution.CodeExecutionView.as_view(), name='code-execution'),
    path('v1/ai-assistance/', code_execution.AIAssistanceView.as_view(), name='ai-assistance'),
    path('v1/exercise-evaluation/', code_execution.ExerciseEvaluationView.as_view(), name='exercise-evaluation'),
    
    # Docker-based code execution endpoints
    path('v1/execute/', code_execution.execute_code, name='execute-code'),
    path('v1/exercises/<int:exercise_id>/submit/', code_execution.submit_exercise_code, name='submit-exercise-code'),
    path('v1/docker/status/', code_execution.docker_status, name='docker-status'),
    
    # Forum API endpoints
    path('v1/forums/', forum_api.forum_list, name='forum-list'),
    path('v1/forums/<slug:forum_slug>/<int:forum_id>/', forum_api.forum_detail, name='forum-detail'),
    path('v1/forums/<slug:forum_slug>/<int:forum_id>/topics/<slug:topic_slug>/<int:topic_id>/', forum_api.forum_topic_detail, name='forum-topic-detail'),
    
    # Forum Topic CRUD endpoints
    path('v1/topics/create/', forum_api.topic_create, name='topic-create'),
    path('v1/topics/<int:topic_id>/edit/', forum_api.topic_edit, name='topic-edit'),
    path('v1/topics/<int:topic_id>/delete/', forum_api.topic_delete, name='topic-delete'),
    
    # Forum Post CRUD endpoints
    path('v1/posts/create/', forum_api.post_create, name='post-create'),
    path('v1/topics/<int:topic_id>/reply/', forum_api.post_reply, name='post-reply'),
    path('v1/posts/<int:post_id>/edit/', forum_api.post_edit, name='post-edit'),
    path('v1/posts/<int:post_id>/delete/', forum_api.post_delete, name='post-delete'),
    path('v1/posts/<int:post_id>/quote/', forum_api.post_quote, name='post-quote'),
    
    # Dashboard Forum Stats
    path('v1/dashboard/forum-stats/', forum_api.dashboard_forum_stats, name='dashboard-forum-stats'),
    
    # Integrated Content API (Wagtail + Forum)
    path('v1/integrated-content/create/', integrated_content.create_integrated_content, name='create-integrated-content'),
    path('v1/integrated-content/permissions/', integrated_content.user_permissions, name='integrated-content-permissions'),
    path('v1/integrated-content/forums/', integrated_content.available_forums, name='available-forums'),
    path('v1/integrated-content/stats/', integrated_content.integrated_content_stats, name='integrated-content-stats'),
    path('v1/integrated-content/recent/', integrated_content.recent_integrated_content, name='recent-integrated-content'),
    path('v1/integrated-content/blog/<int:blog_post_id>/sync-forum/', integrated_content.sync_forum_topic, name='sync-forum-topic'),
    
    # Blog/Wagtail API endpoints - using views for compatibility during migration
    path('v1/blog/', wagtail.blog_index, name='blog-index'),
    path('v1/blog/categories/', wagtail.blog_categories, name='blog-categories'),
    path('v1/blog/<slug:post_slug>/', wagtail.blog_post_detail, name='blog-post-detail'),
    path('v1/wagtail/homepage/', wagtail.wagtail_homepage, name='wagtail-homepage'),
    path('v1/wagtail/playground/', wagtail.wagtail_playground, name='wagtail-playground'),
    
    # Wagtail Learning Content API endpoints
    path('v1/learning/', wagtail.learning_index, name='learning-index'),
    path('v1/learning/courses/', wagtail.courses_list, name='courses-list'),
    path('v1/learning/courses/<slug:course_slug>/', wagtail.course_detail, name='course-detail'),
    path('v1/learning/courses/<slug:course_slug>/lessons/<slug:lesson_slug>/', wagtail.lesson_detail, name='lesson-detail'),
    path('v1/learning/courses/<slug:course_slug>/lessons/<slug:lesson_slug>/exercises/<slug:exercise_slug>/', wagtail.exercise_detail, name='exercise-detail'),
    
    # Wagtail Exercise API endpoints
    path('v1/wagtail/exercises/', wagtail.exercises_list, name='wagtail-exercises-list'),
    path('v1/wagtail/exercises/<slug:exercise_slug>/', wagtail.exercise_detail, name='wagtail-exercise-detail'),
    path('v1/wagtail/step-exercises/<slug:exercise_slug>/', wagtail.step_exercise_detail, name='step-exercise-detail'),
    
    # Wagtail Course Enrollment endpoints
    path('v1/learning/courses/<slug:course_slug>/enroll/', wagtail.wagtail_course_enroll, name='wagtail-course-enroll'),
    path('v1/learning/courses/<slug:course_slug>/unenroll/', wagtail.wagtail_course_unenroll, name='wagtail-course-unenroll'),
    path('v1/learning/courses/<slug:course_slug>/enrollment-status/', wagtail.wagtail_course_enrollment_status, name='wagtail-course-enrollment-status'),
    path('v1/wagtail/user-enrollments/', wagtail.wagtail_user_enrollments, name='wagtail-user-enrollments'),

    # API Schema & Docs (public)
    path('schema/', SpectacularAPIView.as_view(permission_classes=[permissions.AllowAny]), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[permissions.AllowAny]), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema', permission_classes=[permissions.AllowAny]), name='redoc'),
]