"""
Template tags for forum statistics and utilities
Note: This is separate from machina's forum_tags to avoid conflicts
"""
from django import template
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from django.db.models import Count, Max, Prefetch
from datetime import timedelta
from machina.apps.forum_conversation.models import Topic, Post
from machina.apps.forum.models import Forum
from ..statistics_service import forum_stats_service

register = template.Library()
User = get_user_model()


@register.simple_tag
def get_forum_stats():
    """
    Get comprehensive forum statistics for display in sidebar
    """
    try:
        # Get statistics using the centralized service
        overall_stats = forum_stats_service.get_forum_statistics()
        recent_online_users = forum_stats_service.get_online_users_list(5)
        
        return {
            'total_topics': overall_stats['total_topics'],
            'total_posts': overall_stats['total_posts'],
            'total_users': overall_stats['total_users'],
            'online_users': overall_stats['online_users'],
            'recent_online_users': recent_online_users,
            'latest_member': overall_stats['latest_member'],
        }
    except Exception as e:
        # Return default values if there's an error
        return {
            'total_topics': 0,
            'total_posts': 0,
            'total_users': 0,
            'online_users': 0,
            'recent_online_users': [],
            'latest_member': None,
        }


@register.simple_tag
def get_forum_breadcrumbs(forum):
    """
    Get breadcrumb trail for a forum
    """
    try:
        breadcrumbs = []
        for ancestor in forum.get_ancestors(include_self=True):
            breadcrumbs.append({
                'name': ancestor.name,
                'url': ancestor.get_absolute_url() if hasattr(ancestor, 'get_absolute_url') else '#',
                'is_current': ancestor.pk == forum.pk
            })
        return breadcrumbs
    except:
        return []


@register.filter
def topic_is_unread(topic, user):
    """
    Check if a topic is unread for the given user
    """
    if not user.is_authenticated:
        return False
    
    try:
        # Simple logic: if user hasn't read the topic or 
        # if topic was updated after user's last visit
        # This would normally use django-machina's read tracking
        return True  # Placeholder - implement proper read tracking
    except:
        return False


@register.filter
def format_post_count(count):
    """
    Format post count for display (e.g., 1.2k for 1200)
    """
    try:
        count = int(count)
        if count >= 1000000:
            return f"{count/1000000:.1f}M"
        elif count >= 1000:
            return f"{count/1000:.1f}K"
        else:
            return str(count)
    except:
        return "0"


@register.inclusion_tag('forum_integration/forum_stats_widget.html')
def forum_stats_widget():
    """
    Render a forum stats widget
    """
    stats = get_forum_stats()
    return {'stats': stats}


@register.simple_tag
def get_subforum_stats(forum):
    """
    Get statistics for a specific forum's subforums (optimized with aggregation)
    """
    try:
        # Get subforums with aggregated data in a single query
        subforums = forum.get_children().filter(type=Forum.FORUM_POST).annotate(
            topics_count=Count('topics', filter=models.Q(topics__approved=True)),
            posts_count=Count('topics__posts', filter=models.Q(topics__posts__approved=True)),
            last_post_created=Max('topics__posts__created', filter=models.Q(topics__posts__approved=True))
        ).prefetch_related(
            # Prefetch the last post for each forum
            Prefetch(
                'topics__posts',
                queryset=Post.objects.filter(approved=True).order_by('-created'),
                to_attr='latest_posts'
            )
        )
        
        stats = []
        for subforum in subforums:
            # Get the actual last post object
            last_post = None
            if hasattr(subforum, 'latest_posts') and subforum.latest_posts:
                last_post = subforum.latest_posts[0]
            
            stats.append({
                'forum': subforum,
                'topics_count': subforum.topics_count or 0,
                'posts_count': subforum.posts_count or 0,
                'last_post': last_post,
            })
        
        return stats
    except Exception as e:
        # Log the error in development
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_subforum_stats: {e}")
        return []


@register.filter
def multiply(value, arg):
    """
    Multiply two values - useful for template calculations
    """
    try:
        return float(value) * float(arg)
    except:
        return 0


@register.filter
def get_forum_posts_count(forum):
    """
    Get the total number of posts in a forum (including all topics)
    Note: Consider using forum.posts_count if available from tracker
    """
    try:
        # Check if forum has cached posts_count first (from tracker)
        if hasattr(forum, 'posts_count') and forum.posts_count is not None:
            return forum.posts_count
        
        # Fallback to database query
        return Post.objects.filter(topic__forum=forum, approved=True).count()
    except:
        return 0


@register.filter
def get_forum_last_post(forum):
    """
    Get the last post in a forum
    Note: Consider using forum.last_post if available from tracker
    """
    try:
        # Check if forum has cached last_post first (from tracker)
        if hasattr(forum, 'last_post') and forum.last_post is not None:
            return forum.last_post
        
        # Fallback to database query
        return Post.objects.filter(
            topic__forum=forum, 
            approved=True
        ).select_related('poster', 'topic').order_by('-created').first()
    except:
        return None