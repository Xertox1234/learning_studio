"""
Exercise and code execution models for Python Learning Studio.
These models support programming exercises, submissions, and AI-powered feedback.
"""

import json
import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings

User = get_user_model()


class ProgrammingLanguage(models.Model):
    """Supported programming languages for exercises."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    file_extension = models.CharField(max_length=10, help_text="e.g., .py, .js, .cpp")
    docker_image = models.CharField(
        max_length=100, 
        help_text="Docker image for code execution",
        default="python:3.11-slim"
    )
    syntax_highlighter = models.CharField(
        max_length=50, 
        help_text="Syntax highlighter identifier",
        default="python"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ExerciseType(models.Model):
    """Types of coding exercises."""
    TYPE_CHOICES = [
        ('function', 'Function Implementation'),
        ('class', 'Class Implementation'),
        ('algorithm', 'Algorithm Challenge'),
        ('debug', 'Debug Exercise'),
        ('fill_blank', 'Fill in the Blanks'),
        ('multiple_choice', 'Multiple Choice'),
        ('project', 'Mini Project'),
        ('quiz', 'Code Quiz'),
    ]

    name = models.CharField(max_length=50, choices=TYPE_CHOICES, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    supports_code_execution = models.BooleanField(default=True)
    max_execution_time = models.PositiveIntegerField(
        default=30, 
        help_text="Maximum execution time in seconds"
    )

    def __str__(self):
        return self.get_name_display()


class Exercise(models.Model):
    """Programming exercise model with AI integration."""
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(help_text="Exercise description and requirements")
    instructions = models.TextField(help_text="Step-by-step instructions")
    
    # Categorization
    lesson = models.ForeignKey(
        'learning.Lesson', 
        on_delete=models.CASCADE, 
        related_name='exercises'
    )
    exercise_type = models.ForeignKey(
        ExerciseType, 
        on_delete=models.CASCADE, 
        related_name='exercises'
    )
    programming_language = models.ForeignKey(
        ProgrammingLanguage, 
        on_delete=models.CASCADE, 
        related_name='exercises'
    )
    difficulty_level = models.CharField(
        max_length=20, 
        choices=DIFFICULTY_CHOICES, 
        default='beginner'
    )
    
    # Exercise Content
    starter_code = models.TextField(
        blank=True, 
        help_text="Initial code template for students"
    )
    solution_code = models.TextField(
        help_text="Complete solution (hidden from students)"
    )
    expected_output = models.TextField(
        blank=True, 
        help_text="Expected output for validation"
    )
    
    # Metadata
    estimated_time = models.PositiveIntegerField(
        help_text="Estimated completion time in minutes",
        validators=[MinValueValidator(1), MaxValueValidator(300)]
    )
    points = models.PositiveIntegerField(
        default=10, 
        help_text="Points awarded for completion"
    )
    is_published = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    # AI Enhancement
    ai_generated_hints = models.TextField(blank=True)
    ai_common_mistakes = models.TextField(blank=True)
    ai_learning_notes = models.TextField(blank=True)
    
    # Execution Settings
    execution_timeout = models.PositiveIntegerField(
        default=10, 
        help_text="Code execution timeout in seconds"
    )
    memory_limit = models.PositiveIntegerField(
        default=128, 
        help_text="Memory limit in MB"
    )
    allow_imports = models.BooleanField(
        default=False, 
        help_text="Allow import statements in student code"
    )
    
    # Tracking
    total_submissions = models.PositiveIntegerField(default=0)
    successful_submissions = models.PositiveIntegerField(default=0)
    average_attempts = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.0
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['lesson', 'order']
        unique_together = [['lesson', 'slug']]

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"

    def get_success_rate(self):
        """Calculate success rate percentage."""
        if self.total_submissions == 0:
            return 0
        return (self.successful_submissions / self.total_submissions) * 100

    def generate_ai_hints(self):
        """Generate AI-powered hints for the exercise."""
        from .services import learning_ai
        if not self.ai_generated_hints:
            hints = learning_ai.generate_hints_for_exercise(
                self.description, 
                self.starter_code
            )
            self.ai_generated_hints = hints
            self.save(update_fields=['ai_generated_hints'])
        return self.ai_generated_hints


class TestCase(models.Model):
    """Test cases for exercise validation."""
    exercise = models.ForeignKey(
        Exercise, 
        on_delete=models.CASCADE, 
        related_name='test_cases'
    )
    name = models.CharField(max_length=100)
    input_data = models.TextField(
        blank=True, 
        help_text="JSON formatted input data"
    )
    expected_output = models.TextField(help_text="Expected output")
    is_hidden = models.BooleanField(
        default=False, 
        help_text="Hidden test cases for assessment"
    )
    is_sample = models.BooleanField(
        default=False, 
        help_text="Sample test case shown to students"
    )
    weight = models.PositiveIntegerField(
        default=1, 
        help_text="Weight for scoring"
    )
    timeout = models.PositiveIntegerField(
        default=5, 
        help_text="Test case timeout in seconds"
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['exercise', 'order']

    def __str__(self):
        return f"{self.exercise.title} - {self.name}"

    def get_input_as_dict(self):
        """Parse input data as dictionary."""
        try:
            return json.loads(self.input_data) if self.input_data else {}
        except json.JSONDecodeError:
            return {}


class Submission(models.Model):
    """Student code submissions."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('error', 'Error'),
        ('timeout', 'Timeout'),
        ('memory_exceeded', 'Memory Exceeded'),
    ]

    # Basic Information
    exercise = models.ForeignKey(
        Exercise, 
        on_delete=models.CASCADE, 
        related_name='submissions'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='exercise_submissions'
    )
    submission_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Code and Results
    code = models.TextField(help_text="Student's submitted code")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    score = models.PositiveIntegerField(
        default=0, 
        validators=[MaxValueValidator(100)]
    )
    passed_tests = models.PositiveIntegerField(default=0)
    total_tests = models.PositiveIntegerField(default=0)
    
    # Execution Details
    execution_time = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Execution time in seconds"
    )
    memory_used = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Memory used in MB"
    )
    output = models.TextField(blank=True, help_text="Program output")
    error_message = models.TextField(blank=True, help_text="Error messages")
    
    # AI Feedback
    ai_feedback = models.TextField(blank=True)
    ai_suggestions = models.TextField(blank=True)
    feedback_generated = models.BooleanField(default=False)
    
    # Tracking
    attempt_number = models.PositiveIntegerField(default=1)
    is_final = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = [['user', 'exercise', 'attempt_number']]

    def __str__(self):
        return f"{self.user.username} - {self.exercise.title} (Attempt {self.attempt_number})"

    def is_successful(self):
        """Check if submission passed all tests."""
        return self.status == 'passed' and self.score >= 80

    def generate_ai_feedback(self):
        """Generate AI-powered feedback for the submission."""
        from .services import learning_ai
        if not self.ai_feedback and self.code:
            feedback = learning_ai.review_student_code(
                self.code, 
                self.exercise.description
            )
            self.ai_feedback = feedback
            self.feedback_generated = True
            self.save(update_fields=['ai_feedback', 'feedback_generated'])
        return self.ai_feedback


