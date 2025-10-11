"""
Custom forum URL configuration that overrides specific Machina views
"""
from django.urls import path, include, re_path
from .views import CustomForumIndexView, RichTopicCreateView, RichPostCreateView

# Custom forum URLs - override specific views, include the rest from machina
urlpatterns = [
    # Override the forum index with our custom view
    path('', CustomForumIndexView.as_view(), name='forum_index'),
    
    # Override topic creation with rich content editor
    re_path(
        r'^forum/(?P<slug>[\w-]+)-(?P<pk>\d+)/topics/create/$',
        RichTopicCreateView.as_view(),
        name='topic_create'
    ),
    
    # Override post/reply creation with rich content editor
    re_path(
        r'^forum/(?P<slug>[\w-]+)-(?P<pk>\d+)/topics/(?P<topic_slug>[\w-]+)-(?P<topic_pk>\d+)/posts/create/$',
        RichPostCreateView.as_view(),
        name='post_create'
    ),
    
    # Include all other machina URLs (this must come last)
    path('', include('machina.urls')),
]