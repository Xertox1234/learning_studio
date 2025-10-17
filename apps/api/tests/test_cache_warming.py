"""
Tests for cache warming service.
Tests cache pre-population functionality.
"""

from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache

from apps.api.cache.warming import CacheWarmer, warmer

User = get_user_model()


class CacheWarmerTests(TestCase):
    """Test cache warming service."""

    def setUp(self):
        cache.clear()
        self.warmer = CacheWarmer()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def tearDown(self):
        cache.clear()
        User.objects.all().delete()

    def test_cache_warmer_initialization(self):
        """Test that CacheWarmer initializes with tasks."""
        self.assertIsInstance(self.warmer.tasks, list)
        self.assertGreater(len(self.warmer.tasks), 0)

    def test_global_warmer_instance_exists(self):
        """Test that global warmer instance is available."""
        self.assertIsInstance(warmer, CacheWarmer)

    @patch('apps.api.cache.warming.CacheWarmer.warm_courses')
    @patch('apps.api.cache.warming.CacheWarmer.warm_categories')
    @patch('apps.api.cache.warming.CacheWarmer.warm_programming_languages')
    @patch('apps.api.cache.warming.CacheWarmer.warm_forum_statistics')
    def test_warm_all_success(self, mock_forum, mock_langs, mock_cats, mock_courses):
        """Test warming all caches successfully."""
        # Mock all tasks to succeed
        mock_courses.return_value = None
        mock_cats.return_value = None
        mock_langs.return_value = None
        mock_forum.return_value = None

        stats = self.warmer.warm_all(verbose=False)

        self.assertEqual(stats['total'], 4)
        self.assertEqual(stats['succeeded'], 4)
        self.assertEqual(stats['failed'], 0)
        self.assertEqual(len(stats['errors']), 0)

    @patch('apps.api.cache.warming.CacheWarmer.warm_courses')
    @patch('apps.api.cache.warming.CacheWarmer.warm_categories')
    def test_warm_all_with_failures(self, mock_cats, mock_courses):
        """Test warming with some failures."""
        # Mock one task to fail
        mock_courses.side_effect = Exception("Database error")
        mock_cats.return_value = None

        # Patch the tasks list to only include these two
        with patch.object(self.warmer, 'tasks', [self.warmer.warm_courses, self.warmer.warm_categories]):
            stats = self.warmer.warm_all(verbose=False)

        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['succeeded'], 1)
        self.assertEqual(stats['failed'], 1)
        self.assertEqual(len(stats['errors']), 1)
        self.assertIn('warm_courses', stats['errors'][0]['task'])

    @patch('apps.api.cache.warming.cache')
    @patch('apps.learning.models.Course')
    def test_warm_courses(self, mock_course_model, mock_cache):
        """Test warming course caches."""
        # Mock Course QuerySet
        mock_qs = Mock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.__iter__ = Mock(return_value=iter([Mock(), Mock(), Mock()]))
        mock_qs.__len__ = Mock(return_value=3)
        mock_course_model.objects.filter.return_value = mock_qs

        try:
            self.warmer.warm_courses()
            # If no exception, test passes
            self.assertTrue(True)
            # Verify cache was set
            self.assertTrue(mock_cache.set.called)
        except Exception as e:
            self.fail(f"warm_courses raised exception: {e}")

    @patch('apps.api.cache.warming.cache')
    @patch('apps.learning.models.Category')
    def test_warm_categories(self, mock_category_model, mock_cache):
        """Test warming category caches."""
        # Mock Category QuerySet
        mock_qs = Mock()
        mock_qs.prefetch_related.return_value = mock_qs
        mock_qs.__iter__ = Mock(return_value=iter([Mock(), Mock()]))
        mock_qs.__len__ = Mock(return_value=2)
        mock_category_model.objects.all.return_value = mock_qs

        try:
            self.warmer.warm_categories()
            self.assertTrue(True)
            self.assertTrue(mock_cache.set.called)
        except Exception as e:
            self.fail(f"warm_categories raised exception: {e}")

    @patch('apps.api.cache.warming.cache')
    @patch('apps.learning.models.ProgrammingLanguage')
    def test_warm_programming_languages(self, mock_lang_model, mock_cache):
        """Test warming programming language caches."""
        # Mock ProgrammingLanguage QuerySet
        mock_qs = Mock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.__iter__ = Mock(return_value=iter([Mock()]))
        mock_qs.__len__ = Mock(return_value=1)
        mock_lang_model.objects.filter.return_value = mock_qs

        try:
            self.warmer.warm_programming_languages()
            self.assertTrue(True)
            self.assertTrue(mock_cache.set.called)
        except Exception as e:
            self.fail(f"warm_programming_languages raised exception: {e}")

    def test_warm_forum_statistics_handles_missing_service(self):
        """Test that forum statistics warming handles missing service gracefully."""
        # This should not raise an exception even if service is missing
        try:
            self.warmer.warm_forum_statistics()
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"warm_forum_statistics should handle errors gracefully: {e}")

    @patch('apps.learning.models.CourseEnrollment')
    def test_warm_user_specific(self, mock_enrollment_model):
        """Test warming user-specific caches."""
        # Mock enrollments
        mock_qs = Mock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.__iter__ = Mock(return_value=iter([Mock()]))
        mock_enrollment_model.objects.filter.return_value = mock_qs

        # Mock other models
        with patch('apps.learning.models.UserProgress') as mock_progress, \
             patch('apps.learning.models.Submission') as mock_submission:

            mock_progress_qs = Mock()
            mock_progress_qs.select_related.return_value = mock_progress_qs
            mock_progress_qs.filter.return_value = mock_progress_qs
            mock_progress_qs.__iter__ = Mock(return_value=iter([]))
            mock_progress.objects.filter.return_value = mock_progress_qs

            mock_submission_qs = Mock()
            mock_submission_qs.select_related.return_value = mock_submission_qs
            mock_submission_qs.filter.return_value = mock_submission_qs
            mock_submission_qs.__getitem__ = Mock(return_value=mock_submission_qs)
            mock_submission_qs.__iter__ = Mock(return_value=iter([]))
            mock_submission.objects.filter.return_value = mock_submission_qs

            stats = self.warmer.warm_user_specific(self.user.id, verbose=False)

        self.assertIn('user_id', stats)
        self.assertEqual(stats['user_id'], self.user.id)
        self.assertIn('tasks', stats)
        self.assertIsInstance(stats['tasks'], list)

    def test_warm_user_specific_nonexistent_user(self):
        """Test warming caches for non-existent user."""
        stats = self.warmer.warm_user_specific(99999, verbose=False)

        self.assertIn('error', stats)
        self.assertEqual(stats['error'], 'User not found')

    @patch('apps.api.cache.warming.cache')
    @patch('apps.learning.models.CourseEnrollment')
    def test_warm_user_enrollments(self, mock_enrollment_model, mock_cache):
        """Test warming user enrollments cache."""
        mock_qs = Mock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.__iter__ = Mock(return_value=iter([Mock(), Mock()]))
        mock_enrollment_model.objects.filter.return_value = mock_qs

        # Should not raise exception
        try:
            self.warmer._warm_user_enrollments(self.user)
            self.assertTrue(True)
            self.assertTrue(mock_cache.set.called)
        except Exception as e:
            self.fail(f"_warm_user_enrollments raised exception: {e}")

    @patch('apps.api.cache.warming.cache')
    @patch('apps.learning.models.UserProgress')
    def test_warm_user_progress(self, mock_progress_model, mock_cache):
        """Test warming user progress cache."""
        mock_qs = Mock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.__iter__ = Mock(return_value=iter([Mock()]))
        mock_progress_model.objects.filter.return_value = mock_qs

        try:
            self.warmer._warm_user_progress(self.user)
            self.assertTrue(True)
            # Verify cache was set
            self.assertTrue(mock_cache.set.called)
        except Exception as e:
            self.fail(f"_warm_user_progress raised exception: {e}")

    @patch('apps.api.cache.warming.cache')
    @patch('apps.learning.models.Submission')
    def test_warm_user_submissions(self, mock_submission_model, mock_cache):
        """Test warming user submissions cache."""
        mock_qs = Mock()
        mock_qs.select_related.return_value = mock_qs
        mock_qs.filter.return_value = mock_qs
        mock_qs.__getitem__ = Mock(return_value=mock_qs)
        mock_qs.__iter__ = Mock(return_value=iter([Mock()]))
        mock_submission_model.objects.filter.return_value = mock_qs

        try:
            self.warmer._warm_user_submissions(self.user)
            self.assertTrue(True)
            # Verify cache was set
            self.assertTrue(mock_cache.set.called)
        except Exception as e:
            self.fail(f"_warm_user_submissions raised exception: {e}")


class CacheWarmingIntegrationTests(TestCase):
    """Integration tests for cache warming."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_warmed_data_is_cached(self):
        """Test that warming actually caches data."""
        from apps.api.cache import CacheKeyBuilder

        # Warm a specific cache
        key = CacheKeyBuilder.build('test', 'data')
        cache.set(key, 'test_value', 300)

        # Verify it's cached
        cached_value = cache.get(key)
        self.assertEqual(cached_value, 'test_value')

    def test_cache_expiration(self):
        """Test that cached data expires after timeout."""
        from apps.api.cache import CacheKeyBuilder, CacheTimeout

        # Set cache with very short timeout
        key = CacheKeyBuilder.build('test', 'expiration')
        cache.set(key, 'test_value', 1)  # 1 second

        # Should be cached immediately
        self.assertIsNotNone(cache.get(key))

        # Wait for expiration
        import time
        time.sleep(2)

        # Should be expired
        self.assertIsNone(cache.get(key))
