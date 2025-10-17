"""
Tests for middleware components.
Tests query logging and performance tracking middleware.
"""

import time
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory, override_settings
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.core.cache import cache

from apps.api.middleware.query_logger import QueryLoggingMiddleware
from apps.api.middleware.performance import PerformanceTrackingMiddleware

User = get_user_model()


class QueryLoggingMiddlewareTests(TestCase):
    """Test QueryLoggingMiddleware functionality."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = QueryLoggingMiddleware(get_response=lambda r: HttpResponse())

    @override_settings(DEBUG=True, QUERY_LOGGING_ENABLED=True)
    @patch('apps.api.middleware.query_logger.reset_queries')
    def test_process_request_resets_queries(self, mock_reset):
        """Test that process_request resets queries when enabled."""
        request = self.factory.get('/test/')

        self.middleware.process_request(request)

        # Should reset queries and set start time
        mock_reset.assert_called_once()
        self.assertTrue(hasattr(request, '_query_start_time'))

    @override_settings(DEBUG=False)
    @patch('apps.api.middleware.query_logger.reset_queries')
    def test_process_request_skips_when_debug_false(self, mock_reset):
        """Test that process_request skips when DEBUG=False."""
        request = self.factory.get('/test/')

        self.middleware.process_request(request)

        # Should not reset queries or set start time
        mock_reset.assert_not_called()
        self.assertFalse(hasattr(request, '_query_start_time'))

    @override_settings(DEBUG=True, QUERY_LOGGING_ENABLED=False)
    @patch('apps.api.middleware.query_logger.reset_queries')
    def test_process_request_skips_when_logging_disabled(self, mock_reset):
        """Test that process_request skips when logging disabled."""
        request = self.factory.get('/test/')

        self.middleware.process_request(request)

        mock_reset.assert_not_called()

    @override_settings(DEBUG=True, QUERY_LOGGING_ENABLED=True)
    @patch('apps.api.middleware.query_logger.connection')
    @patch('apps.api.middleware.query_logger.logger')
    def test_process_response_logs_queries(self, mock_logger, mock_connection):
        """Test that process_response logs query information."""
        request = self.factory.get('/test/')
        request._query_start_time = time.time() - 0.1  # 100ms ago
        response = HttpResponse()

        # Mock queries
        mock_connection.queries = [
            {'time': '0.015', 'sql': 'SELECT * FROM users WHERE id = 1'},
            {'time': '0.023', 'sql': 'SELECT * FROM courses WHERE published = true'},
        ]

        result = self.middleware.process_response(request, response)

        # Should log query information
        self.assertTrue(mock_logger.info.called)
        log_message = mock_logger.info.call_args[0][0]
        self.assertIn('Total queries: 2', log_message)
        self.assertIn('Query time:', log_message)

    @override_settings(DEBUG=True, QUERY_LOGGING_ENABLED=True)
    @patch('apps.api.middleware.query_logger.connection')
    @patch('apps.api.middleware.query_logger.logger')
    def test_process_response_detects_slow_queries(self, mock_logger, mock_connection):
        """Test that slow queries are detected and logged."""
        request = self.factory.get('/test/')
        request._query_start_time = time.time()
        response = HttpResponse()

        # Mock slow query (>50ms)
        mock_connection.queries = [
            {'time': '0.075', 'sql': 'SELECT * FROM users JOIN courses ON ...'},
        ]

        self.middleware.process_response(request, response)

        log_message = mock_logger.info.call_args[0][0]
        self.assertIn('SLOW QUERIES', log_message)
        self.assertIn('75.0ms', log_message)

    @override_settings(DEBUG=True, QUERY_LOGGING_ENABLED=True)
    @patch('apps.api.middleware.query_logger.connection')
    @patch('apps.api.middleware.query_logger.logger')
    def test_process_response_detects_n_plus_1_queries(self, mock_logger, mock_connection):
        """Test that N+1 queries are detected."""
        request = self.factory.get('/test/')
        request._query_start_time = time.time()
        response = HttpResponse()

        # Mock N+1 queries (15 similar queries)
        similar_queries = [
            {'time': '0.005', 'sql': f'SELECT * FROM courses WHERE id = {i}'}
            for i in range(15)
        ]
        mock_connection.queries = similar_queries

        self.middleware.process_response(request, response)

        log_message = mock_logger.info.call_args[0][0]
        self.assertIn('POTENTIAL N+1 QUERIES', log_message)

    @override_settings(DEBUG=True, QUERY_LOGGING_ENABLED=True)
    @patch('apps.api.middleware.query_logger.connection')
    @patch('apps.api.middleware.query_logger.logger')
    def test_process_response_performance_rating_good(self, mock_logger, mock_connection):
        """Test good performance rating."""
        request = self.factory.get('/test/')
        request._query_start_time = time.time()
        response = HttpResponse()

        # Mock few queries, all fast
        mock_connection.queries = [
            {'time': '0.005', 'sql': 'SELECT * FROM users WHERE id = 1'},
            {'time': '0.008', 'sql': 'SELECT * FROM courses'},
        ]

        self.middleware.process_response(request, response)

        log_message = mock_logger.info.call_args[0][0]
        self.assertIn('✅ GOOD', log_message)

    @override_settings(DEBUG=True, QUERY_LOGGING_ENABLED=True)
    @patch('apps.api.middleware.query_logger.connection')
    @patch('apps.api.middleware.query_logger.logger')
    def test_process_response_performance_rating_warning(self, mock_logger, mock_connection):
        """Test warning performance rating for high query count."""
        request = self.factory.get('/test/')
        request._query_start_time = time.time()
        response = HttpResponse()

        # Mock many queries (>20)
        mock_connection.queries = [
            {'time': '0.005', 'sql': f'SELECT * FROM table WHERE id = {i}'}
            for i in range(25)
        ]

        self.middleware.process_response(request, response)

        log_message = mock_logger.info.call_args[0][0]
        self.assertIn('WARNING: High query count', log_message)

    @override_settings(DEBUG=True, QUERY_LOGGING_ENABLED=True)
    @patch('apps.api.middleware.query_logger.connection')
    @patch('apps.api.middleware.query_logger.logger')
    def test_process_response_performance_rating_poor(self, mock_logger, mock_connection):
        """Test poor performance rating for very high query count."""
        request = self.factory.get('/test/')
        request._query_start_time = time.time()
        response = HttpResponse()

        # Mock too many queries (>50)
        mock_connection.queries = [
            {'time': '0.005', 'sql': f'SELECT * FROM table WHERE id = {i}'}
            for i in range(55)
        ]

        self.middleware.process_response(request, response)

        log_message = mock_logger.info.call_args[0][0]
        self.assertIn('❌ POOR', log_message)

    @override_settings(DEBUG=False)
    @patch('apps.api.middleware.query_logger.logger')
    def test_process_response_skips_when_debug_false(self, mock_logger):
        """Test that process_response skips when DEBUG=False."""
        request = self.factory.get('/test/')
        response = HttpResponse()

        result = self.middleware.process_response(request, response)

        # Should not log anything
        mock_logger.info.assert_not_called()
        self.assertEqual(result, response)

    def test_detect_similar_queries(self):
        """Test similar query detection logic."""
        queries = [
            {'sql': "SELECT * FROM users WHERE id = 1"},
            {'sql': "SELECT * FROM users WHERE id = 2"},
            {'sql': "SELECT * FROM users WHERE id = 3"},
            {'sql': "SELECT * FROM users WHERE id = 4"},
            {'sql': "SELECT * FROM users WHERE id = 5"},
            {'sql': "SELECT * FROM users WHERE id = 6"},
            {'sql': "SELECT * FROM users WHERE id = 7"},
            {'sql': "SELECT * FROM users WHERE id = 8"},
            {'sql': "SELECT * FROM users WHERE id = 9"},
            {'sql': "SELECT * FROM users WHERE id = 10"},
            {'sql': "SELECT * FROM users WHERE id = 11"},
        ]

        similar = self.middleware._detect_similar_queries(queries)

        # Should detect the pattern (>10 similar queries)
        self.assertGreater(len(similar), 0)


class PerformanceTrackingMiddlewareTests(TestCase):
    """Test PerformanceTrackingMiddleware functionality."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = PerformanceTrackingMiddleware(get_response=lambda r: HttpResponse())
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_process_request_sets_start_time(self):
        """Test that process_request sets start time."""
        request = self.factory.get('/test/')

        self.middleware.process_request(request)

        self.assertTrue(hasattr(request, '_perf_start_time'))
        self.assertIsInstance(request._perf_start_time, float)

    def test_process_request_initializes_cache_tracking(self):
        """Test that process_request initializes cache tracking."""
        request = self.factory.get('/test/')

        self.middleware.process_request(request)

        self.assertTrue(hasattr(request, '_perf_cache_hits'))
        self.assertTrue(hasattr(request, '_perf_cache_misses'))
        self.assertEqual(request._perf_cache_hits, 0)
        self.assertEqual(request._perf_cache_misses, 0)

    @override_settings(DEBUG=True)
    @patch('apps.api.middleware.performance.connection')
    def test_process_response_adds_performance_headers_in_debug(self, mock_connection):
        """Test that performance headers are added in DEBUG mode."""
        request = self.factory.get('/test/')
        request._perf_start_time = time.time() - 0.1  # 100ms ago
        request._cache_hits = 5
        request._cache_misses = 2
        response = HttpResponse()

        # Mock queries
        mock_connection.queries = [
            {'time': '0.015'},
            {'time': '0.023'},
        ]

        result = self.middleware.process_response(request, response)

        # Should have performance headers
        self.assertIn('X-Request-Time', result)
        self.assertIn('X-Query-Count', result)
        self.assertIn('X-Query-Time', result)
        self.assertIn('X-Cache-Hits', result)
        self.assertIn('X-Cache-Misses', result)
        self.assertIn('X-Cache-Hit-Ratio', result)

    @override_settings(DEBUG=False)
    def test_process_response_no_headers_in_production(self):
        """Test that performance headers are not added in production."""
        request = self.factory.get('/test/')
        request._perf_start_time = time.time()
        request._cache_hits = 0
        request._cache_misses = 0
        response = HttpResponse()

        result = self.middleware.process_response(request, response)

        # Should not have performance headers
        self.assertNotIn('X-Request-Time', result)
        self.assertNotIn('X-Query-Count', result)

    @override_settings(DEBUG=True)
    @patch('apps.api.middleware.performance.connection')
    def test_process_response_calculates_cache_hit_ratio(self, mock_connection):
        """Test cache hit ratio calculation."""
        request = self.factory.get('/test/')
        request._perf_start_time = time.time()
        request._cache_hits = 7
        request._cache_misses = 3
        response = HttpResponse()

        mock_connection.queries = []

        result = self.middleware.process_response(request, response)

        # Cache hit ratio should be 70% (7/10)
        self.assertIn('X-Cache-Hit-Ratio', result)
        self.assertEqual(result['X-Cache-Hit-Ratio'], '70.0%')

    @override_settings(DEBUG=True)
    @patch('apps.api.middleware.performance.connection')
    def test_process_response_handles_no_cache_operations(self, mock_connection):
        """Test handling when there are no cache operations."""
        request = self.factory.get('/test/')
        request._perf_start_time = time.time()
        request._cache_hits = 0
        request._cache_misses = 0
        response = HttpResponse()

        mock_connection.queries = []

        result = self.middleware.process_response(request, response)

        # Should handle 0/0 gracefully
        self.assertIn('X-Cache-Hit-Ratio', result)
        self.assertEqual(result['X-Cache-Hit-Ratio'], '0.0%')

    @patch('apps.api.middleware.performance.logger')
    @patch('apps.api.middleware.performance.connection')
    def test_process_response_logs_slow_requests(self, mock_connection, mock_logger):
        """Test that slow requests are logged."""
        request = self.factory.get('/test/')
        request._perf_start_time = time.time() - 1.5  # 1500ms ago (>1s threshold)
        request._cache_hits = 0
        request._cache_misses = 0
        response = HttpResponse()

        # Mock many queries
        mock_connection.queries = [
            {'time': '0.100'} for _ in range(20)
        ]

        self.middleware.process_response(request, response)

        # Should log slow request warning
        self.assertTrue(mock_logger.warning.called)
        log_message = mock_logger.warning.call_args[0][0]
        self.assertIn('SLOW REQUEST', log_message)

    @override_settings(DEBUG=True)
    @patch('apps.api.middleware.performance.connection')
    def test_process_response_query_time_calculation(self, mock_connection):
        """Test query time calculation."""
        request = self.factory.get('/test/')
        request._perf_start_time = time.time()
        request._cache_hits = 0
        request._cache_misses = 0
        response = HttpResponse()

        # Mock queries with known times
        mock_connection.queries = [
            {'time': '0.015'},
            {'time': '0.025'},
            {'time': '0.010'},
        ]

        result = self.middleware.process_response(request, response)

        # Total query time should be 50ms
        self.assertIn('X-Query-Time', result)
        query_time = float(result['X-Query-Time'].replace('s', ''))
        self.assertAlmostEqual(query_time, 0.050, places=3)

    def test_process_response_handles_missing_start_time(self):
        """Test that missing start time is handled gracefully."""
        request = self.factory.get('/test/')
        # Deliberately don't set _perf_start_time
        response = HttpResponse()

        # Should not crash
        result = self.middleware.process_response(request, response)
        self.assertEqual(result, response)

    @override_settings(DEBUG=True)
    @patch('apps.api.middleware.performance.connection')
    def test_response_time_header_format(self, mock_connection):
        """Test that response time header has correct format."""
        request = self.factory.get('/test/')
        request._perf_start_time = time.time() - 0.123  # 123ms ago
        request._cache_hits = 0
        request._cache_misses = 0
        response = HttpResponse()

        mock_connection.queries = []

        result = self.middleware.process_response(request, response)

        # Should be formatted as "0.123s"
        self.assertIn('X-Request-Time', result)
        self.assertRegex(result['X-Request-Time'], r'^\d+\.\d{3}s$')


