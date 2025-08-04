"""
Management command to show trust level statistics
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg
from apps.forum_integration.models import TrustLevel

User = get_user_model()


class Command(BaseCommand):
    help = 'Show trust level statistics and distribution'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed breakdown by level',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Trust Level Statistics'))
        self.stdout.write('=' * 50)
        
        # Overall statistics
        total_users = User.objects.count()
        users_with_trust_levels = TrustLevel.objects.count()
        
        self.stdout.write(f'Total Users: {total_users}')
        self.stdout.write(f'Users with Trust Levels: {users_with_trust_levels}')
        self.stdout.write(f'Coverage: {(users_with_trust_levels/total_users*100):.1f}%')
        self.stdout.write('')
        
        # Trust level distribution
        level_distribution = TrustLevel.objects.values('level').annotate(
            count=Count('level')
        ).order_by('level')
        
        self.stdout.write('Trust Level Distribution:')
        for level_data in level_distribution:
            level = level_data['level']
            count = level_data['count']
            percentage = (count / users_with_trust_levels * 100) if users_with_trust_levels else 0
            level_name = dict(TrustLevel.TRUST_LEVELS)[level]
            
            self.stdout.write(f'  TL{level} ({level_name}): {count} users ({percentage:.1f}%)')
        
        self.stdout.write('')
        
        # Average metrics
        avg_metrics = TrustLevel.objects.aggregate(
            avg_posts_read=Avg('posts_read'),
            avg_topics_viewed=Avg('topics_viewed'),
            avg_days_visited=Avg('days_visited'),
            avg_likes_received=Avg('likes_received'),
            avg_likes_given=Avg('likes_given'),
        )
        
        self.stdout.write('Average Metrics:')
        self.stdout.write(f'  Posts Read: {avg_metrics["avg_posts_read"]:.1f}')
        self.stdout.write(f'  Topics Viewed: {avg_metrics["avg_topics_viewed"]:.1f}')
        self.stdout.write(f'  Days Visited: {avg_metrics["avg_days_visited"]:.1f}')
        self.stdout.write(f'  Likes Received: {avg_metrics["avg_likes_received"]:.1f}')
        self.stdout.write(f'  Likes Given: {avg_metrics["avg_likes_given"]:.1f}')
        
        if options['detailed']:
            self.stdout.write('')
            self.show_detailed_breakdown()
    
    def show_detailed_breakdown(self):
        """Show detailed breakdown by trust level"""
        self.stdout.write('Detailed Breakdown by Trust Level:')
        self.stdout.write('-' * 50)
        
        for level, level_name in TrustLevel.TRUST_LEVELS:
            trust_levels = TrustLevel.objects.filter(level=level)
            count = trust_levels.count()
            
            if count == 0:
                continue
            
            avg_metrics = trust_levels.aggregate(
                avg_posts_read=Avg('posts_read'),
                avg_topics_viewed=Avg('topics_viewed'),
                avg_days_visited=Avg('days_visited'),
                avg_likes_received=Avg('likes_received'),
                avg_likes_given=Avg('likes_given'),
            )
            
            self.stdout.write(f'TL{level} - {level_name} ({count} users):')
            self.stdout.write(f'  Avg Posts Read: {avg_metrics["avg_posts_read"]:.1f}')
            self.stdout.write(f'  Avg Topics Viewed: {avg_metrics["avg_topics_viewed"]:.1f}')
            self.stdout.write(f'  Avg Days Visited: {avg_metrics["avg_days_visited"]:.1f}')
            self.stdout.write(f'  Avg Likes Received: {avg_metrics["avg_likes_received"]:.1f}')
            self.stdout.write(f'  Avg Likes Given: {avg_metrics["avg_likes_given"]:.1f}')
            self.stdout.write('')
        
        # Show users eligible for promotion
        eligible_count = 0
        for trust_level in TrustLevel.objects.filter(level__lt=3):  # TL0-2 can auto-promote
            if trust_level.check_for_promotion():
                eligible_count += 1
        
        if eligible_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'{eligible_count} users are eligible for promotion!'
                )
            )
            self.stdout.write('Run "python manage.py calculate_trust_levels" to promote them.')
        else:
            self.stdout.write(
                self.style.SUCCESS('No users are currently eligible for promotion.')
            )