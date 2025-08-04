"""
Management command to calculate and update trust levels for all users
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.forum_integration.models import TrustLevel

User = get_user_model()


class Command(BaseCommand):
    help = 'Calculate and update trust levels for all users based on their activity'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Update trust level for specific user (username)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about each user',
        )
    
    def handle(self, *args, **options):
        if options['user']:
            # Update specific user
            try:
                user = User.objects.get(username=options['user'])
                self.update_user_trust_level(user, options)
            except User.DoesNotExist:
                raise CommandError(f'User "{options["user"]}" does not exist')
        else:
            # Update all users
            self.update_all_trust_levels(options)
    
    def update_all_trust_levels(self, options):
        """Update trust levels for all users"""
        users_with_trust_levels = User.objects.filter(trust_level__isnull=False)
        users_without_trust_levels = User.objects.filter(trust_level__isnull=True)
        
        # Create trust levels for users who don't have them
        for user in users_without_trust_levels:
            if not options['dry_run']:
                TrustLevel.objects.create(user=user, level=0)
            if options['verbose']:
                self.stdout.write(f'Created trust level for {user.username}')
        
        # Update existing trust levels
        promoted_count = 0
        total_users = users_with_trust_levels.count() + users_without_trust_levels.count()
        
        for user in User.objects.filter(trust_level__isnull=False):
            was_promoted = self.update_user_trust_level(user, options)
            if was_promoted:
                promoted_count += 1
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would promote {promoted_count} out of {total_users} users'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully promoted {promoted_count} out of {total_users} users'
                )
            )
    
    def update_user_trust_level(self, user, options):
        """Update trust level for a specific user"""
        try:
            trust_level = user.trust_level
        except TrustLevel.DoesNotExist:
            if not options['dry_run']:
                trust_level = TrustLevel.objects.create(user=user, level=0)
            else:
                trust_level = TrustLevel(user=user, level=0)
        
        old_level = trust_level.level
        new_level = trust_level.check_for_promotion()
        
        if new_level and new_level > old_level:
            if options['verbose']:
                self.stdout.write(
                    f'{user.username}: TL{old_level} -> TL{new_level} '
                    f'(Posts read: {trust_level.posts_read}, '
                    f'Days visited: {trust_level.days_visited}, '
                    f'Likes received: {trust_level.likes_received})'
                )
            
            if not options['dry_run']:
                trust_level.promote_to_level(new_level)
            
            return True
        
        elif options['verbose']:
            requirements = self.get_next_level_requirements(trust_level)
            self.stdout.write(
                f'{user.username}: TL{old_level} (no promotion) - {requirements}'
            )
        
        return False
    
    def get_next_level_requirements(self, trust_level):
        """Get requirements for next level as a string"""
        current_level = trust_level.level
        
        if current_level == 0:
            posts_needed = max(0, 10 - trust_level.posts_read)
            time_needed = max(0, 10 - (trust_level.time_read.total_seconds() / 60))
            return f'Needs {posts_needed} more posts read, {time_needed:.1f} more minutes reading'
        
        elif current_level == 1:
            days_needed = max(0, 15 - trust_level.days_visited)
            posts_needed = max(0, 100 - trust_level.posts_read)
            likes_needed = max(0, 1 - trust_level.likes_received)
            return f'Needs {days_needed} more days visited, {posts_needed} more posts read, {likes_needed} more likes'
        
        elif current_level == 2:
            days_needed = max(0, 50 - trust_level.days_visited)
            posts_needed = max(0, 500 - trust_level.posts_read)
            likes_received_needed = max(0, 10 - trust_level.likes_received)
            likes_given_needed = max(0, 30 - trust_level.likes_given)
            return (f'Needs {days_needed} more days visited, {posts_needed} more posts read, '
                   f'{likes_received_needed} more likes received, {likes_given_needed} more likes given')
        
        elif current_level == 3:
            return 'Requires manual promotion to TL4 by staff'
        
        else:
            return 'Maximum level reached'