class MiddlewareIntegrationTests(TestCase):
    """Integration tests for middleware components."""

    def setUp(self):
        self.factory = RequestFactory()
        cache.clear()

    def tearDown(self):
        cache.clear()

    @override_settings(DEBUG=True, QUERY_LOGGING_ENABLED=True)
    def test_both_middleware_work_together(self):
        """Test that both middleware can work together without conflicts."""
        request = self.factory.get('/test/')
        response = HttpResponse()

        # Create middleware instances
        query_middleware = QueryLoggingMiddleware(get_response=lambda r: response)
        perf_middleware = PerformanceTrackingMiddleware(get_response=lambda r: response)

        # Process request through both
        query_middleware.process_request(request)
        perf_middleware.process_request(request)

        # Should have attributes from both
        self.assertTrue(hasattr(request, '_query_start_time'))
        self.assertTrue(hasattr(request, '_perf_start_time'))
        self.assertTrue(hasattr(request, '_perf_cache_hits'))

    @override_settings(DEBUG=True)
    @patch('apps.api.middleware.performance.connection')
    def test_performance_headers_contain_valid_data(self, mock_connection):
        """Test that performance headers contain valid numeric data."""
        request = self.factory.get('/test/')
        request._perf_start_time = time.time() - 0.1
        request._cache_hits = 3
        request._cache_misses = 1
        response = HttpResponse()

        mock_connection.queries = [{'time': '0.015'}]

        middleware = PerformanceTrackingMiddleware(get_response=lambda r: response)
        result = middleware.process_response(request, response)

        # Verify all headers are present and valid
        self.assertRegex(result['X-Request-Time'], r'^\d+\.\d{3}s$')
        self.assertEqual(result['X-Query-Count'], '1')
        self.assertRegex(result['X-Query-Time'], r'^\d+\.\d{3}s$')
        self.assertEqual(result['X-Cache-Hits'], '3')
        self.assertEqual(result['X-Cache-Misses'], '1')
        self.assertEqual(result['X-Cache-Hit-Ratio'], '75.0%')
