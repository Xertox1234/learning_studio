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


# Rich Forum Post Views
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from machina.core.loading import get_class
from .forms import RichTopicForm, RichReplyForm
from .models import RichForumPost

# Import machina permission handlers
PermissionHandler = get_class('forum_permission.handler', 'PermissionHandler')
assign_perm = get_class('forum_permission.shortcuts', 'assign_perm')
remove_perm = get_class('forum_permission.shortcuts', 'remove_perm')

# Import required machina views
TopicCreateView = get_class('forum_conversation.views', 'TopicCreateView')
PostCreateView = get_class('forum_conversation.views', 'PostCreateView')


class RichTopicCreateView(TopicCreateView):
    """
    Custom topic creation view that uses the rich content form
    """
    form_class = RichTopicForm
    template_name = 'forum_integration/rich_topic_create.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass any additional context needed for rich content
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Let the parent handle most of the logic
        response = super().form_valid(form)
        
        # Add success message
        messages.success(
            self.request, 
            "Your topic has been created successfully with rich content!" if form.cleaned_data.get('content_type') == 'rich' else "Your topic has been created successfully!"
        )
        
        return response


class RichPostCreateView(PostCreateView):
    """
    Custom post/reply creation view that uses the rich content form
    """
    form_class = RichReplyForm
    template_name = 'forum_integration/rich_post_create.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            "Your reply has been posted successfully with rich content!" if form.cleaned_data.get('content_type') == 'rich' else "Your reply has been posted successfully!"
        )
        
        return response


@login_required
@require_http_methods(["GET"])
def rich_content_demo(request):
    """
    Demo view to showcase the rich content editor
    """
    from .models import FORUM_CONTENT_BLOCKS
    
    # Sample content blocks for demonstration
    sample_blocks = [
        {
            'type': 'paragraph',
            'value': {'text': 'This is a sample paragraph with rich text formatting.'}
        },
        {
            'type': 'code',
            'value': {
                'language': 'python',
                'code': 'def hello_world():\n    print("Hello, World!")\n    return "Welcome to the forum!"',
                'caption': 'Sample Python function'
            }
        },
        {
            'type': 'quote',
            'value': {
                'text': 'The only way to learn a new programming language is by writing programs in it.',
                'source': 'Dennis Ritchie'
            }
        },
        {
            'type': 'callout',
            'value': {
                'type': 'tip',
                'title': 'Pro Tip',
                'text': 'Always test your code with different inputs to ensure it works correctly.'
            }
        }
    ]
    
    context = {
        'available_blocks': FORUM_CONTENT_BLOCKS,
        'sample_blocks': sample_blocks,
    }
    
    return render(request, 'forum_integration/rich_content_demo.html', context)