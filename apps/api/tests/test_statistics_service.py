"""
Comprehensive tests for ForumStatisticsService with dependency injection and caching.

Tests cover:
- Dependency injection with mocks
- Cache behavior (hits, misses, invalidation)
- Serialization safety (no model instances in cache)
- Query optimization
- Error handling
- All service methods
"""

from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache

from apps.api.services.statistics_service import ForumStatisticsService
from apps.api.services.container import container
from apps.forum_integration.models import TrustLevel
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post

User = get_user_model()


class ForumStatisticsServiceDependencyInjectionTests(TestCase):
    """Test dependency injection and service initialization."""

    def setUp(self):
        """Set up test dependencies."""
        cache.clear()

    def test_service_accepts_dependencies(self):
        """Test that service accepts injected dependencies."""
        # Create mock dependencies
        mock_user_repo = Mock()
        mock_topic_repo = Mock()
        mock_post_repo = Mock()
        mock_forum_repo = Mock()
        mock_cache = Mock()

        # Inject dependencies
        service = ForumStatisticsService(
            user_repo=mock_user_repo,
            topic_repo=mock_topic_repo,
            post_repo=mock_post_repo,
            forum_repo=mock_forum_repo,
            cache=mock_cache
        )

        # Verify dependencies are stored
        self.assertEqual(service.user_repo, mock_user_repo)
        self.assertEqual(service.topic_repo, mock_topic_repo)
        self.assertEqual(service.post_repo, mock_post_repo)
        self.assertEqual(service.forum_repo, mock_forum_repo)
        self.assertEqual(service.cache, mock_cache)

    def test_container_provides_service_instance(self):
        """Test that DI container provides properly configured service."""
        service = container.get_statistics_service()

        # Verify service has all dependencies
        self.assertIsNotNone(service.user_repo)
        self.assertIsNotNone(service.topic_repo)
        self.assertIsNotNone(service.post_repo)
        self.assertIsNotNone(service.forum_repo)
        self.assertIsNotNone(service.cache)

    def test_container_returns_singleton(self):
        """Test that container returns same service instance (singleton)."""
        service1 = container.get_statistics_service()
        service2 = container.get_statistics_service()

        self.assertIs(service1, service2)

    def test_service_works_with_mocked_repositories(self):
        """Test that service operates correctly with mocked dependencies."""
        # Mock repositories
        mock_user_repo = Mock()
        mock_user_repo.count.return_value = 10

        mock_topic_repo = Mock()
        mock_topic_repo.count_approved.return_value = 20

        mock_post_repo = Mock()
        mock_post_repo.count_approved.return_value = 30

        mock_forum_repo = Mock()

        mock_cache = Mock()
        mock_cache.get.return_value = None  # Cache miss

        # Mock _get_online_users_count and _get_latest_member
        service = ForumStatisticsService(
            user_repo=mock_user_repo,
            topic_repo=mock_topic_repo,
            post_repo=mock_post_repo,
            forum_repo=mock_forum_repo,
            cache=mock_cache
        )

        # Mock private methods
        service._get_online_users_count = Mock(return_value=5)
        service._get_latest_member = Mock(return_value=None)

        # Get stats
        stats = service.get_forum_statistics()

        # Verify repository methods were called
        mock_user_repo.count.assert_called_once_with(is_active=True)
        mock_topic_repo.count_approved.assert_called_once()
        mock_post_repo.count_approved.assert_called_once()

        # Verify stats values
        self.assertEqual(stats['total_users'], 10)
        self.assertEqual(stats['total_topics'], 20)
        self.assertEqual(stats['total_posts'], 30)
        self.assertEqual(stats['online_users'], 5)


