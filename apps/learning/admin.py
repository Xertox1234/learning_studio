"""
Admin configuration for Learning Management models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Category, Course, Lesson, CourseEnrollment, UserProgress,
    LearningPath, LearningPathCourse, CourseReview, StudySession, Exercise
)
from .exercise_models import Submission, TestCaseResult


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for learning categories."""
    list_display = ['name', 'parent', 'course_count', 'color_preview', 'order']
    list_filter = ['parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Courses'
    
    def color_preview(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color
        )
    color_preview.short_description = 'Color'


class LessonInline(admin.TabularInline):
    """Inline for lessons within courses."""
    model = Lesson
    extra = 0
    fields = ['title', 'lesson_type', 'order', 'estimated_duration', 'is_published']
    readonly_fields = []


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin for courses."""
    list_display = [
        'title', 'instructor', 'category', 'difficulty_level',
        'total_lessons', 'total_enrollments', 'average_rating', 'is_published'
    ]
    list_filter = [
        'difficulty_level', 'category', 'is_published', 'is_featured', 'is_free'
    ]
    search_fields = ['title', 'description', 'instructor__username']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = []
    inlines = [LessonInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'short_description')
        }),
        ('Content', {
            'fields': ('learning_objectives', 'prerequisites')
        }),
        ('Classification', {
            'fields': ('category', 'instructor', 'difficulty_level', 'estimated_duration')
        }),
        ('Media', {
            'fields': ('thumbnail', 'banner_image')
        }),
        ('Settings', {
            'fields': ('is_published', 'is_featured', 'is_free', 'price')
        }),
        ('AI Enhancement', {
            'fields': ('ai_generated_summary', 'ai_suggested_prerequisites', 'ai_learning_path'),
            'classes': ('collapse',)
        }),
        ('Statistics (Read Only)', {
            'fields': ('total_lessons', 'total_enrollments', 'average_rating', 'total_reviews'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['total_lessons', 'total_enrollments', 'average_rating', 'total_reviews']
    
    actions = ['publish_courses', 'unpublish_courses', 'update_statistics']
    
    def publish_courses(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} courses published.')
    publish_courses.short_description = "Publish selected courses"
    
    def unpublish_courses(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} courses unpublished.')
    unpublish_courses.short_description = "Unpublish selected courses"
    
    def update_statistics(self, request, queryset):
        for course in queryset:
            course.update_statistics()
        self.message_user(request, f'Statistics updated for {queryset.count()} courses.')
    update_statistics.short_description = "Update course statistics"


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Admin for lessons."""
    list_display = [
        'title', 'course', 'lesson_type', 'difficulty_level',
        'order', 'estimated_duration', 'is_published'
    ]
    list_filter = ['lesson_type', 'difficulty_level', 'is_published', 'course__category']
    search_fields = ['title', 'description', 'course__title']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'course')
        }),
        ('Content', {
            'fields': ('content_format', 'enable_structured_content', 'content', 'structured_content', 'video_url'),
            'description': 'Choose content format: Plain text, Markdown, or Structured blocks for enhanced interactivity.'
        }),
        ('Classification', {
            'fields': ('lesson_type', 'difficulty_level', 'order', 'estimated_duration')
        }),
        ('Prerequisites', {
            'fields': ('required_lessons',)
        }),
        ('Settings', {
            'fields': ('is_published', 'is_free')
        }),
        ('AI Enhancement', {
            'fields': ('ai_generated_summary', 'ai_suggested_exercises'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['required_lessons']
    actions = ['convert_to_structured_content', 'enable_structured_content', 'disable_structured_content']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course')
    
    def convert_to_structured_content(self, request, queryset):
        """Convert selected lessons to use structured content."""
        converted = 0
        for lesson in queryset:
            if not lesson.enable_structured_content and lesson.content:
                lesson.create_default_structured_content()
                lesson.save()
                converted += 1
        
        self.message_user(request, f'{converted} lessons converted to structured content.')
    convert_to_structured_content.short_description = "Convert to structured content"
    
    def enable_structured_content(self, request, queryset):
        """Enable structured content for selected lessons."""
        updated = queryset.update(enable_structured_content=True, content_format='structured')
        self.message_user(request, f'{updated} lessons enabled for structured content.')
    enable_structured_content.short_description = "Enable structured content"
    
    def disable_structured_content(self, request, queryset):
        """Disable structured content for selected lessons."""
        updated = queryset.update(enable_structured_content=False, content_format='plain')
        self.message_user(request, f'{updated} lessons disabled for structured content.')
    disable_structured_content.short_description = "Disable structured content"


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    """Admin for course enrollments."""
    list_display = [
        'user', 'course', 'progress_percentage', 'completed',
        'enrolled_at', 'last_activity'
    ]
    list_filter = ['completed', 'enrolled_at', 'course__category']
    search_fields = ['user__username', 'course__title']
    readonly_fields = ['enrolled_at', 'last_activity']
    
    fieldsets = (
        ('Enrollment Info', {
            'fields': ('user', 'course', 'enrolled_at')
        }),
        ('Progress', {
            'fields': ('progress_percentage', 'completed', 'completed_at', 'last_accessed_lesson')
        }),
        ('Activity', {
            'fields': ('total_time_spent', 'last_activity')
        }),
    )
    
    actions = ['update_progress']
    
    def update_progress(self, request, queryset):
        for enrollment in queryset:
            enrollment.update_progress()
        self.message_user(request, f'Progress updated for {queryset.count()} enrollments.')
    update_progress.short_description = "Update enrollment progress"


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    """Admin for user lesson progress."""
    list_display = [
        'user', 'lesson', 'started', 'completed',
        'time_spent', 'last_accessed', 'bookmarked'
    ]
    list_filter = ['started', 'completed', 'bookmarked', 'lesson__course']
    search_fields = ['user__username', 'lesson__title']
    readonly_fields = ['started_at', 'completed_at', 'last_accessed']
    
    fieldsets = (
        ('Progress Info', {
            'fields': ('user', 'lesson', 'started', 'completed')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'last_accessed')
        }),
        ('Tracking', {
            'fields': ('time_spent', 'content_position', 'bookmarked')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )


class LearningPathCourseInline(admin.TabularInline):
    """Inline for courses in learning paths."""
    model = LearningPathCourse
    extra = 0
    fields = ['course', 'order', 'is_required']


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    """Admin for learning paths."""
    list_display = [
        'title', 'creator', 'difficulty_level', 'course_count',
        'estimated_duration', 'is_published'
    ]
    list_filter = ['difficulty_level', 'is_published', 'is_featured']
    search_fields = ['title', 'description', 'creator__username']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LearningPathCourseInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description')
        }),
        ('Path Details', {
            'fields': ('creator', 'difficulty_level', 'estimated_duration')
        }),
        ('Settings', {
            'fields': ('is_published', 'is_featured')
        }),
        ('AI Enhancement', {
            'fields': ('ai_generated_description', 'ai_recommended_order'),
            'classes': ('collapse',)
        }),
    )
    
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Courses'


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    """Admin for course reviews."""
    list_display = [
        'user', 'course', 'rating', 'title',
        'helpful_votes', 'verified_purchase', 'created_at'
    ]
    list_filter = ['rating', 'verified_purchase', 'created_at']
    search_fields = ['user__username', 'course__title', 'title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Review Info', {
            'fields': ('user', 'course', 'rating')
        }),
        ('Content', {
            'fields': ('title', 'content')
        }),
        ('Metadata', {
            'fields': ('helpful_votes', 'verified_purchase', 'created_at', 'updated_at')
        }),
    )


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    """Admin for study sessions."""
    list_display = [
        'user', 'lesson', 'started_at', 'duration_display',
        'completed_lesson'
    ]
    list_filter = ['completed_lesson', 'started_at']
    search_fields = ['user__username', 'lesson__title']
    readonly_fields = ['started_at', 'ended_at', 'duration']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'lesson', 'started_at', 'ended_at')
        }),
        ('Tracking', {
            'fields': ('duration', 'completed_lesson')
        }),
        ('Notes', {
            'fields': ('notes_taken',)
        }),
    )
    
    def duration_display(self, obj):
        if obj.duration:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            return f"{minutes}m {seconds}s"
        return "0m 0s"
    duration_display.short_description = 'Duration'


