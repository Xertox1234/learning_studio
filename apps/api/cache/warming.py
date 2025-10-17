"""
Cache warming service for preloading frequently accessed data.

Warms caches on server startup or via management command to improve
initial request performance.
"""

import logging
from typing import List, Callable
from django.core.cache import cache
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()


class CacheWarmer:
    """
    Service for warming up caches with frequently accessed data.

    Usage:
        warmer = CacheWarmer()
        warmer.warm_all()
    """

    def __init__(self):
        self.tasks: List[Callable] = [
            self.warm_courses,
            self.warm_categories,
            self.warm_programming_languages,
            self.warm_forum_statistics,
        ]

    def warm_all(self, verbose: bool = True) -> dict:
        """
        Warm all caches.

        Args:
            verbose: Print progress messages

        Returns:
            dict: Statistics about cache warming
        """
        stats = {
            'total': len(self.tasks),
            'succeeded': 0,
            'failed': 0,
            'errors': [],
        }

        for task in self.tasks:
            task_name = getattr(task, '__name__', str(task))
            try:
                if verbose:
                    logger.info(f"Warming cache: {task_name}")

                task()
                stats['succeeded'] += 1

                if verbose:
                    logger.info(f"✓ {task_name} completed")

            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append({
                    'task': task_name,
                    'error': str(e),
                })

                logger.error(f"✗ {task_name} failed: {e}")

        if verbose:
            logger.info(
                f"\nCache warming complete: "
                f"{stats['succeeded']}/{stats['total']} tasks succeeded"
            )

        return stats

    def warm_courses(self):
        """Warm course list caches."""
        from apps.learning.models import Course
        from apps.api.cache import CacheKeyBuilder, CacheTimeout

        # Published courses
        courses = Course.objects.filter(is_published=True).select_related(
            'instructor', 'category'
        )

        cache_key = CacheKeyBuilder.build('courses', 'published')
        cache.set(cache_key, list(courses), CacheTimeout.MEDIUM)

        logger.info(f"Warmed {len(courses)} published courses")

        # Featured courses
        featured = Course.objects.filter(
            is_published=True,
            is_featured=True
        ).select_related('instructor', 'category')

        cache_key = CacheKeyBuilder.build('courses', 'featured')
        cache.set(cache_key, list(featured), CacheTimeout.LONG)

        logger.info(f"Warmed {len(featured)} featured courses")

    def warm_categories(self):
        """Warm category caches."""
        from apps.learning.models import Category
        from apps.api.cache import CacheKeyBuilder, CacheTimeout

        categories = Category.objects.all().prefetch_related('subcategories')

        cache_key = CacheKeyBuilder.build('categories', 'all')
        cache.set(cache_key, list(categories), CacheTimeout.VERY_LONG)

        logger.info(f"Warmed {len(categories)} categories")

    def warm_programming_languages(self):
        """Warm programming language caches."""
        from apps.learning.models import ProgrammingLanguage
        from apps.api.cache import CacheKeyBuilder, CacheTimeout

        languages = ProgrammingLanguage.objects.filter(is_active=True)

        cache_key = CacheKeyBuilder.build('languages', 'active')
        cache.set(cache_key, list(languages), CacheTimeout.VERY_LONG)

        logger.info(f"Warmed {len(languages)} programming languages")

    def warm_forum_statistics(self):
        """Warm forum statistics caches."""
        try:
            from apps.api.services.statistics_service import ForumStatisticsService
            from apps.api.cache import CacheKeyBuilder, CacheTimeout

            service = ForumStatisticsService()

            # Warm global statistics
            stats = service.get_global_statistics()
            cache_key = CacheKeyBuilder.build('forum', 'global_stats')
            cache.set(cache_key, stats, CacheTimeout.SHORT)

            logger.info("Warmed forum global statistics")

        except Exception as e:
            logger.warning(f"Could not warm forum statistics: {e}")

    def warm_user_specific(self, user_id: int, verbose: bool = True):
        """
        Warm caches for a specific user.

        Args:
            user_id: User ID
            verbose: Print progress messages

        Returns:
            dict: Statistics about cache warming
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return {'error': 'User not found'}

        stats = {
            'user_id': user_id,
            'tasks': [],
        }

        try:
            # Warm user enrollments
            self._warm_user_enrollments(user)
            stats['tasks'].append('enrollments')

            # Warm user progress
            self._warm_user_progress(user)
            stats['tasks'].append('progress')

            # Warm user submissions
            self._warm_user_submissions(user)
            stats['tasks'].append('submissions')

            if verbose:
                logger.info(f"Warmed user-specific caches for user {user_id}")

        except Exception as e:
            stats['error'] = str(e)
            logger.error(f"Error warming user caches: {e}")

        return stats

    def _warm_user_enrollments(self, user):
        """Warm user enrollments cache."""
        from apps.learning.models import CourseEnrollment
        from apps.api.cache import CacheKeyBuilder, CacheTimeout

        enrollments = CourseEnrollment.objects.filter(
            user=user
        ).select_related('course', 'course__instructor')

        cache_key = CacheKeyBuilder.build_user_key(user.id, 'enrollments')
        cache.set(cache_key, list(enrollments), CacheTimeout.MEDIUM)

    def _warm_user_progress(self, user):
        """Warm user progress cache."""
        from apps.learning.models import UserProgress
        from apps.api.cache import CacheKeyBuilder, CacheTimeout

        progress = UserProgress.objects.filter(
            user=user
        ).select_related('lesson', 'lesson__course')

        cache_key = CacheKeyBuilder.build_user_key(user.id, 'progress')
        cache.set(cache_key, list(progress), CacheTimeout.SHORT)

    def _warm_user_submissions(self, user):
        """Warm user submissions cache."""
        from apps.learning.models import Submission
        from apps.api.cache import CacheKeyBuilder, CacheTimeout

        submissions = Submission.objects.filter(
            user=user
        ).select_related('exercise')[:20]  # Last 20 submissions

        cache_key = CacheKeyBuilder.build_user_key(user.id, 'submissions')
        cache.set(cache_key, list(submissions), CacheTimeout.SHORT)


# Global warmer instance
warmer = CacheWarmer()
