"""
Tests for management commands.
Tests benchmark and warm_cache commands.
"""

import io
from unittest.mock import Mock, patch, MagicMock, call
from django.test import TestCase
from django.core.management import call_command
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()


class BenchmarkCommandTests(TestCase):
    """Test benchmark management command."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()
        # Clean up any test users
        User.objects.filter(username='benchmark_user').delete()

    @patch('apps.api.management.commands.benchmark.Client')
    def test_benchmark_command_basic_execution(self, mock_client_class):
        """Test basic benchmark command execution."""
        # Mock client responses
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client.force_login.return_value = None

        # Mock connection queries
        with patch('apps.api.management.commands.benchmark.connection') as mock_conn:
            mock_conn.queries = []

            # Capture output
            out = io.StringIO()
            call_command('benchmark', iterations=2, stdout=out)

        output = out.getvalue()

        # Should have benchmark header
        self.assertIn('Performance Benchmark', output)
        self.assertIn('Benchmark Results', output)

    @patch('apps.api.management.commands.benchmark.Client')
    def test_benchmark_with_warm_cache_option(self, mock_client_class):
        """Test benchmark with cache warming."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client.force_login.return_value = None

        with patch('apps.api.management.commands.benchmark.warmer') as mock_warmer, \
             patch('apps.api.management.commands.benchmark.connection') as mock_conn:
            mock_conn.queries = []
            mock_warmer.warm_all.return_value = {'total': 4, 'succeeded': 4}

            out = io.StringIO()
            call_command('benchmark', iterations=1, warm_cache=True, stdout=out)

        # Should call cache warming
        mock_warmer.warm_all.assert_called_once_with(verbose=False)

        output = out.getvalue()
        self.assertIn('Warming caches', output)

    @patch('apps.api.management.commands.benchmark.Client')
    def test_benchmark_with_clear_cache_option(self, mock_client_class):
        """Test benchmark with cache clearing."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client.force_login.return_value = None

        # Set some cache data
        cache.set('test_key', 'test_value')
        self.assertIsNotNone(cache.get('test_key'))

        with patch('apps.api.management.commands.benchmark.connection') as mock_conn:
            mock_conn.queries = []

            out = io.StringIO()
            call_command('benchmark', iterations=1, clear_cache=True, stdout=out)

        output = out.getvalue()
        self.assertIn('Clearing caches', output)

        # Cache should be cleared
        self.assertIsNone(cache.get('test_key'))

    @patch('apps.api.management.commands.benchmark.Client')
    def test_benchmark_verbose_mode(self, mock_client_class):
        """Test benchmark with verbose output."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client.force_login.return_value = None

        with patch('apps.api.management.commands.benchmark.connection') as mock_conn:
            mock_conn.queries = []

            out = io.StringIO()
            call_command('benchmark', iterations=2, verbose=True, stdout=out)

        output = out.getvalue()

        # Should show iteration details in verbose mode
        self.assertIn('Iteration 1:', output)
        self.assertIn('Iteration 2:', output)

    @patch('apps.api.management.commands.benchmark.Client')
    def test_benchmark_creates_test_user(self, mock_client_class):
        """Test that benchmark creates test user if needed."""
        # Ensure user doesn't exist
        User.objects.filter(username='benchmark_user').delete()

        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client.force_login.return_value = None

        with patch('apps.api.management.commands.benchmark.connection') as mock_conn:
            mock_conn.queries = []

            out = io.StringIO()
            call_command('benchmark', iterations=1, stdout=out)

        # User should have been created and deleted
        self.assertFalse(User.objects.filter(username='benchmark_user').exists())

    @patch('apps.api.management.commands.benchmark.Client')
    def test_benchmark_uses_existing_user(self, mock_client_class):
        """Test that benchmark uses existing user if available."""
        # Create user beforehand
        user = User.objects.create_user(
            username='benchmark_user',
            email='benchmark@test.com',
            password='test123'
        )

        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client.force_login.return_value = None

        with patch('apps.api.management.commands.benchmark.connection') as mock_conn:
            mock_conn.queries = []

            out = io.StringIO()
            call_command('benchmark', iterations=1, stdout=out)

        # User should still exist (not deleted)
        self.assertTrue(User.objects.filter(username='benchmark_user').exists())

        # Cleanup
        user.delete()

    @patch('apps.api.management.commands.benchmark.Client')
    def test_benchmark_endpoint_method(self, mock_client_class):
        """Test _benchmark_endpoint method."""
        from apps.api.management.commands.benchmark import Command

        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response

        command = Command()
        command.stdout = io.StringIO()

        with patch('apps.api.management.commands.benchmark.connection') as mock_conn, \
             patch('apps.api.management.commands.benchmark.reset_queries'):
            mock_conn.queries = [{'time': '0.015'}, {'time': '0.023'}]

            result = command._benchmark_endpoint(
                mock_client, 'GET', '/api/v1/test/', iterations=3, verbose=False
            )

        # Should return result dict
        self.assertIn('endpoint', result)
        self.assertIn('avg_time_ms', result)
        self.assertIn('min_time_ms', result)
        self.assertIn('max_time_ms', result)
        self.assertIn('avg_queries', result)
        self.assertEqual(result['endpoint'], 'GET /api/v1/test/')
        self.assertEqual(result['iterations'], 3)

    @patch('apps.api.management.commands.benchmark.Client')
    def test_benchmark_print_results_method(self, mock_client_class):
        """Test _print_results method."""
        from apps.api.management.commands.benchmark import Command

        command = Command()
        out = io.StringIO()
        command.stdout = out

        results = [
            {
                'endpoint': 'GET /api/v1/courses/',
                'iterations': 10,
                'avg_time_ms': 125.5,
                'min_time_ms': 98.2,
                'max_time_ms': 203.1,
                'avg_queries': 15.2,
                'status_code': 200,
            },
            {
                'endpoint': 'GET /api/v1/categories/',
                'iterations': 10,
                'avg_time_ms': 45.3,
                'min_time_ms': 32.1,
                'max_time_ms': 78.9,
                'avg_queries': 5.0,
                'status_code': 200,
            },
        ]

        command._print_results(results)

        output = out.getvalue()

        # Should have formatted table
        self.assertIn('Benchmark Results', output)
        self.assertIn('Endpoint', output)
        self.assertIn('Avg (ms)', output)
        self.assertIn('GET /api/v1/courses/', output)
        self.assertIn('GET /api/v1/categories/', output)
        self.assertIn('Average response time:', output)
        self.assertIn('Average queries per request:', output)

    @patch('apps.api.management.commands.benchmark.Client')
    def test_benchmark_performance_rating_excellent(self, mock_client_class):
        """Test performance rating for excellent performance."""
        from apps.api.management.commands.benchmark import Command

        command = Command()
        out = io.StringIO()
        command.stdout = out

        # Results with excellent performance
        results = [
            {
                'endpoint': 'GET /api/v1/test/',
                'iterations': 10,
                'avg_time_ms': 50.0,  # <100ms = excellent
                'min_time_ms': 45.0,
                'max_time_ms': 55.0,
                'avg_queries': 5.0,   # <10 = excellent
                'status_code': 200,
            }
        ]

        command._print_results(results)

        output = out.getvalue()
        self.assertIn('✅ EXCELLENT', output)

    @patch('apps.api.management.commands.benchmark.Client')
    def test_benchmark_performance_rating_slow(self, mock_client_class):
        """Test performance rating for slow performance."""
        from apps.api.management.commands.benchmark import Command

        command = Command()
        out = io.StringIO()
        command.stdout = out

        # Results with poor performance
        results = [
            {
                'endpoint': 'GET /api/v1/test/',
                'iterations': 10,
                'avg_time_ms': 600.0,  # >500ms = slow
                'min_time_ms': 550.0,
                'max_time_ms': 650.0,
                'avg_queries': 60.0,   # >50 = poor
                'status_code': 200,
            }
        ]

        command._print_results(results)

        output = out.getvalue()
        self.assertIn('❌', output)