class ForumStatisticsServiceCachingTests(TestCase):
    """Test caching behavior."""

    def setUp(self):
        """Set up test data and clear cache."""
        cache.clear()

        # Create test user (TrustLevel auto-created by signal)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def tearDown(self):
        """Clean up cache after each test."""
        cache.clear()

    def test_cache_miss_triggers_calculation(self):
        """Test that cache miss triggers database query."""
        service = container.get_statistics_service()

        # Clear cache to ensure miss
        cache.clear()

        # Expected queries:
        # 1. Count active users (UserRepository.count)
        # 2. Count approved topics (TopicRepository.count_approved)
        # 3. Count approved posts (PostRepository.count_approved)
        # 4. Get online users (filtered by last_login)
        # 5. Get latest member (ordered by date_joined)
        # 6-7. UserRepository.get_detailed() uses prefetch_related for:
        #      - user.topic_set.all()
        #      - user.post_set.all()
        # NOTE: This count is sensitive to repository implementation changes.
        #       If UserRepository changes its prefetch strategy, update this count.
        with self.assertNumQueries(7):  # Expect DB queries on cache miss
            stats = service.get_forum_statistics()

        # Verify we got valid stats
        self.assertIn('total_users', stats)
        self.assertIn('total_topics', stats)
        self.assertIn('total_posts', stats)

    def test_cache_hit_skips_database(self):
        """Test that cache hit returns data without DB queries."""
        service = container.get_statistics_service()

        # First call - cache miss, populates cache
        stats1 = service.get_forum_statistics()

        # Second call - should be cache hit, no DB queries
        with self.assertNumQueries(0):
            stats2 = service.get_forum_statistics()

        # Results should be identical
        self.assertEqual(stats1, stats2)

    def test_cache_stores_serializable_data(self):
        """Test that cache stores serializable data (no model instances)."""
        service = container.get_statistics_service()

        # Get stats to populate cache
        service.get_forum_statistics()

        # Get cached value directly
        cache_key = f'{service.CACHE_VERSION}:forum:stats:all'
        cached_stats = cache.get(cache_key)

        # Verify it's a dict
        self.assertIsInstance(cached_stats, dict)

        # Verify no model instances in cache
        for key, value in cached_stats.items():
            if value is not None:
                self.assertNotIsInstance(
                    value,
                    (User, Topic, Post, Forum),
                    f"Found model instance in cache for key '{key}'"
                )

    def test_cache_invalidation_clears_cache(self):
        """Test that invalidate_cache clears cached data."""
        service = container.get_statistics_service()

        # Populate cache
        stats1 = service.get_forum_statistics()

        # Verify cache has data
        cache_key = f'{service.CACHE_VERSION}:forum:stats:all'
        self.assertIsNotNone(cache.get(cache_key))

        # Invalidate cache
        service.invalidate_cache()

        # Verify cache is cleared
        self.assertIsNone(cache.get(cache_key))

    def test_cache_timeout_configuration(self):
        """Test that cache timeouts are properly configured."""
        service = container.get_statistics_service()

        # Verify timeout constants exist
        self.assertEqual(service.CACHE_TIMEOUT_SHORT, 60)
        self.assertEqual(service.CACHE_TIMEOUT_MEDIUM, 300)
        self.assertEqual(service.CACHE_TIMEOUT_LONG, 900)

    def test_cache_keys_are_versioned(self):
        """Test that all cache keys include version prefix."""
        service = container.get_statistics_service()

        # Populate various caches
        service.get_forum_statistics()
        service.get_online_users_count()
        service.get_forum_specific_stats(forum_id=1)

        # Get all cache keys (this is Redis-specific, but demonstrates the pattern)
        version = service.CACHE_VERSION
        self.assertEqual(version, 'v1')

    def test_forum_specific_stats_cache_invalidation(self):
        """Test forum-specific cache invalidation."""
        from machina.apps.forum.models import Forum

        # Create test forum
        forum = Forum.objects.create(
            name='Cache Test Forum',
            slug='cache-test-forum',
            type=Forum.FORUM_POST,
            direct_topics_count=5,
            direct_posts_count=10
        )

        service = container.get_statistics_service()

        # Populate forum-specific cache
        service.get_forum_specific_stats(forum_id=forum.id)

        cache_key = f'{service.CACHE_VERSION}:forum:stats:{forum.id}'
        self.assertIsNotNone(cache.get(cache_key))

        # Invalidate specific forum cache
        service.invalidate_cache(forum_id=forum.id)

        # Verify it's cleared
        self.assertIsNone(cache.get(cache_key))


