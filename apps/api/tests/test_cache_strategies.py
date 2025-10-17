"""
Tests for cache strategies module.
Tests cache decorators, key building, and invalidation functions.
"""

import time
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.api.cache.strategies import (
    CacheKeyBuilder,
    CacheTimeout,
    cache_response,
    cache_queryset,
    cache_method,
    invalidate_cache,
    invalidate_user_cache,
    invalidate_model_cache,
)

User = get_user_model()


class CacheKeyBuilderTests(TestCase):
    """Test cache key building functionality."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_build_basic_key(self):
        """Test building a basic cache key."""
        key = CacheKeyBuilder.build('courses', 'list')
        self.assertIn('api_cache', key)
        self.assertIn('courses', key)
        self.assertIn('list', key)

    def test_build_key_with_params(self):
        """Test building cache key with parameters."""
        key1 = CacheKeyBuilder.build('courses', 'list', page=1, category='python')
        key2 = CacheKeyBuilder.build('courses', 'list', page=1, category='python')
        key3 = CacheKeyBuilder.build('courses', 'list', page=2, category='python')

        # Same parameters should produce same key
        self.assertEqual(key1, key2)
        # Different parameters should produce different key
        self.assertNotEqual(key1, key3)

    def test_build_user_key(self):
        """Test building user-specific cache key."""
        user_id = 123
        key = CacheKeyBuilder.build_user_key(user_id, 'progress')

        self.assertIn('api_cache', key)
        self.assertIn('user', key)
        self.assertIn(str(user_id), key)
        self.assertIn('progress', key)

    def test_build_pattern(self):
        """Test building cache key pattern for wildcard matching."""
        pattern = CacheKeyBuilder.pattern('courses', 'list')

        self.assertIn('api_cache', pattern)
        self.assertIn('courses', pattern)
        self.assertIn('list', pattern)
        self.assertTrue(pattern.endswith(':*'))

    def test_key_consistency(self):
        """Test that key building is consistent across calls."""
        keys = [
            CacheKeyBuilder.build('test', 'key', value=1)
            for _ in range(5)
        ]

        # All keys should be identical
        self.assertEqual(len(set(keys)), 1)


class CacheResponseDecoratorTests(TestCase):
    """Test cache_response decorator."""

    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def tearDown(self):
        cache.clear()
        User.objects.all().delete()

    def test_cache_response_basic(self):
        """Test basic response caching."""
        call_count = {'count': 0}

        @cache_response(timeout=60)
        @api_view(['GET'])
        def test_view(request):
            call_count['count'] += 1
            return Response({'data': 'test', 'count': call_count['count']})

        request = self.factory.get('/test/')

        # First call - cache miss
        response1 = test_view(request)
        self.assertEqual(response1.data['count'], 1)

        # Second call - cache hit
        response2 = test_view(request)
        self.assertEqual(response2.data['count'], 1)  # Should be cached
        self.assertEqual(call_count['count'], 1)  # View called only once

    def test_cache_response_vary_on_user(self):
        """Test response caching with user variation."""
        call_count = {'count': 0}

        @cache_response(timeout=60, vary_on_user=True)
        @api_view(['GET'])
        def test_view(request):
            call_count['count'] += 1
            return Response({'data': 'test', 'count': call_count['count']})

        # Request with authenticated user
        request1 = self.factory.get('/test/')
        request1.user = self.user

        # Request without user
        request2 = self.factory.get('/test/')
        request2.user = Mock(is_authenticated=False)

        # Different users should have different cache
        response1 = test_view(request1)
        response2 = test_view(request2)

        self.assertEqual(response1.data['count'], 1)
        self.assertEqual(response2.data['count'], 2)
        self.assertEqual(call_count['count'], 2)

    def test_cache_response_vary_on_query_params(self):
        """Test response caching with query parameter variation."""
        call_count = {'count': 0}

        @cache_response(timeout=60, vary_on_query_params=True)
        @api_view(['GET'])
        def test_view(request):
            call_count['count'] += 1
            return Response({'data': 'test', 'count': call_count['count']})

        # Different query parameters should have different cache
        request1 = self.factory.get('/test/?page=1')
        request2 = self.factory.get('/test/?page=2')
        request3 = self.factory.get('/test/?page=1')

        response1 = test_view(request1)
        response2 = test_view(request2)
        response3 = test_view(request3)

        self.assertEqual(response1.data['count'], 1)
        self.assertEqual(response2.data['count'], 2)
        self.assertEqual(response3.data['count'], 1)  # Cached from request1


class CacheQuerysetDecoratorTests(TestCase):
    """Test cache_queryset decorator."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_cache_queryset_basic(self):
        """Test basic queryset caching."""
        call_count = {'count': 0}

        @cache_queryset(timeout=60, key='test_queryset')
        def get_data():
            call_count['count'] += 1
            return [1, 2, 3, 4, 5]

        # First call - cache miss
        result1 = get_data()
        self.assertEqual(result1, [1, 2, 3, 4, 5])
        self.assertEqual(call_count['count'], 1)

        # Second call - cache hit
        result2 = get_data()
        self.assertEqual(result2, [1, 2, 3, 4, 5])
        self.assertEqual(call_count['count'], 1)  # Function called only once

    def test_cache_queryset_with_mock_queryset(self):
        """Test queryset caching with mock QuerySet."""
        call_count = {'count': 0}

        @cache_queryset(timeout=60)
        def get_queryset():
            call_count['count'] += 1
            # Mock QuerySet
            mock_qs = Mock()
            mock_qs.__iter__ = Mock(return_value=iter([1, 2, 3]))
            return mock_qs

        # First call
        result1 = get_queryset()
        self.assertEqual(call_count['count'], 1)

        # Second call - should be cached
        result2 = get_queryset()
        self.assertEqual(call_count['count'], 1)