# Exercise and Submission Admin
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    """Admin for exercises."""
    list_display = [
        'title', 'difficulty_level', 'submission_count', 
        'success_rate', 'is_published', 'created_at'
    ]
    list_filter = ['difficulty_level', 'is_published', 'created_at']
    search_fields = ['title', 'description', 'solution_code']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'difficulty_level')
        }),
        ('Code & Solution', {
            'fields': ('starter_code', 'solution_code', 'hints')
        }),
        ('Settings', {
            'fields': ('time_limit', 'memory_limit', 'is_published')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def submission_count(self, obj):
        return obj.submissions.count()
    submission_count.short_description = 'Submissions'
    
    def success_rate(self, obj):
        total = obj.submissions.count()
        if total == 0:
            return "N/A"
        passed = obj.submissions.filter(status='passed').count()
        rate = (passed / total) * 100
        return f"{rate:.1f}%"
    success_rate.short_description = 'Success Rate'


class TestCaseResultInline(admin.TabularInline):
    """Inline for test case results within submissions."""
    model = TestCaseResult
    extra = 0
    fields = ['test_case', 'passed', 'actual_output', 'error_message']
    readonly_fields = ['test_case', 'passed', 'actual_output', 'error_message']
    can_delete = False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Admin for code submissions."""
    list_display = [
        'user', 'exercise', 'status_display', 'score_display', 
        'test_results', 'attempt_number', 'submitted_at'
    ]
    list_filter = ['status', 'is_final', 'feedback_generated', 'submitted_at']
    search_fields = ['user__username', 'exercise__title', 'code']
    readonly_fields = [
        'submission_id', 'submitted_at', 'processed_at', 
        'execution_time', 'memory_used'
    ]
    inlines = [TestCaseResultInline]
    
    fieldsets = (
        ('Submission Info', {
            'fields': (
                'submission_id', 'user', 'exercise', 
                'attempt_number', 'is_final'
            )
        }),
        ('Code', {
            'fields': ('code',),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': (
                'status', 'score', 'passed_tests', 'total_tests',
                'output', 'error_message'
            )
        }),
        ('Execution Details', {
            'fields': ('execution_time', 'memory_used', 'submitted_at', 'processed_at'),
            'classes': ('collapse',)
        }),
        ('AI Feedback', {
            'fields': ('ai_feedback', 'ai_suggestions', 'feedback_generated'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        status_colors = {
            'passed': 'green',
            'failed': 'red',
            'error': 'orange',
            'timeout': 'gray',
            'memory_exceeded': 'gray',
            'pending': 'blue',
            'running': 'blue',
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def score_display(self, obj):
        if obj.score >= 80:
            color = 'green'
        elif obj.score >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/100</span>',
            color,
            obj.score
        )
    score_display.short_description = 'Score'
    
    def test_results(self, obj):
        return f"{obj.passed_tests}/{obj.total_tests}"
    test_results.short_description = 'Tests'
    
    actions = ['generate_ai_feedback']
    
    def generate_ai_feedback(self, request, queryset):
        """Generate AI feedback for selected submissions."""
        count = 0
        for submission in queryset:
            if not submission.feedback_generated:
                submission.generate_ai_feedback()
                count += 1
        self.message_user(request, f'Generated AI feedback for {count} submissions.')
    generate_ai_feedback.short_description = "Generate AI feedback"
