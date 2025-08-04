"""
Management command to create default badges and categories.
"""

from django.core.management.base import BaseCommand
from apps.forum_integration.gamification_service import GamificationService


class Command(BaseCommand):
    help = 'Create default badge categories and badges for the forum'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing badges and recreate them',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating default badges...'))
        
        if options['reset']:
            from apps.forum_integration.models import Badge, BadgeCategory
            Badge.objects.all().delete()
            BadgeCategory.objects.all().delete()
            self.stdout.write(self.style.WARNING('Deleted existing badges and categories'))
        
        created_count = GamificationService.create_default_badges()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} default badges'
            )
        )