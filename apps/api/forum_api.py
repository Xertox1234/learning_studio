"""
Forum API endpoints extracted from views.py with pagination added.
"""

import logging
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


# Forum API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forum_list(request):
    """Get forum data for React frontend."""
    try:
        from machina.apps.forum.models import Forum
        from machina.apps.forum_conversation.models import Topic
        from django.contrib.auth import get_user_model
        from apps.forum_integration.statistics_service import forum_stats_service

        User = get_user_model()

        # Get forum categories and their children
        forum_categories = Forum.objects.filter(type=Forum.FORUM_CAT)

        forums_data = []
        for category in forum_categories:
            category_data = {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': str(category.description) if category.description else '',
                'type': 'category',
                'forums': []
            }

            # Get child forums
            for forum in category.get_children():
                if forum.type == Forum.FORUM_POST:
                    # Get latest topic for this forum
                    latest_topic = Topic.objects.filter(
                        forum=forum, approved=True
                    ).select_related('poster', 'last_post', 'last_post__poster').order_by('-last_post_on').first()

                    last_post_data = None
                    if latest_topic and latest_topic.last_post:
                        last_post_data = {
                            'id': latest_topic.last_post.id,
                            'title': latest_topic.subject,
                            'author': {
                                'username': latest_topic.last_post.poster.username,
                                'avatar': None,
                                'trust_level': 1
                            },
                            'created_at': latest_topic.last_post_on.isoformat() if latest_topic.last_post_on else None
                        }

                    # Get real statistics for this forum
                    forum_stats = forum_stats_service.get_forum_specific_stats(forum.id)

                    forum_data = {
                        'id': forum.id,
                        'name': forum.name,
                        'slug': forum.slug,
                        'description': str(forum.description) if forum.description else '',
                        'icon': '💬',
                        'topics_count': forum.direct_topics_count,
                        'posts_count': forum.direct_posts_count,
                        'last_post': last_post_data,
                        'stats': {
                            'online_users': forum_stats['online_users'],
                            'weekly_posts': forum_stats['weekly_posts'],
                            'trending': forum_stats['trending']
                        },
                        'color': 'bg-blue-500'
                    }
                    category_data['forums'].append(forum_data)

            if category_data['forums']:  # Only include categories that have forums
                forums_data.append(category_data)

        # Get overall stats using the statistics service
        overall_stats = forum_stats_service.get_forum_statistics()

        return Response({
            'categories': forums_data,
            'stats': {
                'total_topics': overall_stats['total_topics'],
                'total_posts': overall_stats['total_posts'],
                'total_users': overall_stats['total_users'],
                'online_users': overall_stats['online_users']
            }
        })

    except Exception as e:
        return Response({
            'error': f'Failed to fetch forum data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forum_topic_detail(request, forum_slug, forum_id, topic_slug, topic_id):
    """Get topic detail with posts for React frontend (paginated)."""
    try:
        from machina.apps.forum_conversation.models import Topic, Post

        # Get the topic
        topic = Topic.objects.select_related('poster', 'forum').get(
            id=topic_id,
            forum_id=forum_id,
            approved=True
        )

        # Base queryset for posts
        posts_qs = Post.objects.select_related('poster').filter(
            topic=topic,
            approved=True
        ).order_by('created')

        # Pagination params
        try:
            page = int(request.GET.get('page', 1) or 1)
        except ValueError:
            page = 1
        try:
            page_size = int(request.GET.get('page_size', 20) or 20)
        except ValueError:
            page_size = 20
        page = max(page, 1)
        page_size = max(1, min(page_size, 100))

        total_count = posts_qs.count()
        start = (page - 1) * page_size
        if total_count and start >= total_count:
            page = (total_count - 1) // page_size + 1
            start = (page - 1) * page_size
        end = start + page_size
        posts = posts_qs[start:end]

        # Serialize posts
        posts_data = []
        for idx, post in enumerate(posts):
            posts_data.append({
                'id': post.id,
                'content': str(post.content),
                'created': post.created.isoformat(),
                'updated': post.updated.isoformat() if post.updated else None,
                'poster': {
                    'id': post.poster.id,
                    'username': post.poster.username,
                    'first_name': post.poster.first_name,
                    'last_name': post.poster.last_name,
                    'avatar': None,
                },
                'position': start + idx + 1,
            })

        total_pages = (total_count + page_size - 1) // page_size if page_size else 1
        posts_pagination = {
            'current_page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1,
        }

        # Format topic data
        topic_data = {
            'id': topic.id,
            'subject': topic.subject,
            'slug': topic.slug,
            'created': topic.created.isoformat(),
            'updated': topic.updated.isoformat(),
            'posts_count': topic.posts_count,
            'views_count': topic.views_count,
            'poster': {
                'id': topic.poster.id,
                'username': topic.poster.username,
                'first_name': topic.poster.first_name,
                'last_name': topic.poster.last_name,
                'avatar': None,
            },
            'forum': {
                'id': topic.forum.id,
                'name': topic.forum.name,
                'slug': topic.forum.slug,
                'description': str(topic.forum.description) if topic.forum.description else '',
            },
            'posts': posts_data,
            'posts_pagination': posts_pagination,
        }

        return Response(topic_data)

    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'Failed to fetch topic: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forum_detail(request, forum_slug, forum_id):
    """Get forum detail with topics list for React frontend (paginated)."""
    try:
        from machina.apps.forum.models import Forum
        from machina.apps.forum_conversation.models import Topic

        # Get the forum
        forum = Forum.objects.get(id=forum_id, slug=forum_slug)

        # Base queryset for topics in this forum
        topics_qs = Topic.objects.select_related('poster', 'last_post', 'last_post__poster').filter(
            forum=forum,
            approved=True
        ).order_by('-last_post_on')

        # Pagination params
        try:
            page = int(request.GET.get('page', 1) or 1)
        except ValueError:
            page = 1
        try:
            page_size = int(request.GET.get('page_size', 20) or 20)
        except ValueError:
            page_size = 20
        page = max(page, 1)
        page_size = max(1, min(page_size, 100))

        total_count = topics_qs.count()
        start = (page - 1) * page_size
        if total_count and start >= total_count:
            page = (total_count - 1) // page_size + 1
            start = (page - 1) * page_size
        end = start + page_size
        topics = topics_qs[start:end]

        # Format topics data
        topics_data = []
        for topic in topics:
            last_post_data = None
            if topic.last_post:
                last_post_data = {
                    'id': topic.last_post.id,
                    'created': topic.last_post.created.isoformat(),
                    'poster': {
                        'username': topic.last_post.poster.username,
                        'display_name': topic.last_post.poster.get_display_name() if hasattr(topic.last_post.poster, 'get_display_name') else topic.last_post.poster.username
                    }
                }

            topics_data.append({
                'id': topic.id,
                'subject': topic.subject,
                'slug': topic.slug,
                'created': topic.created.isoformat(),
                'posts_count': topic.posts_count,
                'views_count': topic.views_count,
                'last_post_on': topic.last_post_on.isoformat() if topic.last_post_on else None,
                'poster': {
                    'id': topic.poster.id,
                    'username': topic.poster.username,
                    'display_name': topic.poster.get_display_name() if hasattr(topic.poster, 'get_display_name') else topic.poster.username
                },
                'last_post': last_post_data
            })

        total_pages = (total_count + page_size - 1) // page_size if page_size else 1
        topics_pagination = {
            'current_page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1,
        }

        # Format forum data
        forum_data = {
            'id': forum.id,
            'name': forum.name,
            'slug': forum.slug,
            'description': str(forum.description) if forum.description else '',
            'topics_count': forum.direct_topics_count,
            'posts_count': forum.direct_posts_count,
            'topics': topics_data,
            'topics_pagination': topics_pagination,
        }

        return Response(forum_data)

    except Forum.DoesNotExist:
        return Response({'error': 'Forum not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'Failed to fetch forum: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Forum Topic CRUD API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def topic_create(request):
    """Create a new forum topic."""
    try:
        from machina.apps.forum.models import Forum
        from machina.apps.forum_conversation.models import Topic, Post

        logger.info(f"Topic creation request from user {request.user.id}: {request.data}")

        # Get forum
        forum_id = request.data.get('forum_id')
        if not forum_id:
            return Response({'error': 'Forum ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            forum = Forum.objects.get(id=forum_id)
            logger.info(f"Found forum: {forum.name} (ID: {forum.id}, Type: {forum.type})")
        except Forum.DoesNotExist:
            return Response({'error': 'Forum not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if forum allows posting
        if forum.type != Forum.FORUM_POST:
            return Response({'error': 'Cannot create topics in this forum type'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate required fields
        subject = request.data.get('subject', '').strip()
        content = request.data.get('content', '').strip()

        if not subject:
            return Response({'error': 'Subject is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not content:
            return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Create topic
        topic = Topic.objects.create(
            forum=forum,
            subject=subject,
            poster=request.user,
            type=request.data.get('topic_type', Topic.TOPIC_POST),
            status=Topic.TOPIC_UNLOCKED,
            approved=True,
            created=timezone.now(),
            updated=timezone.now()
        )

        # Create the first post
        post = Post.objects.create(
            topic=topic,
            poster=request.user,
            subject=subject,
            content=content,
            approved=True,
            enable_signature=request.data.get('enable_signature', False),
            created=timezone.now(),
            updated=timezone.now()
        )

        # Update topic references
        topic.first_post = post
        topic.last_post = post
        topic.last_post_on = post.created
        topic.posts_count = 1
        topic.save()

        # Update forum statistics
        forum.refresh_from_db()

        # Return successful response
        topic_data = {
            'id': topic.id,
            'subject': topic.subject,
            'slug': topic.slug,
            'created': topic.created.isoformat(),
            'posts_count': topic.posts_count,
            'views_count': getattr(topic, 'views_count', 0),
            'forum': {
                'id': forum.id,
                'name': forum.name,
                'slug': forum.slug,
            },
            'poster': {
                'id': request.user.id,
                'username': request.user.username,
                'display_name': request.user.get_display_name() if hasattr(request.user, 'get_display_name') else request.user.username
            }
        }

        return Response({'success': True, 'topic': topic_data, 'message': 'Topic created successfully'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Failed to create topic: {str(e)}")
        return Response({'error': f'Failed to create topic: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def topic_edit(request, topic_id):
    """Edit an existing forum topic."""
    try:
        from machina.apps.forum_conversation.models import Topic
        from machina.apps.forum_conversation.forms import TopicForm

        # Get the topic
        try:
            topic = Topic.objects.select_related('forum', 'first_post').get(
                id=topic_id,
                approved=True
            )
        except Topic.DoesNotExist:
            return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check permissions - user must be topic creator or have moderation permissions
        if topic.poster != request.user:
            return Response({'error': 'You do not have permission to edit this topic'}, status=status.HTTP_403_FORBIDDEN)

        # Get the first post (topic post)
        first_post = topic.first_post
        if not first_post:
            return Response({'error': 'Topic post not found'}, status=status.HTTP_404_NOT_FOUND)

        # Update fields
        subject = request.data.get('subject', '').strip()
        content = request.data.get('content', '').strip()

        if not subject:
            return Response({'error': 'Subject is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not content:
            return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare form data
        form_data = {
            'subject': subject,
            'content': content,
            'topic_type': request.data.get('topic_type', topic.type),
            'enable_signature': request.data.get('enable_signature', first_post.enable_signature),
            'update_reason': request.data.get('update_reason', ''),
        }

        # Use TopicForm for validation and update
        form = TopicForm(
            data=form_data,
            instance=first_post,
            user=request.user,
            forum=topic.forum,
            topic=topic
        )

        if form.is_valid():
            post = form.save()
            updated_topic = post.topic

            topic_data = {
                'id': updated_topic.id,
                'subject': updated_topic.subject,
                'slug': updated_topic.slug,
                'updated': updated_topic.updated.isoformat(),
                'posts_count': updated_topic.posts_count,
                'views_count': updated_topic.views_count,
                'forum': {
                    'id': updated_topic.forum.id,
                    'name': updated_topic.forum.name,
                    'slug': updated_topic.forum.slug,
                },
                'poster': {
                    'id': updated_topic.poster.id,
                    'username': updated_topic.poster.username,
                    'display_name': updated_topic.poster.get_display_name() if hasattr(updated_topic.poster, 'get_display_name') else updated_topic.poster.username
                }
            }

            return Response({'success': True, 'topic': topic_data, 'message': 'Topic updated successfully'})
        else:
            return Response({'error': 'Validation failed', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': f'Failed to update topic: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def topic_delete(request, topic_id):
    """Delete a forum topic."""
    try:
        from machina.apps.forum_conversation.models import Topic

        # Get the topic
        try:
            topic = Topic.objects.select_related('forum', 'first_post').get(
                id=topic_id,
                approved=True
            )
        except Topic.DoesNotExist:
            return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check permissions
        if topic.poster != request.user:
            return Response({'error': 'You do not have permission to delete this topic'}, status=status.HTTP_403_FORBIDDEN)

        forum_data = {
            'id': topic.forum.id,
            'name': topic.forum.name,
            'slug': topic.forum.slug,
        }

        topic_subject = topic.subject
        topic.delete()

        return Response({'success': True, 'message': f'Topic "{topic_subject}" deleted successfully', 'forum': forum_data})

    except Exception as e:
        return Response({'error': f'Failed to delete topic: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Forum Post CRUD API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate=settings.RATE_LIMIT_SETTINGS['FORUM_POSTS'], method='POST', block=True)
@csrf_exempt
def post_create(request):
    """Create a new forum post (reply to a topic)."""
    try:
        from machina.apps.forum_conversation.models import Topic, Post

        # Get topic ID from request data
        topic_id = request.data.get('topic_id')
        if not topic_id:
            return Response({'error': 'Topic ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get content
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get the topic
        try:
            topic = Topic.objects.get(id=topic_id)
        except Topic.DoesNotExist:
            return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

        # Create the post
        post = Post.objects.create(
            topic=topic,
            poster=request.user,
            subject=f'Re: {topic.subject}',
            content=content,
            approved=True,
            enable_signature=request.data.get('enable_signature', True),
            created=timezone.now(),
            updated=timezone.now()
        )

        # Update topic statistics
        topic.posts_count = topic.posts.filter(approved=True).count()
        topic.last_post = post
        topic.last_post_on = post.created
        topic.save()

        # Update forum statistics
        forum = topic.forum
        forum.posts_count = forum.posts_count  # ensure field exists; or recalc if needed
        forum.last_post = post
        forum.save()

        # Calculate position safely
        post_position = topic.posts.filter(approved=True).count()

        return Response({
            'success': True,
            'message': 'Post created successfully',
            'post': {
                'id': post.id,
                'content': str(post.content),
                'created': post.created.isoformat() if post.created else timezone.now().isoformat(),
                'updated': post.updated.isoformat() if post.updated else None,
                'poster': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                },
                'position': post_position,
                'topic': {
                    'id': topic.id,
                    'subject': topic.subject,
                    'slug': topic.slug,
                }
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating post: {str(e)}")
        return Response({'error': f'Failed to create post: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_reply(request, topic_id):
    """Create a reply post to a topic."""
    try:
        from machina.apps.forum_conversation.models import Topic
        from machina.apps.forum_conversation.forms import PostForm

        # Get the topic
        try:
            topic = Topic.objects.select_related('forum').get(
                id=topic_id,
                approved=True
            )
        except Topic.DoesNotExist:
            return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if topic is locked
        if topic.status == Topic.TOPIC_LOCKED:
            return Response({'error': 'Topic is locked'}, status=status.HTTP_403_FORBIDDEN)

        # Validate required fields
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare form data
        form_data = {
            'subject': f"Re: {topic.subject}",
            'content': content,
            'enable_signature': request.data.get('enable_signature', False),
        }

        # Use PostForm for validation and creation
        form = PostForm(
            data=form_data,
            user=request.user,
            forum=topic.forum,
            topic=topic
        )

        if form.is_valid():
            post = form.save()

            post_data = {
                'id': post.id,
                'content': str(post.content),
                'created': post.created.isoformat(),
                'poster': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'display_name': request.user.get_display_name() if hasattr(request.user, 'get_display_name') else request.user.username
                },
                'topic': {
                    'id': topic.id,
                    'subject': topic.subject,
                    'slug': topic.slug,
                },
                'position': topic.posts.count()
            }

            return Response({'success': True, 'post': post_data, 'message': 'Reply posted successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Validation failed', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': f'Failed to create reply: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def post_edit(request, post_id):
    """Edit an existing forum post."""
    try:
        from machina.apps.forum_conversation.models import Post
        from machina.apps.forum_conversation.forms import PostForm

        # Get the post
        try:
            post = Post.objects.select_related('topic', 'topic__forum', 'poster').get(
                id=post_id,
                approved=True
            )
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check permissions
        if post.poster != request.user:
            return Response({'error': 'You do not have permission to edit this post'}, status=status.HTTP_403_FORBIDDEN)

        # Validate required fields
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare form data
        form_data = {
            'subject': request.data.get('subject', post.subject),
            'content': content,
            'enable_signature': request.data.get('enable_signature', post.enable_signature),
            'update_reason': request.data.get('update_reason', ''),
        }

        # Use PostForm for validation and update
        form = PostForm(
            data=form_data,
            instance=post,
            user=request.user,
            forum=post.topic.forum,
            topic=post.topic
        )

        if form.is_valid():
            updated_post = form.save()

            post_data = {
                'id': updated_post.id,
                'subject': updated_post.subject,
                'content': str(updated_post.content),
                'updated': updated_post.updated.isoformat(),
                'updates_count': updated_post.updates_count,
                'poster': {
                    'id': updated_post.poster.id,
                    'username': updated_post.poster.username,
                    'display_name': updated_post.poster.get_display_name() if hasattr(updated_post.poster, 'get_display_name') else updated_post.poster.username
                },
                'updated_by': {
                    'id': updated_post.updated_by.id,
                    'username': updated_post.updated_by.username,
                } if updated_post.updated_by else None
            }

            return Response({'success': True, 'post': post_data, 'message': 'Post updated successfully'})
        else:
            return Response({'error': 'Validation failed', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': f'Failed to update post: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def post_delete(request, post_id):
    """Delete a forum post."""
    try:
        from machina.apps.forum_conversation.models import Post

        # Get the post
        try:
            post = Post.objects.select_related('topic', 'topic__forum', 'poster').get(
                id=post_id,
                approved=True
            )
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check permissions
        if post.poster != request.user:
            return Response({'error': 'You do not have permission to delete this post'}, status=status.HTTP_403_FORBIDDEN)

        # Check if first post of a topic
        if post.is_topic_head:
            return Response({'error': 'Cannot delete the first post of a topic. Delete the topic instead.'}, status=status.HTTP_400_BAD_REQUEST)

        topic_data = {
            'id': post.topic.id,
            'subject': post.topic.subject,
            'slug': post.topic.slug,
        }

        post_id_deleted = post.id
        post.delete()

        return Response({'success': True, 'message': f'Post #{post_id_deleted} deleted successfully', 'topic': topic_data})

    except Exception as e:
        return Response({'error': f'Failed to delete post: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_quote(request, post_id):
    """Get a post for quoting."""
    try:
        from machina.apps.forum_conversation.models import Post

        # Get the post
        try:
            post = Post.objects.select_related('topic', 'poster').get(
                id=post_id,
                approved=True
            )
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        quoted_content = f"""[quote=\"{post.poster.username}\"]
{str(post.content)}
[/quote]

"""

        return Response({
            'success': True,
            'quoted_content': quoted_content,
            'original_post': {
                'id': post.id,
                'poster': {
                    'username': post.poster.username,
                    'display_name': post.poster.get_display_name() if hasattr(post.poster, 'get_display_name') else post.poster.username
                },
                'created': post.created.isoformat(),
                'content': str(post.content)[:200] + '...' if len(str(post.content)) > 200 else str(post.content)
            },
            'topic': {
                'id': post.topic.id,
                'subject': post.topic.subject,
                'slug': post.topic.slug,
            }
        })

    except Exception as e:
        return Response({'error': f'Failed to quote post: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Dashboard Forum Stats API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_forum_stats(request):
    """Get forum statistics for the user dashboard."""
    try:
        from machina.apps.forum.models import Forum
        from machina.apps.forum_conversation.models import Topic, Post
        from django.contrib.auth import get_user_model
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta
        from apps.forum_integration.statistics_service import forum_stats_service

        User = get_user_model()

        # Get user's recent activity
        user_recent_posts = Post.objects.filter(
            poster=request.user,
            approved=True
        ).select_related('topic', 'topic__forum').order_by('-created')[:5]

        user_recent_topics = Topic.objects.filter(
            poster=request.user,
            approved=True
        ).select_related('forum').order_by('-created')[:5]

        recent_posts_data = []
        for post in user_recent_posts:
            recent_posts_data.append({
                'id': post.id,
                'content': str(post.content)[:150] + '...' if len(str(post.content)) > 150 else str(post.content),
                'created': post.created.isoformat(),
                'topic': {
                    'id': post.topic.id,
                    'subject': post.topic.subject,
                    'slug': post.topic.slug,
                },
                'forum': {
                    'id': post.topic.forum.id,
                    'name': post.topic.forum.name,
                    'slug': post.topic.forum.slug,
                }
            })

        recent_topics_data = []
        for topic in user_recent_topics:
            recent_topics_data.append({
                'id': topic.id,
                'subject': topic.subject,
                'slug': topic.slug,
                'created': topic.created.isoformat(),
                'posts_count': topic.posts_count,
                'views_count': topic.views_count,
                'forum': {
                    'id': topic.forum.id,
                    'name': topic.forum.name,
                    'slug': topic.forum.slug,
                }
            })

        overall_stats = forum_stats_service.get_forum_statistics()
        total_forums = Forum.objects.filter(type=Forum.FORUM_POST).count()

        week_ago = timezone.now() - timedelta(days=7)
        recent_topics_count = Topic.objects.filter(created__gte=week_ago, approved=True).count()
        recent_posts_count = Post.objects.filter(created__gte=week_ago, approved=True).count()

        user_topics_count = Topic.objects.filter(poster=request.user, approved=True).count()
        user_posts_count = Post.objects.filter(poster=request.user, approved=True).count()

        active_forums = Forum.objects.filter(type=Forum.FORUM_POST).annotate(
            recent_posts=Count(
                'topics__posts',
                filter=Q(
                    topics__posts__created__gte=week_ago,
                    topics__posts__approved=True
                )
            )
        ).order_by('-recent_posts')[:5]

        active_forums_data = []
        for forum in active_forums:
            latest_topic = Topic.objects.filter(
                forum=forum,
                approved=True
            ).select_related('poster').order_by('-last_post_on').first()

            latest_topic_data = None
            if latest_topic:
                latest_topic_data = {
                    'id': latest_topic.id,
                    'subject': latest_topic.subject,
                    'slug': latest_topic.slug,
                    'last_post_on': latest_topic.last_post_on.isoformat() if latest_topic.last_post_on else None,
                    'poster': {
                        'username': latest_topic.poster.username,
                    }
                }

            active_forums_data.append({
                'id': forum.id,
                'name': forum.name,
                'slug': forum.slug,
                'description': str(forum.description) if forum.description else '',
                'topics_count': forum.direct_topics_count,
                'posts_count': forum.direct_posts_count,
                'recent_posts': forum.recent_posts,
                'latest_topic': latest_topic_data
            })

        return Response({
            'user_stats': {
                'topics_created': user_topics_count,
                'posts_made': user_posts_count,
                'recent_posts': recent_posts_data,
                'recent_topics': recent_topics_data
            },
            'forum_stats': {
                'total_topics': overall_stats['total_topics'],
                'total_posts': overall_stats['total_posts'],
                'total_users': overall_stats['total_users'],
                'online_users': overall_stats['online_users'],
                'total_forums': total_forums,
                'recent_topics': recent_topics_count,
                'recent_posts': recent_posts_count
            },
            'active_forums': active_forums_data
        })

    except Exception as e:
        return Response({'error': f'Failed to fetch dashboard stats: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
