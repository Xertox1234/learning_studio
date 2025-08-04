from django.urls import path, re_path
from . import views

urlpatterns = [
    # API status endpoint
    path('api/status/', views.api_status_view, name='api_status'),
    
    # React authentication pages
    path('login/', views.react_login_view, name='login'),
    path('register/', views.react_register_view, name='register'),
    
    # React app catch-all (must be last)
    re_path(r'^(?P<path>.*)$', views.react_app_view, name='react_app'),
]