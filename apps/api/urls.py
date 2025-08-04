"""
API URL configuration for Python Learning Studio.
Provides REST API endpoints for all core functionality.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import auth_views

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
    
    # Authentication endpoints for React frontend
    path('v1/auth/user/', auth_views.current_user, name='current-user'),
    path('v1/auth/login/', auth_views.login, name='auth-login'),
    path('v1/auth/register/', auth_views.register, name='auth-register'),
    path('v1/auth/logout/', auth_views.logout, name='auth-logout'),
    path('v1/auth/status/', auth_views.auth_status, name='auth-status'),
    
    # DRF Authentication (for browsable API)
    path('auth/', include('rest_framework.urls')),
    
    # Custom API endpoints
    path('v1/code-execution/', views.CodeExecutionView.as_view(), name='code-execution'),
    path('v1/ai-assistance/', views.AIAssistanceView.as_view(), name='ai-assistance'),
    path('v1/exercise-evaluation/', views.ExerciseEvaluationView.as_view(), name='exercise-evaluation'),
    
    # Docker-based code execution endpoints
    path('v1/execute/', views.execute_code, name='execute-code'),
    path('v1/exercises/<int:exercise_id>/submit/', views.submit_exercise_code, name='submit-exercise-code'),
    path('v1/docker/status/', views.docker_status, name='docker-status'),
    
    # Forum API endpoints
    path('v1/forums/', views.forum_list, name='forum-list'),
    path('v1/forums/<slug:forum_slug>/<int:forum_id>/', views.forum_detail, name='forum-detail'),
    path('v1/forums/<slug:forum_slug>/<int:forum_id>/topics/<slug:topic_slug>/<int:topic_id>/', views.forum_topic_detail, name='forum-topic-detail'),
    
    # Forum Topic CRUD endpoints
    path('v1/topics/create/', views.topic_create, name='topic-create'),
    path('v1/topics/<int:topic_id>/edit/', views.topic_edit, name='topic-edit'),
    path('v1/topics/<int:topic_id>/delete/', views.topic_delete, name='topic-delete'),
    
    # Forum Post CRUD endpoints
    path('v1/posts/create/', views.post_create, name='post-create'),
    path('v1/topics/<int:topic_id>/reply/', views.post_reply, name='post-reply'),
    path('v1/posts/<int:post_id>/edit/', views.post_edit, name='post-edit'),
    path('v1/posts/<int:post_id>/delete/', views.post_delete, name='post-delete'),
    path('v1/posts/<int:post_id>/quote/', views.post_quote, name='post-quote'),
    
    # Dashboard Forum Stats
    path('v1/dashboard/forum-stats/', views.dashboard_forum_stats, name='dashboard-forum-stats'),
    
    # Blog/Wagtail API endpoints
    path('v1/blog/', views.blog_index, name='blog-index'),
    path('v1/blog/categories/', views.blog_categories, name='blog-categories'),
    path('v1/blog/<slug:post_slug>/', views.blog_post_detail, name='blog-post-detail'),
    path('v1/wagtail/homepage/', views.wagtail_homepage, name='wagtail-homepage'),
    path('v1/wagtail/playground/', views.wagtail_playground, name='wagtail-playground'),
    
    # Wagtail Learning Content API endpoints
    path('v1/learning/', views.learning_index, name='learning-index'),
    path('v1/learning/courses/', views.courses_list, name='courses-list'),
    path('v1/learning/courses/<slug:course_slug>/', views.course_detail, name='course-detail'),
    path('v1/learning/courses/<slug:course_slug>/lessons/<slug:lesson_slug>/', views.lesson_detail, name='lesson-detail'),
    path('v1/learning/courses/<slug:course_slug>/lessons/<slug:lesson_slug>/exercises/<slug:exercise_slug>/', views.exercise_detail, name='exercise-detail'),
    
    # API Documentation (to be implemented)
    # path('docs/', include_docs_urls(title='Python Learning Studio API')),
]