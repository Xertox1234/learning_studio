import time
from django.db import connection
from django.conf import settings


class QueryCountMiddleware:
    """
    Log slow requests with high query counts.
    Only active in development or with DEBUG=True.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start timer
        start_time = time.time()

        # Track queries
        if settings.DEBUG:
            start_queries = len(connection.queries)

        response = self.get_response(request)

        # Calculate metrics
        duration = time.time() - start_time

        if settings.DEBUG:
            query_count = len(connection.queries) - start_queries

            # Log if slow or high query count
            if duration > 1.0 or query_count > 20:
                print(f"\n⚠️  Slow request detected:")
                print(f"  Path: {request.path}")
                print(f"  Duration: {duration:.2f}s")
                print(f"  Queries: {query_count}")

                if query_count > 20:
                    print(f"  ⚠️  High query count! Consider optimization.")

        return response