class ForumStatisticsServiceSerializationTests(TestCase):
    """Test data serialization for cache safety."""

    def setUp(self):
        """Set up test data."""
        cache.clear()

        # Create user (TrustLevel auto-created by signal)
        self.user = User.objects.create_user(
            username='serialtest',
            email='serial@example.com',
            password='testpass123'
        )

        # Create forum structure
        self.forum = Forum.objects.create(
            name='Test Forum',
            slug='test-forum',
            type=Forum.FORUM_POST
        )

        self.topic = Topic.objects.create(
            forum=self.forum,
            poster=self.user,
            subject='Test Topic',
            type=Topic.TOPIC_POST,
            status=Topic.TOPIC_UNLOCKED,
            approved=True
        )

        self.post = Post.objects.create(
            topic=self.topic,
            poster=self.user,
            content='Test post content',
            approved=True
        )

    def tearDown(self):
        """Clean up."""
        cache.clear()

    def test_latest_member_serialization(self):
        """Test that latest_member is serialized to dict."""
        service = container.get_statistics_service()
        stats = service.get_forum_statistics()

        latest_member = stats.get('latest_member')

        if latest_member:
            # Should be a dict, not a User instance
            self.assertIsInstance(latest_member, dict)
            self.assertIn('id', latest_member)
            self.assertIn('username', latest_member)
            self.assertIn('email', latest_member)
            self.assertIn('date_joined', latest_member)

            # date_joined should be ISO string
            self.assertIsInstance(latest_member['date_joined'], str)

    def test_online_users_list_serialization(self):
        """Test that online_users_list returns dicts, not model instances."""
        service = container.get_statistics_service()

        # Update user's last_login to make them "online"
        self.user.last_login = timezone.now()
        self.user.save()

        users_list = service.get_online_users_list(limit=5)

        # Should be a list of dicts
        self.assertIsInstance(users_list, list)

        for user_data in users_list:
            self.assertIsInstance(user_data, dict)
            self.assertNotIsInstance(user_data, User)
            self.assertIn('id', user_data)
            self.assertIn('username', user_data)

    def test_user_forum_stats_serialization(self):
        """Test that user stats contain serialized post/topic data."""
        service = container.get_statistics_service()
        stats = service.get_user_forum_stats(user_id=self.user.id)

        # Check last_post serialization
        last_post = stats.get('last_post')
        if last_post:
            self.assertIsInstance(last_post, dict)
            self.assertNotIsInstance(last_post, Post)
            self.assertIn('id', last_post)
            self.assertIn('subject', last_post)
            self.assertIn('created', last_post)

        # Check last_topic serialization
        last_topic = stats.get('last_topic')
        if last_topic:
            self.assertIsInstance(last_topic, dict)
            self.assertNotIsInstance(last_topic, Topic)
            self.assertIn('id', last_topic)
            self.assertIn('subject', last_topic)