class WarmCacheCommandTests(TestCase):
    """Test warm_cache management command."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def tearDown(self):
        cache.clear()
        User.objects.all().delete()

    @patch('apps.api.management.commands.warm_cache.warmer')
    def test_warm_cache_all_caches(self, mock_warmer):
        """Test warming all caches."""
        mock_warmer.warm_all.return_value = {
            'total': 4,
            'succeeded': 4,
            'failed': 0,
            'errors': []
        }

        out = io.StringIO()
        call_command('warm_cache', stdout=out)

        # Should call warmer.warm_all
        mock_warmer.warm_all.assert_called_once_with(verbose=True)

        output = out.getvalue()
        self.assertIn('Successfully warmed all 4 caches', output)

    @patch('apps.api.management.commands.warm_cache.warmer')
    def test_warm_cache_with_failures(self, mock_warmer):
        """Test warming caches with some failures."""
        mock_warmer.warm_all.return_value = {
            'total': 4,
            'succeeded': 3,
            'failed': 1,
            'errors': [
                {'task': 'warm_courses', 'error': 'Database error'}
            ]
        }

        out = io.StringIO()
        call_command('warm_cache', stdout=out)

        output = out.getvalue()
        self.assertIn('Warmed 3/4 caches', output)
        self.assertIn('warm_courses', output)
        self.assertIn('Database error', output)

    @patch('apps.api.management.commands.warm_cache.warmer')
    def test_warm_cache_quiet_mode(self, mock_warmer):
        """Test warm_cache with quiet mode."""
        mock_warmer.warm_all.return_value = {
            'total': 4,
            'succeeded': 4,
            'failed': 0,
            'errors': []
        }

        out = io.StringIO()
        call_command('warm_cache', quiet=True, stdout=out)

        # Should call with verbose=False
        mock_warmer.warm_all.assert_called_once_with(verbose=False)

    @patch('apps.api.management.commands.warm_cache.warmer')
    def test_warm_cache_user_specific(self, mock_warmer):
        """Test warming user-specific caches."""
        mock_warmer.warm_user_specific.return_value = {
            'user_id': self.user.id,
            'tasks': ['enrollments', 'progress', 'submissions']
        }

        out = io.StringIO()
        call_command('warm_cache', user_id=self.user.id, stdout=out)

        # Should call warmer.warm_user_specific
        mock_warmer.warm_user_specific.assert_called_once_with(
            self.user.id,
            verbose=True
        )

        output = out.getvalue()
        self.assertIn(f'Warmed caches for user {self.user.id}', output)
        self.assertIn('enrollments', output)
        self.assertIn('progress', output)
        self.assertIn('submissions', output)

    @patch('apps.api.management.commands.warm_cache.warmer')
    def test_warm_cache_nonexistent_user(self, mock_warmer):
        """Test warming caches for non-existent user."""
        mock_warmer.warm_user_specific.return_value = {
            'error': 'User not found'
        }

        out = io.StringIO()
        call_command('warm_cache', user_id=99999, stdout=out)

        output = out.getvalue()
        self.assertIn('Error: User not found', output)

    @patch('apps.api.management.commands.warm_cache.warmer')
    def test_warm_cache_user_with_quiet(self, mock_warmer):
        """Test user-specific warming with quiet mode."""
        mock_warmer.warm_user_specific.return_value = {
            'user_id': self.user.id,
            'tasks': ['enrollments']
        }

        out = io.StringIO()
        call_command('warm_cache', user_id=self.user.id, quiet=True, stdout=out)

        # Should call with verbose=False
        mock_warmer.warm_user_specific.assert_called_once_with(
            self.user.id,
            verbose=False
        )


class CommandIntegrationTests(TestCase):
    """Integration tests for management commands."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_warm_cache_command_exists(self):
        """Test that warm_cache command is available."""
        # Should not raise CommandError
        out = io.StringIO()
        with patch('apps.api.management.commands.warm_cache.warmer') as mock_warmer:
            mock_warmer.warm_all.return_value = {
                'total': 0, 'succeeded': 0, 'failed': 0, 'errors': []
            }
            call_command('warm_cache', stdout=out)

    def test_benchmark_command_exists(self):
        """Test that benchmark command is available."""
        # Should not raise CommandError
        out = io.StringIO()
        with patch('apps.api.management.commands.benchmark.Client') as mock_client_class, \
             patch('apps.api.management.commands.benchmark.connection') as mock_conn:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client.force_login.return_value = None
            mock_conn.queries = []

            call_command('benchmark', iterations=1, stdout=out)

    def test_commands_help_text(self):
        """Test that commands have help text."""
        from apps.api.management.commands.warm_cache import Command as WarmCacheCommand
        from apps.api.management.commands.benchmark import Command as BenchmarkCommand

        self.assertIn('warm', WarmCacheCommand.help.lower())
        self.assertIn('benchmark', BenchmarkCommand.help.lower())
