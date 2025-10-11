"""
Function-based views for API endpoints.
"""

from .code_execution import (
    execute_code, submit_exercise_code, docker_status,
    CodeExecutionView, AIAssistanceView, ExerciseEvaluationView
)
from .wagtail import (
    blog_index, blog_post_detail, blog_categories,
    wagtail_homepage, wagtail_playground,
    learning_index, courses_list, course_detail,
    lesson_detail, exercise_detail,
    wagtail_course_enroll, wagtail_course_unenroll,
    wagtail_course_enrollment_status, wagtail_user_enrollments
)

__all__ = [
    # Code Execution
    'execute_code', 'submit_exercise_code', 'docker_status',
    'CodeExecutionView', 'AIAssistanceView', 'ExerciseEvaluationView',
    
    # Wagtail/Blog
    'blog_index', 'blog_post_detail', 'blog_categories',
    'wagtail_homepage', 'wagtail_playground',
    'learning_index', 'courses_list', 'course_detail',
    'lesson_detail', 'exercise_detail',
    
    # Wagtail Enrollment
    'wagtail_course_enroll', 'wagtail_course_unenroll',
    'wagtail_course_enrollment_status', 'wagtail_user_enrollments'
]