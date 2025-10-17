"""
Views for the learning app.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from .models import Course, Category, Exercise, ProgrammingLanguage, Lesson, CourseEnrollment
import json


def home_view(request):
    """Home page view with platform overview."""
    context = {
        'total_courses': Course.objects.filter(is_published=True).count(),
        'total_exercises': Exercise.objects.filter(is_published=True).count(),
        'total_users': 10000,  # This would be calculated from real user data
        'success_rate': 94,
    }
    return render(request, 'base/home.html', context)


def course_list_view(request):
    """Course listing view with filtering and pagination."""
    courses = Course.objects.filter(is_published=True)
    
    # Apply filters
    difficulty = request.GET.get('difficulty')
    category = request.GET.get('category')
    duration = request.GET.get('duration')
    free_only = request.GET.get('free')
    
    if difficulty:
        courses = courses.filter(difficulty_level=difficulty)
    
    if category:
        courses = courses.filter(category__slug=category)
    
    if duration:
        if duration == 'short':
            courses = courses.filter(estimated_duration__lt=5)
        elif duration == 'medium':
            courses = courses.filter(estimated_duration__gte=5, estimated_duration__lte=20)
        elif duration == 'long':
            courses = courses.filter(estimated_duration__gt=20)
    
    if free_only:
        courses = courses.filter(is_free=True)
    
    # Apply sorting
    sort_by = request.GET.get('sort', 'popularity')
    if sort_by == 'newest':
        courses = courses.order_by('-created_at')
    elif sort_by == 'difficulty':
        courses = courses.order_by('difficulty_level')
    elif sort_by == 'rating':
        courses = courses.order_by('-average_rating')
    else:  # popularity
        courses = courses.order_by('-total_enrollments')
    
    # Pagination
    paginator = Paginator(courses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add user-specific data to courses if authenticated
    if request.user.is_authenticated:
        for course in page_obj:
            course.user_enrolled = course.is_user_enrolled(request.user)
            course.user_progress = course.get_user_progress(request.user)
    
    context = {
        'courses': page_obj,
        'categories': Category.objects.all(),
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    return render(request, 'learning/course_list.html', context)


def course_detail_view(request, slug):
    """Course detail view."""
    course = get_object_or_404(Course, slug=slug, is_published=True)
    
    # Add user-specific data if authenticated
    if request.user.is_authenticated:
        course.user_enrolled = course.is_user_enrolled(request.user)
        course.user_progress = course.get_user_progress(request.user)
    
    context = {
        'course': course,
    }
    return render(request, 'learning/course_detail.html', context)


def lesson_detail_view(request, course_slug, lesson_slug):
    """Lesson detail view."""
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lesson = get_object_or_404(Lesson, slug=lesson_slug, course=course, is_published=True)
    
    context = {
        'course': course,
        'lesson': lesson,
    }
    return render(request, 'learning/lesson_detail.html', context)


def exercise_detail_view(request, exercise_id):
    """Exercise detail view."""
    exercise = get_object_or_404(Exercise, id=exercise_id, is_published=True)
    
    # Get sample test cases (visible to all users)
    sample_test_cases = exercise.test_cases.filter(is_sample=True)
    
    context = {
        'exercise': exercise,
        'sample_test_cases': sample_test_cases,
    }
    return render(request, 'learning/exercise.html', context)


def exercises_list_view(request):
    """Exercise listing view with filtering."""
    exercises = Exercise.objects.filter(is_published=True)
    
    # Apply filters
    difficulty = request.GET.get('difficulty')
    language = request.GET.get('language')
    exercise_type = request.GET.get('type')
    
    if difficulty:
        exercises = exercises.filter(difficulty_level=difficulty)
    
    if language:
        exercises = exercises.filter(programming_language__slug=language)
        
    if exercise_type:
        exercises = exercises.filter(exercise_type__slug=exercise_type)
    
    # Pagination
    paginator = Paginator(exercises, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'exercises': page_obj,
        'programming_languages': ProgrammingLanguage.objects.all(),
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    return render(request, 'learning/exercises_list.html', context)


def code_playground_view(request):
    """Code playground view."""
    return render(request, 'learning/code_playground.html')


@csrf_exempt  # Exempt ONLY for deprecation message - endpoint doesn't execute code
def execute_code_view(request):
    """
    DEPRECATED: This endpoint has been deprecated for security reasons.

    This endpoint was insecure because:
    1. No authentication required (public code execution)
    2. No CSRF protection
    3. No rate limiting
    4. No audit logging

    Use the secure authenticated endpoint instead:
    POST /api/v1/code-execution/

    Requires:
    - Authentication (JWT token or session)
    - Proper CSRF handling for session auth
    - Rate limiting enforced
    - Audit trail maintained
    """
    import logging
    logger = logging.getLogger(__name__)

    # Log attempted use of deprecated endpoint
    logger.warning(
        f"DEPRECATED ENDPOINT ACCESSED: execute_code_view by "
        f"{'authenticated user ' + str(request.user.id) if request.user.is_authenticated else 'unauthenticated user'} "
        f"from IP {request.META.get('REMOTE_ADDR', 'unknown')}"
    )

    return JsonResponse({
        'success': False,
        'error': 'This endpoint has been deprecated for security reasons.',
        'message': 'Please use the secure authenticated endpoint: POST /api/v1/code-execution/',
        'documentation': 'See CLAUDE.md for API documentation',
        'migration_guide': {
            'old_endpoint': '/execute-code/',
            'new_endpoint': '/api/v1/code-execution/',
            'authentication_required': True,
            'example': {
                'method': 'POST',
                'url': '/api/v1/code-execution/',
                'headers': {
                    'Authorization': 'Bearer YOUR_JWT_TOKEN',
                    'Content-Type': 'application/json'
                },
                'body': {
                    'code': 'print("Hello World")'
                }
            }
        }
    }, status=410)  # 410 Gone - endpoint permanently removed


@login_required
def submit_exercise(request, exercise_id):
    """
    DEPRECATED: Legacy exercise submission endpoint.
    Use /api/exercises/<id>/submit/ endpoint instead.
    """
    return JsonResponse({
        'success': False,
        'error': 'This endpoint is deprecated. Please use /api/exercises/{}/submit/ instead.'.format(exercise_id),
        'deprecated': True,
        'new_endpoint': f'/api/exercises/{exercise_id}/submit/'
    }, status=410)  # 410 Gone status indicates deprecated resource


@login_required  
def my_courses_view(request):
    """User's enrolled courses view."""
    # For now, show all courses since enrollment system needs to be implemented
    courses = Course.objects.filter(is_published=True)
    
    context = {
        'courses': courses,
    }
    return render(request, 'learning/my_courses.html', context)


