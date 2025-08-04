"""
Management command to set up proper forum permissions for anonymous and authenticated users.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from machina.apps.forum.models import Forum
from machina.apps.forum_permission.models import ForumPermission, UserForumPermission, GroupForumPermission


class Command(BaseCommand):
    help = 'Set up forum permissions: anonymous users can read, authenticated users can post'

    def handle(self, *args, **options):
        self.stdout.write('Setting up forum permissions...')
        
        # Get all forums
        forums = Forum.objects.all()
        
        if not forums.exists():
            self.stdout.write(
                self.style.WARNING('No forums found. Create some forums first.')
            )
            return
        
        # Get or create the registered users group
        registered_group, created = Group.objects.get_or_create(name='Registered Users')
        if created:
            self.stdout.write(f'Created group: {registered_group.name}')
        
        # Define permissions
        read_permissions = ['can_see_forum', 'can_read_forum']
        write_permissions = [
            'can_start_new_topics', 'can_reply_to_topics', 
            'can_edit_own_posts', 'can_post_without_approval',
            'can_create_polls', 'can_vote_in_polls', 'can_download_file'
        ]
        
        # Set up permissions for each forum
        for forum in forums:
            self.stdout.write(f'Setting up permissions for forum: {forum.name}')
            
            # Clear existing permissions for this forum
            UserForumPermission.objects.filter(forum=forum).delete()
            GroupForumPermission.objects.filter(forum=forum).delete()
            
            # Set up read permissions for anonymous users
            for perm_codename in read_permissions:
                try:
                    forum_perm = ForumPermission.objects.get(codename=perm_codename)
                    user_perm, created = UserForumPermission.objects.get_or_create(
                        permission=forum_perm,
                        forum=forum,
                        user=None,  # None for anonymous
                        defaults={
                            'has_perm': True,
                            'anonymous_user': True,
                        }
                    )
                    if created:
                        self.stdout.write(f'  ✓ Added {perm_codename} for anonymous users')
                except ForumPermission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Permission {perm_codename} not found')
                    )
            
            # Set up write permissions for registered users only
            for perm_codename in read_permissions + write_permissions:
                try:
                    forum_perm = ForumPermission.objects.get(codename=perm_codename)
                    group_perm, created = GroupForumPermission.objects.get_or_create(
                        permission=forum_perm,
                        forum=forum,
                        group=registered_group,
                        defaults={
                            'has_perm': True,
                        }
                    )
                    if created and perm_codename in write_permissions:
                        self.stdout.write(f'  ✓ Added {perm_codename} for registered users')
                except ForumPermission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Permission {perm_codename} not found')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up permissions for {forums.count()} forums'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                'Anonymous users can now read forums, registered users can post!'
            )
        )