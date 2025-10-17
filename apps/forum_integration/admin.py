from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import TrustLevel, UserActivity, ReadingProgress, ReviewQueue, ModerationLog, FlaggedContent, ForumCustomization


@admin.register(TrustLevel)
class TrustLevelAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'level_name', 'posts_read', 'days_visited', 'likes_received', 'promoted_at']
    list_filter = ['level', 'promoted_at', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'last_calculated']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'level', 'promoted_at')
        }),
        ('Engagement Metrics', {
            'fields': (
                'posts_read', 'topics_viewed', 'time_read',
                'posts_created', 'topics_created', 
                'likes_given', 'likes_received', 'days_visited'
            )
        }),
        ('Tracking', {
            'fields': ('last_visit_date', 'last_calculated', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def level_name(self, obj):
        colors = {
            0: '#6c757d',  # gray
            1: '#198754',  # green
            2: '#0d6efd',  # blue
            3: '#fd7e14',  # orange
            4: '#dc3545',  # red
        }
        color = colors.get(obj.level, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">TL{} - {}</span>',
            color, obj.level, obj.get_level_display()
        )
    level_name.short_description = 'Trust Level'
    
    actions = ['promote_selected_users']
    
    def promote_selected_users(self, request, queryset):
        promoted_count = 0
        for trust_level in queryset:
            new_level = trust_level.check_for_promotion()
            if new_level:
                trust_level.promote_to_level(new_level)
                promoted_count += 1
        
        self.message_user(
            request,
            f"Successfully promoted {promoted_count} users."
        )
    promote_selected_users.short_description = "Check and promote eligible users"


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'posts_read_today', 'topics_viewed_today', 'time_spent_reading', 'posts_created_today']
    list_filter = ['date', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'completion_percentage', 'time_spent', 'completed', 'last_accessed']
    list_filter = ['completed', 'last_accessed', 'first_read']
    search_fields = ['user__username', 'topic__subject']
    readonly_fields = ['first_read', 'last_accessed']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'topic')
    
    def completion_percentage(self, obj):
        percentage = obj.completion_percentage
        if percentage == 100:
            color = '#198754'  # green
        elif percentage >= 75:
            color = '#fd7e14'  # orange
        elif percentage >= 50:
            color = '#ffc107'  # yellow
        else:
            color = '#dc3545'  # red
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, percentage
        )
    completion_percentage.short_description = 'Progress'


@admin.register(ReviewQueue)
class ReviewQueueAdmin(admin.ModelAdmin):
    list_display = ['id', 'review_type_badge', 'content_preview', 'priority_badge', 'status_badge', 'score', 'age_hours', 'assigned_moderator', 'created_at']
    list_filter = ['status', 'review_type', 'priority', 'created_at', 'assigned_moderator']
    search_fields = ['reason', 'post__content', 'topic__subject', 'reported_user__username', 'reporter__username']
    readonly_fields = ['score', 'created_at', 'updated_at', 'resolved_at']
    
    fieldsets = (
        ('Review Information', {
            'fields': ('review_type', 'status', 'priority', 'score')
        }),
        ('Content References', {
            'fields': ('post', 'topic', 'reported_user')
        }),
        ('Moderation', {
            'fields': ('reporter', 'assigned_moderator', 'reason', 'moderator_notes', 'resolution_notes')
        }),
        ('Metadata', {
            'fields': ('upvotes', 'created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        })
    )
    
    def review_type_badge(self, obj):
        colors = {
            'flagged_post': '#dc3545',
            'new_user_post': '#0d6efd',
            'edited_post': '#ffc107',
            'user_report': '#fd7e14',
            'spam_detection': '#dc3545',
            'trust_level_review': '#6f42c1',
        }
        color = colors.get(obj.review_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">{}</span>',
            color, obj.get_review_type_display()
        )
    review_type_badge.short_description = 'Type'
    
    def priority_badge(self, obj):
        colors = {1: '#dc3545', 2: '#fd7e14', 3: '#ffc107', 4: '#6c757d'}
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">P{}</span>',
            color, obj.priority
        )
    priority_badge.short_description = 'Priority'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'approved': '#198754',
            'rejected': '#dc3545',
            'needs_info': '#0d6efd',
            'escalated': '#fd7e14',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def content_preview(self, obj):
        if obj.post:
            content = str(obj.post.content)[:100] + "..." if len(str(obj.post.content)) > 100 else str(obj.post.content)
            return format_html('<em>Post:</em> {}', content)
        elif obj.topic:
            return format_html('<em>Topic:</em> {}', obj.topic.subject)
        elif obj.reported_user:
            return format_html('<em>User:</em> {}', obj.reported_user.username)
        return '-'
    content_preview.short_description = 'Content'
    
    def age_hours(self, obj):
        return f"{obj.age_in_hours:.1f}h"
    age_hours.short_description = 'Age'
    
    actions = ['approve_selected', 'reject_selected', 'assign_to_me']
    
    def approve_selected(self, request, queryset):
        count = queryset.filter(status='pending').update(status='approved')
        self.message_user(request, f"Approved {count} items.")
    approve_selected.short_description = "Approve selected pending items"
    
    def reject_selected(self, request, queryset):
        count = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f"Rejected {count} items.")
    reject_selected.short_description = "Reject selected pending items"
    
    def assign_to_me(self, request, queryset):
        count = queryset.filter(status='pending').update(assigned_moderator=request.user)
        self.message_user(request, f"Assigned {count} items to you.")
    assign_to_me.short_description = "Assign selected items to me"


@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'action_type_badge', 'moderator', 'target_description', 'reason_preview']
    list_filter = ['action_type', 'timestamp', 'moderator']
    search_fields = ['reason', 'moderator__username', 'target_user__username']
    readonly_fields = ['timestamp', 'details']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Action Details', {
            'fields': ('action_type', 'moderator', 'timestamp', 'reason')
        }),
        ('Targets', {
            'fields': ('review_item', 'target_user', 'target_post', 'target_topic')
        }),
        ('Additional Information', {
            'fields': ('details', 'ip_address'),
            'classes': ('collapse',)
        })
    )
    
    def action_type_badge(self, obj):
        colors = {
            'approve': '#198754',
            'reject': '#dc3545',
            'edit': '#0d6efd',
            'delete': '#dc3545',
            'ban_user': '#dc3545',
            'trust_level_change': '#6f42c1',
            'assign_moderator': '#ffc107',
            'escalate': '#fd7e14',
            'bulk_action': '#6c757d',
        }
        color = colors.get(obj.action_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_action_type_display()
        )
    action_type_badge.short_description = 'Action'
    
    def target_description(self, obj):
        if obj.target_user:
            return f"User: {obj.target_user.username}"
        elif obj.target_post:
            return f"Post: {obj.target_post.id}"
        elif obj.target_topic:
            return f"Topic: {obj.target_topic.subject[:50]}"
        elif obj.review_item:
            return f"Review: {obj.review_item.id}"
        return '-'
    target_description.short_description = 'Target'
    
    def reason_preview(self, obj):
        return obj.reason[:100] + "..." if len(obj.reason) > 100 else obj.reason
    reason_preview.short_description = 'Reason'


