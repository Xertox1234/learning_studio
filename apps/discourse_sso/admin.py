"""
Django admin configuration for Discourse SSO models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import DiscourseUser, DiscourseGroupMapping, DiscourseSsoLog


@admin.register(DiscourseUser)
class DiscourseUserAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'discourse_username', 'discourse_user_id', 
        'sync_enabled', 'last_sync', 'created_at'
    ]
    list_filter = ['sync_enabled', 'last_sync', 'created_at']
    search_fields = [
        'user__username', 'user__email', 'discourse_username', 'discourse_user_id'
    ]
    readonly_fields = ['created_at', 'updated_at', 'last_sync']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'discourse_username', 'discourse_user_id')
        }),
        ('Sync Settings', {
            'fields': ('sync_enabled', 'last_sync')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_link.short_description = 'Django User'
    user_link.admin_order_field = 'user__username'
    
    actions = ['sync_to_discourse']
    
    def sync_to_discourse(self, request, queryset):
        """Admin action to manually sync users to Discourse."""
        from .services import DiscourseSSO
        sso_service = DiscourseSSO()
        
        success_count = 0
        for discourse_user in queryset:
            if sso_service.sync_user_to_discourse(discourse_user.user):
                success_count += 1
        
        self.message_user(
            request,
            f"Successfully synced {success_count} out of {queryset.count()} users."
        )
    sync_to_discourse.short_description = "Sync selected users to Discourse"


@admin.register(DiscourseGroupMapping)
class DiscourseGroupMappingAdmin(admin.ModelAdmin):
    list_display = [
        'django_group_link', 'discourse_group_name', 
        'auto_sync', 'created_at'
    ]
    list_filter = ['auto_sync', 'created_at']
    search_fields = ['django_group__name', 'discourse_group_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Group Mapping', {
            'fields': ('django_group', 'discourse_group_name', 'auto_sync')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def django_group_link(self, obj):
        if obj.django_group:
            url = reverse('admin:auth_group_change', args=[obj.django_group.pk])
            return format_html('<a href="{}">{}</a>', url, obj.django_group.name)
        return '-'
    django_group_link.short_description = 'Django Group'
    django_group_link.admin_order_field = 'django_group__name'


@admin.register(DiscourseSsoLog)
class DiscourseSsoLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'user_link', 'action', 'success_icon', 
        'ip_address', 'nonce_short'
    ]
    list_filter = [
        'action', 'success', 'timestamp'
    ]
    search_fields = [
        'user__username', 'user__email', 'ip_address', 
        'nonce', 'error_message'
    ]
    readonly_fields = [
        'timestamp', 'user', 'action', 'success', 'error_message',
        'ip_address', 'user_agent', 'nonce'
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('timestamp', 'user', 'action', 'success')
        }),
        ('Request Details', {
            'fields': ('ip_address', 'user_agent', 'nonce')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return 'Anonymous'
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def success_icon(self, obj):
        if obj.success:
            return format_html(
                '<span style="color: green;">✓</span>'
            )
        else:
            return format_html(
                '<span style="color: red;" title="{}">✗</span>',
                obj.error_message[:100] if obj.error_message else 'Unknown error'
            )
    success_icon.short_description = 'Success'
    success_icon.admin_order_field = 'success'
    
    def nonce_short(self, obj):
        if obj.nonce:
            return obj.nonce[:8] + '...' if len(obj.nonce) > 8 else obj.nonce
        return '-'
    nonce_short.short_description = 'Nonce'
    
    def has_add_permission(self, request):
        """Disable adding logs manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make logs read-only."""
        return False