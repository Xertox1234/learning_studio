"""
Progress tracking API endpoints for courses and lessons.
"""

import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.learning.models import (
    Lesson, Course, UserProgress, CourseEnrollment
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_lesson_complete(request, lesson_id):
    """
    Mark a lesson as completed for the authenticated user.
    
    Updates or creates UserProgress record and updates CourseEnrollment progress.
    
    Args:
        lesson_id: ID of the Lesson to mark complete
        
    Request Body:
        time_spent: Optional time spent on lesson in seconds
        
    Returns:
        {
            'success': bool,
            'lesson': {
                'id': int,
                'title': str,
                'completed': bool,
                'completed_at': datetime
            },
            'course_progress': {
                'progress_percentage': int,
                'completed_lessons': int,
                'total_lessons': int
            }
        }
    """
    try:
        lesson = get_object_or_404(Lesson, id=lesson_id, is_published=True)
        time_spent = request.data.get('time_spent', 0)
        
        # Get or create user progress for this lesson
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'time_spent': time_spent}
        )
        
        # Mark as completed if not already
        if not progress.completed:
            progress.mark_completed()
        
        # Update time spent if provided
        if time_spent > 0 and not created:
            progress.time_spent += int(time_spent)
            progress.save(update_fields=['time_spent'])
        
        # Get or create course enrollment
        enrollment, _ = CourseEnrollment.objects.get_or_create(
            user=request.user,
            course=lesson.course
        )
        
        # Update course progress
        enrollment.update_progress()
        
        return Response({
            'success': True,
            'lesson': {
                'id': lesson.id,
                'title': lesson.title,
                'completed': progress.completed,
                'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
                'time_spent': progress.time_spent
            },
            'course_progress': {
                'progress_percentage': enrollment.progress_percentage,
                'completed_lessons': UserProgress.objects.filter(
                    user=request.user,
                    lesson__course=lesson.course,
                    completed=True
                ).count(),
                'total_lessons': lesson.course.lessons.count()
            }
        })
        
    except Exception as e:
        logger.error(f"Error marking lesson complete: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lesson_progress(request, lesson_id):
    """
    Get progress information for a specific lesson.
    
    Args:
        lesson_id: ID of the Lesson
        
    Returns:
        {
            'lesson_id': int,
            'started': bool,
            'completed': bool,
            'started_at': datetime,
            'completed_at': datetime,
            'time_spent': int,
            'last_accessed': datetime
        }
    """
    try:
        lesson = get_object_or_404(Lesson, id=lesson_id, is_published=True)
        
        try:
            progress = UserProgress.objects.get(
                user=request.user,
                lesson=lesson
            )
            return Response({
                'lesson_id': lesson.id,
                'started': progress.started,
                'completed': progress.completed,
                'started_at': progress.started_at.isoformat() if progress.started_at else None,
                'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
                'time_spent': progress.time_spent,
                'last_accessed': progress.last_accessed.isoformat(),
                'content_position': progress.content_position,
                'bookmarked': progress.bookmarked
            })
        except UserProgress.DoesNotExist:
            return Response({
                'lesson_id': lesson.id,
                'started': False,
                'completed': False,
                'started_at': None,
                'completed_at': None,
                'time_spent': 0,
                'last_accessed': None,
                'content_position': 0,
                'bookmarked': False
            })
            
    except Exception as e:
        logger.error(f"Error getting lesson progress: {e}", exc_info=True)
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_course_progress(request, course_id):
    """
    Get detailed progress information for a course.
    
    Args:
        course_id: ID of the Course
        
    Returns:
        {
            'course_id': int,
            'progress_percentage': int,
            'completed': bool,
            'completed_at': datetime,
            'enrolled_at': datetime,
            'last_activity': datetime,
            'total_time_spent': int,
            'lessons': [
                {
                    'id': int,
                    'title': str,
                    'completed': bool,
                    'time_spent': int
                }
            ],
            'statistics': {
                'total_lessons': int,
                'completed_lessons': int,
                'remaining_lessons': int
            }
        }
    """
    try:
        course = get_object_or_404(Course, id=course_id, is_published=True)
        
        # Get enrollment info
        try:
            enrollment = CourseEnrollment.objects.get(
                user=request.user,
                course=course
            )
        except CourseEnrollment.DoesNotExist:
            # User not enrolled yet, create enrollment
            enrollment = CourseEnrollment.objects.create(
                user=request.user,
                course=course
            )
        
        # Get all lessons with progress
        lessons = []
        all_lessons = course.lessons.filter(is_published=True).order_by('order')
        lesson_progress_map = {
            p.lesson_id: p for p in UserProgress.objects.filter(
                user=request.user,
                lesson__course=course
            ).select_related('lesson')
        }
        
        for lesson in all_lessons:
            progress = lesson_progress_map.get(lesson.id)
            lessons.append({
                'id': lesson.id,
                'title': lesson.title,
                'order': lesson.order,
                'completed': progress.completed if progress else False,
                'time_spent': progress.time_spent if progress else 0,
                'started_at': progress.started_at.isoformat() if progress and progress.started_at else None
            })
        
        completed_count = sum(1 for l in lessons if l['completed'])
        total_lessons = len(lessons)
        
        return Response({
            'course_id': course.id,
            'progress_percentage': enrollment.progress_percentage,
            'completed': enrollment.completed,
            'completed_at': enrollment.completed_at.isoformat() if enrollment.completed_at else None,
            'enrolled_at': enrollment.enrolled_at.isoformat(),
            'last_activity': enrollment.last_activity.isoformat(),
            'total_time_spent': enrollment.total_time_spent,
            'lessons': lessons,
            'statistics': {
                'total_lessons': total_lessons,
                'completed_lessons': completed_count,
                'remaining_lessons': total_lessons - completed_count
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting course progress: {e}", exc_info=True)
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_lesson_position(request, lesson_id):
    """
    Update the user's current position within a lesson (for video position, scroll position, etc.)
    
    Args:
        lesson_id: ID of the Lesson
        
    Request Body:
        content_position: int - Position in content (seconds for video, scroll position for text)
        time_spent: Optional int - Additional time to add to time_spent counter
        
    Returns:
        {
            'success': bool,
            'content_position': int,
            'time_spent': int
        }
    """
    try:
        lesson = get_object_or_404(Lesson, id=lesson_id, is_published=True)
        content_position = request.data.get('content_position', 0)
        time_spent = request.data.get('time_spent', 0)
        
        # Get or create progress
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'content_position': content_position}
        )
        
        # Mark as started if not already
        if not progress.started:
            progress.mark_started()
        
        # Update position and time
        progress.content_position = int(content_position)
        if time_spent > 0:
            progress.time_spent += int(time_spent)
        progress.save(update_fields=['content_position', 'time_spent'])
        
        return Response({
            'success': True,
            'content_position': progress.content_position,
            'time_spent': progress.time_spent
        })
        
    except Exception as e:
        logger.error(f"Error updating lesson position: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bookmark_lesson(request, lesson_id):
    """
    Toggle bookmark status for a lesson.
    
    Args:
        lesson_id: ID of the Lesson
        
    Request Body:
        bookmarked: bool - Whether to bookmark (true) or unbookmark (false)
        
    Returns:
        {
            'success': bool,
            'bookmarked': bool
        }
    """
    try:
        lesson = get_object_or_404(Lesson, id=lesson_id, is_published=True)
        bookmarked = request.data.get('bookmarked', False)
        
        # Get or create progress
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        
        progress.bookmarked = bool(bookmarked)
        progress.save(update_fields=['bookmarked'])
        
        return Response({
            'success': True,
            'bookmarked': progress.bookmarked
        })
        
    except Exception as e:
        logger.error(f"Error toggling lesson bookmark: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
