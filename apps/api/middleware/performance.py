"""
Performance tracking middleware.

Tracks response times, cache hits/misses, and database query counts.
"""

import time
import logging
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class PerformanceTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track performance metrics for each request.

    Metrics tracked:
    - Total request time
    - Database query count
    - Database query time
    - Cache hit/miss ratio
    - Response size
    """

    def process_request(self, request):
        """Start timing and reset query counters."""
        request._perf_start_time = time.time()
        request._perf_query_count_start = len(connection.queries)

        # Track cache hits/misses
        request._perf_cache_hits = 0
        request._perf_cache_misses = 0

    def process_response(self, request, response):
        """Log performance metrics."""
        if not hasattr(request, '_perf_start_time'):
            return response

        # Calculate metrics
        total_time = time.time() - request._perf_start_time
        query_count = len(connection.queries) - request._perf_query_count_start

        # Calculate query time
        query_time = 0
        if settings.DEBUG:
            query_time = sum(
                float(q['time'])
                for q in connection.queries[request._perf_query_count_start:]
            )

        # Add performance headers (for development/debugging)
        if settings.DEBUG:
            response['X-Request-Time'] = f'{total_time:.3f}s'
            response['X-Query-Count'] = str(query_count)
            response['X-Query-Time'] = f'{query_time:.3f}s'

        # Log slow requests
        threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD', 1.0)  # 1 second
        if total_time > threshold:
            logger.warning(
                f"SLOW REQUEST: {request.method} {request.path} "
                f"took {total_time:.3f}s "
                f"({query_count} queries, {query_time:.3f}s query time)"
            )

        # Log to performance metrics cache
        self._log_metrics(request, total_time, query_count, query_time)

        return response

    def _log_metrics(self, request, total_time, query_count, query_time):
        """
        Log performance metrics to cache for monitoring.

        Metrics are stored with a rolling window approach.
        """
        try:
            # Create metric key
            metric_key = f'perf_metrics:{request.path}'

            # Get existing metrics
            metrics = cache.get(metric_key, {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'max_time': 0,
                'min_time': float('inf'),
                'total_queries': 0,
                'avg_queries': 0,
            })

            # Update metrics
            metrics['count'] += 1
            metrics['total_time'] += total_time
            metrics['avg_time'] = metrics['total_time'] / metrics['count']
            metrics['max_time'] = max(metrics['max_time'], total_time)
            metrics['min_time'] = min(metrics['min_time'], total_time)
            metrics['total_queries'] += query_count
            metrics['avg_queries'] = metrics['total_queries'] / metrics['count']

            # Store updated metrics (5 minute rolling window)
            cache.set(metric_key, metrics, 300)

        except Exception as e:
            logger.error(f"Error logging performance metrics: {e}")


class CacheTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track cache hit/miss ratios.

    Adds metrics about cache usage to responses.
    """

    def process_response(self, request, response):
        """Add cache metrics to response headers."""
        if settings.DEBUG:
            # These would need to be set by the cache backend or decorators
            cache_hits = getattr(request, '_perf_cache_hits', 0)
            cache_misses = getattr(request, '_perf_cache_misses', 0)

            if cache_hits + cache_misses > 0:
                hit_ratio = cache_hits / (cache_hits + cache_misses) * 100
                response['X-Cache-Hits'] = str(cache_hits)
                response['X-Cache-Misses'] = str(cache_misses)
                response['X-Cache-Hit-Ratio'] = f'{hit_ratio:.1f}%'

        return response
