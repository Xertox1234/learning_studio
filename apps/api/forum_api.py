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
        from apps.api.services.container import container

        User = get_user_model()
        stats_service = container.get_statistics_service()

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
                    forum_stats = stats_service.get_forum_specific_stats(forum.id)

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
        overall_stats = stats_service.get_forum_statistics()

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
        from apps.api.services.container import container

        User = get_user_model()
        stats_service = container.get_statistics_service()

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

        overall_stats = stats_service.get_forum_statistics()
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


# User Profile & Activity API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_forum_profile(request, user_id):
    """Get a user's forum profile with statistics and recent activity."""
    try:
        from machina.apps.forum_conversation.models import Topic, Post
        from django.contrib.auth import get_user_model
        from apps.forum_integration.models import TrustLevel
        from apps.api.services.container import container

        User = get_user_model()
        stats_service = container.get_statistics_service()

        # Get the user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get user's trust level
        trust_level, _ = TrustLevel.objects.get_or_create(
            user=user,
            defaults={'level': 0}
        )

        # Get user statistics
        topics_created = Topic.objects.filter(poster=user, approved=True).count()
        posts_created = Post.objects.filter(poster=user, approved=True).count()

        # Get recent activity
        recent_topics = Topic.objects.filter(
            poster=user,
            approved=True
        ).select_related('forum').order_by('-created')[:5]

        recent_posts = Post.objects.filter(
            poster=user,
            approved=True
        ).select_related('topic', 'topic__forum').order_by('-created')[:10]

        # Serialize recent topics
        recent_topics_data = []
        for topic in recent_topics:
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
                    'slug': topic.forum.slug
                }
            })

        # Serialize recent posts
        recent_posts_data = []
        for post in recent_posts:
            recent_posts_data.append({
                'id': post.id,
                'content': str(post.content)[:200] + '...' if len(str(post.content)) > 200 else str(post.content),
                'created': post.created.isoformat(),
                'topic': {
                    'id': post.topic.id,
                    'subject': post.topic.subject,
                    'slug': post.topic.slug
                },
                'forum': {
                    'id': post.topic.forum.id,
                    'name': post.topic.forum.name,
                    'slug': post.topic.forum.slug
                }
            })

        # Build profile response
        profile_data = {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name() or user.username,
            'date_joined': user.date_joined.isoformat(),
            'trust_level': {
                'level': trust_level.level,
                'level_name': trust_level.get_level_display(),
                'days_visited': trust_level.days_visited,
                'posts_read': trust_level.posts_read,
                'topics_viewed': trust_level.topics_viewed,
                'posts_created': trust_level.posts_created,
                'topics_created': trust_level.topics_created,
                'likes_given': trust_level.likes_given,
                'likes_received': trust_level.likes_received
            },
            'statistics': {
                'topics_created': topics_created,
                'posts_created': posts_created,
                'total_contributions': topics_created + posts_created
            },
            'recent_topics': recent_topics_data,
            'recent_posts': recent_posts_data
        }

        return Response(profile_data)

    except Exception as e:
        logger.error(f"Error fetching user forum profile: {str(e)}")
        return Response({
            'error': f'Failed to fetch user profile: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_forum_posts(request, user_id):
    """Get all posts by a specific user with pagination."""
    try:
        from machina.apps.forum_conversation.models import Post
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Get the user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get pagination params
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

        # Get user's posts
        posts_qs = Post.objects.filter(
            poster=user,
            approved=True
        ).select_related('topic', 'topic__forum').order_by('-created')

        # Pagination
        total_count = posts_qs.count()
        start = (page - 1) * page_size
        if total_count and start >= total_count:
            page = (total_count - 1) // page_size + 1
            start = (page - 1) * page_size
        end = start + page_size
        posts = posts_qs[start:end]

        # Serialize posts
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post.id,
                'content': str(post.content),
                'created': post.created.isoformat(),
                'updated': post.updated.isoformat() if post.updated else None,
                'topic': {
                    'id': post.topic.id,
                    'subject': post.topic.subject,
                    'slug': post.topic.slug
                },
                'forum': {
                    'id': post.topic.forum.id,
                    'name': post.topic.forum.name,
                    'slug': post.topic.forum.slug
                }
            })

        # Pagination info
        total_pages = (total_count + page_size - 1) // page_size if page_size else 1

        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name() or user.username
            },
            'posts': posts_data,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
        })

    except Exception as e:
        logger.error(f"Error fetching user posts: {str(e)}")
        return Response({
            'error': f'Failed to fetch user posts: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_forum_topics(request, user_id):
    """Get all topics created by a specific user with pagination."""
    try:
        from machina.apps.forum_conversation.models import Topic
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Get the user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get pagination params
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

        # Get user's topics
        topics_qs = Topic.objects.filter(
            poster=user,
            approved=True
        ).select_related('forum', 'last_post', 'last_post__poster').order_by('-created')

        # Pagination
        total_count = topics_qs.count()
        start = (page - 1) * page_size
        if total_count and start >= total_count:
            page = (total_count - 1) // page_size + 1
            start = (page - 1) * page_size
        end = start + page_size
        topics = topics_qs[start:end]

        # Serialize topics
        topics_data = []
        for topic in topics:
            last_post_data = None
            if topic.last_post and topic.last_post.poster:
                last_post_data = {
                    'id': topic.last_post.id,
                    'poster': {
                        'username': topic.last_post.poster.username
                    },
                    'created': topic.last_post_on.isoformat() if topic.last_post_on else None
                }

            topics_data.append({
                'id': topic.id,
                'subject': topic.subject,
                'slug': topic.slug,
                'created': topic.created.isoformat(),
                'updated': topic.updated.isoformat(),
                'posts_count': topic.posts_count,
                'views_count': topic.views_count,
                'forum': {
                    'id': topic.forum.id,
                    'name': topic.forum.name,
                    'slug': topic.forum.slug
                },
                'last_post': last_post_data
            })

        # Pagination info
        total_pages = (total_count + page_size - 1) // page_size if page_size else 1

        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name() or user.username
            },
            'topics': topics_data,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
        })

    except Exception as e:
        logger.error(f"Error fetching user topics: {str(e)}")
        return Response({
            'error': f'Failed to fetch user topics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Topic Subscription API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_topic_subscriptions(request, user_id):
    """Get all topics a user is subscribed to."""
    try:
        from machina.apps.forum_conversation.models import Topic
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Get the user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Only allow users to view their own subscriptions
        if request.user.id != user.id and not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        # Get topics the user is subscribed to using the ManyToManyField
        subscribed_topics = Topic.objects.filter(
            subscribers=user
        ).select_related('forum').order_by('-created')

        # Serialize subscriptions
        subscriptions_data = []
        for topic in subscribed_topics:
            subscriptions_data.append({
                'topic': {
                    'id': topic.id,
                    'subject': topic.subject,
                    'slug': topic.slug,
                    'posts_count': topic.posts_count,
                    'views_count': topic.views_count
                },
                'forum': {
                    'id': topic.forum.id,
                    'name': topic.forum.name,
                    'slug': topic.forum.slug
                },
                'subscribed_at': topic.created.isoformat() if hasattr(topic, 'created') else None
            })

        return Response({
            'user': {
                'id': user.id,
                'username': user.username
            },
            'subscriptions': subscriptions_data,
            'total_count': len(subscriptions_data)
        })

    except Exception as e:
        logger.error(f"Error fetching user subscriptions: {str(e)}")
        return Response({
            'error': f'Failed to fetch subscriptions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def topic_subscribe(request, topic_id):
    """Subscribe to a topic for notifications."""
    try:
        from machina.apps.forum_conversation.models import Topic

        # Get the topic
        try:
            topic = Topic.objects.get(id=topic_id, approved=True)
        except Topic.DoesNotExist:
            return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if already subscribed
        already_subscribed = topic.subscribers.filter(id=request.user.id).exists()

        if not already_subscribed:
            # Add subscriber using ManyToManyField
            topic.subscribers.add(request.user)
            created = True
        else:
            created = False

        return Response({
            'success': True,
            'subscribed': True,
            'created': created,
            'message': 'Subscribed to topic' if created else 'Already subscribed',
            'topic': {
                'id': topic.id,
                'subject': topic.subject,
                'slug': topic.slug
            }
        })

    except Exception as e:
        logger.error(f"Error subscribing to topic: {str(e)}")
        return Response({
            'error': f'Failed to subscribe: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated])
def topic_unsubscribe(request, topic_id):
    """Unsubscribe from a topic."""
    try:
        from machina.apps.forum_conversation.models import Topic

        # Get the topic
        try:
            topic = Topic.objects.get(id=topic_id)
        except Topic.DoesNotExist:
            return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

        # Remove subscriber using ManyToManyField
        was_subscribed = topic.subscribers.filter(id=request.user.id).exists()
        if was_subscribed:
            topic.subscribers.remove(request.user)
            deleted_count = 1
        else:
            deleted_count = 0

        return Response({
            'success': True,
            'subscribed': False,
            'message': 'Unsubscribed from topic' if deleted_count > 0 else 'Was not subscribed',
            'topic': {
                'id': topic.id,
                'subject': topic.subject,
                'slug': topic.slug
            }
        })

    except Exception as e:
        logger.error(f"Error unsubscribing from topic: {str(e)}")
        return Response({
            'error': f'Failed to unsubscribe: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Forum Search API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forum_search(request):
    """Search topics and posts across all forums."""
    try:
        from machina.apps.forum_conversation.models import Topic, Post
        from django.db.models import Q

        # Get search parameters
        query = request.GET.get('q', '').strip()
        search_type = request.GET.get('type', 'all')  # all, topics, posts
        forum_id = request.GET.get('forum_id')

        if not query:
            return Response({
                'error': 'Search query required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(query) < 3:
            return Response({
                'error': 'Search query must be at least 3 characters'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Pagination
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

        results = {
            'query': query,
            'topics': [],
            'posts': [],
            'pagination': {}
        }

        # Search topics
        if search_type in ['all', 'topics']:
            topics_qs = Topic.objects.filter(
                Q(subject__icontains=query) | Q(first_post__content__icontains=query),
                approved=True
            ).select_related('poster', 'forum').distinct()

            if forum_id:
                topics_qs = topics_qs.filter(forum_id=forum_id)

            # Pagination for topics
            total_topics = topics_qs.count()
            start = (page - 1) * page_size
            end = start + page_size
            topics = topics_qs[start:end]

            topics_data = []
            for topic in topics:
                topics_data.append({
                    'id': topic.id,
                    'subject': topic.subject,
                    'slug': topic.slug,
                    'created': topic.created.isoformat(),
                    'posts_count': topic.posts_count,
                    'views_count': topic.views_count,
                    'poster': {
                        'username': topic.poster.username
                    },
                    'forum': {
                        'id': topic.forum.id,
                        'name': topic.forum.name,
                        'slug': topic.forum.slug
                    }
                })

            results['topics'] = topics_data
            results['topics_count'] = total_topics

        # Search posts
        if search_type in ['all', 'posts']:
            posts_qs = Post.objects.filter(
                content__icontains=query,
                approved=True
            ).select_related('poster', 'topic', 'topic__forum')

            if forum_id:
                posts_qs = posts_qs.filter(topic__forum_id=forum_id)

            # Pagination for posts
            total_posts = posts_qs.count()
            start = (page - 1) * page_size
            end = start + page_size
            posts = posts_qs[start:end]

            posts_data = []
            for post in posts:
                # Highlight search term in content (simple excerpt)
                content = str(post.content)
                excerpt_length = 200
                query_pos = content.lower().find(query.lower())

                if query_pos != -1:
                    start_pos = max(0, query_pos - 50)
                    end_pos = min(len(content), query_pos + excerpt_length)
                    excerpt = content[start_pos:end_pos]
                    if start_pos > 0:
                        excerpt = '...' + excerpt
                    if end_pos < len(content):
                        excerpt = excerpt + '...'
                else:
                    excerpt = content[:excerpt_length] + ('...' if len(content) > excerpt_length else '')

                posts_data.append({
                    'id': post.id,
                    'excerpt': excerpt,
                    'created': post.created.isoformat(),
                    'poster': {
                        'username': post.poster.username
                    },
                    'topic': {
                        'id': post.topic.id,
                        'subject': post.topic.subject,
                        'slug': post.topic.slug
                    },
                    'forum': {
                        'id': post.topic.forum.id,
                        'name': post.topic.forum.name,
                        'slug': post.topic.forum.slug
                    }
                })

            results['posts'] = posts_data
            results['posts_count'] = total_posts

        # Overall pagination
        total_results = results.get('topics_count', 0) + results.get('posts_count', 0)
        total_pages = (total_results + page_size - 1) // page_size if page_size else 1

        results['pagination'] = {
            'current_page': page,
            'page_size': page_size,
            'total_results': total_results,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }

        return Response(results)

    except Exception as e:
        logger.error(f"Error searching forums: {str(e)}")
        return Response({
            'error': f'Search failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Recent Activity API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forum_recent_activity(request):
    """Get recent forum activity across all forums."""
    try:
        from machina.apps.forum_conversation.models import Topic, Post
        from django.utils import timezone
        from datetime import timedelta

        # Get time range parameter
        hours = request.GET.get('hours', 24)
        try:
            hours = int(hours)
            hours = max(1, min(hours, 168))  # 1 hour to 1 week
        except ValueError:
            hours = 24

        since = timezone.now() - timedelta(hours=hours)

        # Get recent topics
        recent_topics = Topic.objects.filter(
            created__gte=since,
            approved=True
        ).select_related('poster', 'forum').order_by('-created')[:10]

        # Get recent posts
        recent_posts = Post.objects.filter(
            created__gte=since,
            approved=True
        ).select_related('poster', 'topic', 'topic__forum').order_by('-created')[:20]

        # Serialize recent topics
        topics_data = []
        for topic in recent_topics:
            topics_data.append({
                'type': 'topic',
                'id': topic.id,
                'subject': topic.subject,
                'slug': topic.slug,
                'created': topic.created.isoformat(),
                'poster': {
                    'id': topic.poster.id,
                    'username': topic.poster.username
                },
                'forum': {
                    'id': topic.forum.id,
                    'name': topic.forum.name,
                    'slug': topic.forum.slug
                }
            })

        # Serialize recent posts
        posts_data = []
        for post in recent_posts:
            posts_data.append({
                'type': 'post',
                'id': post.id,
                'excerpt': str(post.content)[:150] + ('...' if len(str(post.content)) > 150 else ''),
                'created': post.created.isoformat(),
                'poster': {
                    'id': post.poster.id,
                    'username': post.poster.username
                },
                'topic': {
                    'id': post.topic.id,
                    'subject': post.topic.subject,
                    'slug': post.topic.slug
                },
                'forum': {
                    'id': post.topic.forum.id,
                    'name': post.topic.forum.name,
                    'slug': post.topic.forum.slug
                }
            })

        # Combine and sort by timestamp
        all_activity = []
        for topic in topics_data:
            topic['timestamp'] = topic['created']
            all_activity.append(topic)
        for post in posts_data:
            post['timestamp'] = post['created']
            all_activity.append(post)

        # Sort by timestamp descending
        all_activity.sort(key=lambda x: x['timestamp'], reverse=True)

        # Limit to 30 most recent items
        all_activity = all_activity[:30]

        return Response({
            'activity': all_activity,
            'time_range_hours': hours,
            'since': since.isoformat(),
            'count': len(all_activity)
        })

    except Exception as e:
        logger.error(f"Error fetching recent activity: {str(e)}")
        return Response({
            'error': f'Failed to fetch activity: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==============================================================================
# MODERATION API ENDPOINTS
# ==============================================================================

def _check_moderation_permission(user, forum=None):
    """
    Check if user has moderation permissions.

    Moderators are:
    - Staff/superusers
    - TL3+ users (Regular and Leader)
    - Forum-specific moderators (if forum provided)
    """
    # Staff and superusers can always moderate
    if user.is_staff or user.is_superuser:
        return True

    # Check trust level - TL3+ can moderate
    try:
        trust_level = user.trust_level.level
        if trust_level >= 3:  # Regular (TL3) and Leader (TL4)
            return True
    except (AttributeError, Exception):
        # User doesn't have a trust_level relationship or trust_level doesn't exist
        pass

    # TODO: Check forum-specific moderators when that feature is added
    # if forum and user in forum.moderators.all():
    #     return True

    return False


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def topic_lock(request, topic_id):
    """Lock a topic to prevent new replies."""
    try:
        from machina.apps.forum_conversation.models import Topic

        # Get the topic
        try:
            topic = Topic.objects.select_related('forum').get(id=topic_id)
        except Topic.DoesNotExist:
            return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check moderation permissions
        if not _check_moderation_permission(request.user, topic.forum):
            return Response({
                'error': 'You do not have permission to moderate this topic'
            }, status=status.HTTP_403_FORBIDDEN)

        # Lock the topic
        topic.status = Topic.TOPIC_LOCKED
        topic.save()

        logger.info(f"Topic {topic.id} '{topic.subject}' locked by {request.user.username}")

        return Response({
            'success': True,
            'message': 'Topic locked successfully',
            'topic': {
                'id': topic.id,
                'subject': topic.subject,
                'status': topic.status,
                'locked': topic.status == Topic.TOPIC_LOCKED
            }
        })

    except Exception as e:
        logger.error(f"Error locking topic {topic_id}: {str(e)}")
        return Response({
            'error': f'Failed to lock topic: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def topic_unlock(request, topic_id):
    """Unlock a topic to allow new replies."""
    try:
        from machina.apps.forum_conversation.models import Topic

        # Get the topic
        try:
            topic = Topic.objects.select_related('forum').get(id=topic_id)
        except Topic.DoesNotExist:
            return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check moderation permissions
        if not _check_moderation_permission(request.user, topic.forum):
            return Response({
                'error': 'You do not have permission to moderate this topic'
            }, status=status.HTTP_403_FORBIDDEN)

        # Unlock the topic
        topic.status = Topic.TOPIC_UNLOCKED
        topic.save()

        logger.info(f"Topic {topic.id} '{topic.subject}' unlocked by {request.user.username}")

        return Response({
            'success': True,
            'message': 'Topic unlocked successfully',
            'topic': {
                'id': topic.id,
                'subject': topic.subject,
                'status': topic.status,
                'locked': topic.status == Topic.TOPIC_LOCKED
            }
        })

    except Exception as e:
        logger.error(f"Error unlocking topic {topic_id}: {str(e)}")
        return Response({
            'error': f'Failed to unlock topic: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def topic_pin(request, topic_id):
    """Pin a topic (sticky/announcement)."""
    try:
        from machina.apps.forum_conversation.models import Topic

        # Get the topic
        try:
            topic = Topic.objects.select_related('forum').get(id=topic_id)
        except Topic.DoesNotExist:
            return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check moderation permissions
        if not _check_moderation_permission(request.user, topic.forum):
            return Response({
                'error': 'You do not have permission to moderate this topic'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get pin type from request data
        pin_type = request.data.get('type', 'sticky')  # 'sticky' or 'announce'

        # Validate pin type
        if pin_type not in ['sticky', 'announce']:
            return Response({
                'error': f'Invalid pin type "{pin_type}". Must be "sticky" or "announce"'
            }, status=status.HTTP_400_BAD_REQUEST)

        if pin_type == 'announce':
            topic.type = Topic.TOPIC_ANNOUNCE
        else:
            topic.type = Topic.TOPIC_STICKY

        topic.save()

        logger.info(f"Topic {topic.id} '{topic.subject}' pinned as {pin_type} by {request.user.username}")

        return Response({
            'success': True,
            'message': f'Topic pinned as {pin_type} successfully',
            'topic': {
                'id': topic.id,
                'subject': topic.subject,
                'type': topic.type,
                'is_pinned': topic.type in [Topic.TOPIC_STICKY, Topic.TOPIC_ANNOUNCE],
                'pin_type': pin_type
            }
        })

    except Exception as e:
        logger.error(f"Error pinning topic {topic_id}: {str(e)}")
        return Response({
            'error': f'Failed to pin topic: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def topic_unpin(request, topic_id):
    """Unpin a topic."""
    try:
        from machina.apps.forum_conversation.models import Topic

        # Get the topic
        try:
            topic = Topic.objects.select_related('forum').get(id=topic_id)
        except Topic.DoesNotExist:
            return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check moderation permissions
        if not _check_moderation_permission(request.user, topic.forum):
            return Response({
                'error': 'You do not have permission to moderate this topic'
            }, status=status.HTTP_403_FORBIDDEN)

        # Unpin the topic
        topic.type = Topic.TOPIC_POST
        topic.save()

        logger.info(f"Topic {topic.id} '{topic.subject}' unpinned by {request.user.username}")

        return Response({
            'success': True,
            'message': 'Topic unpinned successfully',
            'topic': {
                'id': topic.id,
                'subject': topic.subject,
                'type': topic.type,
                'is_pinned': False
            }
        })

    except Exception as e:
        logger.error(f"Error unpinning topic {topic_id}: {str(e)}")
        return Response({
            'error': f'Failed to unpin topic: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def topic_move(request, topic_id):
    """Move a topic to a different forum."""
    try:
        from machina.apps.forum_conversation.models import Topic
        from machina.apps.forum.models import Forum

        # Get the topic
        try:
            topic = Topic.objects.select_related('forum').get(id=topic_id)
        except Topic.DoesNotExist:
            return Response({'error': 'Topic not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check moderation permissions
        if not _check_moderation_permission(request.user, topic.forum):
            return Response({
                'error': 'You do not have permission to moderate this topic'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get target forum
        target_forum_id = request.data.get('forum_id')
        if not target_forum_id:
            return Response({
                'error': 'Target forum_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_forum = Forum.objects.get(id=target_forum_id, type=Forum.FORUM_POST)
        except Forum.DoesNotExist:
            return Response({
                'error': 'Target forum not found or not a postable forum'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check permission on target forum
        if not _check_moderation_permission(request.user, target_forum):
            return Response({
                'error': 'You do not have permission to moderate the target forum'
            }, status=status.HTTP_403_FORBIDDEN)

        old_forum = topic.forum
        topic.forum = target_forum
        topic.save()

        # Update trackers for both forums
        old_forum.save()  # Triggers signal to update counts
        target_forum.save()

        logger.info(f"Topic {topic.id} '{topic.subject}' moved from {old_forum.name} to {target_forum.name} by {request.user.username}")

        return Response({
            'success': True,
            'message': f'Topic moved to {target_forum.name} successfully',
            'topic': {
                'id': topic.id,
                'subject': topic.subject,
                'forum': {
                    'id': target_forum.id,
                    'name': target_forum.name,
                    'slug': target_forum.slug
                },
                'old_forum': {
                    'id': old_forum.id,
                    'name': old_forum.name,
                    'slug': old_forum.slug
                }
            }
        })

    except Exception as e:
        logger.error(f"Error moving topic {topic_id}: {str(e)}")
        return Response({
            'error': f'Failed to move topic: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def moderation_queue(request):
    """Get the moderation queue - posts and topics awaiting review."""
    try:
        # Check moderation permissions
        if not _check_moderation_permission(request.user):
            return Response({
                'error': 'You do not have permission to access the moderation queue'
            }, status=status.HTTP_403_FORBIDDEN)

        from machina.apps.forum_conversation.models import Topic, Post
        from apps.forum_integration.models import ReviewQueue
        from django.core.paginator import Paginator

        # Get page number
        page = request.GET.get('page', 1)
        try:
            page = int(page)
        except ValueError:
            page = 1

        # Get filter type
        filter_type = request.GET.get('type', 'all')  # all, posts, topics, users
        status_filter = request.GET.get('status', 'pending')  # pending, approved, rejected

        # Build query
        queue_items = ReviewQueue.objects.select_related(
            'post__topic__forum', 'topic__forum', 'topic__poster',
            'reported_user', 'reporter', 'assigned_moderator'
        ).order_by('-priority', '-created_at')

        # Apply filters
        if status_filter == 'pending':
            queue_items = queue_items.filter(status='pending')
        elif status_filter == 'approved':
            queue_items = queue_items.filter(status='approved')
        elif status_filter == 'rejected':
            queue_items = queue_items.filter(status='rejected')

        if filter_type == 'posts':
            queue_items = queue_items.filter(post__isnull=False)
        elif filter_type == 'topics':
            queue_items = queue_items.filter(topic__isnull=False)
        elif filter_type == 'users':
            queue_items = queue_items.filter(reported_user__isnull=False)

        # Paginate
        paginator = Paginator(queue_items, 20)
        page_obj = paginator.get_page(page)

        # Serialize items
        items_data = []
        for item in page_obj:
            item_data = {
                'id': item.id,
                'review_type': item.review_type,
                'reason': item.reason,
                'priority': item.priority,
                'status': item.status,
                'created_at': item.created_at.isoformat(),
                'resolved_at': item.resolved_at.isoformat() if item.resolved_at else None,
                'moderator_notes': item.moderator_notes or '',
                'resolution_notes': item.resolution_notes or '',
            }

            # Add reporter info
            if item.reporter:
                item_data['reporter'] = {
                    'id': item.reporter.id,
                    'username': item.reporter.username
                }

            # Add assigned moderator info
            if item.assigned_moderator:
                item_data['assigned_moderator'] = {
                    'id': item.assigned_moderator.id,
                    'username': item.assigned_moderator.username
                }

            # Add content based on type
            if item.post:
                item_data['content_type'] = 'post'
                item_data['post'] = {
                    'id': item.post.id,
                    'content': item.post.content[:200] + '...' if len(item.post.content) > 200 else item.post.content,
                    'poster': {
                        'id': item.post.poster.id,
                        'username': item.post.poster.username
                    },
                    'topic': {
                        'id': item.post.topic.id,
                        'subject': item.post.topic.subject
                    }
                }
            elif item.topic:
                item_data['content_type'] = 'topic'
                item_data['topic'] = {
                    'id': item.topic.id,
                    'subject': item.topic.subject,
                    'poster': {
                        'id': item.topic.poster.id,
                        'username': item.topic.poster.username
                    },
                    'forum': {
                        'id': item.topic.forum.id,
                        'name': item.topic.forum.name
                    }
                }
            elif item.reported_user:
                item_data['content_type'] = 'user'
                item_data['user'] = {
                    'id': item.reported_user.id,
                    'username': item.reported_user.username
                }

            items_data.append(item_data)

        return Response({
            'queue': items_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'total_items': paginator.count,
                'items_per_page': 20
            },
            'filters': {
                'type': filter_type,
                'status': status_filter
            },
            'stats': {
                'pending_count': ReviewQueue.objects.filter(status='pending').count(),
                'approved_count': ReviewQueue.objects.filter(status='approved').count(),
                'rejected_count': ReviewQueue.objects.filter(status='rejected').count()
            }
        })

    except Exception as e:
        logger.error(f"Error fetching moderation queue: {str(e)}")
        return Response({
            'error': f'Failed to fetch moderation queue: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def moderation_review(request, item_id):
    """Approve or reject a moderation queue item."""
    try:
        # Check moderation permissions
        if not _check_moderation_permission(request.user):
            return Response({
                'error': 'You do not have permission to review moderation items'
            }, status=status.HTTP_403_FORBIDDEN)

        from apps.forum_integration.models import ReviewQueue

        # Get the queue item
        try:
            item = ReviewQueue.objects.select_related(
                'post__topic', 'topic', 'reported_user'
            ).get(id=item_id)
        except ReviewQueue.DoesNotExist:
            return Response({'error': 'Queue item not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get action and notes
        action = request.data.get('action')  # 'approve' or 'reject'
        notes = request.data.get('notes', '')

        if action not in ['approve', 'reject']:
            return Response({
                'error': 'Action must be "approve" or "reject"'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update the item
        item.status = 'approved' if action == 'approve' else 'rejected'
        item.assigned_moderator = request.user
        item.resolved_at = timezone.now()
        item.resolution_notes = notes
        item.save()

        # Take action on the content
        if action == 'approve':
            if item.post and not item.post.approved:
                item.post.approved = True
                item.post.save()
            elif item.topic and not item.topic.approved:
                item.topic.approved = True
                item.topic.save()
        else:  # reject
            if item.post:
                item.post.approved = False
                item.post.save()
            elif item.topic:
                item.topic.approved = False
                item.topic.save()

        logger.info(f"Queue item {item.id} {action}ed by {request.user.username}")

        return Response({
            'success': True,
            'message': f'Item {action}ed successfully',
            'item': {
                'id': item.id,
                'status': item.status,
                'resolved_at': item.resolved_at.isoformat() if item.resolved_at else None,
                'moderator': request.user.username
            }
        })

    except Exception as e:
        logger.error(f"Error reviewing queue item {item_id}: {str(e)}")
        return Response({
            'error': f'Failed to review item: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def moderation_stats(request):
    """Get moderation queue statistics."""
    try:
        # Check moderation permissions
        if not _check_moderation_permission(request.user):
            return Response({
                'error': 'You do not have permission to access moderation statistics'
            }, status=status.HTTP_403_FORBIDDEN)

        from apps.forum_integration.models import ReviewQueue
        from django.utils import timezone
        from datetime import timedelta

        # Get count by status
        pending_count = ReviewQueue.objects.filter(status='pending').count()
        approved_count = ReviewQueue.objects.filter(status='approved').count()
        rejected_count = ReviewQueue.objects.filter(status='rejected').count()

        # Get today's review count (items resolved today)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = ReviewQueue.objects.filter(
            resolved_at__gte=today_start,
            status__in=['approved', 'rejected']
        ).count()

        return Response({
            'pending': pending_count,
            'approved': approved_count,
            'rejected': rejected_count,
            'today_count': today_count,
            'total': pending_count + approved_count + rejected_count
        })

    except Exception as e:
        logger.error(f"Error fetching moderation stats: {str(e)}")
        return Response({
            'error': f'Failed to fetch moderation statistics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
