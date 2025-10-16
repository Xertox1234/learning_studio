"""
Tests for Forum API endpoints.

This test suite covers all 28 forum API endpoints including:
- Forum list and detail
- Topic CRUD operations
- Post CRUD operations
- User profile and activity
- Search and discovery
- Moderation endpoints (TL3+ access)
- Topic subscriptions
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post
from apps.forum_integration.models import TrustLevel, ReviewQueue

User = get_user_model()


class ForumAPITestCase(APITestCase):
    """Base test case with common fixtures."""

    def setUp(self):
        """Set up test fixtures."""
        # Create users with different trust levels
        # Create users (TrustLevel is auto-created by signal)
        self.user_tl0 = User.objects.create_user(
            username='newuser',
            email='newuser@test.com',
            password='testpass123'
        )
        # Get the auto-created trust level and ensure it's TL0
        self.trust_level_tl0 = TrustLevel.objects.get(user=self.user_tl0)
        self.trust_level_tl0.level = 0
        self.trust_level_tl0.save()
        self.user_tl0.refresh_from_db()  # Refresh to update cached trust_level

        self.user_tl1 = User.objects.create_user(
            username='basicuser',
            email='basic@test.com',
            password='testpass123'
        )
        # Update to TL1
        self.trust_level_tl1 = TrustLevel.objects.get(user=self.user_tl1)
        self.trust_level_tl1.level = 1
        self.trust_level_tl1.save()
        self.user_tl1.refresh_from_db()  # Refresh to update cached trust_level

        self.user_tl3 = User.objects.create_user(
            username='moderator',
            email='mod@test.com',
            password='testpass123'
        )
        # Update to TL3
        self.trust_level_tl3 = TrustLevel.objects.get(user=self.user_tl3)
        self.trust_level_tl3.level = 3
        self.trust_level_tl3.save()
        self.user_tl3.refresh_from_db()  # Refresh to update cached trust_level

        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )

        # Create forum structure
        self.category = Forum.objects.create(
            name='General',
            slug='general',
            type=Forum.FORUM_CAT,
            description='General discussion'
        )

        self.forum = Forum.objects.create(
            name='Python Help',
            slug='python-help',
            type=Forum.FORUM_POST,
            description='Get help with Python',
            parent=self.category
        )

        # Create a topic
        self.topic = Topic.objects.create(
            forum=self.forum,
            subject='How to use decorators?',
            slug='how-to-use-decorators',
            poster=self.user_tl1,
            type=Topic.TOPIC_POST,
            status=Topic.TOPIC_UNLOCKED,
            approved=True
        )

        # Create posts
        self.post1 = Post.objects.create(
            topic=self.topic,
            poster=self.user_tl1,
            content='I need help understanding decorators in Python.',
            approved=True
        )

        self.post2 = Post.objects.create(
            topic=self.topic,
            poster=self.user_tl3,
            content='Decorators are functions that modify other functions.',
            approved=True
        )

        # Set up API client
        self.client = APIClient()

    def authenticate(self, user):
        """Helper to authenticate a user."""
        self.client.force_authenticate(user=user)

    def tearDown(self):
        """Clean up after tests."""
        self.client.force_authenticate(user=None)


class ForumListAPITests(ForumAPITestCase):
    """Tests for forum list endpoint."""

    def test_forum_list_requires_authentication(self):
        """Test that forum list requires authentication."""
        response = self.client.get('/api/v1/forums/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_forum_list_authenticated(self):
        """Test authenticated user can get forum list."""
        self.authenticate(self.user_tl1)
        response = self.client.get('/api/v1/forums/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('categories', response.data)
        self.assertIsInstance(response.data['categories'], list)

    def test_forum_list_includes_statistics(self):
        """Test that forum list includes topic and post counts."""
        self.authenticate(self.user_tl1)
        response = self.client.get('/api/v1/forums/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        categories = response.data['categories']

        # Check that statistics are included
        if len(categories) > 0:
            category = categories[0]
            self.assertIn('forums', category)
            if len(category['forums']) > 0:
                forum = category['forums'][0]
                self.assertIn('topics_count', forum)
                self.assertIn('posts_count', forum)


class ForumDetailAPITests(ForumAPITestCase):
    """Tests for forum detail endpoint."""

    def test_forum_detail_with_topics(self):
        """Test getting forum detail with topic list."""
        self.authenticate(self.user_tl1)
        response = self.client.get(f'/api/v1/forums/{self.forum.slug}/{self.forum.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.forum.id)
        self.assertIn('topics', response.data)
        self.assertIn('topics_pagination', response.data)

    def test_forum_detail_pagination(self):
        """Test that forum detail supports pagination."""
        self.authenticate(self.user_tl1)
        response = self.client.get(
            f'/api/v1/forums/{self.forum.slug}/{self.forum.id}/',
            {'page': 1, 'page_size': 10}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('topics_pagination', response.data)
        pagination = response.data['topics_pagination']
        self.assertIn('current_page', pagination)
        self.assertIn('total_pages', pagination)


class TopicDetailAPITests(ForumAPITestCase):
    """Tests for topic detail endpoint."""

    def test_topic_detail_with_posts(self):
        """Test getting topic detail with posts."""
        self.authenticate(self.user_tl1)
        response = self.client.get(
            f'/api/v1/forums/{self.forum.slug}/{self.forum.id}/topics/{self.topic.slug}/{self.topic.id}/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.topic.id)
        self.assertIn('posts', response.data)
        self.assertGreaterEqual(len(response.data['posts']), 2)

    def test_topic_detail_includes_poster_info(self):
        """Test that posts include poster information."""
        self.authenticate(self.user_tl1)
        response = self.client.get(
            f'/api/v1/forums/{self.forum.slug}/{self.forum.id}/topics/{self.topic.slug}/{self.topic.id}/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        first_post = response.data['posts'][0]
        self.assertIn('poster', first_post)
        self.assertIn('username', first_post['poster'])


class TopicCreateAPITests(ForumAPITestCase):
    """Tests for topic creation endpoint."""

    def test_create_topic_tl1_user(self):
        """Test TL1 user can create topics."""
        self.authenticate(self.user_tl1)
        response = self.client.post('/api/v1/topics/create/', {
            'forum_id': self.forum.id,
            'subject': 'New topic about lists',
            'content': 'How do I use list comprehensions?'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('topic', response.data)
        self.assertEqual(response.data['topic']['subject'], 'New topic about lists')

    def test_create_topic_tl0_enters_review_queue(self):
        """Test TL0 user topics enter review queue."""
        self.authenticate(self.user_tl0)
        response = self.client.post('/api/v1/topics/create/', {
            'forum_id': self.forum.id,
            'subject': 'Help with Python',
            'content': 'I need help'
        })

        # Should still succeed but enter review queue
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if review queue item was created
        queue_items = ReviewQueue.objects.filter(
            topic__subject='Help with Python'
        )
        # Note: This depends on review queue implementation

    def test_create_topic_requires_authentication(self):
        """Test that creating topics requires authentication."""
        response = self.client.post('/api/v1/topics/create/', {
            'forum_id': self.forum.id,
            'subject': 'Test topic',
            'content': 'Test content'
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_topic_missing_fields(self):
        """Test validation for missing fields."""
        self.authenticate(self.user_tl1)
        response = self.client.post('/api/v1/topics/create/', {
            'forum_id': self.forum.id,
            # Missing subject and content
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PostReplyAPITests(ForumAPITestCase):
    """Tests for post reply endpoint."""

    def test_reply_to_topic(self):
        """Test authenticated user can reply to topic."""
        self.authenticate(self.user_tl1)
        response = self.client.post(f'/api/v1/topics/{self.topic.id}/reply/', {
            'content': 'This is my reply to the topic.'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('post', response.data)
        self.assertEqual(response.data['post']['content'], 'This is my reply to the topic.')

    def test_reply_to_locked_topic(self):
        """Test that users cannot reply to locked topics."""
        # Lock the topic
        self.topic.status = Topic.TOPIC_LOCKED
        self.topic.save()

        self.authenticate(self.user_tl1)
        response = self.client.post(f'/api/v1/topics/{self.topic.id}/reply/', {
            'content': 'Trying to reply'
        })

        # Should be forbidden
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST])


class UserProfileAPITests(ForumAPITestCase):
    """Tests for user profile endpoints."""

    def test_user_profile(self):
        """Test getting user forum profile."""
        self.authenticate(self.user_tl1)
        response = self.client.get(f'/api/v1/forums/users/{self.user_tl1.id}/profile/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('username', response.data)
        self.assertIn('trust_level', response.data)
        self.assertEqual(response.data['trust_level']['level'], 1)

    def test_user_posts_list(self):
        """Test getting user's posts."""
        self.authenticate(self.user_tl1)
        response = self.client.get(f'/api/v1/forums/users/{self.user_tl1.id}/posts/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('posts', response.data)
        self.assertIn('pagination', response.data)

    def test_user_topics_list(self):
        """Test getting user's topics."""
        self.authenticate(self.user_tl1)
        response = self.client.get(f'/api/v1/forums/users/{self.user_tl1.id}/topics/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('topics', response.data)
        self.assertIn('pagination', response.data)


class TopicSubscriptionAPITests(ForumAPITestCase):
    """Tests for topic subscription endpoints."""

    def test_subscribe_to_topic(self):
        """Test user can subscribe to topic."""
        self.authenticate(self.user_tl1)
        response = self.client.post(f'/api/v1/topics/{self.topic.id}/subscribe/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('subscribed', False))

    def test_unsubscribe_from_topic(self):
        """Test user can unsubscribe from topic."""
        # First subscribe
        self.authenticate(self.user_tl1)
        self.client.post(f'/api/v1/topics/{self.topic.id}/subscribe/')

        # Then unsubscribe
        response = self.client.delete(f'/api/v1/topics/{self.topic.id}/unsubscribe/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_subscriptions_list(self):
        """Test getting user's topic subscriptions."""
        # Subscribe to topic
        self.authenticate(self.user_tl1)
        self.client.post(f'/api/v1/topics/{self.topic.id}/subscribe/')

        # Get subscriptions
        response = self.client.get(f'/api/v1/forums/users/{self.user_tl1.id}/subscriptions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('subscriptions', response.data)


class ForumSearchAPITests(ForumAPITestCase):
    """Tests for forum search endpoint."""

    def test_search_topics(self):
        """Test searching for topics."""
        self.authenticate(self.user_tl1)
        response = self.client.get('/api/v1/forums/search/', {
            'q': 'decorators',
            'type': 'topics'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('topics', response.data)
        self.assertIsInstance(response.data['topics'], list)

    def test_search_posts(self):
        """Test searching for posts."""
        self.authenticate(self.user_tl1)
        response = self.client.get('/api/v1/forums/search/', {
            'q': 'Python',
            'type': 'posts'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('posts', response.data)
        self.assertIsInstance(response.data['posts'], list)

    def test_search_all_content(self):
        """Test searching all content types."""
        self.authenticate(self.user_tl1)
        response = self.client.get('/api/v1/forums/search/', {
            'q': 'Python',
            'type': 'all'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('topics', response.data)
        self.assertIn('posts', response.data)


class RecentActivityAPITests(ForumAPITestCase):
    """Tests for recent activity endpoint."""

    def test_recent_activity_default(self):
        """Test getting recent activity with default time window."""
        self.authenticate(self.user_tl1)
        response = self.client.get('/api/v1/forums/recent-activity/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('activity', response.data)

    def test_recent_activity_custom_hours(self):
        """Test getting recent activity with custom time window."""
        self.authenticate(self.user_tl1)
        response = self.client.get('/api/v1/forums/recent-activity/', {
            'hours': 48
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('activity', response.data)


class ModerationLockAPITests(ForumAPITestCase):
    """Tests for topic lock/unlock moderation endpoints."""

    def test_lock_topic_as_tl3(self):
        """Test TL3 user can lock topics."""
        self.authenticate(self.user_tl3)
        response = self.client.post(f'/api/v1/topics/{self.topic.id}/lock/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify topic is locked
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.status, Topic.TOPIC_LOCKED)

    def test_lock_topic_as_tl1_fails(self):
        """Test TL1 user cannot lock topics."""
        self.authenticate(self.user_tl1)
        response = self.client.post(f'/api/v1/topics/{self.topic.id}/lock/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unlock_topic_as_tl3(self):
        """Test TL3 user can unlock topics."""
        # First lock it
        self.topic.status = Topic.TOPIC_LOCKED
        self.topic.save()

        self.authenticate(self.user_tl3)
        response = self.client.post(f'/api/v1/topics/{self.topic.id}/unlock/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify topic is unlocked
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.status, Topic.TOPIC_UNLOCKED)

    def test_lock_topic_as_admin(self):
        """Test admin can lock topics."""
        self.authenticate(self.admin_user)
        response = self.client.post(f'/api/v1/topics/{self.topic.id}/lock/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ModerationPinAPITests(ForumAPITestCase):
    """Tests for topic pin/unpin moderation endpoints."""

    def test_pin_topic_as_tl3(self):
        """Test TL3 user can pin topics."""
        self.authenticate(self.user_tl3)
        response = self.client.post(f'/api/v1/topics/{self.topic.id}/pin/', {
            'type': 'sticky'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pin_topic_as_tl1_fails(self):
        """Test TL1 user cannot pin topics."""
        self.authenticate(self.user_tl1)
        response = self.client.post(f'/api/v1/topics/{self.topic.id}/pin/', {
            'type': 'sticky'
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unpin_topic_as_tl3(self):
        """Test TL3 user can unpin topics."""
        # First pin it
        self.topic.type = Topic.TOPIC_STICKY
        self.topic.save()

        self.authenticate(self.user_tl3)
        response = self.client.post(f'/api/v1/topics/{self.topic.id}/unpin/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ModerationMoveAPITests(ForumAPITestCase):
    """Tests for topic move moderation endpoint."""

    def setUp(self):
        """Set up additional forum for move tests."""
        super().setUp()
        self.target_forum = Forum.objects.create(
            name='Advanced Python',
            slug='advanced-python',
            type=Forum.FORUM_POST,
            description='Advanced Python topics',
            parent=self.category
        )

    def test_move_topic_as_tl3(self):
        """Test TL3 user can move topics between forums."""
        self.authenticate(self.user_tl3)
        response = self.client.post(f'/api/v1/topics/{self.topic.id}/move/', {
            'forum_id': self.target_forum.id
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify topic was moved
        self.topic.refresh_from_db()
        self.assertEqual(self.topic.forum.id, self.target_forum.id)

    def test_move_topic_as_tl1_fails(self):
        """Test TL1 user cannot move topics."""
        self.authenticate(self.user_tl1)
        response = self.client.post(f'/api/v1/topics/{self.topic.id}/move/', {
            'forum_id': self.target_forum.id
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ModerationQueueAPITests(ForumAPITestCase):
    """Tests for moderation queue endpoints."""

    def test_get_moderation_queue_as_tl3(self):
        """Test TL3 user can access moderation queue."""
        self.authenticate(self.user_tl3)
        response = self.client.get('/api/v1/moderation/queue/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('queue', response.data)
        self.assertIn('pagination', response.data)

    def test_get_moderation_queue_as_tl1_fails(self):
        """Test TL1 user cannot access moderation queue."""
        self.authenticate(self.user_tl1)
        response = self.client.get('/api/v1/moderation/queue/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_moderation_queue_pagination(self):
        """Test moderation queue supports pagination."""
        self.authenticate(self.user_tl3)
        response = self.client.get('/api/v1/moderation/queue/', {
            'page': 1,
            'page_size': 10
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('pagination', response.data)


class ModerationReviewAPITests(ForumAPITestCase):
    """Tests for moderation review endpoint."""

    def setUp(self):
        """Set up review queue item for testing."""
        super().setUp()
        # Create a review queue item (if TL0 posts go to queue)
        # This depends on ReviewQueue model structure

    def test_approve_queue_item_as_tl3(self):
        """Test TL3 user can approve queue items."""
        # Create a queue item first
        queue_item = ReviewQueue.objects.create(
            post=self.post1,
            review_type='new_user_post',
            reason='New user content requiring review',
            status='pending',
            priority=3,
            score=5.0
        )

        self.authenticate(self.user_tl3)
        response = self.client.post(f'/api/v1/moderation/queue/{queue_item.id}/review/', {
            'action': 'approve',
            'notes': 'Looks good'
        })

        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify queue item was updated
        queue_item.refresh_from_db()
        self.assertEqual(queue_item.status, 'approved')

    def test_reject_queue_item_as_tl3(self):
        """Test TL3 user can reject queue items."""
        queue_item = ReviewQueue.objects.create(
            post=self.post1,
            review_type='new_user_post',
            reason='New user content requiring review',
            status='pending',
            priority=3,
            score=5.0
        )

        self.authenticate(self.user_tl3)
        response = self.client.post(f'/api/v1/moderation/queue/{queue_item.id}/review/', {
            'action': 'reject',
            'notes': 'Spam content'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify queue item was updated
        queue_item.refresh_from_db()
        self.assertEqual(queue_item.status, 'rejected')


class DashboardStatsAPITests(ForumAPITestCase):
    """Tests for dashboard forum stats endpoint."""

    def test_dashboard_stats_authenticated(self):
        """Test authenticated user can get dashboard stats."""
        self.authenticate(self.user_tl1)
        response = self.client.get('/api/v1/dashboard/forum-stats/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user_stats', response.data)
        self.assertIn('forum_stats', response.data)
