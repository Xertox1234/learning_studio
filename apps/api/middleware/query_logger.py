"""
Query logging middleware for development.
Logs database queries and helps identify N+1 query problems and slow queries.
"""

import re
import time
import logging
from django.db import connection, reset_queries
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class QueryLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log database queries in development.

    Features:
    - Logs total query count per request
    - Logs slow queries (> threshold)
    - Detects potential N+1 query problems
    - Only active when DEBUG=True and QUERY_LOGGING_ENABLED=True
    """

    # Configuration
    SLOW_QUERY_THRESHOLD = 0.05  # 50ms
    N_PLUS_1_THRESHOLD = 10  # If more than 10 similar queries, likely N+1

    def process_request(self, request):
        """Reset queries at start of request."""
        if settings.DEBUG and getattr(settings, 'QUERY_LOGGING_ENABLED', False):
            reset_queries()
            request._query_start_time = time.time()

    def process_response(self, request, response):
        """Log queries at end of request."""
        if not settings.DEBUG or not getattr(settings, 'QUERY_LOGGING_ENABLED', False):
            return response

        if not hasattr(request, '_query_start_time'):
            return response

        # Calculate total time
        total_time = time.time() - request._query_start_time

        # Get all queries
        queries = connection.queries
        num_queries = len(queries)

        if num_queries == 0:
            return response

        # Calculate query time
        query_time = sum(float(q['time']) for q in queries)

        # Log summary
        log_message = (
            f"\n{'='*80}\n"
            f"Query Summary for {request.method} {request.path}\n"
            f"{'='*80}\n"
            f"Total queries: {num_queries}\n"
            f"Query time: {query_time:.3f}s\n"
            f"Total time: {total_time:.3f}s\n"
            f"Query percentage: {(query_time/total_time*100):.1f}%\n"
        )

        # Detect slow queries
        slow_queries = [q for q in queries if float(q['time']) > self.SLOW_QUERY_THRESHOLD]
        if slow_queries:
            log_message += f"\n⚠️  {len(slow_queries)} SLOW QUERIES (>{self.SLOW_QUERY_THRESHOLD*1000}ms):\n"
            for i, query in enumerate(slow_queries, 1):
                log_message += f"\n{i}. Time: {float(query['time'])*1000:.1f}ms\n"
                log_message += f"   SQL: {query['sql'][:200]}...\n"

        # Detect potential N+1 queries
        similar_queries = self._detect_similar_queries(queries)
        if similar_queries:
            log_message += f"\n⚠️  POTENTIAL N+1 QUERIES DETECTED:\n"
            for pattern, count in similar_queries.items():
                if count > self.N_PLUS_1_THRESHOLD:
                    log_message += f"   {count}x: {pattern[:150]}...\n"

        # Performance rating
        if num_queries > 50:
            log_message += "\n❌ POOR: Too many queries (>50)\n"
        elif num_queries > 20:
            log_message += "\n⚠️  WARNING: High query count (>20)\n"
        elif slow_queries:
            log_message += "\n⚠️  WARNING: Slow queries detected\n"
        else:
            log_message += "\n✅ GOOD: Query performance looks good\n"

        log_message += f"{'='*80}\n"

        logger.info(log_message)

        return response

    def _detect_similar_queries(self, queries):
        """
        Detect similar queries that might indicate N+1 problems.
        Groups queries by normalized SQL pattern.
        """
        patterns = {}

        for query in queries:
            sql = query['sql']

            # Normalize SQL by removing specific values
            # This is a simple approach - could be more sophisticated
            normalized = sql

            # Remove specific IDs, strings, numbers
            normalized = re.sub(r'\b\d+\b', 'N', normalized)
            normalized = re.sub(r"'[^']*'", "'X'", normalized)
            normalized = re.sub(r'"[^"]*"', '"X"', normalized)

            # Count occurrences
            patterns[normalized] = patterns.get(normalized, 0) + 1

        # Return only patterns that occur multiple times
        return {k: v for k, v in patterns.items() if v > self.N_PLUS_1_THRESHOLD}
