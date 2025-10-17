"""
Cache invalidation via Django signals.

Automatically invalidates related caches when models are updated.
"""

import logging
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache

from .strategies import invalidate_model_cache, invalidate_user_cache, CacheKeyBuilder

logger = logging.getLogger(__name__)


# Course model signals
@receiver(post_save, sender='learning.Course')
@receiver(post_delete, sender='learning.Course')
def invalidate_course_cache(sender, instance, **kwargs):
    """Invalidate course-related caches when course is modified."""
    logger.info(f"Invalidating course cache for: {instance.id}")

    # Invalidate all course list caches
    invalidate_model_cache('courses')

    # Invalidate course detail cache
    invalidate_model_cache('courses', 'detail', instance.id)

    # Invalidate category courses cache
    if instance.category:
        invalidate_model_cache('courses', 'category', instance.category.id)

    # Invalidate instructor courses cache
    if instance.instructor:
        invalidate_model_cache('courses', 'instructor', instance.instructor.id)


@receiver(post_save, sender='learning.Lesson')
@receiver(post_delete, sender='learning.Lesson')
def invalidate_lesson_cache(sender, instance, **kwargs):
    """Invalidate lesson-related caches when lesson is modified."""
    logger.info(f"Invalidating lesson cache for: {instance.id}")

    # Invalidate course lessons cache
    if instance.course:
        invalidate_model_cache('courses', instance.course.id, 'lessons')

    # Invalidate lesson detail cache
    invalidate_model_cache('lessons', 'detail', instance.id)


@receiver(post_save, sender='learning.Exercise')
@receiver(post_delete, sender='learning.Exercise')
def invalidate_exercise_cache(sender, instance, **kwargs):
    """Invalidate exercise-related caches when exercise is modified."""
    logger.info(f"Invalidating exercise cache for: {instance.id}")

    # Invalidate lesson exercises cache
    if instance.lesson:
        invalidate_model_cache('lessons', instance.lesson.id, 'exercises')

    # Invalidate exercise detail cache
    invalidate_model_cache('exercises', 'detail', instance.id)


@receiver(post_save, sender='learning.Submission')
def invalidate_submission_cache(sender, instance, **kwargs):
    """Invalidate submission-related caches when submission is created/updated."""
    logger.info(f"Invalidating submission cache for user: {instance.user.id}")

    # Invalidate user submissions cache
    invalidate_user_cache(instance.user.id, 'submissions')

    # Invalidate user progress cache
    invalidate_user_cache(instance.user.id, 'progress')

    # Invalidate exercise submission cache
    if instance.exercise:
        invalidate_model_cache('exercises', instance.exercise.id, 'submissions')


@receiver(post_save, sender='learning.CourseEnrollment')
@receiver(post_delete, sender='learning.CourseEnrollment')
def invalidate_enrollment_cache(sender, instance, **kwargs):
    """Invalidate enrollment-related caches when enrollment changes."""
    logger.info(f"Invalidating enrollment cache for user: {instance.user.id}")

    # Invalidate user enrollments cache
    invalidate_user_cache(instance.user.id, 'enrollments')

    # Invalidate course enrollments cache
    if instance.course:
        invalidate_model_cache('courses', instance.course.id, 'enrollments')


@receiver(post_save, sender='learning.UserProgress')
@receiver(post_delete, sender='learning.UserProgress')
def invalidate_progress_cache(sender, instance, **kwargs):
    """Invalidate progress-related caches when progress changes."""
    logger.info(f"Invalidating progress cache for user: {instance.user.id}")

    # Invalidate user progress cache
    invalidate_user_cache(instance.user.id, 'progress')

    # Invalidate lesson progress cache
    if instance.lesson:
        invalidate_model_cache('lessons', instance.lesson.id, 'progress')


@receiver(post_save, sender='learning.Category')
@receiver(post_delete, sender='learning.Category')
def invalidate_category_cache(sender, instance, **kwargs):
    """Invalidate category-related caches when category changes."""
    logger.info(f"Invalidating category cache for: {instance.id}")

    # Invalidate all category caches
    invalidate_model_cache('categories')

    # Invalidate category courses cache
    invalidate_model_cache('courses', 'category', instance.id)


# Forum model signals
@receiver(post_save, sender='forum_conversation.Topic')
@receiver(post_delete, sender='forum_conversation.Topic')
def invalidate_topic_cache(sender, instance, **kwargs):
    """Invalidate topic-related caches when topic changes."""
    try:
        logger.info(f"Invalidating topic cache for: {instance.id}")

        # Invalidate forum topics cache
        if hasattr(instance, 'forum') and instance.forum:
            invalidate_model_cache('forums', instance.forum.id, 'topics')

        # Invalidate topic detail cache
        invalidate_model_cache('topics', 'detail', instance.id)

        # Invalidate forum statistics cache
        invalidate_model_cache('forum', 'statistics')

        # Invalidate user topics cache
        if hasattr(instance, 'poster') and instance.poster:
            invalidate_user_cache(instance.poster.id, 'topics')

    except Exception as e:
        logger.error(f"Error invalidating topic cache: {e}")


@receiver(post_save, sender='forum_conversation.Post')
@receiver(post_delete, sender='forum_conversation.Post')
def invalidate_post_cache(sender, instance, **kwargs):
    """Invalidate post-related caches when post changes."""
    try:
        logger.info(f"Invalidating post cache for: {instance.id}")

        # Invalidate topic posts cache
        if hasattr(instance, 'topic') and instance.topic:
            invalidate_model_cache('topics', instance.topic.id, 'posts')

        # Invalidate forum statistics cache
        invalidate_model_cache('forum', 'statistics')

        # Invalidate user posts cache
        if hasattr(instance, 'poster') and instance.poster:
            invalidate_user_cache(instance.poster.id, 'posts')

    except Exception as e:
        logger.error(f"Error invalidating post cache: {e}")


# User model signals
@receiver(post_save, sender='users.User')
def invalidate_user_profile_cache(sender, instance, **kwargs):
    """Invalidate user profile cache when user is updated."""
    logger.info(f"Invalidating user profile cache for: {instance.id}")

    # Invalidate all user-specific caches
    invalidate_user_cache(instance.id)


# Review Queue signals
@receiver(post_save, sender='forum_integration.ReviewQueue')
@receiver(post_delete, sender='forum_integration.ReviewQueue')
def invalidate_review_queue_cache(sender, instance, **kwargs):
    """Invalidate review queue caches when queue changes."""
    try:
        logger.info(f"Invalidating review queue cache")

        # Invalidate review queue caches
        invalidate_model_cache('review_queue')

        # Invalidate user review queue cache
        if hasattr(instance, 'content_author'):
            invalidate_user_cache(instance.content_author.id, 'review_queue')

    except Exception as e:
        logger.error(f"Error invalidating review queue cache: {e}")


def setup_cache_invalidation():
    """
    Setup cache invalidation signals.
    Call this in AppConfig.ready() to ensure signals are connected.
    """
    logger.info("Cache invalidation signals registered")