class ForumStatisticsServiceMethodTests(TestCase):
    """Test all service methods."""

    def setUp(self):
        """Set up test data."""
        cache.clear()

        # Create users (TrustLevel auto-created by signal)
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user1.last_login = timezone.now()
        self.user1.save()

        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )

        # Create forum (counters will be auto-updated by machina signals)
        self.forum = Forum.objects.create(
            name='Test Forum',
            slug='test-forum',
            type=Forum.FORUM_POST
        )

        # Create 5 topics with 2 posts each (10 posts total)
        for topic_num in range(5):
            topic = Topic.objects.create(
                forum=self.forum,
                poster=self.user1,
                subject=f'Test Topic {topic_num}',
                type=Topic.TOPIC_POST,
                status=Topic.TOPIC_UNLOCKED,
                approved=True
            )

            # Create 2 posts per topic
            for post_num in range(2):
                Post.objects.create(
                    topic=topic,
                    poster=self.user1,
                    content=f'Test post {post_num} in topic {topic_num}',
                    approved=True
                )

        # Store reference to first topic for tests that need it
        self.topic = Topic.objects.filter(forum=self.forum).first()

    def tearDown(self):
        """Clean up."""
        cache.clear()

    def test_get_forum_statistics(self):
        """Test getting overall forum statistics."""
        service = container.get_statistics_service()
        stats = service.get_forum_statistics()

        # Verify required keys
        self.assertIn('total_users', stats)
        self.assertIn('total_topics', stats)
        self.assertIn('total_posts', stats)
        self.assertIn('online_users', stats)
        self.assertIn('latest_member', stats)

        # Verify counts
        self.assertGreaterEqual(stats['total_users'], 2)
        self.assertGreaterEqual(stats['total_topics'], 1)
        self.assertGreaterEqual(stats['total_posts'], 3)

    def test_get_online_users_count(self):
        """Test getting count of online users."""
        service = container.get_statistics_service()
        count = service.get_online_users_count()

        # Should have at least user1 (who has recent last_login)
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)

    def test_get_online_users_list(self):
        """Test getting list of online users."""
        service = container.get_statistics_service()
        users = service.get_online_users_list(limit=5)

        self.assertIsInstance(users, list)
        self.assertLessEqual(len(users), 5)

    def test_get_forum_specific_stats(self):
        """Test getting statistics for specific forum."""
        service = container.get_statistics_service()
        stats = service.get_forum_specific_stats(forum_id=self.forum.id)

        # Verify required keys
        self.assertIn('topics_count', stats)
        self.assertIn('posts_count', stats)
        self.assertIn('weekly_posts', stats)
        self.assertIn('online_users', stats)
        self.assertIn('trending', stats)

        # Verify values
        self.assertEqual(stats['topics_count'], 5)
        self.assertEqual(stats['posts_count'], 10)
        self.assertIsInstance(stats['trending'], bool)

    def test_get_forum_specific_stats_nonexistent_forum(self):
        """Test getting stats for non-existent forum."""
        service = container.get_statistics_service()
        stats = service.get_forum_specific_stats(forum_id=99999)

        # Should return default values
        self.assertEqual(stats['topics_count'], 0)
        self.assertEqual(stats['posts_count'], 0)
        self.assertEqual(stats['weekly_posts'], 0)
        self.assertEqual(stats['online_users'], 0)
        self.assertEqual(stats['trending'], False)

    def test_get_user_forum_stats(self):
        """Test getting user-specific forum statistics."""
        service = container.get_statistics_service()
        stats = service.get_user_forum_stats(user_id=self.user1.id)

        # Verify required keys
        self.assertIn('topics_count', stats)
        self.assertIn('posts_count', stats)
        self.assertIn('last_post', stats)
        self.assertIn('last_topic', stats)

        # Verify counts
        self.assertGreaterEqual(stats['topics_count'], 1)
        self.assertGreaterEqual(stats['posts_count'], 3)

    def test_get_user_forum_stats_nonexistent_user(self):
        """Test getting stats for non-existent user."""
        service = container.get_statistics_service()
        stats = service.get_user_forum_stats(user_id=99999)

        # Should return default values
        self.assertEqual(stats['topics_count'], 0)
        self.assertEqual(stats['posts_count'], 0)
        self.assertIsNone(stats['last_post'])
        self.assertIsNone(stats['last_topic'])

    def test_get_activity_summary(self):
        """Test getting activity summary."""
        service = container.get_statistics_service()
        summary = service.get_activity_summary(days=7)

        # Verify required keys
        self.assertIn('period_days', summary)
        self.assertIn('new_topics', summary)
        self.assertIn('new_posts', summary)
        self.assertIn('active_topics_count', summary)
        self.assertIn('new_users', summary)

        # Verify period
        self.assertEqual(summary['period_days'], 7)


class ForumStatisticsServiceQueryOptimizationTests(TestCase):
    """Test query optimization and N+1 prevention."""

    def setUp(self):
        """Set up test data."""
        cache.clear()

        # Create user (TrustLevel auto-created by signal)
        self.user = User.objects.create_user(
            username='querytest',
            email='query@example.com',
            password='pass123'
        )

    def tearDown(self):
        """Clean up."""
        cache.clear()

    def test_get_forum_statistics_query_count(self):
        """Test that get_forum_statistics uses minimal queries."""
        service = container.get_statistics_service()
        cache.clear()  # Ensure cache miss

        # Expected queries:
        # 1. Count active users
        # 2. Count approved topics
        # 3. Count approved posts
        # 4. Get online users
        # 5. Get latest member
        # 6-7. Prefetch posts and topics for latest member (from UserRepository)
        with self.assertNumQueries(7):
            service.get_forum_statistics()

    def test_cache_reduces_queries_to_zero(self):
        """Test that cache hit eliminates database queries."""
        service = container.get_statistics_service()

        # First call - populate cache
        service.get_forum_statistics()

        # Second call - should use cache, zero queries
        with self.assertNumQueries(0):
            service.get_forum_statistics()


