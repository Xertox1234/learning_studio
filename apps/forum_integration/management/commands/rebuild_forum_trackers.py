"""
Management command to rebuild forum tracker statistics for all forums.
This ensures that all forums show correct last post information.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post


class Command(BaseCommand):
    help = 'Rebuild forum tracker statistics (last_post_id, last_post_on) for all forums'

    def add_arguments(self, parser):
        parser.add_argument(
            '--forum-id',
            type=int,
            help='Rebuild trackers for a specific forum ID only'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        forum_id = options.get('forum_id')
        dry_run = options.get('dry_run')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Get forums to update
        if forum_id:
            try:
                forums = [Forum.objects.get(id=forum_id)]
                self.stdout.write(f'Updating forum ID {forum_id}')
            except Forum.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Forum with ID {forum_id} not found')
                )
                return
        else:
            # Get all forums that can have posts
            forums = Forum.objects.filter(type=Forum.FORUM_POST)
            self.stdout.write(f'Updating {forums.count()} forums')
        
        updated_count = 0
        
        for forum in forums:
            self.stdout.write(f'Processing forum: {forum.name} (ID: {forum.id})')
            
            # Get current values
            old_last_post_id = forum.last_post_id
            old_last_post_on = forum.last_post_on
            
            # Update trackers to calculate new values
            forum.update_trackers()
            
            # Check what changed
            new_last_post_id = forum.last_post_id
            new_last_post_on = forum.last_post_on
            
            # Show changes
            if old_last_post_id != new_last_post_id or old_last_post_on != new_last_post_on:
                self.stdout.write(f'  Changes detected:')
                self.stdout.write(f'    last_post_id: {old_last_post_id} -> {new_last_post_id}')
                self.stdout.write(f'    last_post_on: {old_last_post_on} -> {new_last_post_on}')
                
                if not dry_run:
                    try:
                        with transaction.atomic():
                            forum.save(update_fields=['last_post_id', 'last_post_on'])
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Updated forum: {forum.name}')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Error updating forum {forum.name}: {e}')
                        )
                else:
                    self.stdout.write(f'  Would update forum: {forum.name}')
            else:
                self.stdout.write(f'  No changes needed for: {forum.name}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN COMPLETE - No changes were made')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} forums')
            )
            
            if updated_count > 0:
                self.stdout.write(
                    'Forum tracker statistics have been rebuilt. '
                    'Latest post information should now display correctly on the forum index.'
                )