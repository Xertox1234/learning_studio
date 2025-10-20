"""
Performance tests for forum topic pagination.

Ensures database-level pagination prevents OOM issues at scale.
"""

from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.contrib.auth import get_user_model
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post
from rest_framework.test import APIClient
import tracemalloc

User = get_user_model()


class ForumPaginationPerformanceTests(TestCase):
    """
    Tests to ensure forum pagination uses database-level LIMIT/OFFSET.

    Related: Todo #021 - Fix Forum Topics In-Memory Pagination (OOM Risk)
    """

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='password123'
        )

    def test_pagination_uses_database_limit_offset(self):
        """
        Ensure topic pagination uses SQL LIMIT/OFFSET, not in-memory slicing.

        This prevents loading all topics into memory.
        Related: CVE-2025-PERF-001 (OOM risk)
        """
        # Create test forum
        forum = Forum.objects.create(
            name="Performance Test Forum",
            slug="perf-test",
            type=Forum.FORUM_POST
        )

        # Create 100 topics (mix of regular and pinned)
        for i in range(100):
            topic_type = Topic.TOPIC_STICKY if i < 5 else Topic.TOPIC_POST
            topic = Topic.objects.create(
                forum=forum,
                subject=f"Test Topic {i}",
                type=topic_type,
                poster=self.user,
                approved=True
            )

            # Create first post (required by machina)
            Post.objects.create(
                topic=topic,
                subject=topic.subject,
                content=f"Content for topic {i}",
                poster=self.user,
                approved=True
            )

        # Count queries for first page
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(f'/api/v1/forums/perf-test/topics/?page=1&page_size=20')

        self.assertEqual(response.status_code, 200)

        # Verify SQL uses LIMIT
        topic_query = None
        for query in ctx.captured_queries:
            sql = query['sql'].upper()
            if 'FROM "FORUM_CONVERSATION_TOPIC"' in sql or 'FROM "MACHINA_FORUM_CONVERSATION_TOPIC"' in sql:
                topic_query = sql
                break

        self.assertIsNotNone(topic_query, "Could not find topic query")
        self.assertIn('LIMIT', topic_query, "Query should use LIMIT (database-level pagination)")

        # Query count should be reasonable (not proportional to topic count)
        # Expected queries:
        # 1. Get forum by slug
        # 2. Count topics (for pagination metadata)
        # 3. Get page of topics with prefetch
        # 4-6. Prefetch related data (poster, trust_level, last_post)
        query_count = len(ctx.captured_queries)
        self.assertLessEqual(
            query_count,
            10,
            f"Too many queries ({query_count}). Should use database-level pagination."
        )

    def test_pagination_memory_efficiency(self):
        """
        Ensure pagination doesn't load all topics into memory.

        Memory usage should be constant regardless of total topic count.
        """
        # Create test forum
        forum = Forum.objects.create(
            name="Memory Test Forum",
            slug="memory-test",
            type=Forum.FORUM_POST
        )

        # Create 500 topics
        for i in range(500):
            topic = Topic.objects.create(
                forum=forum,
                subject=f"Topic {i}",
                type=Topic.TOPIC_POST,
                poster=self.user,
                approved=True
            )

            Post.objects.create(
                topic=topic,
                subject=topic.subject,
                content=f"Content {i}",
                poster=self.user,
                approved=True
            )

        # Measure memory for page 1
        tracemalloc.start()
        response = self.client.get(f'/api/v1/forums/memory-test/topics/?page=1&page_size=20')
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.assertEqual(response.status_code, 200)

        # Peak memory should be <10MB (not proportional to 500 topics)
        peak_mb = peak / 1024 / 1024
        self.assertLess(
            peak_mb,
            10,
            f"Memory usage too high: {peak_mb:.1f}MB. "
            f"Should use database-level pagination, not in-memory lists."
        )

    def test_pinned_topics_appear_first(self):
        """
        Pinned topics should appear first even with database pagination.

        Tests the pin_priority annotation works correctly.
        """
        # Create test forum
        forum = Forum.objects.create(
            name="Pinned Test Forum",
            slug="pinned-test",
            type=Forum.FORUM_POST
        )

        # Create topics in specific order to test sorting
        # Create regular topics first
        regular1 = Topic.objects.create(
            forum=forum,
            subject="Regular Topic 1",
            type=Topic.TOPIC_POST,
            poster=self.user,
            approved=True
        )
        Post.objects.create(
            topic=regular1,
            subject=regular1.subject,
            content="Content",
            poster=self.user,
            approved=True
        )

        # Create sticky topic
        sticky = Topic.objects.create(
            forum=forum,
            subject="Sticky Topic",
            type=Topic.TOPIC_STICKY,
            poster=self.user,
            approved=True
        )
        Post.objects.create(
            topic=sticky,
            subject=sticky.subject,
            content="Content",
            poster=self.user,
            approved=True
        )

        # Create announcement
        announce = Topic.objects.create(
            forum=forum,
            subject="Announcement",
            type=Topic.TOPIC_ANNOUNCE,
            poster=self.user,
            approved=True
        )
        Post.objects.create(
            topic=announce,
            subject=announce.subject,
            content="Content",
            poster=self.user,
            approved=True
        )

        # Create another regular topic
        regular2 = Topic.objects.create(
            forum=forum,
            subject="Regular Topic 2",
            type=Topic.TOPIC_POST,
            poster=self.user,
            approved=True
        )
        Post.objects.create(
            topic=regular2,
            subject=regular2.subject,
            content="Content",
            poster=self.user,
            approved=True
        )

        # Get topics
        response = self.client.get('/api/v1/forums/pinned-test/topics/')
        self.assertEqual(response.status_code, 200)

        topics = response.json()['results']

        # First two topics should be pinned (sticky or announce)
        pinned_subjects = {topics[0]['subject'], topics[1]['subject']}
        self.assertEqual(
            pinned_subjects,
            {'Sticky Topic', 'Announcement'},
            "Pinned topics should appear first"
        )

        # Last two should be regular topics
        regular_subjects = {topics[2]['subject'], topics[3]['subject']}
        self.assertEqual(
            regular_subjects,
            {'Regular Topic 1', 'Regular Topic 2'},
            "Regular topics should appear after pinned"
        )

    def test_pagination_metadata_accuracy(self):
        """
        Pagination metadata should be accurate with database-level pagination.

        Tests total_count, total_pages, has_next, has_previous.
        """
        # Create test forum
        forum = Forum.objects.create(
            name="Metadata Test Forum",
            slug="metadata-test",
            type=Forum.FORUM_POST
        )

        # Create exactly 45 topics
        for i in range(45):
            topic = Topic.objects.create(
                forum=forum,
                subject=f"Topic {i}",
                type=Topic.TOPIC_POST,
                poster=self.user,
                approved=True
            )
            Post.objects.create(
                topic=topic,
                subject=topic.subject,
                content="Content",
                poster=self.user,
                approved=True
            )

        # Test page 1
        response = self.client.get('/api/v1/forums/metadata-test/topics/?page=1&page_size=20')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        pagination = data['pagination']

        self.assertEqual(pagination['total_count'], 45)
        self.assertEqual(pagination['total_pages'], 3)  # 45 / 20 = 2.25 → 3 pages
        self.assertEqual(pagination['current_page'], 1)
        self.assertTrue(pagination['has_next'])
        self.assertFalse(pagination['has_previous'])

        # Test page 2
        response = self.client.get('/api/v1/forums/metadata-test/topics/?page=2&page_size=20')
        data = response.json()
        pagination = data['pagination']

        self.assertEqual(pagination['current_page'], 2)
        self.assertTrue(pagination['has_next'])
        self.assertTrue(pagination['has_previous'])

        # Test page 3 (last page)
        response = self.client.get('/api/v1/forums/metadata-test/topics/?page=3&page_size=20')
        data = response.json()
        pagination = data['pagination']

        self.assertEqual(pagination['current_page'], 3)
        self.assertFalse(pagination['has_next'])
        self.assertTrue(pagination['has_previous'])
        self.assertEqual(len(data['results']), 5)  # 45 - (2 * 20) = 5 topics on last page
