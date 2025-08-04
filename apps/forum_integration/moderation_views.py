"""
Moderation views for the unified review queue system.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth import get_user_model
import json

from .models import ReviewQueue, ModerationLog, FlaggedContent, TrustLevel
from machina.apps.forum_conversation.models import Post, Topic

User = get_user_model()


def is_moderator(user):
    """Check if user has moderation privileges"""
    return user.is_staff or user.is_superuser or (
        hasattr(user, 'trust_level') and user.trust_level.level >= 3
    )


@login_required
@user_passes_test(is_moderator)
def moderation_dashboard(request):
    """
    Main moderation dashboard showing unified review queue
    """
    # Get filter parameters
    status_filter = request.GET.get('status', 'pending')
    type_filter = request.GET.get('type', 'all')
    assigned_filter = request.GET.get('assigned', 'all')
    priority_filter = request.GET.get('priority', 'all')
    
    # Base queryset
    queryset = ReviewQueue.objects.select_related(
        'post', 'topic', 'reported_user', 'reporter', 'assigned_moderator'
    )
    
    # Apply filters
    if status_filter != 'all':
        queryset = queryset.filter(status=status_filter)
    
    if type_filter != 'all':
        queryset = queryset.filter(review_type=type_filter)
    
    if assigned_filter == 'mine':
        queryset = queryset.filter(assigned_moderator=request.user)
    elif assigned_filter == 'unassigned':
        queryset = queryset.filter(assigned_moderator__isnull=True)
    
    if priority_filter != 'all':
        queryset = queryset.filter(priority=int(priority_filter))
    
    # Pagination
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_pending': ReviewQueue.objects.filter(status='pending').count(),
        'assigned_to_me': ReviewQueue.objects.filter(
            assigned_moderator=request.user, status='pending'
        ).count(),
        'critical_items': ReviewQueue.objects.filter(
            priority=1, status='pending'
        ).count(),
        'avg_resolution_time': ReviewQueue.objects.filter(
            status__in=['approved', 'rejected'], resolved_at__isnull=False
        ).aggregate(
            avg_time=Avg('resolved_at') - Avg('created_at')
        )['avg_time'],
    }
    
    # Review type choices for filter
    review_type_choices = ReviewQueue.REVIEW_TYPES
    priority_choices = ReviewQueue.PRIORITY_CHOICES
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'assigned_filter': assigned_filter,
        'priority_filter': priority_filter,
        'review_type_choices': review_type_choices,
        'priority_choices': priority_choices,
    }
    
    return render(request, 'forum_integration/moderation_dashboard.html', context)


@login_required
@user_passes_test(is_moderator)
def review_item_detail(request, item_id):
    """
    Detailed view of a review queue item
    """
    item = get_object_or_404(ReviewQueue, id=item_id)
    
    # Get moderation history for this item
    moderation_history = ModerationLog.objects.filter(
        review_item=item
    ).select_related('moderator').order_by('-timestamp')
    
    # Get related content context
    content_context = {}
    if item.post:
        content_context['post'] = item.post
        content_context['topic'] = item.post.topic
    elif item.topic:
        content_context['topic'] = item.topic
    
    if item.reported_user:
        # Get user's trust level and recent activity
        try:
            trust_level = item.reported_user.trust_level
            content_context['user_trust_level'] = trust_level
        except TrustLevel.DoesNotExist:
            content_context['user_trust_level'] = None
        
        # Get recent moderation actions for this user
        recent_actions = ModerationLog.objects.filter(
            target_user=item.reported_user
        ).select_related('moderator').order_by('-timestamp')[:10]
        content_context['recent_user_actions'] = recent_actions
    
    context = {
        'item': item,
        'moderation_history': moderation_history,
        'content_context': content_context,
    }
    
    return render(request, 'forum_integration/review_item_detail.html', context)


@login_required
@user_passes_test(is_moderator)
@require_POST
def moderate_item(request, item_id):
    """
    Handle moderation actions on a review queue item
    """
    item = get_object_or_404(ReviewQueue, id=item_id)
    action = request.POST.get('action')
    reason = request.POST.get('reason', '')
    moderator_notes = request.POST.get('moderator_notes', '')
    
    valid_actions = ['approve', 'reject', 'escalate', 'assign_to_me', 'needs_info']
    
    if action not in valid_actions:
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    try:
        with transaction.atomic():
            # Update the review item
            if action == 'approve':
                item.status = 'approved'
                item.resolved_at = timezone.now()
                log_action = 'approve'
            elif action == 'reject':
                item.status = 'rejected'
                item.resolved_at = timezone.now()
                log_action = 'reject'
            elif action == 'escalate':
                item.status = 'escalated'
                item.priority = max(1, item.priority - 1)  # Increase priority
                log_action = 'escalate'
            elif action == 'assign_to_me':
                item.assigned_moderator = request.user
                log_action = 'assign_moderator'
            elif action == 'needs_info':
                item.status = 'needs_info'
                log_action = 'needs_info'
            
            # Update moderator notes if provided
            if moderator_notes:
                item.moderator_notes = moderator_notes
            
            item.save()
            
            # Create moderation log entry
            ModerationLog.objects.create(
                action_type=log_action,
                moderator=request.user,
                review_item=item,
                target_user=item.reported_user,
                target_post=item.post,
                target_topic=item.topic,
                reason=reason,
                details={
                    'action': action,
                    'moderator_notes': moderator_notes,
                    'previous_status': item.status,
                },
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            # Handle specific post-moderation actions
            if action == 'approve' and item.review_type == 'new_user_post':
                # Auto-approve similar content from this user in the future
                pass  # Could implement auto-approval logic here
            
            elif action == 'reject':
                # Handle content removal if needed
                if item.post and item.review_type in ['flagged_post', 'spam_detection']:
                    # Mark post as hidden or delete
                    pass  # Implement content removal logic
        
        return JsonResponse({
            'success': True,
            'message': f'Item {action}d successfully',
            'new_status': item.get_status_display()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_moderator)
@require_POST
def bulk_moderate(request):
    """
    Handle bulk moderation actions
    """
    try:
        data = json.loads(request.body)
        item_ids = data.get('item_ids', [])
        action = data.get('action')
        reason = data.get('reason', '')
        
        if not item_ids or not action:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        valid_actions = ['approve', 'reject', 'assign_to_me', 'escalate']
        if action not in valid_actions:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        with transaction.atomic():
            items = ReviewQueue.objects.filter(id__in=item_ids, status='pending')
            updated_count = 0
            
            for item in items:
                if action == 'approve':
                    item.status = 'approved'
                    item.resolved_at = timezone.now()
                elif action == 'reject':
                    item.status = 'rejected'
                    item.resolved_at = timezone.now()
                elif action == 'assign_to_me':
                    item.assigned_moderator = request.user
                elif action == 'escalate':
                    item.status = 'escalated'
                    item.priority = max(1, item.priority - 1)
                
                item.save()
                updated_count += 1
                
                # Create log entry for each item
                ModerationLog.objects.create(
                    action_type='bulk_action',
                    moderator=request.user,
                    review_item=item,
                    target_user=item.reported_user,
                    target_post=item.post,
                    target_topic=item.topic,
                    reason=reason,
                    details={
                        'bulk_action': action,
                        'total_items': len(item_ids),
                    },
                    ip_address=request.META.get('REMOTE_ADDR')
                )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully {action}d {updated_count} items',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_moderator)
def moderation_stats(request):
    """
    Detailed moderation statistics and analytics
    """
    # Time-based statistics
    from datetime import timedelta
    now = timezone.now()
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)
    
    stats = {
        'queue_summary': {
            'total_pending': ReviewQueue.objects.filter(status='pending').count(),
            'total_resolved_today': ReviewQueue.objects.filter(
                resolved_at__date=now.date()
            ).count(),
            'total_resolved_week': ReviewQueue.objects.filter(
                resolved_at__gte=last_week
            ).count(),
        },
        'by_type': ReviewQueue.objects.values('review_type').annotate(
            count=Count('id')
        ).order_by('-count'),
        'by_status': ReviewQueue.objects.values('status').annotate(
            count=Count('id')
        ),
        'moderator_activity': User.objects.filter(
            moderation_actions__timestamp__gte=last_week
        ).annotate(
            action_count=Count('moderation_actions')
        ).order_by('-action_count')[:10],
        'resolution_times': ReviewQueue.objects.filter(
            status__in=['approved', 'rejected'],
            resolved_at__isnull=False
        ).extra(select={
            'resolution_hours': "ROUND((JULIANDAY(resolved_at) - JULIANDAY(created_at)) * 24)"
        }).values('resolution_hours').annotate(count=Count('id')),
    }
    
    context = {'stats': stats}
    return render(request, 'forum_integration/moderation_stats.html', context)


@login_required
@user_passes_test(is_moderator)
def flag_content(request):
    """
    Handle content flagging (can be called via AJAX)
    """
    if request.method == 'POST':
        content_type = request.POST.get('content_type')  # 'post' or 'topic'
        content_id = request.POST.get('content_id')
        reason = request.POST.get('reason')
        description = request.POST.get('description', '')
        
        try:
            with transaction.atomic():
                # Create flagged content record
                flag_data = {
                    'flagger': request.user,
                    'reason': reason,
                    'description': description,
                }
                
                if content_type == 'post':
                    post = get_object_or_404(Post, id=content_id)
                    flag_data['post'] = post
                elif content_type == 'topic':
                    topic = get_object_or_404(Topic, id=content_id)
                    flag_data['topic'] = topic
                else:
                    return JsonResponse({'error': 'Invalid content type'}, status=400)
                
                flagged_content = FlaggedContent.objects.create(**flag_data)
                
                # Create review queue item
                review_item = ReviewQueue.objects.create(
                    review_type='flagged_post',
                    post=flagged_content.post,
                    topic=flagged_content.topic,
                    reporter=request.user,
                    reason=f"Flagged for {flagged_content.get_reason_display()}: {description}",
                    priority=2 if reason in ['spam', 'harassment'] else 3,
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Content flagged successfully',
                    'review_id': review_item.id
                })
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # GET request - show flagging form
    content_type = request.GET.get('content_type')
    content_id = request.GET.get('content_id')
    
    context = {
        'content_type': content_type,
        'content_id': content_id,
        'flag_reasons': FlaggedContent.FLAG_REASONS,
    }
    
    return render(request, 'forum_integration/flag_content.html', context)


@login_required
@user_passes_test(is_moderator)
def auto_moderate_suggestions(request):
    """
    Provide automatic moderation suggestions based on patterns
    """
    # Get items that might benefit from auto-moderation
    suggestions = []
    
    # Check for users with multiple flags
    frequent_flagged_users = User.objects.annotate(
        flag_count=Count('forum_reported_reviews')
    ).filter(flag_count__gte=3)
    
    for user in frequent_flagged_users:
        suggestions.append({
            'type': 'user_pattern',
            'user': user,
            'reason': f'User has {user.flag_count} pending reviews',
            'action': 'review_user_activity',
            'confidence': 'high' if user.flag_count >= 5 else 'medium'
        })
    
    # Check for posts with similar content to previously rejected posts
    # This would require more sophisticated text analysis
    
    # Check for trust level inconsistencies
    tl_inconsistencies = TrustLevel.objects.filter(
        level__gte=2,
        user__forum_reported_reviews__status='pending'
    ).distinct()
    
    for trust_level in tl_inconsistencies:
        suggestions.append({
            'type': 'trust_level_review',
            'user': trust_level.user,
            'reason': f'TL{trust_level.level} user has pending moderation reviews',
            'action': 'review_trust_level',
            'confidence': 'medium'
        })
    
    context = {'suggestions': suggestions}
    return render(request, 'forum_integration/auto_moderate_suggestions.html', context)