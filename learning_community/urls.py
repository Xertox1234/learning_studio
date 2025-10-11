"""
URL configuration for learning_community project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from apps.learning.views import (
    home_view, course_list_view, course_detail_view, 
    lesson_detail_view, exercises_list_view, exercise_detail_view, my_courses_view,
    enroll_course, execute_code_view, submit_exercise, code_playground_view, test_exercise_interface_view
)
from apps.users.views import dashboard_view
from apps.community.views import community_index_view
from apps.frontend.views import react_login_view, react_register_view
from apps.api.mixins import ratelimited

urlpatterns = [
    # Django Admin (moved to different URL)
    path('django-admin/', admin.site.urls),
    
    # API (must be before Wagtail catch-all)
    path('api/', include('apps.api.urls')),
    
    # Authentication
    path('accounts/', include('allauth.urls')),
    
    # React authentication pages
    path('login/', react_login_view, name='react_login'),
    path('register/', react_register_view, name='react_register'),
    
    
    # User dashboard
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Learning views
    path('courses/', course_list_view, name='course_list'),
    path('courses/<slug:slug>/', course_detail_view, name='course_detail'),
    path('courses/<slug:course_slug>/lessons/<slug:lesson_slug>/', lesson_detail_view, name='lesson_detail'),
    path('exercises/', exercises_list_view, name='exercises_list'),
    path('exercises/<int:exercise_id>/', exercise_detail_view, name='exercise_detail'),
    path('exercises/<int:exercise_id>/submit/', submit_exercise, name='submit_exercise'),
    path('my-courses/', my_courses_view, name='my_courses'),
    path('enroll/<int:course_id>/', enroll_course, name='enroll_course'),
    path('execute-code/', execute_code_view, name='execute_code'),
    path('code-playground/', code_playground_view, name='code_playground'),
    path('playground/', lambda request: render(request, 'learning/code_playground_modern.html'), name='playground'),
    path('test-exercise/', test_exercise_interface_view, name='test_exercise_interface'),
    path('test-editor/', lambda request: render(request, 'test-editor.html'), name='test_editor'),
    path('simple-test/', lambda request: render(request, 'simple-test.html'), name='simple_test'),
    
    # Community views
    path('community/', community_index_view, name='community_index'),
    
    # Forum (Django-machina with custom overrides)
    path('forum/', include('apps.forum_integration.forum_urls')),
    
    # Forum integration features
    path('forum-features/', include('apps.forum_integration.urls')),
    
    # PWA support
    path('offline/', lambda request: render(request, 'offline.html'), name='offline'),
    
    # Wagtail CMS (now at /admin/)
    path('admin/', include('wagtail.admin.urls')),
    path('documents/', include('wagtail.documents.urls')),
    path('images/', include('wagtail.images.urls')),
    
    # React frontend for modern UI (specific routes)
    path('frontend/', include('apps.frontend.urls')),
    
    # Wagtail pages (catch-all - must be last)
    path('', include('wagtail.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include('debug_toolbar.urls')),
        ] + urlpatterns
    except ImportError:
        pass

# Custom error handlers
handler429 = ratelimited