@login_required
def enroll_course(request, course_id):
    """Enroll user in course."""
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id, is_published=True)
        
        # Check if user is already enrolled
        if course.is_user_enrolled(request.user):
            return JsonResponse({
                'success': False,
                'error': 'You are already enrolled in this course'
            })
        
        # Create enrollment
        try:
            enrollment = CourseEnrollment.objects.create(
                user=request.user,
                course=course
            )
            
            # Update course statistics
            course.update_statistics()
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully enrolled in {course.title}',
                'enrollment_id': enrollment.id,
                'redirect_url': course.get_absolute_url()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Enrollment failed: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Only POST requests allowed'
    })


def test_exercise_interface_view(request):
    """Test the new exercise interface"""
    # Mock exercise data for testing
    class MockExercise:
        def __init__(self):
            self.id = 1
            self.title = 'Find Maximum'
            self.description = 'Find the maximum number in a list'
            self.instructions = 'Follow these steps to complete the Find Maximum exercise:'
            self.difficulty_level = 'intermediate'
            self.estimated_time = 29
            self.points = 10
            self.programming_language = type('MockLang', (), {'name': 'Python'})()
            self.function_name = 'TODO'
            self.starter_code = 'def TODO(numbers):\n    # Find max number\n    pass'
            self.solution_code = 'def TODO(numbers):\n    return max(numbers)'
            self.hint = 'Try using the max() function or iterate through the list.'
            self.lesson = type('MockLesson', (), {
                'title': 'Lesson 3',
                'course': type('MockCourse', (), {'title': 'Python for Beginners'})()
            })()
            
        @property
        def test_cases(self):
            return type('MockManager', (), {
                'all': lambda: [
                    type('MockTest', (), {
                        'input_data': '[1,5,3,9,2]',
                        'expected_output': '9',
                        'is_sample': True
                    })()
                ]
            })()
    
    return render(request, 'learning/exercise_interface.html', {
        'exercise': MockExercise(),
        'title': 'Test Exercise Interface',
    })
