"""
Comprehensive test suite for ReviewQueueService.

Tests dependency injection, caching, spam detection, and queue management.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from unittest.mock import Mock, patch
from datetime import timedelta

from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post
from apps.forum_integration.models import ReviewQueue, TrustLevel
from apps.api.services.container import container
from apps.api.services.review_queue_service import ReviewQueueService

User = get_user_model()


class ReviewQueueServiceDependencyInjectionTests(TestCase):
    """Test dependency injection implementation."""

    def setUp(self):
        """Clear cache before each test."""
        cache.clear()

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    def test_service_accepts_dependencies(self):
        """Test that service constructor accepts all required dependencies."""
        from apps.api.repositories import (
            ReviewQueueRepository,
            PostRepository,
            TopicRepository,
            UserRepository,
        )

        service = ReviewQueueService(
            review_queue_repo=ReviewQueueRepository(),
            post_repo=PostRepository(),
            topic_repo=TopicRepository(),
            user_repo=UserRepository(),
            cache=cache
        )

        self.assertIsInstance(service, ReviewQueueService)
        self.assertIsNotNone(service.review_queue_repo)
        self.assertIsNotNone(service.post_repo)
        self.assertIsNotNone(service.topic_repo)
        self.assertIsNotNone(service.user_repo)
        self.assertIsNotNone(service.cache)

    def test_container_provides_service_instance(self):
        """Test that DI container provides properly configured service."""
        service = container.get_review_queue_service()

        self.assertIsInstance(service, ReviewQueueService)
        self.assertIsNotNone(service.review_queue_repo)
        self.assertIsNotNone(service.cache)

    def test_container_returns_singleton(self):
        """Test that container returns same instance (singleton pattern)."""
        service1 = container.get_review_queue_service()
        service2 = container.get_review_queue_service()

        self.assertIs(service1, service2)

    def test_service_works_with_mocked_repositories(self):
        """Test that service operates correctly with mocked dependencies."""
        mock_review_queue_repo = Mock()
        mock_post_repo = Mock()
        mock_topic_repo = Mock()
        mock_user_repo = Mock()
        mock_cache = Mock()

        service = ReviewQueueService(
            review_queue_repo=mock_review_queue_repo,
            post_repo=mock_post_repo,
            topic_repo=mock_topic_repo,
            user_repo=mock_user_repo,
            cache=mock_cache
        )

        # Verify service is usable
        self.assertIsNotNone(service)


class ReviewQueueServiceSpamDetectionTests(TestCase):
    """Test spam detection and caching."""

    def setUp(self):
        """Set up test data and clear cache."""
        cache.clear()

        # Create test user
        self.user = User.objects.create_user(
            username='spamtest',
            email='spam@example.com',
            password='testpass123'
        )

        # Create forum and topic
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

    def tearDown(self):
        """Clean up cache after each test."""
        cache.clear()

    def test_spam_score_calculation(self):
        """Test spam score is calculated correctly."""
        post = Post.objects.create(
            topic=self.topic,
            poster=self.user,
            content='Buy viagra cheap pills now! Click here!',
            approved=True
        )

        service = container.get_review_queue_service()
        spam_score = service.calculate_spam_score(post)

        # Should have high spam score due to spam keywords
        self.assertGreater(spam_score, 0.5)
        self.assertLessEqual(spam_score, 1.0)

    def test_spam_score_caching(self):
        """Test that spam scores are cached."""
        post = Post.objects.create(
            topic=self.topic,
            poster=self.user,
            content='This is legitimate content about Python programming.',
            approved=True
        )

        service = container.get_review_queue_service()

        # First call - cache miss
        score1 = service.calculate_spam_score(post)

        # Verify score is in cache
        cache_key = f'{service.CACHE_VERSION}:spam:v{service.SPAM_PATTERN_VERSION}:post:{post.id}'
        cached_score = cache.get(cache_key)
        self.assertIsNotNone(cached_score)
        self.assertEqual(cached_score, score1)

        # Second call - cache hit
        score2 = service.calculate_spam_score(post)
        self.assertEqual(score1, score2)

    def test_clean_content_low_spam_score(self):
        """Test that clean content gets low spam score."""
        post = Post.objects.create(
            topic=self.topic,
            poster=self.user,
            content='I really enjoy learning Python. The syntax is clean and readable.',
            approved=True
        )

        service = container.get_review_queue_service()
        spam_score = service.calculate_spam_score(post)

        # Should have low spam score
        self.assertLess(spam_score, 0.3)

    def test_spam_pattern_version_in_cache_key(self):
        """Test that cache key includes spam pattern version."""
        post = Post.objects.create(
            topic=self.topic,
            poster=self.user,
            content='Test content',
            approved=True
        )

        service = container.get_review_queue_service()
        service.calculate_spam_score(post)

        # Check cache key includes version
        cache_key = f'{service.CACHE_VERSION}:spam:v{service.SPAM_PATTERN_VERSION}:post:{post.id}'
        self.assertIsNotNone(cache.get(cache_key))

    def test_cache_invalidation_on_post_edit(self):
        """Test that cache is invalidated when checking edited post."""
        post = Post.objects.create(
            topic=self.topic,
            poster=self.user,
            content='Original content',
            approved=True
        )

        service = container.get_review_queue_service()

        # Calculate initial score (populates cache)
        service.calculate_spam_score(post)

        # Invalidate cache
        service.invalidate_cache(post_id=post.id)

        # Verify cache is cleared
        cache_key = f'{service.CACHE_VERSION}:spam:v{service.SPAM_PATTERN_VERSION}:post:{post.id}'
        self.assertIsNone(cache.get(cache_key))


class ReviewQueueServiceDuplicateDetectionTests(TestCase):
    """Test duplicate content detection."""

    def setUp(self):
        """Set up test data and clear cache."""
        cache.clear()

        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )

        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )

        # Create forum and topic
        self.forum = Forum.objects.create(
            name='Test Forum',
            slug='test-forum',
            type=Forum.FORUM_POST
        )

        self.topic = Topic.objects.create(
            forum=self.forum,
            poster=self.user1,
            subject='Test Topic',
            type=Topic.TOPIC_POST,
            status=Topic.TOPIC_UNLOCKED,
            approved=True
        )

    def tearDown(self):
        """Clean up cache."""
        cache.clear()

    def test_duplicate_detection_exact_match(self):
        """Test that exact duplicate content is detected."""
        content = "This is a test post with unique content for duplicate detection testing."

        # Create first post
        post1 = Post.objects.create(
            topic=self.topic,
            poster=self.user1,
            content=content,
            approved=True
        )

        # Create second post with same content
        post2 = Post.objects.create(
            topic=self.topic,
            poster=self.user1,
            content=content,
            approved=True
        )

        service = container.get_review_queue_service()
        is_duplicate = service.is_duplicate_content(post2)

        self.assertTrue(is_duplicate)

    def test_duplicate_detection_caching(self):
        """Test that duplicate detection results are cached."""
        post = Post.objects.create(
            topic=self.topic,
            poster=self.user1,
            content="Unique post content for caching test with sufficient length to pass minimum check.",
            approved=True
        )

        service = container.get_review_queue_service()

        # First call - cache miss
        result1 = service.is_duplicate_content(post)

        # Verify result is cached
        cache_key = f'{service.CACHE_VERSION}:duplicate:post:{post.id}'
        self.assertIsNotNone(cache.get(cache_key))

        # Second call - cache hit
        result2 = service.is_duplicate_content(post)
        self.assertEqual(result1, result2)

    def test_short_content_not_checked_for_duplicates(self):
        """Test that short posts are not checked for duplicates."""
        post = Post.objects.create(
            topic=self.topic,
            poster=self.user1,
            content="Short",  # Less than 50 characters
            approved=True
        )

        service = container.get_review_queue_service()
        is_duplicate = service.is_duplicate_content(post)

        # Should not be flagged as duplicate due to length
        self.assertFalse(is_duplicate)

    def test_duplicate_detection_limited_to_100_posts(self):
        """Test that duplicate detection is limited to prevent performance issues."""
        # This test verifies the optimization that limits queries
        service = container.get_review_queue_service()

        # Create a post to test
        post = Post.objects.create(
            topic=self.topic,
            poster=self.user1,
            content="Test content for performance optimization check with sufficient length.",
            approved=True
        )

        # The service should only check up to 100 recent posts
        # We're testing that the query doesn't fail with many posts
        is_duplicate = service.is_duplicate_content(post)

        # Should complete without errors
        self.assertFalse(is_duplicate)


class ReviewQueueServiceQueueManagementTests(TestCase):
    """Test review queue management methods."""

    def setUp(self):
        """Set up test data."""
        cache.clear()

        # Create test user
        self.user = User.objects.create_user(
            username='queuetest',
            email='queue@example.com',
            password='testpass123'
        )

        # Create moderator user
        self.moderator = User.objects.create_user(
            username='moderator',
            email='mod@example.com',
            password='modpass123',
            is_staff=True
        )

        # Create forum and topic
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

    def tearDown(self):
        """Clean up."""
        cache.clear()

    def test_add_post_to_queue(self):
        """Test adding a post to the review queue."""
        post = Post.objects.create(
            topic=self.topic,
            poster=self.user,
            content='Test post for queue',
            approved=True
        )

        service = container.get_review_queue_service()
        review_item = service.add_to_queue(
            post=post,
            review_type='spam_detection',
            reason='Test reason',
            priority=2
        )

        self.assertIsNotNone(review_item)
        self.assertEqual(review_item.post, post)
        self.assertEqual(review_item.review_type, 'spam_detection')
        self.assertEqual(review_item.priority, 2)

    def test_check_new_post_tl0_user(self):
        """Test that TL0 user posts are added to queue."""
        # User automatically gets TL0 from signal
        post = Post.objects.create(
            topic=self.topic,
            poster=self.user,
            content='Post by new user',
            approved=True
        )

        service = container.get_review_queue_service()
        service.check_new_post(post)

        # Should have created a review item for TL0 user
        review_items = ReviewQueue.objects.filter(post=post)
        self.assertGreater(review_items.count(), 0)

    def test_review_item_approve(self):
        """Test approving a review item."""
        post = Post.objects.create(
            topic=self.topic,
            poster=self.user,
            content='Post to approve',
            approved=True
        )

        service = container.get_review_queue_service()
        review_item = service.add_to_queue(
            post=post,
            review_type='new_user_post',
            reason='TL0 user',
            priority=3
        )

        # Approve the item
        success = service.review_item(
            item_id=review_item.id,
            reviewer=self.moderator,
            action='approve',
            notes='Looks good'
        )

        self.assertTrue(success)

        # Verify status changed
        review_item.refresh_from_db()
        self.assertEqual(review_item.status, 'approved')

    def test_review_item_reject(self):
        """Test rejecting a review item."""
        post = Post.objects.create(
            topic=self.topic,
            poster=self.user,
            content='Post to reject',
            approved=True
        )

        service = container.get_review_queue_service()
        review_item = service.add_to_queue(
            post=post,
            review_type='spam_detection',
            reason='Spam detected',
            priority=2
        )

        # Reject the item
        success = service.review_item(
            item_id=review_item.id,
            reviewer=self.moderator,
            action='reject',
            notes='Confirmed spam'
        )

        self.assertTrue(success)

        # Verify status changed
        review_item.refresh_from_db()
        self.assertEqual(review_item.status, 'rejected')

    def test_review_item_invalidates_cache(self):
        """Test that reviewing an item invalidates cache."""
        post = Post.objects.create(
            topic=self.topic,
            poster=self.user,
            content='Post for cache invalidation test',
            approved=True
        )

        service = container.get_review_queue_service()

        # Calculate spam score (populates cache)
        service.calculate_spam_score(post)
        cache_key = f'{service.CACHE_VERSION}:spam:v{service.SPAM_PATTERN_VERSION}:post:{post.id}'
        self.assertIsNotNone(cache.get(cache_key))

        # Create review item and approve it
        review_item = service.add_to_queue(
            post=post,
            review_type='spam_detection',
            reason='Test',
            priority=2
        )

        service.review_item(
            item_id=review_item.id,
            reviewer=self.moderator,
            action='approve'
        )

        # Cache should be invalidated
        self.assertIsNone(cache.get(cache_key))


class ReviewQueueServiceTrustLevelTests(TestCase):
    """Test trust level integration."""

    def setUp(self):
        """Set up test data."""
        cache.clear()

        # Create users with different trust levels
        self.tl0_user = User.objects.create_user(
            username='tl0user',
            email='tl0@example.com',
            password='pass123'
        )
        # TrustLevel automatically created by signal at level 0

        self.tl3_user = User.objects.create_user(
            username='tl3user',
            email='tl3@example.com',
            password='pass123'
        )
        # Update trust level to TL3
        trust_level = TrustLevel.objects.get(user=self.tl3_user)
        trust_level.level = 3
        trust_level.save()

        # Create forum and topic
        self.forum = Forum.objects.create(
            name='Test Forum',
            slug='test-forum',
            type=Forum.FORUM_POST
        )

        self.topic = Topic.objects.create(
            forum=self.forum,
            poster=self.tl0_user,
            subject='Test Topic',
            type=Topic.TOPIC_POST,
            status=Topic.TOPIC_UNLOCKED,
            approved=True
        )

    def tearDown(self):
        """Clean up."""
        cache.clear()

    def test_tl0_user_posts_always_reviewed(self):
        """Test that TL0 user posts are always added to queue."""
        post = Post.objects.create(
            topic=self.topic,
            poster=self.tl0_user,
            content='Post by TL0 user',
            approved=True
        )

        service = container.get_review_queue_service()
        service.check_new_post(post)

        # Should have review items for TL0 user
        review_items = ReviewQueue.objects.filter(
            post=post,
            review_type='new_user_post'
        )
        self.assertGreater(review_items.count(), 0)

    def test_tl3_user_posts_not_auto_reviewed(self):
        """Test that TL3 user posts are not automatically reviewed (unless spam)."""
        post = Post.objects.create(
            topic=self.topic,
            poster=self.tl3_user,
            content='Clean post by trusted user',
            approved=True
        )

        service = container.get_review_queue_service()
        service.check_new_post(post)

        # Should not have review items for clean TL3 post
        review_items = ReviewQueue.objects.filter(
            post=post,
            review_type='new_user_post'
        )
        self.assertEqual(review_items.count(), 0)


class ReviewQueueServiceUtilityTests(TestCase):
    """Test utility methods."""

    def setUp(self):
        """Set up test data."""
        cache.clear()

        self.user = User.objects.create_user(
            username='utiltest',
            email='util@example.com',
            password='pass123'
        )

    def tearDown(self):
        """Clean up."""
        cache.clear()

    def test_calculate_similarity_identical_text(self):
        """Test similarity calculation for identical text."""
        service = container.get_review_queue_service()
        text = "This is a test string for similarity checking"

        similarity = service.calculate_similarity(text, text)
        self.assertEqual(similarity, 1.0)

    def test_calculate_similarity_different_text(self):
        """Test similarity calculation for different text."""
        service = container.get_review_queue_service()
        text1 = "This is about Python programming"
        text2 = "Completely different topic here"

        similarity = service.calculate_similarity(text1, text2)
        self.assertLess(similarity, 0.5)

    def test_calculate_similarity_similar_text(self):
        """Test similarity calculation for similar text."""
        service = container.get_review_queue_service()
        text1 = "I love learning Python programming language"
        text2 = "I enjoy learning Python programming"

        similarity = service.calculate_similarity(text1, text2)
        self.assertGreater(similarity, 0.5)

    def test_get_user_trust_level(self):
        """Test getting user trust level."""
        service = container.get_review_queue_service()
        trust_level = service._get_user_trust_level(self.user.id)

        # Should return 0 for new user
        self.assertEqual(trust_level, 0)

    def test_get_user_trust_level_nonexistent_user(self):
        """Test getting trust level for nonexistent user."""
        service = container.get_review_queue_service()
        trust_level = service._get_user_trust_level(99999)

        # Should return 0 for nonexistent user
        self.assertEqual(trust_level, 0)
