"""
Management command to rebuild topic tracker statistics.
This ensures topics have correct post counts and last post information.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post


class Command(BaseCommand):
    help = 'Rebuild topic tracker statistics (posts_count, first_post_id, last_post_id, last_post_on)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--forum-id',
            type=int,
            help='Rebuild trackers for topics in a specific forum ID only'
        )
        parser.add_argument(
            '--topic-id',
            type=int,
            help='Rebuild trackers for a specific topic ID only'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        forum_id = options.get('forum_id')
        topic_id = options.get('topic_id')
        dry_run = options.get('dry_run')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Get topics to update
        if topic_id:
            try:
                topics = [Topic.objects.get(id=topic_id)]
                self.stdout.write(f'Updating topic ID {topic_id}')
            except Topic.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Topic with ID {topic_id} not found')
                )
                return
        elif forum_id:
            try:
                forum = Forum.objects.get(id=forum_id)
                topics = Topic.objects.filter(forum=forum)
                self.stdout.write(f'Updating {topics.count()} topics in forum: {forum.name}')
            except Forum.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Forum with ID {forum_id} not found')
                )
                return
        else:
            # Get all topics
            topics = Topic.objects.all()
            self.stdout.write(f'Updating {topics.count()} topics')
        
        updated_count = 0
        
        for topic in topics:
            self.stdout.write(f'\nProcessing topic: {topic.subject} (ID: {topic.id})')
            
            # Get actual posts
            posts = Post.objects.filter(topic=topic, approved=True).order_by('created')
            actual_posts_count = posts.count()
            
            # Get first and last posts
            first_post = posts.first()
            last_post = posts.last()
            
            # Show current vs new values
            self.stdout.write(f'  Current values:')
            self.stdout.write(f'    posts_count: {topic.posts_count}')
            self.stdout.write(f'    first_post_id: {topic.first_post_id}')
            self.stdout.write(f'    last_post_id: {topic.last_post_id}')
            self.stdout.write(f'    last_post_on: {topic.last_post_on}')
            
            self.stdout.write(f'  New values:')
            self.stdout.write(f'    posts_count: {actual_posts_count}')
            self.stdout.write(f'    first_post_id: {first_post.id if first_post else None}')
            self.stdout.write(f'    last_post_id: {last_post.id if last_post else None}')
            self.stdout.write(f'    last_post_on: {last_post.created if last_post else None}')
            
            # Check if update is needed
            needs_update = (
                topic.posts_count != actual_posts_count or
                topic.first_post_id != (first_post.id if first_post else None) or
                topic.last_post_id != (last_post.id if last_post else None) or
                topic.last_post_on != (last_post.created if last_post else None)
            )
            
            if needs_update:
                if not dry_run:
                    try:
                        with transaction.atomic():
                            topic.posts_count = actual_posts_count
                            topic.first_post_id = first_post.id if first_post else None
                            topic.last_post_id = last_post.id if last_post else None
                            topic.last_post_on = last_post.created if last_post else None
                            topic.save(update_fields=[
                                'posts_count', 'first_post_id', 
                                'last_post_id', 'last_post_on'
                            ])
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Updated topic: {topic.subject}')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Error updating topic {topic.subject}: {e}')
                        )
                else:
                    self.stdout.write(f'  Would update topic: {topic.subject}')
            else:
                self.stdout.write(f'  No changes needed')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nDRY RUN COMPLETE - No changes were made')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully updated {updated_count} topics')
            )
            
            if updated_count > 0:
                self.stdout.write(
                    'Topic tracker statistics have been rebuilt. '
                    'Now run rebuild_forum_trackers to update forum statistics.'
                )