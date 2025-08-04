"""
Management command to add performance indexes to django-machina tables.
Since these are third-party tables, we use a management command instead of migrations.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Add performance indexes to django-machina forum tables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what indexes would be created without actually creating them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Define the indexes to create
        indexes = [
            # Forum Post Indexes - Critical for forum performance
            {
                'name': 'idx_forum_post_approved_created',
                'table': 'forum_conversation_post',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forum_post_approved_created ON forum_conversation_post (approved, created DESC) WHERE approved = true;'
            },
            {
                'name': 'idx_forum_post_topic_approved',
                'table': 'forum_conversation_post',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forum_post_topic_approved ON forum_conversation_post (topic_id, approved, created DESC);'
            },
            {
                'name': 'idx_forum_post_poster_created',
                'table': 'forum_conversation_post',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forum_post_poster_created ON forum_conversation_post (poster_id, created DESC) WHERE approved = true;'
            },
            
            # Forum Topic Indexes - Essential for topic listing and filtering
            {
                'name': 'idx_forum_topic_forum_approved',
                'table': 'forum_conversation_topic',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forum_topic_forum_approved ON forum_conversation_topic (forum_id, approved, last_post_on DESC);'
            },
            {
                'name': 'idx_forum_topic_approved_created',
                'table': 'forum_conversation_topic',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forum_topic_approved_created ON forum_conversation_topic (approved, created DESC) WHERE approved = true;'
            },
            {
                'name': 'idx_forum_topic_poster_approved',
                'table': 'forum_conversation_topic',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forum_topic_poster_approved ON forum_conversation_topic (poster_id, approved, created DESC);'
            },
            {
                'name': 'idx_forum_topic_sticky_approved',
                'table': 'forum_conversation_topic',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forum_topic_sticky_approved ON forum_conversation_topic (type, approved, last_post_on DESC) WHERE type = 1 AND approved = true;'
            },
            
            # Forum Indexes - For forum navigation and statistics
            {
                'name': 'idx_forum_type_parent',
                'table': 'forum_forum',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forum_type_parent ON forum_forum (type, parent_id);'
            },
            {
                'name': 'idx_forum_parent_position',
                'table': 'forum_forum',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forum_parent_position ON forum_forum (parent_id, display_order) WHERE parent_id IS NOT NULL;'
            },
            
            # Forum Permission Indexes - For permission checking
            {
                'name': 'idx_forum_permission_forum_user',
                'table': 'forum_permission_forumpermission',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forum_permission_forum_user ON forum_permission_forumpermission (forum_id, user_id) WHERE user_id IS NOT NULL;'
            },
            {
                'name': 'idx_forum_permission_forum_group',
                'table': 'forum_permission_forumpermission',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forum_permission_forum_group ON forum_permission_forumpermission (forum_id, group_id) WHERE group_id IS NOT NULL;'
            },
            
            # Forum Tracking Indexes - For read/unread functionality
            {
                'name': 'idx_forum_topicread_user_topic',
                'table': 'forum_tracking_topicreadtrack',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forum_topicread_user_topic ON forum_tracking_topicreadtrack (user_id, topic_id);'
            },
            {
                'name': 'idx_forum_forumread_user_forum',
                'table': 'forum_tracking_forumreadtrack',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_forum_forumread_user_forum ON forum_tracking_forumreadtrack (user_id, forum_id);'
            },
        ]
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN: The following indexes would be created:')
            )
            for index in indexes:
                self.stdout.write(f"  - {index['name']} on {index['table']}")
            return
        
        with connection.cursor() as cursor:
            created_count = 0
            for index in indexes:
                try:
                    self.stdout.write(f"Creating index {index['name']}...")
                    cursor.execute(index['sql'])
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Created {index['name']}")
                    )
                except Exception as e:
                    if 'already exists' in str(e).lower():
                        self.stdout.write(
                            self.style.WARNING(f"  - {index['name']} already exists")
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"  ✗ Failed to create {index['name']}: {e}")
                        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} new indexes for forum performance.'
            )
        )
        
        # Provide usage recommendations
        self.stdout.write('\n' + '='*60)
        self.stdout.write('PERFORMANCE RECOMMENDATIONS:')
        self.stdout.write('='*60)
        self.stdout.write('1. Monitor query performance with EXPLAIN ANALYZE')
        self.stdout.write('2. Run VACUUM ANALYZE after creating indexes')
        self.stdout.write('3. Monitor index usage with pg_stat_user_indexes')
        self.stdout.write('4. Consider partitioning for very large tables')
        self.stdout.write('5. Regular maintenance: REINDEX if fragmentation occurs')