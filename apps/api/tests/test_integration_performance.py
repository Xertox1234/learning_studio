"""
Performance Integration Test.

Validates performance fixes including:
- Forum pagination (N+1 query prevention)
- Query count optimization
- Wagtail API N+1 prevention
"""

from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.contrib.auth import get_user_model
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post

User = get_user_model()


@override_settings(DEBUG=True)  # Required for query logging
class PerformanceIntegrationTest(TestCase):
    """Validate performance fixes (N+1, pagination)."""

    def setUp(self):
        """Set up test data."""
        # Create test user for posts
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_forum_pagination_query_count(self):
        """
        Forum pagination should use constant queries regardless of topic count.

        Validates fix for #021 - Forum Pagination Memory Issue.
        """
        # Create root forum category
        category = Forum.objects.create(
            name="Test Category",
            slug="test-category",
            type=Forum.FORUM_CAT
        )

        # Create forum under category
        forum = Forum.objects.create(
            name="Test Forum",
            slug="test-forum",
            type=Forum.FORUM_POST,
            parent=category
        )

        # Create 1000 topics to test pagination scalability
        topics = []
        for i in range(1000):
            topic = Topic.objects.create(
                forum=forum,
                subject=f"Topic {i}",
                poster=self.user,
                type=Topic.TOPIC_POST if i > 10 else Topic.TOPIC_STICKY
            )
            topics.append(topic)

            # Create first post for each topic
            Post.objects.create(
                topic=topic,
                poster=self.user,
                subject=f"Topic {i}",
                content=f"This is test topic {i}",
                approved=True
            )

        # Test page 1 query count
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(f'/api/v1/forums/{forum.slug}/topics/?page=1')

        page1_queries = len(ctx.captured_queries)
        self.assertEqual(response.status_code, 200)

        # Test page 50 query count
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(f'/api/v1/forums/{forum.slug}/topics/?page=50')

        page50_queries = len(ctx.captured_queries)
        self.assertEqual(response.status_code, 200)

        # Query count should be constant across pages
        self.assertEqual(page1_queries, page50_queries,
            f"Query count varies by page: page1={page1_queries}, page50={page50_queries}")

        # Should be reasonable number of queries (< 15 is acceptable)
        self.assertLessEqual(page1_queries, 15,
            f"Too many queries: {page1_queries}. Expected < 15.")

        # Verify pagination is working (using LIMIT/OFFSET)
        # Check the last SELECT query which should be the topics query
        topics_queries = [
            q for q in ctx.captured_queries
            if 'SELECT' in q['sql'] and 'forum_conversation_topic' in q['sql']
        ]

        if topics_queries:
            sql = topics_queries[-1]['sql'].upper()
            self.assertIn('LIMIT', sql,
                "Pagination should use LIMIT")
            self.assertIn('OFFSET', sql,
                "Pagination should use OFFSET")

    def test_wagtail_blog_query_count(self):
        """
        Wagtail blog listing should use optimized queries.

        Validates fix for #025 - N+1 Query Storm.
        """
        try:
            from apps.blog.models import BlogPage, HomePage, BlogCategory
            from wagtail.models import Page, Site

            # Create root and home page
            root_page = Page.objects.filter(depth=1).first()
            if not root_page:
                root_page = Page.add_root(title="Root", slug="root")

            site, created = Site.objects.get_or_create(
                is_default_site=True,
                defaults={
                    'hostname': 'localhost',
                    'root_page': root_page
                }
            )

            home_page = root_page.add_child(instance=HomePage(
                title="Home",
                slug="home"
            ))

            # Create categories
            categories = []
            for i in range(3):
                category = BlogCategory.objects.create(
                    name=f"Category {i}",
                    slug=f"category-{i}"
                )
                categories.append(category)

            # Create 50 blog posts with categories and tags
            for i in range(50):
                blog_page = home_page.add_child(instance=BlogPage(
                    title=f"Blog Post {i}",
                    slug=f"blog-post-{i}",
                    intro=f"Intro for post {i}",
                    body=f"Content for post {i}"
                ))

                # Add categories
                blog_page.categories.add(categories[i % 3])
                blog_page.save_revision().publish()

            # Test query count for blog listing
            with CaptureQueriesContext(connection) as ctx:
                response = self.client.get('/api/v1/blog/')

            query_count = len(ctx.captured_queries)
            self.assertEqual(response.status_code, 200)

            # Should use prefetch_related to prevent N+1
            # Expected: ~5-12 queries (base query + prefetches)
            # NOT: 50+ queries (one per blog post for categories)
            self.assertLessEqual(query_count, 15,
                f"Too many queries: {query_count}. Likely N+1 issue.")

        except ImportError:
            self.skipTest("Wagtail models not available")

    def test_wagtail_courses_query_count(self):
        """
        Wagtail course listing should use optimized queries.

        Validates fix for #025 - N+1 Query Storm.
        """
        try:
            from apps.blog.models import CoursePage, HomePage
            from wagtail.models import Page, Site

            # Create root and home page
            root_page = Page.objects.filter(depth=1).first()
            if not root_page:
                root_page = Page.add_root(title="Root", slug="root")

            site, created = Site.objects.get_or_create(
                is_default_site=True,
                defaults={
                    'hostname': 'localhost',
                    'root_page': root_page
                }
            )

            home_page = root_page.add_child(instance=HomePage(
                title="Home",
                slug="home"
            ))

            # Create 30 courses
            for i in range(30):
                course_page = home_page.add_child(instance=CoursePage(
                    title=f"Course {i}",
                    slug=f"course-{i}",
                    intro=f"Intro for course {i}"
                ))
                course_page.save_revision().publish()

            # Test query count for course listing
            with CaptureQueriesContext(connection) as ctx:
                response = self.client.get('/api/v1/learning/courses/')

            query_count = len(ctx.captured_queries)
            self.assertEqual(response.status_code, 200)

            # Should use select_related/prefetch_related
            # Expected: ~5-12 queries
            # NOT: 30+ queries
            self.assertLessEqual(query_count, 15,
                f"Too many queries: {query_count}. Likely N+1 issue.")

        except ImportError:
            self.skipTest("Wagtail models not available")

    def test_forum_statistics_performance(self):
        """
        Forum statistics should execute efficiently.

        Validates that statistics calculations don't cause N+1 queries.
        """
        # Create 10 forums with topics and posts
        for f in range(10):
            category = Forum.objects.create(
                name=f"Category {f}",
                slug=f"category-{f}",
                type=Forum.FORUM_CAT
            )

            forum = Forum.objects.create(
                name=f"Forum {f}",
                slug=f"forum-{f}",
                type=Forum.FORUM_POST,
                parent=category
            )

            # Create 10 topics per forum
            for t in range(10):
                topic = Topic.objects.create(
                    forum=forum,
                    subject=f"Topic {t} in Forum {f}",
                    poster=self.user,
                    type=Topic.TOPIC_POST
                )

                # Create 5 posts per topic
                for p in range(5):
                    Post.objects.create(
                        topic=topic,
                        poster=self.user,
                        subject=f"Post {p}",
                        content=f"Content {p}",
                        approved=True
                    )

        # Test forum listing with statistics
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get('/api/v1/forums/')

        query_count = len(ctx.captured_queries)
        self.assertEqual(response.status_code, 200)

        # Should be efficient even with 10 forums
        # Expected: ~10-20 queries (with aggregation)
        # NOT: 100+ queries (one per forum/topic/post)
        self.assertLessEqual(query_count, 25,
            f"Too many queries for forum listing: {query_count}")

    def test_pagination_page_size_limits(self):
        """
        Validate that pagination respects page size limits.

        Prevents memory exhaustion attacks via large page_size parameters.
        """
        # Create forum with 100 topics
        category = Forum.objects.create(
            name="Pagination Test Category",
            slug="pagination-test-cat",
            type=Forum.FORUM_CAT
        )

        forum = Forum.objects.create(
            name="Pagination Test Forum",
            slug="pagination-test",
            type=Forum.FORUM_POST,
            parent=category
        )

        for i in range(100):
            topic = Topic.objects.create(
                forum=forum,
                subject=f"Topic {i}",
                poster=self.user,
                type=Topic.TOPIC_POST
            )
            Post.objects.create(
                topic=topic,
                poster=self.user,
                subject=f"Topic {i}",
                content=f"Content {i}",
                approved=True
            )

        # Test with reasonable page size
        response = self.client.get(f'/api/v1/forums/{forum.slug}/topics/?page_size=20')
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Should return 20 results
        results_count = len(data.get('results', data.get('topics', [])))
        self.assertLessEqual(results_count, 20,
            "Page size limit not enforced")

        # Test with excessive page size (should be capped)
        response = self.client.get(f'/api/v1/forums/{forum.slug}/topics/?page_size=10000')
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Should be capped at reasonable limit (e.g., 100)
        results_count = len(data.get('results', data.get('topics', [])))
        self.assertLessEqual(results_count, 100,
            "Excessive page size not capped - memory exhaustion risk")