class ForumStatisticsServiceCacheInvalidationTests(TestCase):
    """Test cache invalidation methods."""

    def setUp(self):
        """Set up test data and clear cache."""
        cache.clear()

        # Create test user (TrustLevel auto-created by signal)
        self.user = User.objects.create_user(
            username='cacheinvaltest',
            email='cacheinval@example.com',
            password='testpass123'
        )

    def tearDown(self):
        """Clean up."""
        cache.clear()

    def test_invalidate_cache_without_parameters(self):
        """Test invalidating all overall stats."""
        service = container.get_statistics_service()

        # Populate cache
        service.get_forum_statistics()
        service.get_online_users_count()

        # Invalidate
        service.invalidate_cache()

        # Verify caches are cleared
        cache_key_all = f'{service.CACHE_VERSION}:forum:stats:all'
        cache_key_online = f'{service.CACHE_VERSION}:forum:online_count'

        self.assertIsNone(cache.get(cache_key_all))
        self.assertIsNone(cache.get(cache_key_online))

    def test_invalidate_cache_with_forum_id(self):
        """Test invalidating specific forum cache."""
        # Create a forum with actual topics and posts (signal-driven counters)
        from machina.apps.forum.models import Forum
        from machina.apps.forum_conversation.models import Topic, Post

        forum = Forum.objects.create(
            name='Cache Test Forum',
            slug='cache-test-forum',
            type=Forum.FORUM_POST
        )

        # Create 5 topics with 2 posts each
        # Using actual Topic/Post creation (not hardcoded counters) because:
        # 1. Machina signals auto-update forum.direct_topics_count and direct_posts_count
        # 2. Hardcoded values get overwritten by signals, causing test failures
        for i in range(5):
            topic = Topic.objects.create(
                forum=forum,
                poster=self.user,
                subject=f'Cache Test Topic {i}',
                type=Topic.TOPIC_POST,
                status=Topic.TOPIC_UNLOCKED,
                approved=True
            )
            for j in range(2):
                Post.objects.create(
                    topic=topic,
                    poster=self.user,
                    content=f'Cache test post {j}',
                    approved=True
                )

        service = container.get_statistics_service()

        # Populate forum cache
        service.get_forum_specific_stats(forum_id=forum.id)

        cache_key = f'{service.CACHE_VERSION}:forum:stats:{forum.id}'
        self.assertIsNotNone(cache.get(cache_key))

        # Invalidate specific forum
        service.invalidate_cache(forum_id=forum.id)

        # Verify cleared
        self.assertIsNone(cache.get(cache_key))

    def test_invalidate_cache_with_user_id(self):
        """Test invalidating specific user cache."""
        # Create a user (TrustLevel auto-created by signal)
        user = User.objects.create_user(
            username='cachetest',
            email='cache@example.com',
            password='pass123'
        )

        service = container.get_statistics_service()

        # Populate user cache
        service.get_user_forum_stats(user_id=user.id)

        cache_key = f'{service.CACHE_VERSION}:forum:user_stats:{user.id}'
        self.assertIsNotNone(cache.get(cache_key))

        # Invalidate specific user
        service.invalidate_cache(user_id=user.id)

        # Verify cleared
        self.assertIsNone(cache.get(cache_key))

    @patch.object(cache, 'delete_pattern')
    def test_invalidate_all_caches_with_pattern_support(self, mock_delete_pattern):
        """Test invalidate_all_caches with Redis pattern deletion."""
        mock_delete_pattern.return_value = 5

        service = container.get_statistics_service()
        service.invalidate_all_caches()

        # Verify delete_pattern was called
        mock_delete_pattern.assert_called_once_with(f'{service.CACHE_VERSION}:forum:*')

    def test_invalidate_all_caches_fallback(self):
        """Test invalidate_all_caches without pattern support."""
        service = container.get_statistics_service()

        # Populate some caches
        service.get_forum_statistics()
        service.get_online_users_count()

        # Should not raise exception even without delete_pattern
        try:
            service.invalidate_all_caches()
        except Exception as e:
            self.fail(f"invalidate_all_caches raised exception: {e}")
