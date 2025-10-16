"""
API views for integrated Wagtail-Forum content creation.
Handles unified content publishing across both systems.
"""

import logging
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_ratelimit.decorators import ratelimit
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.api.services.container import container

logger = logging.getLogger(__name__)
User = get_user_model()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='10/h', method='POST', block=True)  # Rate limit integrated content creation
def create_integrated_content(request):
    """
    Create content that can publish to both Wagtail and forum systems.
    
    Expected payload:
    {
        "title": "Content Title",
        "intro": "Brief introduction",
        "content_type": "blog_post" | "forum_topic",
        "body": [...],  // StreamField blocks for rich content
        "forum_enabled": true,  // Whether to create forum discussion
        "forum_id": 1,  // Target forum ID (optional for blog posts)
        "forum_topic_title": "Custom forum title",
        "forum_discussion_intro": "Custom discussion intro",
        "enable_rich_content": true,
        "trust_level_required": 0,
        "ai_generated": false,
        "ai_summary": "",
        "tags": ["python", "tutorial"],
        "categories": [1, 2]
    }
    """
    try:
        # Validate required fields
        required_fields = ['title', 'content_type']
        for field in required_fields:
            if not request.data.get(field):
                return Response({
                    'error': f'{field} is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        content_type = request.data.get('content_type')
        if content_type not in ['blog_post', 'forum_topic']:
            return Response({
                'error': 'content_type must be "blog_post" or "forum_topic"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check user permissions
        forum_content_service = container.get_forum_content_service()
        permissions_check = forum_content_service.check_user_permissions(
            user=request.user,
            action=f'create_{content_type}',
            forum_id=request.data.get('forum_id')
        )
        
        if not permissions_check['allowed']:
            return Response({
                'error': 'Insufficient permissions for this action',
                'permissions': permissions_check,
                'message': f'Trust level {permissions_check["requirements"].get(f"create_{content_type}", 1)} required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Additional validation for forum topics
        if content_type == 'forum_topic' and not request.data.get('forum_id'):
            return Response({
                'error': 'forum_id is required for forum topics'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create the integrated content
        result = forum_content_service.create_integrated_content(
            user=request.user,
            content_data=request.data
        )
        
        if result.get('success'):
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': result.get('error', 'Failed to create content'),
                'details': result
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Error creating integrated content: {str(e)}")
        return Response({
            'error': f'Failed to create integrated content: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_permissions(request):
    """Get user's permissions for content creation."""
    try:
        forum_content_service = container.get_forum_content_service()

        # Get permissions for all actions
        actions = ['create_blog_post', 'create_forum_topic', 'create_integrated_content', 'use_rich_content']

        all_permissions = {}
        for action in actions:
            permissions_check = forum_content_service.check_user_permissions(
                user=request.user,
                action=action
            )
            all_permissions[action] = permissions_check['allowed']

        # Get detailed trust level info
        trust_level_info = forum_content_service.check_user_permissions(
            user=request.user,
            action='create_blog_post'  # Any action to get trust level
        )
        
        return Response({
            'permissions': all_permissions,
            'trust_level': trust_level_info.get('trust_level', 0),
            'trust_level_name': trust_level_info.get('trust_level_name', 'TL0'),
            'requirements': trust_level_info.get('requirements', {}),
            'detailed_permissions': trust_level_info.get('permissions', {})
        })
    
    except Exception as e:
        logger.error(f"Error getting user permissions: {str(e)}")
        return Response({
            'error': f'Failed to get permissions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def available_forums(request):
    """Get list of forums available for content creation."""
    try:
        from machina.apps.forum.models import Forum
        
        # Get forums that allow posting
        forums = Forum.objects.filter(
            type=Forum.FORUM_POST
        ).select_related('parent').order_by('tree_id', 'lft')
        
        forums_data = []
        for forum in forums:
            # Get category info
            category = None
            if forum.parent and forum.parent.type == Forum.FORUM_CAT:
                category = {
                    'id': forum.parent.id,
                    'name': forum.parent.name,
                    'slug': forum.parent.slug
                }
            
            forums_data.append({
                'id': forum.id,
                'name': forum.name,
                'slug': forum.slug,
                'description': str(forum.description) if forum.description else '',
                'category': category,
                'topics_count': forum.direct_topics_count,
                'posts_count': forum.direct_posts_count,
                'allows_integrated_content': True  # All forums support integrated content
            })
        
        return Response({
            'forums': forums_data,
            'total_count': len(forums_data)
        })
    
    except Exception as e:
        logger.error(f"Error getting available forums: {str(e)}")
        return Response({
            'error': f'Failed to get forums: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def integrated_content_stats(request):
    """Get statistics about integrated content."""
    try:
        forum_content_service = container.get_forum_content_service()
        forum_id = request.GET.get('forum_id')

        # Get forum statistics including integrated content
        stats = forum_content_service.get_forum_statistics(
            forum_id=int(forum_id) if forum_id else None
        )
        
        # Add additional integrated content stats
        from apps.blog.models import ForumIntegratedBlogPage
        
        if forum_id:
            # Stats for specific forum
            integrated_posts = ForumIntegratedBlogPage.objects.live().filter(
                discussion_forum_id=forum_id,
                forum_topic_id__isnull=False
            )
            
            active_discussions = integrated_posts.exclude(
                forum_topic_id__isnull=True
            ).count()
            
            stats.update({
                'forum_integrated_posts': integrated_posts.count(),
                'active_discussions': active_discussions
            })
        else:
            # Overall stats
            all_integrated = ForumIntegratedBlogPage.objects.live()
            total_integrated = all_integrated.count()
            with_discussions = all_integrated.filter(forum_topic_id__isnull=False).count()
            
            stats.update({
                'total_integrated_posts': total_integrated,
                'posts_with_discussions': with_discussions,
                'integration_ratio': with_discussions / total_integrated if total_integrated > 0 else 0
            })
        
        return Response(stats)
    
    except Exception as e:
        logger.error(f"Error getting integrated content stats: {str(e)}")
        return Response({
            'error': f'Failed to get stats: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def recent_integrated_content(request):
    """Get recent integrated content (blog posts with forum discussions)."""
    try:
        from apps.blog.models import ForumIntegratedBlogPage
        
        # Get query parameters
        limit = min(int(request.GET.get('limit', 10)), 50)  # Max 50
        forum_id = request.GET.get('forum_id')
        
        # Build queryset
        integrated_posts = ForumIntegratedBlogPage.objects.live().select_related(
            'author', 'discussion_forum'
        ).filter(
            forum_topic_id__isnull=False  # Only posts with forum discussions
        ).order_by('-first_published_at')
        
        if forum_id:
            integrated_posts = integrated_posts.filter(discussion_forum_id=forum_id)
        
        # Paginate
        integrated_posts = integrated_posts[:limit]
        
        # Serialize
        content_data = []
        for post in integrated_posts:
            forum_topic = post.get_forum_topic()
            
            content_data.append({
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'intro': post.intro,
                'url': post.url,
                'author': {
                    'id': post.author.id if post.author else None,
                    'username': post.author.username if post.author else 'Anonymous',
                    'display_name': post.author.get_full_name() if post.author else 'Anonymous'
                },
                'published_at': post.first_published_at.isoformat() if post.first_published_at else None,
                'reading_time': post.reading_time,
                'ai_generated': post.ai_generated,
                'forum_discussion': {
                    'topic_id': forum_topic.id if forum_topic else None,
                    'title': forum_topic.subject if forum_topic else None,
                    'posts_count': forum_topic.posts_count if forum_topic else 0,
                    'views_count': getattr(forum_topic, 'views_count', 0) if forum_topic else 0,
                    'last_activity': forum_topic.last_post_on.isoformat() if forum_topic and forum_topic.last_post_on else None,
                    'url': post.get_forum_url()
                },
                'discussion_forum': {
                    'id': post.discussion_forum.id if post.discussion_forum else None,
                    'name': post.discussion_forum.name if post.discussion_forum else None,
                    'slug': post.discussion_forum.slug if post.discussion_forum else None
                } if post.discussion_forum else None
            })
        
        return Response({
            'content': content_data,
            'count': len(content_data),
            'limit': limit
        })
    
    except Exception as e:
        logger.error(f"Error getting recent integrated content: {str(e)}")
        return Response({
            'error': f'Failed to get recent content: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='20/h', method='POST', block=True)
def sync_forum_topic(request, blog_post_id):
    """Manually sync an existing blog post with a forum topic."""
    try:
        from apps.blog.models import ForumIntegratedBlogPage
        
        # Get the blog post
        try:
            blog_post = ForumIntegratedBlogPage.objects.get(
                id=blog_post_id,
                live=True
            )
        except ForumIntegratedBlogPage.DoesNotExist:
            return Response({
                'error': 'Blog post not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions - only author or staff can sync
        if blog_post.author != request.user and not request.user.is_staff:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if already has forum topic
        if blog_post.forum_topic_id:
            return Response({
                'error': 'Blog post already has a forum topic',
                'forum_topic_id': blog_post.forum_topic_id,
                'forum_url': blog_post.get_forum_url()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Enable forum topic creation and save
        blog_post.create_forum_topic = True
        blog_post.save()
        
        # Check if forum topic was created
        forum_topic = blog_post.get_forum_topic()
        if forum_topic:
            return Response({
                'success': True,
                'message': 'Forum topic created successfully',
                'forum_topic': {
                    'id': forum_topic.id,
                    'title': forum_topic.subject,
                    'url': blog_post.get_forum_url(),
                    'forum_name': forum_topic.forum.name
                }
            })
        else:
            return Response({
                'error': 'Failed to create forum topic',
                'message': 'Check if a discussion forum is configured for this blog post'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Error syncing forum topic: {str(e)}")
        return Response({
            'error': f'Failed to sync forum topic: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)