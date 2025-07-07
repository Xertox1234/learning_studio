"""
Community and social learning models for Python Learning Studio.
These models support discussions, user interactions, and collaborative learning features.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
import uuid

User = get_user_model()


class Discussion(models.Model):
    """Discussion threads for courses and lessons."""
    
    DISCUSSION_TYPES = [
        ('general', 'General Discussion'),
        ('question', 'Question'),
        ('help', 'Help Request'),
        ('announcement', 'Announcement'),
        ('project_share', 'Project Share'),
        ('code_review', 'Code Review'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    discussion_type = models.CharField(max_length=20, choices=DISCUSSION_TYPES, default='general')
    
    # Relationships
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='started_discussions')
    course = models.ForeignKey(
        'learning.Course', 
        on_delete=models.CASCADE, 
        related_name='discussions',
        null=True,
        blank=True
    )
    lesson = models.ForeignKey(
        'learning.Lesson', 
        on_delete=models.CASCADE, 
        related_name='discussions',
        null=True,
        blank=True
    )
    exercise = models.ForeignKey(
        'learning.Exercise', 
        on_delete=models.CASCADE, 
        related_name='discussions',
        null=True,
        blank=True
    )
    
    # Discussion Status
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # Statistics
    reply_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(auto_now_add=True)
    
    # Moderation
    is_moderated = models.BooleanField(default=False)
    moderator_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-is_pinned', '-last_activity_at']
        indexes = [
            models.Index(fields=['course', '-last_activity_at']),
            models.Index(fields=['lesson', '-last_activity_at']),
            models.Index(fields=['exercise', '-last_activity_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('learning:discussion_detail', kwargs={'slug': self.slug})
    
    def update_last_activity(self):
        """Update last activity timestamp."""
        self.last_activity_at = timezone.now()
        self.save(update_fields=['last_activity_at'])
    
    def get_context_display(self):
        """Get human-readable context."""
        if self.exercise:
            return f"Exercise: {self.exercise.title}"
        elif self.lesson:
            return f"Lesson: {self.lesson.title}"
        elif self.course:
            return f"Course: {self.course.title}"
        return "General Discussion"


class DiscussionReply(models.Model):
    """Replies to discussion threads."""
    
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_replies')
    content = models.TextField()
    
    # Reply threading
    parent_reply = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='child_replies'
    )
    
    # Status
    is_answer = models.BooleanField(default=False, help_text="Mark as the accepted answer")
    is_helpful = models.BooleanField(default=False)
    
    # Voting
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)
    
    # Code sharing
    shared_code = models.TextField(blank=True, help_text="Code snippet shared in reply")
    code_language = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Moderation
    is_moderated = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['discussion', 'created_at']),
            models.Index(fields=['parent_reply', 'created_at']),
        ]
    
    def __str__(self):
        return f"Reply to {self.discussion.title} by {self.author.username}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update discussion stats and activity
        self.discussion.reply_count = self.discussion.replies.count()
        self.discussion.last_activity_at = timezone.now()
        self.discussion.save(update_fields=['reply_count', 'last_activity_at'])


class StudyGroup(models.Model):
    """Study groups for collaborative learning."""
    
    GROUP_TYPES = [
        ('course', 'Course Study Group'),
        ('topic', 'Topic Study Group'),
        ('project', 'Project Collaboration'),
        ('practice', 'Practice Group'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=100)
    description = models.TextField()
    group_type = models.CharField(max_length=20, choices=GROUP_TYPES, default='course')
    
    # Group Settings
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_study_groups')
    members = models.ManyToManyField(User, through='StudyGroupMembership', related_name='study_groups')
    max_members = models.PositiveIntegerField(default=10, validators=[MinValueValidator(2), MaxValueValidator(50)])
    
    # Content Association
    course = models.ForeignKey(
        'learning.Course', 
        on_delete=models.CASCADE, 
        related_name='study_groups',
        null=True,
        blank=True
    )
    
    # Group Status
    is_public = models.BooleanField(default=True, help_text="Public groups can be discovered and joined")
    requires_approval = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('learning:study_group_detail', kwargs={'pk': self.pk})
    
    @property
    def member_count(self):
        return self.members.count()
    
    @property
    def is_full(self):
        return self.member_count >= self.max_members


class StudyGroupMembership(models.Model):
    """Membership in study groups."""
    
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Status
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Contributions
    posts_count = models.PositiveIntegerField(default=0)
    helpful_contributions = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'study_group']
    
    def __str__(self):
        return f"{self.user.username} in {self.study_group.name}"


class StudyGroupPost(models.Model):
    """Posts within study groups."""
    
    POST_TYPES = [
        ('discussion', 'Discussion'),
        ('question', 'Question'),
        ('resource', 'Resource Share'),
        ('progress', 'Progress Update'),
        ('project', 'Project Share'),
    ]
    
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_group_posts')
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='discussion')
    
    # Attachments
    shared_code = models.TextField(blank=True)
    code_language = models.CharField(max_length=50, blank=True)
    external_link = models.URLField(blank=True)
    
    # Engagement
    likes = models.PositiveIntegerField(default=0)
    replies_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} in {self.study_group.name}"


class PeerReview(models.Model):
    """Peer code review system."""
    
    REVIEW_STATUS = [
        ('pending', 'Pending Review'),
        ('in_review', 'In Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Review Details
    title = models.CharField(max_length=200)
    description = models.TextField()
    code_to_review = models.TextField()
    programming_language = models.ForeignKey(
        'learning.ProgrammingLanguage', 
        on_delete=models.CASCADE
    )
    
    # Participants
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reviews')
    reviewers = models.ManyToManyField(User, through='ReviewAssignment', related_name='assigned_reviews')
    
    # Context
    exercise = models.ForeignKey(
        'learning.Exercise', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    lesson = models.ForeignKey(
        'learning.Lesson', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    # Review Settings
    max_reviewers = models.PositiveIntegerField(default=3)
    review_deadline = models.DateTimeField(null=True, blank=True)
    is_anonymous = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(max_length=20, choices=REVIEW_STATUS, default='pending')
    completed_reviews = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review: {self.title} by {self.author.username}"


class ReviewAssignment(models.Model):
    """Assignment of reviewers to peer reviews."""
    
    peer_review = models.ForeignKey(PeerReview, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Assignment Details
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_accepted = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['peer_review', 'reviewer']
    
    def __str__(self):
        return f"{self.reviewer.username} reviewing {self.peer_review.title}"


class CodeReview(models.Model):
    """Individual code review submissions."""
    
    peer_review = models.ForeignKey(PeerReview, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='code_reviews')
    
    # Review Content
    overall_feedback = models.TextField()
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Overall code quality rating (1-5)"
    )
    
    # Detailed Feedback
    code_quality = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    readability = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    efficiency = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    best_practices = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Suggestions
    improvement_suggestions = models.TextField(blank=True)
    positive_aspects = models.TextField(blank=True)
    
    # Status
    is_helpful = models.BooleanField(null=True, blank=True)
    author_response = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['peer_review', 'reviewer']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.peer_review.title}"
    
    @property
    def average_rating(self):
        """Calculate average rating across all criteria."""
        return (self.code_quality + self.readability + self.efficiency + self.best_practices) / 4


class LearningBuddy(models.Model):
    """Learning buddy/mentor relationships."""
    
    RELATIONSHIP_TYPES = [
        ('mentor_mentee', 'Mentor-Mentee'),
        ('study_partner', 'Study Partner'),
        ('accountability', 'Accountability Partner'),
    ]
    
    # Participants
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buddy_relationships_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buddy_relationships_as_user2')
    
    # Relationship Details
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPES)
    description = models.TextField(blank=True)
    
    # Focus Areas
    focus_topics = models.TextField(help_text="Learning topics to focus on together")
    goals = models.TextField(help_text="Shared learning goals")
    
    # Schedule
    meeting_frequency = models.CharField(
        max_length=20, 
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('biweekly', 'Bi-weekly'),
            ('monthly', 'Monthly'),
            ('as_needed', 'As Needed'),
        ],
        default='weekly'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_mutual = models.BooleanField(default=False, help_text="Both users agreed to the relationship")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user1', 'user2']
    
    def __str__(self):
        return f"{self.user1.username} & {self.user2.username} ({self.get_relationship_type_display()})"


class LearningSession(models.Model):
    """Collaborative learning sessions."""
    
    SESSION_TYPES = [
        ('study_group', 'Study Group Session'),
        ('pair_programming', 'Pair Programming'),
        ('code_review', 'Code Review Session'),
        ('project_work', 'Project Work'),
        ('mentoring', 'Mentoring Session'),
    ]
    
    # Session Details
    title = models.CharField(max_length=200)
    description = models.TextField()
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    
    # Participants
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_sessions')
    participants = models.ManyToManyField(User, related_name='learning_sessions')
    max_participants = models.PositiveIntegerField(default=5)
    
    # Scheduling
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    
    # Content
    agenda = models.TextField(blank=True)
    materials_link = models.URLField(blank=True)
    
    # Meeting Details
    meeting_link = models.URLField(blank=True, help_text="Video call link")
    meeting_password = models.CharField(max_length=50, blank=True)
    
    # Status
    is_public = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    
    # Results
    session_notes = models.TextField(blank=True)
    outcomes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_at']
    
    def __str__(self):
        return f"{self.title} - {self.scheduled_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def participant_count(self):
        return self.participants.count()
    
    @property
    def is_full(self):
        return self.participant_count >= self.max_participants
    
    @property
    def is_upcoming(self):
        return self.scheduled_at > timezone.now() and not self.is_cancelled


class UserInteraction(models.Model):
    """Track user interactions for community features."""
    
    INTERACTION_TYPES = [
        ('like', 'Like'),
        ('bookmark', 'Bookmark'),
        ('follow', 'Follow'),
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
        ('share', 'Share'),
        ('report', 'Report'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    
    # Generic foreign key for different content types
    content_type = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'interaction_type', 'content_type', 'object_id']
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'interaction_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.content_type}:{self.object_id}"


class Notification(models.Model):
    """User notifications for community activities."""
    
    NOTIFICATION_TYPES = [
        ('discussion_reply', 'Discussion Reply'),
        ('study_group_invite', 'Study Group Invitation'),
        ('peer_review_request', 'Peer Review Request'),
        ('session_reminder', 'Session Reminder'),
        ('buddy_request', 'Learning Buddy Request'),
        ('achievement', 'Achievement Unlocked'),
        ('course_update', 'Course Update'),
        ('system', 'System Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Action link
    action_url = models.URLField(blank=True)
    action_text = models.CharField(max_length=50, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])