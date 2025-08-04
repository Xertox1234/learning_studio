from django.shortcuts import render
from django.contrib.auth import get_user_model
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post

User = get_user_model()


def community_index_view(request):
    """Community index page with real forum data."""
    # Get real community statistics
    total_users = User.objects.count()
    total_topics = Topic.objects.count()
    total_posts = Post.objects.count()
    total_forums = Forum.objects.filter(type=Forum.FORUM_POST).count()
    
    # Get recent discussions (latest topics with posts)
    recent_topics = Topic.objects.select_related(
        'poster', 'forum', 'last_post', 'last_post__poster'
    ).filter(
        approved=True
    ).order_by('-last_post_on')[:3]
    
    # Get forum categories for navigation
    forum_categories = Forum.objects.filter(
        type=Forum.FORUM_CAT
    ).prefetch_related('get_children')
    
    context = {
        'total_users': total_users,
        'total_topics': total_topics, 
        'total_posts': total_posts,
        'total_forums': total_forums,
        'recent_topics': recent_topics,
        'forum_categories': forum_categories,
    }
    return render(request, 'community/index.html', context)
