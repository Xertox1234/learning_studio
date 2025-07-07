"""
URL configuration for Discourse SSO integration.
"""

from django.urls import path
from . import views

app_name = 'discourse_sso'

urlpatterns = [
    # Main SSO endpoint that Discourse will call
    path('sso/', views.DiscourseSSOView.as_view(), name='sso'),
    
    # Return endpoint for after login
    path('sso/return/', views.discourse_sso_return, name='sso_return'),
    
    # API endpoint for SSO status
    path('api/status/', views.discourse_sso_status, name='status'),
    
    # Admin endpoint for manual user sync
    path('api/sync/', views.DiscourseUserSyncView.as_view(), name='user_sync'),
]