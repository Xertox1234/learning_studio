"""
Management command to set up anonymous user permissions for forum reading.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import AnonymousUser
from machina.apps.forum.models import Forum
from machina.apps.forum_permission.models import UserForumPermission
from machina.apps.forum_permission.shortcuts import assign_perm


class Command(BaseCommand):
    help = 'Set up anonymous user permissions to read forums'

    def handle(self, *args, **options):
        self.stdout.write('Setting up anonymous user permissions...')
        
        # Get all forums
        forums = Forum.objects.all()
        
        if not forums.exists():
            self.stdout.write(
                self.style.WARNING('No forums found. Create some forums first.')
            )
            return
        
        # Anonymous user permissions (read-only)
        anonymous_perms = [
            'can_see_forum',
            'can_read_forum',
        ]
        
        # Create an anonymous user instance for permission assignment
        anonymous_user = AnonymousUser()
        
        for forum in forums:
            self.stdout.write(f'Setting anonymous permissions for: {forum.name}')
            
            # Remove existing anonymous permissions for this forum
            UserForumPermission.objects.filter(
                forum=forum,
                user=None  # Anonymous user is represented as None
            ).delete()
            
            # Apply read permissions to anonymous users
            for perm_codename in anonymous_perms:
                try:
                    # For Machina, anonymous permissions might need to be set differently
                    # Let's try direct database insertion
                    from machina.apps.forum_permission.models import ForumPermission
                    from django.contrib.auth.models import Permission
                    
                    permission = Permission.objects.get(codename=perm_codename)
                    forum_perm = ForumPermission.objects.get(codename=perm_codename)
                    
                    user_perm, created = UserForumPermission.objects.get_or_create(
                        permission=forum_perm,
                        forum=forum,
                        user=None,  # None represents anonymous user
                        defaults={'has_perm': True}
                    )
                    
                    if created:
                        self.stdout.write(f'  ✓ Granted {perm_codename} to anonymous users')
                    else:
                        self.stdout.write(f'  - {perm_codename} already set for anonymous users')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Could not assign {perm_codename}: {e}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Set up anonymous permissions for {forums.count()} forums'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                'Anonymous users should now be able to read forums!'
            )
        )