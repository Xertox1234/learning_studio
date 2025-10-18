"""
Comprehensive tests for cursor-based pagination in topic posts endpoint.

Tests cover:
- Default page size
- Next/previous links
- Duplicate prevention
- Custom page sizes
- Max page size enforcement
- Empty results
- Single page results
- Authentication requirements
- Cursor integrity
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post
from apps.forum_integration.models import TrustLevel
from datetime import datetime, timedelta
from django.utils import timezone
import time

User = get_user_model()


class TopicCursorPaginationTests(TestCase):
    """Test cursor pagination for topic posts."""

    def setUp(self):
        """Create test user, forum, topic, and posts."""
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Get or create TrustLevel for user (may be created by signal)
        trust_level, created = TrustLevel.objects.get_or_create(
            user=self.user,
            defaults={'level': 1}
        )

        # Create forum hierarchy
        # Create root forum (category)
        self.root_forum = Forum.objects.create(
            name='Test Category',
            type=Forum.FORUM_CAT,
        )

        # Create actual forum for posts
        self.forum = Forum.objects.create(
            name='Test Forum',
            type=Forum.FORUM_POST,
            parent=self.root_forum,
        )

        # Create topic
        self.topic = Topic.objects.create(
            forum=self.forum,
            subject='Test Topic',
            poster=self.user,
            approved=True,
            type=Topic.TOPIC_POST,  # Required field
            status=Topic.TOPIC_UNLOCKED,  # Required field
        )

        # Store base URL for topic posts
        self.posts_url = f'/api/v2/forum/topics/{self.topic.pk}/posts/'

        # Authenticate the test client
        self.client.force_authenticate(user=self.user)

    def _create_posts(self, count):
        """Helper method to create multiple posts for a topic."""
        posts = []
        for i in range(count):
            # Add small time delta to ensure distinct timestamps
            created_time = timezone.now() + timedelta(milliseconds=i)
            post = Post.objects.create(
                topic=self.topic,
                poster=self.user,
                content=f'Test post content {i + 1}',
                approved=True,
            )
            # Manually set created time to ensure ordering
            Post.objects.filter(pk=post.pk).update(created=created_time)
            posts.append(post)
        return posts

    def test_cursor_pagination_returns_correct_page_size(self):
        """Test that default page size is 20 posts."""
        # Create 50 posts
        self._create_posts(50)

        # Fetch first page
        response = self.client.get(self.posts_url)

        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert exactly 20 posts returned (default page size)
        self.assertEqual(len(response.data['results']), 20)

    def test_cursor_pagination_next_link_exists(self):
        """Test that next link is present when more pages exist."""
        # Create 50 posts
        self._create_posts(50)

        # Fetch first page
        response = self.client.get(self.posts_url)

        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert 'next' URL is present
        self.assertIsNotNone(response.data['next'])
        self.assertIn('cursor=', response.data['next'])

        # Assert 'previous' is None for first page
        self.assertIsNone(response.data['previous'])

    def test_cursor_pagination_prevents_duplicates(self):
        """Test that cursor prevents duplicates when new posts added."""
        # Create 30 posts
        initial_posts = self._create_posts(30)

        # Fetch first page (20 posts)
        first_page_response = self.client.get(self.posts_url)
        self.assertEqual(first_page_response.status_code, status.HTTP_200_OK)

        # Extract IDs from first page
        first_page_ids = {post['id'] for post in first_page_response.data['results']}

        # Extract cursor for next page
        next_url = first_page_response.data['next']
        self.assertIsNotNone(next_url)

        # Add 5 new posts AFTER fetching first page
        new_posts = self._create_posts(5)

        # Fetch second page using cursor from first page
        # Parse cursor parameter from next_url
        cursor_param = next_url.split('cursor=')[1].split('&')[0]
        second_page_response = self.client.get(self.posts_url, {'cursor': cursor_param})

        # Extract IDs from second page
        second_page_ids = {post['id'] for post in second_page_response.data['results']}

        # Assert no overlap between pages (no duplicates from first page)
        self.assertEqual(len(first_page_ids & second_page_ids), 0,
                        "Found duplicate posts between pages")

        # Assert second page has remaining posts from initial 30 plus new 5
        # (should have 15 posts: 10 remaining from initial + 5 new)
        # This demonstrates cursor pagination doesn't miss new content
        self.assertEqual(len(second_page_response.data['results']), 15,
                        "Should have 10 remaining initial posts + 5 new posts")

    def test_custom_page_size_parameter(self):
        """Test that custom page_size parameter works."""
        # Create 30 posts
        self._create_posts(30)

        # Fetch with custom page size of 10
        response = self.client.get(self.posts_url, {'page_size': 10})

        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert exactly 10 posts returned
        self.assertEqual(len(response.data['results']), 10)

        # Assert next link exists (since 30 > 10)
        self.assertIsNotNone(response.data['next'])

    def test_max_page_size_enforced(self):
        """Test that max page size of 100 is enforced."""
        # Create 150 posts
        self._create_posts(150)

        # Fetch with page_size=200 (exceeds max of 100)
        response = self.client.get(self.posts_url, {'page_size': 200})

        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert only 100 posts returned (max page size enforced)
        self.assertEqual(len(response.data['results']), 100)

        # Assert next link exists (since 150 > 100)
        self.assertIsNotNone(response.data['next'])

    def test_empty_results(self):
        """Test pagination with no posts."""
        # Don't create any posts

        # Fetch posts
        response = self.client.get(self.posts_url)

        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert empty results array
        self.assertEqual(len(response.data['results']), 0)

        # Assert no next link
        self.assertIsNone(response.data['next'])

        # Assert no previous link
        self.assertIsNone(response.data['previous'])

    def test_single_page_results(self):
        """Test pagination when all results fit on one page."""
        # Create 15 posts (less than default page_size of 20)
        self._create_posts(15)

        # Fetch posts
        response = self.client.get(self.posts_url)

        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert all 15 posts returned
        self.assertEqual(len(response.data['results']), 15)

        # Assert no next link (all results on one page)
        self.assertIsNone(response.data['next'])

        # Assert no previous link
        self.assertIsNone(response.data['previous'])

    def test_unauthenticated_access_allowed(self):
        """Test that unauthenticated users can view posts (read-only)."""
        # Create some posts
        self._create_posts(10)

        # Remove authentication
        self.client.force_authenticate(user=None)

        # Fetch posts
        response = self.client.get(self.posts_url)

        # Assert response is successful (read-only access allowed)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert posts are returned
        self.assertEqual(len(response.data['results']), 10)

    def test_response_structure_matches_drf_cursor_pagination(self):
        """Test that response structure matches DRF cursor pagination format."""
        # Create some posts
        self._create_posts(25)

        # Fetch first page
        response = self.client.get(self.posts_url)

        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert response has expected keys
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)

        # Assert results is a list
        self.assertIsInstance(response.data['results'], list)

        # Assert each result has expected post fields
        if response.data['results']:
            post = response.data['results'][0]
            expected_fields = ['id', 'poster', 'content', 'created', 'updated',
                             'approved', 'position', 'is_topic_head', 'permissions']
            for field in expected_fields:
                self.assertIn(field, post, f"Missing field: {field}")

    def test_posts_ordered_by_created_ascending(self):
        """Test that posts are ordered by created date in ascending order."""
        # Create 10 posts with distinct timestamps
        posts = self._create_posts(10)

        # Fetch posts
        response = self.client.get(self.posts_url)

        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Extract created timestamps from response
        created_times = [post['created'] for post in response.data['results']]

        # Assert timestamps are in ascending order
        self.assertEqual(created_times, sorted(created_times),
                        "Posts are not ordered by created date (ascending)")

    def test_cursor_navigation_through_all_pages(self):
        """Test navigating through all pages using cursor."""
        # Create 55 posts (3 pages with default page_size=20: 20, 20, 15)
        total_posts = 55
        self._create_posts(total_posts)

        all_post_ids = []
        next_url = self.posts_url
        page_count = 0

        # Navigate through all pages
        while next_url:
            # Parse URL to extract path and query params
            if '?' in next_url:
                path = next_url.split('?')[0]
                query_string = next_url.split('?')[1]
                # Parse query parameters
                params = {}
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value
                response = self.client.get(path, params)
            else:
                response = self.client.get(next_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Collect post IDs
            page_ids = [post['id'] for post in response.data['results']]
            all_post_ids.extend(page_ids)

            # Get next URL
            next_url = response.data['next']
            page_count += 1

            # Safety check to prevent infinite loop
            if page_count > 10:
                self.fail("Too many pages - possible infinite loop")

        # Assert we got all posts
        self.assertEqual(len(all_post_ids), total_posts,
                        f"Expected {total_posts} posts, got {len(all_post_ids)}")

        # Assert no duplicates
        self.assertEqual(len(all_post_ids), len(set(all_post_ids)),
                        "Found duplicate posts across pages")

        # Assert correct number of pages
        self.assertEqual(page_count, 3,
                        f"Expected 3 pages for {total_posts} posts, got {page_count}")

    def test_view_count_incremented_on_fetch(self):
        """Test that topic view count is incremented when fetching posts."""
        # Create some posts
        self._create_posts(5)

        # Get initial view count
        initial_views = self.topic.views_count

        # Fetch posts
        response = self.client.get(self.posts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh topic from database
        self.topic.refresh_from_db()

        # Assert view count incremented by 1
        self.assertEqual(self.topic.views_count, initial_views + 1,
                        "View count not incremented")

    def test_invalid_cursor_returns_error(self):
        """Test that invalid cursor parameter returns appropriate error."""
        # Create some posts
        self._create_posts(10)

        # Fetch with invalid cursor
        response = self.client.get(self.posts_url, {'cursor': 'invalid-cursor-123'})

        # DRF cursor pagination returns 404 for invalid cursors
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_only_approved_posts_returned(self):
        """Test that only approved posts are returned in pagination."""
        # Create 10 approved posts
        approved_posts = self._create_posts(10)

        # Create 5 unapproved posts
        for i in range(5):
            Post.objects.create(
                topic=self.topic,
                poster=self.user,
                content=f'Unapproved post {i + 1}',
                approved=False,  # Not approved
            )

        # Fetch posts
        response = self.client.get(self.posts_url)

        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert only approved posts returned (10, not 15)
        self.assertEqual(len(response.data['results']), 10)

        # Assert all returned posts are approved
        for post in response.data['results']:
            self.assertTrue(post['approved'], "Unapproved post found in results")

    def test_posts_from_correct_topic_only(self):
        """Test that only posts from the requested topic are returned."""
        # Create posts for the test topic
        test_posts = self._create_posts(10)

        # Create another topic
        other_topic = Topic.objects.create(
            forum=self.forum,
            subject='Other Topic',
            poster=self.user,
            approved=True,
            type=Topic.TOPIC_POST,
            status=Topic.TOPIC_UNLOCKED,
        )

        # Create posts for the other topic
        for i in range(5):
            Post.objects.create(
                topic=other_topic,
                poster=self.user,
                content=f'Other topic post {i + 1}',
                approved=True,
            )

        # Fetch posts for test topic
        response = self.client.get(self.posts_url)

        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert only posts from test topic returned (10, not 15)
        self.assertEqual(len(response.data['results']), 10)

        # Assert all posts are from the correct topic
        for post_data in response.data['results']:
            # Fetch the actual post to verify topic
            post = Post.objects.get(id=post_data['id'])
            self.assertEqual(post.topic.id, self.topic.id,
                           f"Post {post.id} belongs to wrong topic")

    def test_cursor_pagination_with_page_size_edge_cases(self):
        """Test edge cases for page_size parameter."""
        # Create 25 posts
        self._create_posts(25)

        # Test page_size=1 (minimum)
        response = self.client.get(self.posts_url, {'page_size': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Test page_size=0 (should fall back to default or minimum)
        response = self.client.get(self.posts_url, {'page_size': 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # DRF typically falls back to default page size

        # Test page_size as string
        response = self.client.get(self.posts_url, {'page_size': '5'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

        # Test page_size as negative (should handle gracefully)
        response = self.client.get(self.posts_url, {'page_size': -10})
        # Should either return error or fall back to default
        self.assertIn(response.status_code,
                     [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_nonexistent_topic_returns_404(self):
        """Test that requesting posts for nonexistent topic returns 404."""
        # Use a topic ID that doesn't exist
        nonexistent_url = '/api/v2/forum/topics/99999/posts/'

        # Fetch posts
        response = self.client.get(nonexistent_url)

        # Assert 404 response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_poster_information_included(self):
        """Test that poster information is properly serialized."""
        # Create posts
        self._create_posts(5)

        # Fetch posts
        response = self.client.get(self.posts_url)

        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert poster information is included
        for post in response.data['results']:
            self.assertIn('poster', post)
            self.assertIsNotNone(post['poster'])
            # Check poster has expected fields
            self.assertIn('username', post['poster'])
            self.assertEqual(post['poster']['username'], self.user.username)
