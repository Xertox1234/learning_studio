"""
Custom forum URL configuration that overrides specific Machina views
"""
from django.urls import path, include
from .views import CustomForumIndexView

# Custom forum URLs - override the index view, include the rest from machina
urlpatterns = [
    # Override the forum index with our custom view
    path('', CustomForumIndexView.as_view(), name='forum_index'),
    
    # Include all other machina URLs
    path('', include('machina.urls')),
]