@admin.register(FlaggedContent)
class FlaggedContentAdmin(admin.ModelAdmin):
    list_display = ['id', 'reason_badge', 'flagger', 'content_preview', 'is_resolved', 'created_at']
    list_filter = ['reason', 'is_resolved', 'created_at']
    search_fields = ['description', 'flagger__username', 'post__content', 'topic__subject']
    readonly_fields = ['created_at', 'resolved_at']
    
    fieldsets = (
        ('Flag Information', {
            'fields': ('reason', 'description', 'flagger')
        }),
        ('Flagged Content', {
            'fields': ('post', 'topic')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_by', 'resolution_notes', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def reason_badge(self, obj):
        colors = {
            'spam': '#dc3545',
            'inappropriate': '#dc3545',
            'off_topic': '#ffc107',
            'harassment': '#dc3545',
            'duplicate': '#6c757d',
            'misinformation': '#fd7e14',
            'other': '#6c757d',
        }
        color = colors.get(obj.reason, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">{}</span>',
            color, obj.get_reason_display()
        )
    reason_badge.short_description = 'Reason'
    
    def content_preview(self, obj):
        if obj.post:
            content = str(obj.post.content)[:100] + "..." if len(str(obj.post.content)) > 100 else str(obj.post.content)
            return format_html('<em>Post:</em> {}', content)
        elif obj.topic:
            return format_html('<em>Topic:</em> {}', obj.topic.subject)
        return '-'
    content_preview.short_description = 'Content'
    
    actions = ['mark_resolved']
    
    def mark_resolved(self, request, queryset):
        count = queryset.filter(is_resolved=False).update(
            is_resolved=True,
            resolved_by=request.user
        )
        self.message_user(request, f"Marked {count} flags as resolved.")
    mark_resolved.short_description = "Mark selected flags as resolved"


@admin.register(ForumCustomization)
class ForumCustomizationAdmin(admin.ModelAdmin):
    list_display = ['forum', 'icon_preview', 'color_preview', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['forum__name', 'icon', 'color']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Forum', {
            'fields': ('forum',)
        }),
        ('Customization', {
            'fields': ('icon', 'color')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def icon_preview(self, obj):
        return format_html(
            '<span style="font-size: 1.5em;">{}</span>',
            obj.icon
        )
    icon_preview.short_description = 'Icon'

    def color_preview(self, obj):
        return format_html(
            '<span class="{}" style="display: inline-block; padding: 4px 12px; border-radius: 4px; color: white;">{}</span>',
            obj.color, obj.color
        )
    color_preview.short_description = 'Color'


# Register Wagtail pages with admin
# These will be managed through Wagtail's page tree interface
# No additional admin registration needed for Wagtail pages
