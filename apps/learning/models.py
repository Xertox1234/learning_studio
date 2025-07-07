"""
Learning management models for Python Learning Studio.
These models handle courses, lessons, progress tracking, and AI-enhanced content.
"""

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class Category(models.Model):
    """
    Categories for organizing courses and lessons.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    color = models.CharField(max_length=7, default="#3498db", help_text="Hex color code")
    
    # Hierarchy support
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    
    # Display order
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def get_absolute_url(self):
        return reverse('learning:category', kwargs={'slug': self.slug})


class Course(models.Model):
    """
    Main course model with AI-enhanced features.
    """
    # Basic information
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=250, help_text="Brief course summary")
    
    # Content
    learning_objectives = models.TextField(help_text="What students will learn")
    prerequisites = models.TextField(blank=True, help_text="Required knowledge before starting")
    
    # Course metadata
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taught_courses')
    
    # Difficulty and timing
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        default='beginner'
    )
    
    estimated_duration = models.PositiveIntegerField(
        help_text="Estimated duration in hours",
        validators=[MinValueValidator(1), MaxValueValidator(1000)]
    )
    
    # Course settings
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Images
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='course_banners/', blank=True, null=True)
    
    # Statistics (auto-calculated)
    total_lessons = models.PositiveIntegerField(default=0)
    total_enrollments = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    
    # AI Enhancement
    ai_generated_summary = models.TextField(blank=True, help_text="AI-generated course summary")
    ai_suggested_prerequisites = models.TextField(blank=True, help_text="AI-suggested prerequisites")
    ai_learning_path = models.TextField(blank=True, help_text="AI-recommended learning path")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('learning:course_detail', kwargs={'slug': self.slug})
    
    def update_statistics(self):
        """Update course statistics."""
        self.total_lessons = self.lessons.count()
        self.total_enrollments = self.enrollments.count()
        
        # Calculate average rating
        reviews = self.reviews.all()
        if reviews:
            self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.total_reviews = reviews.count()
        
        self.save(update_fields=['total_lessons', 'total_enrollments', 'average_rating', 'total_reviews'])
    
    @property
    def completion_rate(self):
        """Calculate overall course completion rate."""
        enrollments = self.enrollments.all()
        if not enrollments:
            return 0
        completed = enrollments.filter(completed=True).count()
        return int((completed / enrollments.count()) * 100)
    
    def generate_ai_description(self):
        """Generate AI-enhanced course description (placeholder for AI integration)."""
        # This will be implemented with the LearningContentAI service
        return f"AI-enhanced description for {self.title}"
    
    def generate_learning_objectives(self):
        """Generate AI-powered learning objectives."""
        # This will be implemented with the LearningContentAI service
        return f"AI-generated learning objectives for {self.title}"


class Lesson(models.Model):
    """
    Individual lessons within courses.
    """
    # Basic information
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField()
    
    # Course relationship
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    
    # Content
    content = models.TextField(help_text="Main lesson content")
    video_url = models.URLField(blank=True, help_text="Optional video URL")
    
    # Lesson metadata
    lesson_type = models.CharField(
        max_length=20,
        choices=[
            ('theory', 'Theory'),
            ('practical', 'Practical'),
            ('exercise', 'Exercise'),
            ('project', 'Project'),
            ('quiz', 'Quiz'),
        ],
        default='theory'
    )
    
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    
    # Ordering and timing
    order = models.PositiveIntegerField(default=0)
    estimated_duration = models.PositiveIntegerField(
        help_text="Estimated duration in minutes",
        validators=[MinValueValidator(1), MaxValueValidator(300)]
    )
    
    # Content settings
    is_published = models.BooleanField(default=False)
    is_free = models.BooleanField(default=True)
    
    # Prerequisites
    required_lessons = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        help_text="Lessons that must be completed before this one"
    )
    
    # AI Enhancement
    ai_generated_summary = models.TextField(blank=True)
    ai_suggested_exercises = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'order']
        unique_together = ['course', 'slug']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def get_absolute_url(self):
        return reverse('learning:lesson_detail', kwargs={
            'course_slug': self.course.slug,
            'lesson_slug': self.slug
        })
    
    def get_next_lesson(self):
        """Get the next lesson in the course."""
        return self.course.lessons.filter(order__gt=self.order).first()
    
    def get_previous_lesson(self):
        """Get the previous lesson in the course."""
        return self.course.lessons.filter(order__lt=self.order).last()
    
    def can_access(self, user):
        """Check if user can access this lesson."""
        if not user.is_authenticated:
            return False
        
        # Check if user is enrolled in course
        if not self.course.enrollments.filter(user=user).exists():
            return False
        
        # Check prerequisites
        for required_lesson in self.required_lessons.all():
            if not UserProgress.objects.filter(
                user=user,
                lesson=required_lesson,
                completed=True
            ).exists():
                return False
        
        return True


class CourseEnrollment(models.Model):
    """
    User enrollment in courses.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    
    # Enrollment status
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Progress tracking
    progress_percentage = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)])
    last_accessed_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_accessed_by'
    )
    last_activity = models.DateTimeField(auto_now=True)
    
    # Completion tracking
    total_time_spent = models.PositiveIntegerField(default=0, help_text="Total time in minutes")
    
    class Meta:
        unique_together = ['user', 'course']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    
    def update_progress(self):
        """Update enrollment progress based on lesson completion."""
        total_lessons = self.course.lessons.count()
        if total_lessons == 0:
            self.progress_percentage = 0
            return
        
        completed_lessons = UserProgress.objects.filter(
            user=self.user,
            lesson__course=self.course,
            completed=True
        ).count()
        
        self.progress_percentage = int((completed_lessons / total_lessons) * 100)
        
        # Mark course as completed if all lessons are done
        if self.progress_percentage == 100 and not self.completed:
            self.completed = True
            self.completed_at = timezone.now()
        
        self.save(update_fields=['progress_percentage', 'completed', 'completed_at'])


