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
from .models import Course, Category, Exercise, ProgrammingLanguage, Lesson
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
        courses = courses.order_by('-enrolled_count')
    
    # Pagination
    paginator = Paginator(courses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
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
