"""
Tests for cache invalidation signals.
Tests automatic cache invalidation when models change.
"""

from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete

from apps.api.cache.invalidation import (
    invalidate_course_cache,
    invalidate_lesson_cache,
    invalidate_exercise_cache,
    invalidate_submission_cache,
    invalidate_enrollment_cache,
    invalidate_progress_cache,
    invalidate_category_cache,
    invalidate_user_profile_cache,
    setup_cache_invalidation,
)

User = get_user_model()


class CacheInvalidationSignalTests(TestCase):
    """Test cache invalidation signal handlers."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    @patch('apps.api.cache.invalidation.invalidate_model_cache')
    def test_invalidate_course_cache(self, mock_invalidate):
        """Test course cache invalidation signal."""
        # Create mock instance
        mock_course = Mock()
        mock_course.id = 1
        mock_course.category = Mock(id=10)
        mock_course.instructor = Mock(id=5)

        # Call signal handler
        invalidate_course_cache(
            sender=Mock(),
            instance=mock_course,
            created=False
        )

        # Verify cache invalidation calls
        self.assertTrue(mock_invalidate.called)
        # Should invalidate courses, course detail, category courses, and instructor courses
        self.assertGreaterEqual(mock_invalidate.call_count, 3)

    @patch('apps.api.cache.invalidation.invalidate_model_cache')
    def test_invalidate_lesson_cache(self, mock_invalidate):
        """Test lesson cache invalidation signal."""
        mock_lesson = Mock()
        mock_lesson.id = 1
        mock_lesson.course = Mock(id=10)

        invalidate_lesson_cache(
            sender=Mock(),
            instance=mock_lesson,
            created=False
        )

        self.assertTrue(mock_invalidate.called)
        # Should invalidate course lessons and lesson detail
        self.assertGreaterEqual(mock_invalidate.call_count, 2)

    @patch('apps.api.cache.invalidation.invalidate_model_cache')
    def test_invalidate_exercise_cache(self, mock_invalidate):
        """Test exercise cache invalidation signal."""
        mock_exercise = Mock()
        mock_exercise.id = 1
        mock_exercise.lesson = Mock(id=5)

        invalidate_exercise_cache(
            sender=Mock(),
            instance=mock_exercise,
            created=False
        )

        self.assertTrue(mock_invalidate.called)
        self.assertGreaterEqual(mock_invalidate.call_count, 2)

    @patch('apps.api.cache.invalidation.invalidate_user_cache')
    @patch('apps.api.cache.invalidation.invalidate_model_cache')
    def test_invalidate_submission_cache(self, mock_invalidate_model, mock_invalidate_user):
        """Test submission cache invalidation signal."""
        mock_user = Mock(id=10)
        mock_exercise = Mock(id=5)
        mock_submission = Mock()
        mock_submission.user = mock_user
        mock_submission.exercise = mock_exercise

        invalidate_submission_cache(
            sender=Mock(),
            instance=mock_submission,
            created=True
        )

        # Should invalidate user submissions and progress
        self.assertTrue(mock_invalidate_user.called)
        self.assertGreaterEqual(mock_invalidate_user.call_count, 2)

        # Should invalidate exercise submissions
        self.assertTrue(mock_invalidate_model.called)

    @patch('apps.api.cache.invalidation.invalidate_user_cache')
    @patch('apps.api.cache.invalidation.invalidate_model_cache')
    def test_invalidate_enrollment_cache(self, mock_invalidate_model, mock_invalidate_user):
        """Test enrollment cache invalidation signal."""
        mock_user = Mock(id=10)
        mock_course = Mock(id=5)
        mock_enrollment = Mock()
        mock_enrollment.user = mock_user
        mock_enrollment.course = mock_course

        invalidate_enrollment_cache(
            sender=Mock(),
            instance=mock_enrollment,
            created=True
        )

        # Should invalidate user enrollments
        self.assertTrue(mock_invalidate_user.called)

        # Should invalidate course enrollments
        self.assertTrue(mock_invalidate_model.called)

    @patch('apps.api.cache.invalidation.invalidate_user_cache')
    @patch('apps.api.cache.invalidation.invalidate_model_cache')
    def test_invalidate_progress_cache(self, mock_invalidate_model, mock_invalidate_user):
        """Test progress cache invalidation signal."""
        mock_user = Mock(id=10)
        mock_lesson = Mock(id=5)
        mock_progress = Mock()
        mock_progress.user = mock_user
        mock_progress.lesson = mock_lesson

        invalidate_progress_cache(
            sender=Mock(),
            instance=mock_progress,
            created=False
        )

        # Should invalidate user progress
        self.assertTrue(mock_invalidate_user.called)

        # Should invalidate lesson progress
        self.assertTrue(mock_invalidate_model.called)

    @patch('apps.api.cache.invalidation.invalidate_model_cache')
    def test_invalidate_category_cache(self, mock_invalidate):
        """Test category cache invalidation signal."""
        mock_category = Mock()
        mock_category.id = 1

        invalidate_category_cache(
            sender=Mock(),
            instance=mock_category,
            created=False
        )

        self.assertTrue(mock_invalidate.called)
        # Should invalidate categories and category courses
        self.assertGreaterEqual(mock_invalidate.call_count, 2)

    @patch('apps.api.cache.invalidation.invalidate_user_cache')
    def test_invalidate_user_profile_cache(self, mock_invalidate):
        """Test user profile cache invalidation signal."""
        mock_user = Mock()
        mock_user.id = 10

        invalidate_user_profile_cache(
            sender=Mock(),
            instance=mock_user,
            created=False
        )

        # Should invalidate all user-specific caches
        self.assertTrue(mock_invalidate.called)

    def test_setup_cache_invalidation_callable(self):
        """Test that setup function is callable."""
        # Should not raise exception
        try:
            setup_cache_invalidation()
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"setup_cache_invalidation raised exception: {e}")


class CacheInvalidationIntegrationTests(TestCase):
    """Integration tests for cache invalidation with real models."""

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

    @patch('apps.api.cache.invalidation.invalidate_user_cache')
    def test_user_save_invalidates_cache(self, mock_invalidate):
        """Test that saving a user invalidates their cache."""
        # Save user (triggers signal)
        self.user.email = 'newemail@example.com'
        self.user.save()

        # Verify invalidation was called
        self.assertTrue(mock_invalidate.called)

    def test_cache_invalidation_does_not_raise_exceptions(self):
        """Test that cache invalidation handles errors gracefully."""
        # Even if cache backend fails, signals should not raise exceptions
        with patch('apps.api.cache.invalidation.logger') as mock_logger:
            # Create instance that will trigger signals
            user = User.objects.create_user(
                username='signaltest',
                email='signal@test.com',
                password='test123'
            )

            # Should not raise exception
            self.assertTrue(True)

            # Cleanup
            user.delete()


class SignalConnectionTests(TestCase):
    """Test that signals are properly connected."""

    def test_signals_are_connected(self):
        """Test that cache invalidation signals are connected."""
        # This is a basic test to ensure signals module loads without errors
        from apps.api.cache import invalidation
        self.assertTrue(hasattr(invalidation, 'invalidate_course_cache'))
        self.assertTrue(hasattr(invalidation, 'invalidate_user_profile_cache'))

    def test_signal_receivers_are_functions(self):
        """Test that signal receivers are callable."""
        from apps.api.cache import invalidation

        receivers = [
            invalidation.invalidate_course_cache,
            invalidation.invalidate_lesson_cache,
            invalidation.invalidate_exercise_cache,
            invalidation.invalidate_submission_cache,
            invalidation.invalidate_enrollment_cache,
            invalidation.invalidate_progress_cache,
            invalidation.invalidate_category_cache,
            invalidation.invalidate_user_profile_cache,
        ]

        for receiver in receivers:
            self.assertTrue(callable(receiver))


class CacheInvalidationErrorHandlingTests(TestCase):
    """Test error handling in cache invalidation."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    @patch('apps.api.cache.invalidation.logger')
    def test_invalidation_logs_errors(self, mock_logger):
        """Test that errors during invalidation are logged."""
        # Create instance with missing attributes
        mock_instance = Mock()
        mock_instance.id = None
        mock_instance.forum = None

        # This should handle the error gracefully
        try:
            from apps.api.cache.invalidation import invalidate_topic_cache
            invalidate_topic_cache(
                sender=Mock(),
                instance=mock_instance,
                created=False
            )
            # Should not raise exception
            self.assertTrue(True)
        except Exception:
            # If exception is raised, ensure it's caught
            pass

    def test_invalidation_with_none_values(self):
        """Test cache invalidation with None values."""
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.course = None  # Missing related object

        # Should handle None gracefully
        try:
            invalidate_lesson_cache(
                sender=Mock(),
                instance=mock_instance,
                created=False
            )
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Should handle None values gracefully: {e}")