class UserProgress(models.Model):
    """
    User progress tracking for individual lessons.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='user_progress')
    
    # Progress status
    started = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    # Time tracking
    time_spent = models.PositiveIntegerField(default=0, help_text="Time spent in minutes")
    
    # Content position (for videos, long content)
    content_position = models.PositiveIntegerField(default=0, help_text="Last position in content")
    
    # Notes and bookmarks
    notes = models.TextField(blank=True, help_text="User's personal notes")
    bookmarked = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'lesson']
        ordering = ['-last_accessed']
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"
    
    def mark_started(self):
        """Mark lesson as started."""
        if not self.started:
            self.started = True
            self.started_at = timezone.now()
            self.save(update_fields=['started', 'started_at'])
    
    def mark_completed(self):
        """Mark lesson as completed."""
        if not self.completed:
            self.completed = True
            self.completed_at = timezone.now()
            if not self.started:
                self.mark_started()
            self.save(update_fields=['completed', 'completed_at'])
            
            # Update course enrollment progress
            enrollment = CourseEnrollment.objects.filter(
                user=self.user,
                course=self.lesson.course
            ).first()
            if enrollment:
                enrollment.update_progress()


class LearningPath(models.Model):
    """
    Curated learning paths combining multiple courses.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    
    # Path metadata
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_paths')
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    
    estimated_duration = models.PositiveIntegerField(help_text="Total estimated hours")
    
    # Content
    courses = models.ManyToManyField(Course, through='LearningPathCourse')
    
    # Settings
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # AI Enhancement
    ai_generated_description = models.TextField(blank=True)
    ai_recommended_order = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('learning:learning_path', kwargs={'slug': self.slug})


class LearningPathCourse(models.Model):
    """
    Through model for learning path courses with ordering.
    """
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ['learning_path', 'course']
    
    def __str__(self):
        return f"{self.learning_path.title} - {self.course.title}"


class CourseReview(models.Model):
    """
    User reviews and ratings for courses.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_reviews')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    
    # Review content
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    
    # Review metadata
    helpful_votes = models.PositiveIntegerField(default=0)
    verified_purchase = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'course']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.rating}★)"


class StudySession(models.Model):
    """
    Track individual study sessions for analytics.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='study_sessions')
    
    # Session data
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.PositiveIntegerField(default=0, help_text="Duration in seconds")
    
    # Session outcome
    completed_lesson = models.BooleanField(default=False)
    notes_taken = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} ({self.started_at.date()})"
    
    def end_session(self):
        """End the study session and calculate duration."""
        if not self.ended_at:
            self.ended_at = timezone.now()
            self.duration = int((self.ended_at - self.started_at).total_seconds())
            self.save(update_fields=['ended_at', 'duration'])


# Import exercise models
from .exercise_models import (
    ProgrammingLanguage,
    ExerciseType,
    Exercise,
    TestCase,
    Submission,
    TestCaseResult,
    CodeExecutionSession,
    StudentProgress,
    ExerciseHint,
    HintUsage,
)

# Import community models
from .community_models import (
    Discussion,
    DiscussionReply,
    StudyGroup,
    StudyGroupMembership,
    StudyGroupPost,
    PeerReview,
    ReviewAssignment,
    CodeReview,
    LearningBuddy,
    LearningSession,
    UserInteraction,
    Notification,
)
