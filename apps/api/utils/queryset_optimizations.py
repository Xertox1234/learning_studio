"""
Reusable queryset optimization utilities for preventing N+1 queries.

This module provides standardized optimization functions for common querysets
to ensure consistent performance across the API.
"""

from django.db.models import Count


def optimize_blog_posts(queryset):
    """
    Apply standard optimizations to blog post queryset.

    Prevents N+1 queries by prefetching:
    - categories (M2M)
    - tags (M2M)
    - author (FK)

    Args:
        queryset: BlogPage queryset

    Returns:
        Optimized queryset with prefetch_related and select_related applied
    """
    return queryset.prefetch_related(
        'categories',
        'tags',
    ).select_related(
        'author'
    )


def optimize_courses(queryset):
    """
    Apply standard optimizations to course queryset.

    Prevents N+1 queries by prefetching:
    - categories (M2M)
    - tags (M2M)
    - instructor (FK)
    - skill_level (FK)
    - learning_objectives (reverse FK)

    Args:
        queryset: CoursePage queryset

    Returns:
        Optimized queryset with prefetch_related and select_related applied
    """
    return queryset.prefetch_related(
        'learning_objectives',
        'categories',
        'tags'
    ).select_related(
        'instructor',
        'skill_level'
    )


def optimize_courses_with_counts(queryset):
    """
    Apply optimizations to course queryset including enrollment and lesson counts.

    This extends optimize_courses by adding aggregated counts.

    Args:
        queryset: CoursePage queryset

    Returns:
        Optimized queryset with prefetch, select_related, and annotations
    """
    return optimize_courses(queryset).annotate(
        enrollment_count=Count('enrollments'),
        lesson_count=Count('lessons')
    )


def optimize_exercises(queryset):
    """
    Apply standard optimizations to exercise queryset.

    Prevents N+1 queries by prefetching:
    - tags (M2M)
    - owner (FK)

    Args:
        queryset: ExercisePage or StepBasedExercisePage queryset

    Returns:
        Optimized queryset with prefetch_related and select_related applied
    """
    return queryset.prefetch_related(
        'tags'
    ).select_related(
        'owner'
    )


def optimize_blog_categories(queryset):
    """
    Apply standard optimizations to blog category queryset.

    Prevents N+1 queries when accessing blog posts count per category.

    Args:
        queryset: BlogCategory queryset

    Returns:
        Optimized queryset with prefetch_related applied
    """
    return queryset.prefetch_related('blogpage_set')
