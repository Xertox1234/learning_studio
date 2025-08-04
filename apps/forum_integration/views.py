"""
Custom forum views to override Machina's defaults
"""
from django.shortcuts import render
from machina.apps.forum.views import IndexView as BaseIndexView
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .statistics_service import forum_stats_service

User = get_user_model()


class CustomForumIndexView(BaseIndexView):
    """
    Custom forum index view that provides proper forum hierarchy
    and accurate statistics
    """
    template_name = 'machina/forum/index.html'
    
    def get(self, request, *args, **kwargs):
        # Call the parent's get method to set up object_list
        response = super().get(request, *args, **kwargs)
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the proper forum hierarchy
        root_forums = Forum.objects.filter(
            parent__isnull=False,  # Not the absolute root
            parent__parent__isnull=True,  # Parent is the root 
            type=Forum.FORUM_CAT
        ).order_by('lft')
        
        # Build the category structure with subforums
        forum_categories = []
        for category in root_forums:
            subforums = category.get_children().filter(type=Forum.FORUM_POST)
            if subforums.exists():
                forum_categories.append({
                    'category': category,
                    'subforums': list(subforums)
                })
        
        # Get accurate statistics using the centralized service
        overall_stats = forum_stats_service.get_forum_statistics()
        
        # Override Machina's context variables
        context.update({
            'forum_categories': forum_categories,
            'total_topics_count': overall_stats['total_topics'],
            'total_posts_count': overall_stats['total_posts'],
            'total_users_count': overall_stats['total_users'],
            'online_users_count': overall_stats['online_users'],
            # Also provide backup names
            'forum_total_topics': overall_stats['total_topics'],
            'forum_total_posts': overall_stats['total_posts'],
            'forum_total_users': overall_stats['total_users'],
            'forum_online_users': overall_stats['online_users'],
            'forum_latest_member': overall_stats['latest_member'],
        })
        
        return context