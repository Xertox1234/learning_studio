from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
import json


@login_required
def dashboard_view(request):
    """User dashboard with learning progress and stats."""
    user = request.user
    
    # Get user's course enrollments
    enrolled_courses = user.enrollments.all()
    current_courses = enrolled_courses.filter(progress_percentage__lt=100)[:3]
    
    # Calculate stats
    enrolled_courses_count = enrolled_courses.count()
    completed_exercises_count = user.exercise_submissions.filter(status='passed').count()
    total_study_hours = round(user.total_study_time / 3600, 1) if hasattr(user, 'total_study_time') else 0
    average_score = user.exercise_submissions.aggregate(
        avg_score=models.Avg('score')
    )['avg_score'] or 0
    
    # Recent activities (mock data for now)
    recent_activities = [
        {
            'type': 'exercise_completed',
            'description': 'Completed "List Comprehensions" exercise',
            'created_at': timezone.now() - timedelta(hours=2)
        },
        {
            'type': 'lesson_completed',
            'description': 'Finished "Python Functions" lesson',
            'created_at': timezone.now() - timedelta(days=1)
        },
        {
            'type': 'course_enrolled',
            'description': 'Enrolled in "Advanced Python Concepts"',
            'created_at': timezone.now() - timedelta(days=3)
        }
    ]
    
    # Recent achievements (mock data)
    recent_achievements = [
        {
            'title': 'First Steps',
            'earned_at': timezone.now() - timedelta(days=5)
        },
        {
            'title': 'Code Warrior',
            'earned_at': timezone.now() - timedelta(days=10)
        }
    ]
    
    # Recommended courses (mock data)
    recommended_courses = []
    
    # Streak calendar (mock data)
    streak_calendar = []
    for i in range(7):
        date = timezone.now().date() - timedelta(days=6-i)
        streak_calendar.append({
            'date': date,
            'has_activity': i < 4,  # Mock: last 4 days have activity
            'is_today': date == timezone.now().date()
        })
    
    # Progress chart data (last 7 days)
    progress_chart_labels = []
    progress_chart_data = []
    for i in range(7):
        date = timezone.now().date() - timedelta(days=6-i)
        progress_chart_labels.append(date.strftime('%m/%d'))
        progress_chart_data.append(i + 1)  # Mock increasing data
    
    context = {
        'enrolled_courses_count': enrolled_courses_count,
        'completed_exercises_count': completed_exercises_count,
        'total_study_hours': total_study_hours,
        'average_score': round(average_score),
        'current_courses': current_courses,
        'recent_activities': recent_activities,
        'recent_achievements': recent_achievements,
        'recommended_courses': recommended_courses,
        'streak_calendar': streak_calendar,
        'progress_chart_labels': json.dumps(progress_chart_labels),
        'progress_chart_data': json.dumps(progress_chart_data),
    }
    
    return render(request, 'users/dashboard.html', context)