class CacheMethodDecoratorTests(TestCase):
    """Test cache_method decorator."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_cache_method_basic(self):
        """Test basic method caching."""
        class TestService:
            def __init__(self):
                self.call_count = 0

            @cache_method(timeout=60)
            def get_data(self, value):
                self.call_count += 1
                return value * 2

        service = TestService()

        # First call - cache miss
        result1 = service.get_data(5)
        self.assertEqual(result1, 10)
        self.assertEqual(service.call_count, 1)

        # Second call with same args - cache hit
        result2 = service.get_data(5)
        self.assertEqual(result2, 10)
        self.assertEqual(service.call_count, 1)

        # Call with different args - cache miss
        result3 = service.get_data(10)
        self.assertEqual(result3, 20)
        self.assertEqual(service.call_count, 2)


class CacheInvalidationTests(TestCase):
    """Test cache invalidation functions."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_invalidate_cache_pattern(self):
        """Test invalidating cache by pattern."""
        # Set some cache values
        cache.set('api_cache:1:courses:list:abc123', 'value1', 300)
        cache.set('api_cache:1:courses:detail:xyz789', 'value2', 300)
        cache.set('api_cache:1:lessons:list:def456', 'value3', 300)

        # Verify they're set
        self.assertIsNotNone(cache.get('api_cache:1:courses:list:abc123'))
        self.assertIsNotNone(cache.get('api_cache:1:courses:detail:xyz789'))
        self.assertIsNotNone(cache.get('api_cache:1:lessons:list:def456'))

        # Invalidate courses pattern
        with patch('apps.api.cache.strategies.cache._cache') as mock_cache:
            mock_cache.delete_pattern = Mock(return_value=2)
            invalidate_cache('api_cache:1:courses:*')
            mock_cache.delete_pattern.assert_called_once_with('api_cache:1:courses:*')

    def test_invalidate_user_cache(self):
        """Test invalidating user-specific cache."""
        user_id = 123

        # Set user cache
        key = CacheKeyBuilder.build_user_key(user_id, 'progress')
        cache.set(key, 'user_data', 300)
        self.assertIsNotNone(cache.get(key))

        # Invalidate user cache
        with patch('apps.api.cache.strategies.cache._cache') as mock_cache:
            mock_cache.delete_pattern = Mock(return_value=1)
            invalidate_user_cache(user_id, 'progress')
            # Verify delete_pattern was called
            self.assertTrue(mock_cache.delete_pattern.called)

    def test_invalidate_model_cache(self):
        """Test invalidating model-specific cache."""
        # Set model cache
        key = CacheKeyBuilder.build('courses', 'list')
        cache.set(key, 'model_data', 300)
        self.assertIsNotNone(cache.get(key))

        # Invalidate model cache
        with patch('apps.api.cache.strategies.cache._cache') as mock_cache:
            mock_cache.delete_pattern = Mock(return_value=1)
            invalidate_model_cache('courses')
            # Verify delete_pattern was called
            self.assertTrue(mock_cache.delete_pattern.called)


class CacheTimeoutTests(TestCase):
    """Test CacheTimeout constants."""

    def test_timeout_constants(self):
        """Test that timeout constants have expected values."""
        self.assertEqual(CacheTimeout.VERY_SHORT, 30)
        self.assertEqual(CacheTimeout.SHORT, 60)
        self.assertEqual(CacheTimeout.MEDIUM, 300)
        self.assertEqual(CacheTimeout.LONG, 900)
        self.assertEqual(CacheTimeout.VERY_LONG, 3600)
        self.assertEqual(CacheTimeout.DAY, 86400)

    def test_timeout_constants_are_integers(self):
        """Test that all timeout constants are integers."""
        for attr in ['VERY_SHORT', 'SHORT', 'MEDIUM', 'LONG', 'VERY_LONG', 'DAY']:
            value = getattr(CacheTimeout, attr)
            self.assertIsInstance(value, int)
