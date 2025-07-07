"""
Management command to manually synchronize Django users with Discourse.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.discourse_sso.models import DiscourseUser, DiscourseSsoLog
from apps.discourse_sso.services import DiscourseSSO

User = get_user_model()


class Command(BaseCommand):
    help = 'Synchronize Django users with Discourse'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Sync specific user by ID',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Sync specific user by username',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Sync specific user by email',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sync all users with verified emails',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually syncing',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync even if recently synced',
        )
        parser.add_argument(
            '--max-age',
            type=int,
            default=24,
            help='Only sync users not synced in X hours (default: 24)',
        )

    def handle(self, *args, **options):
        self.sso_service = DiscourseSSO()
        
        if not self.sso_service.secret or not self.sso_service.base_url:
            self.stdout.write(
                self.style.ERROR(
                    'Discourse SSO not configured. Please set DISCOURSE_SSO_SECRET and DISCOURSE_BASE_URL.'
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS('Starting Discourse user synchronization...')
        )

        # Determine which users to sync
        users_to_sync = self.get_users_to_sync(options)
        
        if not users_to_sync:
            self.stdout.write('No users found to sync.')
            return

        self.stdout.write(f'Found {len(users_to_sync)} users to sync.')

        # Sync users
        success_count = 0
        error_count = 0

        for user in users_to_sync:
            try:
                if self.sync_user(user, options['dry_run'], options['force'], options['max_age']):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error syncing user {user.username}: {e}')
                )
                error_count += 1

        # Display summary
        self.display_summary(success_count, error_count, options['dry_run'])

    def get_users_to_sync(self, options):
        """Get the list of users to synchronize based on options."""
        
        if options['user_id']:
            try:
                return [User.objects.get(id=options['user_id'])]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with ID {options['user_id']} not found.")
                )
                return []

        if options['username']:
            try:
                return [User.objects.get(username=options['username'])]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with username '{options['username']}' not found.")
                )
                return []

        if options['email']:
            try:
                return [User.objects.get(email=options['email'])]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with email '{options['email']}' not found.")
                )
                return []

        if options['all']:
            # Get all users with verified emails
            users = User.objects.filter(is_active=True)
            
            # Filter by email verification if the field exists
            if hasattr(User, 'email_verified'):
                users = users.filter(email_verified=True)
            elif hasattr(User, 'emailaddress'):
                # If using django-allauth
                users = users.filter(emailaddress__verified=True)
            
            return list(users.distinct())

        # If no specific option, show help
        self.stdout.write(
            self.style.WARNING(
                'Please specify which users to sync using --user-id, --username, --email, or --all'
            )
        )
        return []

    def sync_user(self, user, dry_run=False, force=False, max_age_hours=24):
        """Sync a single user to Discourse."""
        
        # Check if user has verified email
        if not self.user_has_verified_email(user):
            self.stdout.write(
                self.style.WARNING(f'Skipping {user.username}: email not verified')
            )
            return False

        # Check if recently synced (unless force)
        if not force and self.recently_synced(user, max_age_hours):
            self.stdout.write(
                self.style.WARNING(f'Skipping {user.username}: recently synced')
            )
            return False

        if dry_run:
            self.stdout.write(f'[DRY RUN] Would sync user: {user.username} ({user.email})')
            return True

        # Perform the sync
        try:
            success = self.sso_service.sync_user_to_discourse(user)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Synced user: {user.username}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to sync user: {user.username}')
                )
            
            return success
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error syncing {user.username}: {e}')
            )
            return False

    def user_has_verified_email(self, user):
        """Check if user has a verified email address."""
        
        if hasattr(user, 'email_verified'):
            return user.email_verified
        
        # Check django-allauth email verification
        try:
            from allauth.account.models import EmailAddress
            return EmailAddress.objects.filter(
                user=user, 
                verified=True
            ).exists()
        except ImportError:
            # If allauth not available, assume verified if email exists
            return bool(user.email)

    def recently_synced(self, user, max_age_hours):
        """Check if user was recently synced."""
        
        try:
            discourse_user = DiscourseUser.objects.get(user=user)
            cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
            return discourse_user.last_sync > cutoff_time
        except DiscourseUser.DoesNotExist:
            return False

    def display_summary(self, success_count, error_count, dry_run=False):
        """Display synchronization summary."""
        
        self.stdout.write('\n' + '='*50)
        
        if dry_run:
            self.stdout.write('DRY RUN SUMMARY')
        else:
            self.stdout.write('SYNCHRONIZATION SUMMARY')
        
        self.stdout.write('='*50)
        self.stdout.write(f'Successful syncs: {success_count}')
        self.stdout.write(f'Failed syncs: {error_count}')
        self.stdout.write(f'Total processed: {success_count + error_count}')
        
        if not dry_run:
            # Show recent SSO activity
            recent_logs = DiscourseSsoLog.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=1),
                action='sync'
            ).count()
            
            self.stdout.write(f'Recent sync logs: {recent_logs}')

        self.stdout.write('='*50)

    def display_user_stats(self):
        """Display statistics about Discourse user synchronization."""
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('DISCOURSE USER STATISTICS')
        self.stdout.write('='*50)
        
        total_users = User.objects.filter(is_active=True).count()
        synced_users = DiscourseUser.objects.count()
        verified_users = self.get_verified_user_count()
        
        self.stdout.write(f'Total active users: {total_users}')
        self.stdout.write(f'Users with verified emails: {verified_users}')
        self.stdout.write(f'Users synced to Discourse: {synced_users}')
        
        if verified_users > 0:
            sync_percentage = (synced_users / verified_users) * 100
            self.stdout.write(f'Sync coverage: {sync_percentage:.1f}%')
        
        # Recent sync activity
        recent_syncs = DiscourseSsoLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(days=7),
            action='sync',
            success=True
        ).count()
        
        self.stdout.write(f'Successful syncs (last 7 days): {recent_syncs}')
        
        self.stdout.write('='*50)

    def get_verified_user_count(self):
        """Get count of users with verified emails."""
        
        if hasattr(User, 'email_verified'):
            return User.objects.filter(is_active=True, email_verified=True).count()
        
        try:
            from allauth.account.models import EmailAddress
            verified_emails = EmailAddress.objects.filter(verified=True).values_list('user_id', flat=True)
            return User.objects.filter(is_active=True, id__in=verified_emails).count()
        except ImportError:
            # Fallback: count users with email addresses
            return User.objects.filter(is_active=True, email__isnull=False).exclude(email='').count()