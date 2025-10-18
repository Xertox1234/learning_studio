"""
Reusable query annotations for common patterns.
"""
from django.db.models import Count, Exists, Max, Q, OuterRef


def annotate_enrollment_data(queryset, user):
    """
    Add enrollment-related annotations to course queryset.

    Args:
        queryset: Course queryset
        user: Current user

    Returns:
        Annotated queryset
    """
    from apps.learning.models import Enrollment

    user_enrollment = Enrollment.objects.filter(
        course=OuterRef('pk'),
        user=user,
        is_active=True
    )

    return queryset.annotate(
        enrollment_count=Count('enrollments', distinct=True),
        user_enrolled=Exists(user_enrollment)
    )


def annotate_lesson_progress(queryset, user):
    """
    Add progress annotations to lesson queryset.
    """
    from apps.learning.models import Progress

    user_progress = Progress.objects.filter(
        lesson=OuterRef('pk'),
        user=user,
        is_completed=True
    )

    return queryset.annotate(
        completion_count=Count(
            'progress',
            filter=Q(progress__is_completed=True),
            distinct=True
        ),
        user_completed=Exists(user_progress)
    )


def annotate_exercise_stats(queryset, user):
    """
    Add submission statistics to exercise queryset.
    """
    from apps.learning.models import ExerciseSubmission

    user_submission = ExerciseSubmission.objects.filter(
        exercise=OuterRef('pk'),
        user=user
    )

    return queryset.annotate(
        submission_count=Count('submissions', distinct=True),
        user_has_submitted=Exists(user_submission),
        user_best_score=Max(
            'submissions__score',
            filter=Q(submissions__user=user)
        )
    )