class TestCaseResult(models.Model):
    """Results of individual test case execution."""
    submission = models.ForeignKey(
        Submission, 
        on_delete=models.CASCADE, 
        related_name='test_results'
    )
    test_case = models.ForeignKey(
        TestCase, 
        on_delete=models.CASCADE, 
        related_name='results'
    )
    passed = models.BooleanField(default=False)
    actual_output = models.TextField(blank=True)
    execution_time = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Test execution time in seconds"
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['submission', 'test_case']]

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"{self.submission.submission_id} - {self.test_case.name}: {status}"


class CodeExecutionSession(models.Model):
    """Track code execution sessions for debugging and monitoring."""
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='execution_sessions'
    )
    exercise = models.ForeignKey(
        Exercise, 
        on_delete=models.CASCADE, 
        related_name='execution_sessions',
        null=True,
        blank=True
    )
    
    # Execution Environment
    programming_language = models.ForeignKey(
        ProgrammingLanguage, 
        on_delete=models.CASCADE
    )
    docker_container_id = models.CharField(max_length=100, blank=True)
    
    # Session Details
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    total_executions = models.PositiveIntegerField(default=0)
    successful_executions = models.PositiveIntegerField(default=0)
    
    # Resource Usage
    peak_memory_usage = models.FloatField(
        default=0.0, 
        help_text="Peak memory usage in MB"
    )
    total_cpu_time = models.FloatField(
        default=0.0, 
        help_text="Total CPU time in seconds"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Session {self.session_id} - {self.user.username}"

    def is_expired(self):
        """Check if session has expired (inactive for more than 1 hour)."""
        if not self.last_activity:
            return True
        return timezone.now() - self.last_activity > timedelta(hours=1)

    def end_session(self):
        """End the execution session."""
        self.ended_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['ended_at', 'is_active'])


class StudentProgress(models.Model):
    """Track student progress on exercises."""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='exercise_progress'
    )
    exercise = models.ForeignKey(
        Exercise, 
        on_delete=models.CASCADE, 
        related_name='student_progress'
    )
    
    # Progress Tracking
    started = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    best_score = models.PositiveIntegerField(
        default=0, 
        validators=[MaxValueValidator(100)]
    )
    total_attempts = models.PositiveIntegerField(default=0)
    
    # Time Tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_time_spent = models.PositiveIntegerField(
        default=0, 
        help_text="Total time in minutes"
    )
    
    # Assistance Tracking
    hints_used = models.PositiveIntegerField(default=0)
    ai_help_requested = models.PositiveIntegerField(default=0)
    
    # Notes and Bookmarks
    personal_notes = models.TextField(blank=True)
    bookmarked = models.BooleanField(default=False)
    
    # Tracking
    last_attempt_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'exercise']]
        ordering = ['-last_attempt_at']

    def __str__(self):
        return f"{self.user.username} - {self.exercise.title}"

    def mark_completed(self, score):
        """Mark exercise as completed with given score."""
        self.completed = True
        self.completed_at = timezone.now()
        if score > self.best_score:
            self.best_score = score
        self.save(update_fields=['completed', 'completed_at', 'best_score'])

    def get_completion_rate(self):
        """Get completion rate based on best score."""
        return min(self.best_score, 100)


class ExerciseHint(models.Model):
    """Progressive hints for exercises."""
    exercise = models.ForeignKey(
        Exercise, 
        on_delete=models.CASCADE, 
        related_name='hints'
    )
    title = models.CharField(max_length=100)
    content = models.TextField()
    order = models.PositiveIntegerField(default=0)
    unlock_after_attempts = models.PositiveIntegerField(
        default=1, 
        help_text="Number of failed attempts before hint becomes available"
    )
    point_penalty = models.PositiveIntegerField(
        default=0, 
        help_text="Points deducted for using this hint"
    )
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['exercise', 'order']

    def __str__(self):
        return f"{self.exercise.title} - Hint {self.order}"


class HintUsage(models.Model):
    """Track hint usage by students."""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='hint_usage'
    )
    hint = models.ForeignKey(
        ExerciseHint, 
        on_delete=models.CASCADE, 
        related_name='usage_records'
    )
    used_at = models.DateTimeField(auto_now_add=True)
    helpful = models.BooleanField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = [['user', 'hint']]

    def __str__(self):
        return f"{self.user.username} used hint for {self.hint.exercise.title}"