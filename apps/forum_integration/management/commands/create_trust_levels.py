"""
Management command to create trust level entries for existing users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.forum_integration.models import TrustLevel

User = get_user_model()


class Command(BaseCommand):
    help = 'Create trust level entries for all existing users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--initial-level',
            type=int,
            default=0,
            help='Initial trust level for existing users (default: 0)',
        )
    
    def handle(self, *args, **options):
        initial_level = options['initial_level']
        
        # Find users without trust levels
        users_without_trust_levels = User.objects.filter(trust_level__isnull=True)
        
        created_count = 0
        for user in users_without_trust_levels:
            trust_level, created = TrustLevel.objects.get_or_create(
                user=user,
                defaults={'level': initial_level}
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created TL{initial_level} for {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created trust levels for {created_count} users'
            )
        )
        
        # Show summary
        total_users = User.objects.count()
        users_with_trust_levels = User.objects.filter(trust_level__isnull=False).count()
        
        self.stdout.write(f'Total users: {total_users}')
        self.stdout.write(f'Users with trust levels: {users_with_trust_levels}')
        
        if users_with_trust_levels < total_users:
            self.stdout.write(
                self.style.WARNING(
                    f'{total_users - users_with_trust_levels} users still need trust levels'
                )
            )