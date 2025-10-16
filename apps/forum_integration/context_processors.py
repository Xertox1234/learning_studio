"""
Context processors for forum integration
"""
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post
from apps.api.services.container import container

User = get_user_model()


def forum_stats(request):
    """
    Add forum statistics to template context
    """
    try:
        # Get root forums (top-level categories) - exclude the root itself
        root_categories = Forum.objects.filter(
            parent__isnull=False,  # Not the absolute root
            parent__parent__isnull=True,  # Parent is the root
            type=Forum.FORUM_CAT
        ).order_by('lft')
        
        # Build hierarchical structure
        forum_tree = []
        for category in root_categories:
            subforums = category.get_children().filter(type=Forum.FORUM_POST)
            if subforums.exists():
                forum_tree.append({
                    'category': category,
                    'forums': subforums
                })
        
        # Get statistics using the DI container service
        stats_service = container.get_statistics_service()
        overall_stats = stats_service.get_forum_statistics()
        
        return {
            'forum_tree': forum_tree,
            'forum_total_topics': overall_stats['total_topics'],
            'forum_total_posts': overall_stats['total_posts'],
            'forum_total_users': overall_stats['total_users'],
            'forum_online_users': overall_stats['online_users'],
            'forum_latest_member': overall_stats['latest_member'],
        }
    except Exception as e:
        # Return empty context on error
        return {
            'forum_tree': [],
            'forum_total_topics': 0,
            'forum_total_posts': 0,
            'forum_total_users': 0,
            'forum_online_users': 0,
            'forum_latest_member': None,
        }