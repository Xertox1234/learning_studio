"""
Template tags for displaying trust level information
"""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from apps.forum_integration.models import TrustLevel

register = template.Library()


@register.simple_tag
def trust_level_badge(user):
    """Display a trust level badge for a user"""
    try:
        trust_level = user.trust_level
        level = trust_level.level
        level_name = trust_level.level_name
        
        # Define badge colors and styles
        badge_config = {
            0: {'color': '#6c757d', 'bg': '#f8f9fa', 'icon': 'person'},
            1: {'color': '#198754', 'bg': '#d1e7dd', 'icon': 'person-check'},
            2: {'color': '#0d6efd', 'bg': '#cff4fc', 'icon': 'people'},
            3: {'color': '#fd7e14', 'bg': '#fff3cd', 'icon': 'star'},
            4: {'color': '#dc3545', 'bg': '#f8d7da', 'icon': 'gem'},
        }
        
        config = badge_config.get(level, badge_config[0])
        
        return format_html(
            '<span class="badge trust-level-badge trust-level-{}" '
            'style="color: {}; background-color: {}; border: 1px solid {};" '
            'title="{} - {}">TL{}</span>',
            level, config['color'], config['bg'], config['color'],
            level_name, trust_level_progress_text(user), level
        )
    except TrustLevel.DoesNotExist:
        return format_html(
            '<span class="badge trust-level-badge trust-level-0" '
            'style="color: #6c757d; background-color: #f8f9fa; border: 1px solid #6c757d;" '
            'title="New User">TL0</span>'
        )


@register.simple_tag
def trust_level_icon(user):
    """Display just the trust level icon"""
    try:
        trust_level = user.trust_level
        level = trust_level.level
        
        icons = {
            0: 'bi-person',
            1: 'bi-person-check',
            2: 'bi-people',
            3: 'bi-star',
            4: 'bi-gem',
        }
        
        colors = {
            0: '#6c757d',
            1: '#198754',
            2: '#0d6efd',
            3: '#fd7e14',
            4: '#dc3545',
        }
        
        icon = icons.get(level, icons[0])
        color = colors.get(level, colors[0])
        
        return format_html(
            '<i class="{}" style="color: {};" title="Trust Level {}"></i>',
            icon, color, level
        )
    except TrustLevel.DoesNotExist:
        return format_html(
            '<i class="bi-person" style="color: #6c757d;" title="Trust Level 0"></i>'
        )


@register.simple_tag
def trust_level_progress_text(user):
    """Get progress text for next trust level"""
    try:
        trust_level = user.trust_level
        level = trust_level.level
        
        if level == 0:
            posts_needed = max(0, 10 - trust_level.posts_read)
            time_needed = max(0, 10 - (trust_level.time_read.total_seconds() / 60))
            if posts_needed == 0 and time_needed == 0:
                return "Ready for promotion to TL1!"
            return f"Need {posts_needed} more posts read, {time_needed:.1f} more minutes reading for TL1"
        
        elif level == 1:
            days_needed = max(0, 15 - trust_level.days_visited)
            posts_needed = max(0, 100 - trust_level.posts_read)
            likes_needed = max(0, 1 - trust_level.likes_received)
            if days_needed == 0 and posts_needed == 0 and likes_needed == 0:
                return "Ready for promotion to TL2!"
            return f"Need {days_needed} more days visited, {posts_needed} more posts read, {likes_needed} more likes for TL2"
        
        elif level == 2:
            days_needed = max(0, 50 - trust_level.days_visited)
            posts_needed = max(0, 500 - trust_level.posts_read)
            likes_received_needed = max(0, 10 - trust_level.likes_received)
            likes_given_needed = max(0, 30 - trust_level.likes_given)
            if all(x == 0 for x in [days_needed, posts_needed, likes_received_needed, likes_given_needed]):
                return "Ready for promotion to TL3!"
            return f"Need {days_needed} more days visited, {posts_needed} more posts read, {likes_received_needed} more likes received, {likes_given_needed} more likes given for TL3"
        
        elif level == 3:
            return "Requires manual promotion to TL4 by staff"
        
        else:
            return "Maximum level reached"
            
    except TrustLevel.DoesNotExist:
        return "New user - start participating to gain trust levels!"


@register.simple_tag
def trust_level_permissions(user):
    """Get list of permissions for user's trust level"""
    try:
        trust_level = user.trust_level
        permissions = []
        
        if trust_level.can_post_images:
            permissions.append("Post images")
        if trust_level.can_edit_posts_extended:
            permissions.append("Extended post editing")
        if trust_level.can_create_wiki_posts:
            permissions.append("Create wiki posts")
        if trust_level.can_moderate_basic:
            permissions.append("Basic moderation")
        if trust_level.can_edit_titles:
            permissions.append("Edit topic titles")
        if trust_level.can_moderate_full:
            permissions.append("Full moderation")
        
        if not permissions:
            permissions = ["Basic posting"]
        
        return permissions
    except TrustLevel.DoesNotExist:
        return ["Basic posting"]


@register.inclusion_tag('forum_integration/trust_level_progress.html', takes_context=True)
def trust_level_progress_bar(context, user):
    """Display a progress bar for the user's trust level"""
    try:
        trust_level = user.trust_level
        level = trust_level.level
        
        # Calculate progress to next level
        progress_percentage = 0
        
        if level == 0:
            # Progress to TL1
            posts_progress = min(100, (trust_level.posts_read / 10) * 100)
            time_progress = min(100, (trust_level.time_read.total_seconds() / 600) * 100)  # 10 minutes
            progress_percentage = (posts_progress + time_progress) / 2
        
        elif level == 1:
            # Progress to TL2
            days_progress = min(100, (trust_level.days_visited / 15) * 100)
            posts_progress = min(100, (trust_level.posts_read / 100) * 100)
            likes_progress = min(100, (trust_level.likes_received / 1) * 100)
            progress_percentage = (days_progress + posts_progress + likes_progress) / 3
        
        elif level == 2:
            # Progress to TL3
            days_progress = min(100, (trust_level.days_visited / 50) * 100)
            posts_progress = min(100, (trust_level.posts_read / 500) * 100)
            likes_received_progress = min(100, (trust_level.likes_received / 10) * 100)
            likes_given_progress = min(100, (trust_level.likes_given / 30) * 100)
            progress_percentage = (days_progress + posts_progress + likes_received_progress + likes_given_progress) / 4
        
        else:
            # TL3+ are at 100%
            progress_percentage = 100
        
        return {
            'user': user,
            'trust_level': trust_level,
            'progress_percentage': int(progress_percentage),
            'next_level': level + 1 if level < 4 else None,
        }
    except TrustLevel.DoesNotExist:
        return {
            'user': user,
            'trust_level': None,
            'progress_percentage': 0,
            'next_level': 1,
        }


@register.filter
def has_trust_level(user, minimum_level):
    """Check if user has at least the specified trust level"""
    try:
        return user.trust_level.level >= int(minimum_level)
    except (TrustLevel.DoesNotExist, AttributeError, ValueError):
        return False


@register.filter
def div(value, divisor):
    """Divide the value by the divisor"""
    try:
        return float(value) / float(divisor)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0