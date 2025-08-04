"""
Management command to test badge notifications and celebrations.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.forum_integration.models import Badge, UserBadge
from apps.forum_integration.notification_service import NotificationService
from apps.forum_integration.gamification_service import GamificationService

User = get_user_model()


class Command(BaseCommand):
    help = 'Test badge notification system by awarding test badges'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to award test badge to',
            required=True
        )
        parser.add_argument(
            '--badge-name',
            type=str,
            help='Name of badge to award (default: First Post)',
            default='First Post'
        )

    def handle(self, *args, **options):
        username = options['username']
        badge_name = options['badge_name']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" not found')
            )
            return
        
        try:
            badge = Badge.objects.get(name=badge_name)
        except Badge.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Badge "{badge_name}" not found')
            )
            # List available badges
            available_badges = Badge.objects.values_list('name', flat=True)
            self.stdout.write('Available badges:')
            for badge_name in available_badges:
                self.stdout.write(f'  - {badge_name}')
            return
        
        # Check if user already has this badge
        if UserBadge.objects.filter(user=user, badge=badge).exists():
            self.stdout.write(
                self.style.WARNING(f'User {username} already has badge "{badge.name}"')
            )
            return
        
        # Award the badge
        user_badge = UserBadge.objects.create(
            user=user,
            badge=badge,
            notification_sent=False  # Ensure notification will be sent
        )
        
        # Send notification
        NotificationService.notify_badge_earned(user_badge)
        
        # Award points
        GamificationService.award_points(user, 'badge_earned', amount=badge.points_awarded)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully awarded badge "{badge.name}" to user {username}'
            )
        )
        
        # Test milestone notification
        try:
            user_points = user.points
            if user_points.total_points >= 100:
                NotificationService.notify_milestone_reached(user, 'points', 100)
                self.stdout.write(
                    self.style.SUCCESS('Also sent milestone notification for 100 points')
                )
        except:
            pass
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Badge notification sent! Check the achievement dashboard or WebSocket connection.'
            )
        )