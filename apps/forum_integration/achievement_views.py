"""
Views for user achievements, badges, and gamification dashboard.
"""

import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Badge, UserBadge, UserPoints, PointHistory, BadgeCategory, Achievement, ForumUserAchievement
from .gamification_service import GamificationService

User = get_user_model()


@login_required
def achievement_dashboard(request):
    """
    Main achievement dashboard showing user's progress, badges, and stats.
    """
    user = request.user
    
    # Get comprehensive user stats
    user_stats = GamificationService.get_user_stats(user)
    
    # Get recent activity
    recent_badges = UserBadge.objects.filter(user=user).select_related('badge', 'badge__category')[:5]
    recent_points = PointHistory.objects.filter(user=user)[:10]
    
    # Get progress toward next badges
    available_badges = Badge.objects.filter(
        is_active=True,
        is_hidden=False
    ).exclude(
        id__in=UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    ).select_related('category')[:6]
    
    # Calculate progress for available badges
    badge_progress = []
    for badge in available_badges:
        progress = badge.calculate_progress(user)
        badge_progress.append({
            'badge': badge,
            'progress': progress,
            'percentage': min(100, (progress / badge.condition_value) * 100) if badge.condition_value > 0 else 0
        })
    
    # Get leaderboard position
    try:
        rank = user.points.global_rank
    except (UserPoints.DoesNotExist, AttributeError):
        rank = None
    
    context = {
        'user_stats': user_stats,
        'recent_badges': recent_badges,
        'recent_points': recent_points,
        'badge_progress': badge_progress,
        'leaderboard_rank': rank,
    }
    
    return render(request, 'forum_integration/achievement_dashboard.html', context)


@login_required
def badge_collection(request):
    """
    Display all user's badges organized by category.
    """
    user = request.user
    
    # Get all badge categories with user's badges
    categories = BadgeCategory.objects.prefetch_related(
        'badges__earned_by'
    ).annotate(
        total_badges=Count('badges', filter=Q(badges__is_active=True)),
        earned_badges=Count('badges__earned_by', filter=Q(badges__earned_by__user=user))
    ).order_by('sort_order')
    
    # Get user's badges by category
    user_badges = UserBadge.objects.filter(user=user).select_related(
        'badge', 'badge__category'
    ).order_by('-earned_at')
    
    # Organize badges by category
    badges_by_category = {}
    for category in categories:
        badges_by_category[category.id] = {
            'category': category,
            'badges': user_badges.filter(badge__category=category),
            'progress': category.earned_badges / max(1, category.total_badges) * 100
        }
    
    context = {
        'badges_by_category': badges_by_category,
        'total_badges': user_badges.count(),
    }
    
    return render(request, 'forum_integration/badge_collection.html', context)


@login_required
def leaderboard(request):
    """
    Display leaderboards for different timeframes.
    """
    timeframe = request.GET.get('timeframe', 'all_time')
    
    # Get leaderboard data
    leaderboard_data = GamificationService.get_leaderboard(timeframe=timeframe, limit=50)
    
    # Get current user's position
    user_position = None
    for idx, entry in enumerate(leaderboard_data, 1):
        if entry.user == request.user:
            user_position = idx
            break
    
    context = {
        'leaderboard_data': leaderboard_data,
        'timeframe': timeframe,
        'user_position': user_position,
    }
    
    return render(request, 'forum_integration/leaderboard.html', context)


@login_required
def user_profile_achievements(request, username):
    """
    Display another user's public achievements and badges.
    """
    profile_user = get_object_or_404(User, username=username)
    
    # Get public achievement data
    user_stats = GamificationService.get_user_stats(profile_user)
    badges = UserBadge.objects.filter(user=profile_user).select_related(
        'badge', 'badge__category'
    ).order_by('-earned_at')[:20]
    
    # Get achievements
    achievements = ForumUserAchievement.objects.filter(user=profile_user).select_related(
        'achievement'
    ).order_by('-earned_at')[:10]
    
    context = {
        'profile_user': profile_user,
        'user_stats': user_stats,
        'badges': badges,
        'achievements': achievements,
        'is_own_profile': profile_user == request.user,
    }
    
    return render(request, 'forum_integration/user_profile_achievements.html', context)


@login_required
def badge_detail(request, badge_id):
    """
    Display detailed information about a specific badge.
    """
    badge = get_object_or_404(Badge, id=badge_id, is_active=True)
    
    # Check if user has earned this badge
    user_badge = None
    try:
        user_badge = UserBadge.objects.get(user=request.user, badge=badge)
    except UserBadge.DoesNotExist:
        pass
    
    # Calculate progress if not earned
    progress = None
    if not user_badge:
        progress = badge.calculate_progress(request.user)
    
    # Get other users who have this badge (recent earners)
    recent_earners = UserBadge.objects.filter(badge=badge).select_related(
        'user'
    ).order_by('-earned_at')[:10]
    
    # Get stats
    total_earned = UserBadge.objects.filter(badge=badge).count()
    
    context = {
        'badge': badge,
        'user_badge': user_badge,
        'progress': progress,
        'recent_earners': recent_earners,
        'total_earned': total_earned,
    }
    
    return render(request, 'forum_integration/badge_detail.html', context)


@login_required
def achievements_api(request):
    """
    API endpoint for achievement data (for AJAX updates).
    """
    user = request.user
    
    # Get recent achievements and badges
    recent_badges = list(UserBadge.objects.filter(
        user=user, 
        notification_sent=False
    ).values(
        'badge__name', 
        'badge__description', 
        'badge__icon', 
        'badge__color',
        'earned_at'
    ))
    
    # Mark notifications as sent
    UserBadge.objects.filter(user=user, notification_sent=False).update(notification_sent=True)
    
    # Get updated stats
    try:
        user_points = user.points
        stats = {
            'total_points': user_points.total_points,
            'weekly_points': user_points.weekly_points,
            'current_streak': user_points.current_streak,
        }
    except UserPoints.DoesNotExist:
        stats = {'total_points': 0, 'weekly_points': 0, 'current_streak': 0}
    
    return JsonResponse({
        'recent_badges': recent_badges,
        'stats': stats,
    })


def public_leaderboard(request):
    """
    Public leaderboard view (no login required).
    """
    timeframe = request.GET.get('timeframe', 'all_time')
    
    # Get leaderboard data
    leaderboard_data = GamificationService.get_leaderboard(timeframe=timeframe, limit=20)
    
    context = {
        'leaderboard_data': leaderboard_data,
        'timeframe': timeframe,
    }
    
    return render(request, 'forum_integration/public_leaderboard.html', context)