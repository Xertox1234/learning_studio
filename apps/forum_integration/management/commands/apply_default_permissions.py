"""
Management command to apply default forum permissions according to settings.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from machina.apps.forum.models import Forum
from machina.apps.forum_permission.models import GroupForumPermission, ForumPermission
from machina.apps.forum_permission.shortcuts import assign_perm
from django.contrib.auth.models import Permission


class Command(BaseCommand):
    help = 'Apply default forum permissions for anonymous and authenticated users'

    def handle(self, *args, **options):
        self.stdout.write('Applying default forum permissions...')
        
        # Get all forums
        forums = Forum.objects.all()
        
        if not forums.exists():
            self.stdout.write(
                self.style.WARNING('No forums found. Create some forums first.')
            )
            return
        
        # Get or create a default group for all authenticated users
        auth_group, created = Group.objects.get_or_create(name='Authenticated Users')
        if created:
            self.stdout.write(f'Created group: {auth_group.name}')
        
        # Anonymous user permissions (from settings)
        anonymous_perms = [
            'can_see_forum',
            'can_read_forum',
        ]
        
        # Authenticated user permissions (from settings)
        auth_perms = [
            'can_see_forum',
            'can_read_forum',
            'can_start_new_topics',
            'can_reply_to_topics',
            'can_edit_own_posts',
            'can_post_without_approval',
            'can_create_polls',
            'can_vote_in_polls',
            'can_download_file',
        ]
        
        for forum in forums:
            self.stdout.write(f'Setting permissions for: {forum.name}')
            
            # Remove existing permissions for this forum to start clean
            GroupForumPermission.objects.filter(forum=forum).delete()
            
            # Apply permissions to authenticated users group
            for perm_codename in auth_perms:
                try:
                    assign_perm(perm_codename, auth_group, forum)
                    self.stdout.write(f'  ✓ Granted {perm_codename} to authenticated users')
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Could not assign {perm_codename}: {e}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Applied permissions to {forums.count()} forums'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                'Note: Anonymous users will inherit read permissions from global settings.'
            )
        )