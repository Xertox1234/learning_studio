"""
Performance benchmarking management command.

Runs performance benchmarks against key API endpoints and database queries.
"""

import time
from django.core.management.base import BaseCommand
from django.test.client import Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection, reset_queries
from apps.api.cache.warming import warmer

User = get_user_model()


class Command(BaseCommand):
    help = 'Run performance benchmarks against API endpoints'

    def add_arguments(self, parser):
        parser.add_argument(
            '--iterations',
            type=int,
            default=10,
            help='Number of iterations for each benchmark (default: 10)',
        )
        parser.add_argument(
            '--warm-cache',
            action='store_true',
            help='Warm caches before running benchmarks',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear caches before running benchmarks',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        iterations = options['iterations']
        verbose = options['verbose']

        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"="*80}\n'
                f'Performance Benchmark\n'
                f'{"="*80}\n'
            )
        )

        # Clear cache if requested
        if options['clear_cache']:
            self.stdout.write('Clearing caches...')
            cache.clear()

        # Warm cache if requested
        if options['warm_cache']:
            self.stdout.write('Warming caches...')
            warmer.warm_all(verbose=False)

        # Initialize client
        client = Client()

        # Create test user if doesn't exist
        user, created = User.objects.get_or_create(
            username='benchmark_user',
            defaults={'email': 'benchmark@test.com'}
        )
        if created:
            user.set_password('test123')
            user.save()

        # Run benchmarks
        results = []

        # Benchmark 1: Course list endpoint
        results.append(self._benchmark_endpoint(
            client, 'GET', '/api/v1/courses/', iterations, verbose
        ))

        # Benchmark 2: Categories endpoint
        results.append(self._benchmark_endpoint(
            client, 'GET', '/api/v1/categories/', iterations, verbose
        ))

        # Benchmark 3: Forum topics endpoint
        results.append(self._benchmark_endpoint(
            client, 'GET', '/api/v1/forum/topics/', iterations, verbose
        ))

        # Benchmark 4: User profile endpoint (authenticated)
        client.force_login(user)
        results.append(self._benchmark_endpoint(
            client, 'GET', '/api/v1/auth/user/', iterations, verbose
        ))

        # Print results
        self._print_results(results)

        # Cleanup
        if created:
            user.delete()

    def _benchmark_endpoint(self, client, method, url, iterations, verbose):
        """Benchmark a single endpoint."""
        self.stdout.write(f'\nBenchmarking: {method} {url}')

        times = []
        query_counts = []

        for i in range(iterations):
            reset_queries()
            start_time = time.time()

            if method == 'GET':
                response = client.get(url)
            elif method == 'POST':
                response = client.post(url)
            else:
                raise ValueError(f'Unsupported method: {method}')

            end_time = time.time()

            elapsed = end_time - start_time
            query_count = len(connection.queries)

            times.append(elapsed)
            query_counts.append(query_count)

            if verbose:
                self.stdout.write(
                    f'  Iteration {i+1}: {elapsed*1000:.2f}ms '
                    f'({query_count} queries, status: {response.status_code})'
                )

        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        avg_queries = sum(query_counts) / len(query_counts)

        return {
            'endpoint': f'{method} {url}',
            'iterations': iterations,
            'avg_time_ms': avg_time * 1000,
            'min_time_ms': min_time * 1000,
            'max_time_ms': max_time * 1000,
            'avg_queries': avg_queries,
            'status_code': response.status_code,
        }

    def _print_results(self, results):
        """Print benchmark results in a formatted table."""
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"="*80}\n'
                f'Benchmark Results\n'
                f'{"="*80}\n'
            )
        )

        # Print header
        header = (
            f"{'Endpoint':<40} "
            f"{'Avg (ms)':>10} "
            f"{'Min (ms)':>10} "
            f"{'Max (ms)':>10} "
            f"{'Queries':>8}"
        )
        self.stdout.write(header)
        self.stdout.write('-' * 80)

        # Print results
        for result in results:
            row = (
                f"{result['endpoint']:<40} "
                f"{result['avg_time_ms']:>10.2f} "
                f"{result['min_time_ms']:>10.2f} "
                f"{result['max_time_ms']:>10.2f} "
                f"{result['avg_queries']:>8.1f}"
            )
            self.stdout.write(row)

        self.stdout.write('-' * 80)

        # Performance rating
        avg_response_time = sum(r['avg_time_ms'] for r in results) / len(results)
        avg_queries_total = sum(r['avg_queries'] for r in results) / len(results)

        self.stdout.write(f'\n📊 Average response time: {avg_response_time:.2f}ms')
        self.stdout.write(f'📊 Average queries per request: {avg_queries_total:.1f}')

        if avg_response_time < 100:
            self.stdout.write(self.style.SUCCESS('✅ EXCELLENT: Very fast response times'))
        elif avg_response_time < 200:
            self.stdout.write(self.style.SUCCESS('✅ GOOD: Fast response times'))
        elif avg_response_time < 500:
            self.stdout.write(self.style.WARNING('⚠️  FAIR: Acceptable response times'))
        else:
            self.stdout.write(self.style.ERROR('❌ SLOW: Response times need optimization'))

        if avg_queries_total < 10:
            self.stdout.write(self.style.SUCCESS('✅ EXCELLENT: Low query count'))
        elif avg_queries_total < 20:
            self.stdout.write(self.style.SUCCESS('✅ GOOD: Reasonable query count'))
        elif avg_queries_total < 50:
            self.stdout.write(self.style.WARNING('⚠️  FAIR: High query count, consider optimization'))
        else:
            self.stdout.write(self.style.ERROR('❌ POOR: Very high query count, N+1 queries likely'))

        self.stdout.write('\n' + '=' * 80 + '\n')
