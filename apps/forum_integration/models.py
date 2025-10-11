from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.search import index
from wagtail.images.blocks import ImageChooserBlock
from machina.core.db.models import get_model
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post

User = get_user_model()


# Trust Level System Models

class TrustLevel(models.Model):
    """
    Trust Level model that tracks user progression through 5 tiers (TL0-TL4)
    based on engagement metrics and community behavior.
    """
    TRUST_LEVELS = [
        (0, 'New User'),
        (1, 'Basic User'),
        (2, 'Member'),
        (3, 'Regular'),
        (4, 'Leader'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trust_level')
    level = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        choices=TRUST_LEVELS
    )
    
    # Engagement metrics
    posts_read = models.IntegerField(default=0)
    topics_viewed = models.IntegerField(default=0)
    time_read = models.DurationField(default=timedelta())
    posts_created = models.IntegerField(default=0)
    topics_created = models.IntegerField(default=0)
    likes_given = models.IntegerField(default=0)
    likes_received = models.IntegerField(default=0)
    days_visited = models.IntegerField(default=0)
    
    # Tracking fields
    last_visit_date = models.DateField(null=True, blank=True)
    last_calculated = models.DateTimeField(auto_now=True)
    promoted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Trust Level"
        verbose_name_plural = "Trust Levels"
        indexes = [
            models.Index(fields=['level']),
            models.Index(fields=['last_visit_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - TL{self.level} ({self.get_level_display()})"
    
    @property
    def level_name(self):
        """Return the human-readable level name"""
        return self.get_level_display()
    
    @property
    def can_post_images(self):
        """Users can post images at TL1+"""
        return self.level >= 1
    
    @property
    def can_edit_posts_extended(self):
        """Users can edit posts for longer at TL2+"""
        return self.level >= 2
    
    @property
    def can_create_wiki_posts(self):
        """Users can create wiki posts at TL2+"""
        return self.level >= 2
    
    @property
    def can_moderate_basic(self):
        """Users can perform basic moderation at TL3+"""
        return self.level >= 3
    
    @property
    def can_edit_titles(self):
        """Users can edit topic titles at TL3+"""
        return self.level >= 3
    
    @property
    def can_moderate_full(self):
        """Users can perform full moderation at TL4"""
        return self.level >= 4
    
    def check_for_promotion(self):
        """
        Check if user qualifies for promotion and return the new level
        Returns None if no promotion is warranted
        """
        current_level = self.level
        
        # TL0 -> TL1: Read 10 posts, spend 10 minutes reading
        if current_level == 0:
            if (self.posts_read >= 10 and 
                self.time_read >= timedelta(minutes=10)):
                return 1
        
        # TL1 -> TL2: Visit 15 days, read 100 posts, receive 1 like
        elif current_level == 1:
            if (self.days_visited >= 15 and
                self.posts_read >= 100 and
                self.likes_received >= 1):
                return 2
        
        # TL2 -> TL3: Visit 50 days, read 500 posts, receive 10 likes, give 30 likes
        elif current_level == 2:
            if (self.days_visited >= 50 and
                self.posts_read >= 500 and
                self.likes_received >= 10 and
                self.likes_given >= 30):
                return 3
        
        # TL3 -> TL4: Manual promotion by admins only
        # This requires staff intervention
        
        return None
    
    def promote_to_level(self, new_level):
        """Promote user to a new trust level"""
        if new_level > self.level and new_level <= 4:
            self.level = new_level
            self.promoted_at = timezone.now()
            self.save()
            return True
        return False


class UserActivity(models.Model):
    """
    Track daily user activity for trust level calculations
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_activity')
    date = models.DateField(default=timezone.now)
    
    # Daily metrics
    posts_read_today = models.IntegerField(default=0)
    topics_viewed_today = models.IntegerField(default=0)
    time_spent_reading = models.DurationField(default=timedelta())
    posts_created_today = models.IntegerField(default=0)
    likes_given_today = models.IntegerField(default=0)
    
    # Reading achievements tracking
    topics_completed = models.IntegerField(default=0)
    time_spent = models.DurationField(default=timedelta())
    active_sessions = models.IntegerField(default=0)
    
    # Session tracking
    first_visit_time = models.DateTimeField(null=True, blank=True)
    last_activity_time = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['user', 'date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"


class ReadingProgress(models.Model):
    """
    Track reading progress for individual topics to measure engagement
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_progress')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='reading_progress')
    
    # Reading metrics
    time_spent = models.DurationField(default=timedelta())
    scroll_depth = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    last_read_post = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    
    # Tracking
    first_read = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Reading Progress"
        verbose_name_plural = "Reading Progress"
        unique_together = ['user', 'topic']
        indexes = [
            models.Index(fields=['user', 'completed']),
            models.Index(fields=['topic']),
        ]
    
    def __str__(self):
        status = "Completed" if self.completed else f"{int(self.scroll_depth * 100)}%"
        return f"{self.user.username} - {self.topic.subject} ({status})"
    
    @property
    def completion_percentage(self):
        """Return completion as a percentage"""
        return int(self.scroll_depth * 100)


# Review Queue and Moderation Models

class ReviewQueue(models.Model):
    """
    Unified review queue for all moderation tasks.
    Centralizes flagged posts, new user content, and other reviewable items.
    """
    REVIEW_TYPES = [
        ('flagged_post', 'Flagged Post'),
        ('new_user_post', 'New User Post'),
        ('edited_post', 'Edited Post'),
        ('user_report', 'User Report'),
        ('spam_detection', 'Spam Detection'),
        ('trust_level_review', 'Trust Level Review'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_info', 'Needs More Information'),
        ('escalated', 'Escalated'),
    ]
    
    PRIORITY_CHOICES = [
        (1, 'Critical'),
        (2, 'High'),
        (3, 'Medium'),
        (4, 'Low'),
    ]
    
    # Core fields
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=3)
    
    # Content references (at least one must be set)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True)
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='forum_reported_reviews')
    
    # Reporting and moderation
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='forum_reports_made')
    assigned_moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='forum_assigned_reviews')
    
    # Details
    reason = models.TextField(help_text="Reason for review or flag description")
    moderator_notes = models.TextField(blank=True, help_text="Internal moderator notes")
    resolution_notes = models.TextField(blank=True, help_text="Resolution explanation")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Priority scoring factors
    score = models.FloatField(default=0.0, help_text="Calculated priority score")
    upvotes = models.IntegerField(default=0, help_text="Community upvotes for this review")
    
    class Meta:
        verbose_name = "Review Queue Item"
        verbose_name_plural = "Review Queue Items"
        ordering = ['-priority', '-score', '-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['review_type', 'status']),
            models.Index(fields=['assigned_moderator', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['score']),
        ]
    
    def __str__(self):
        content_desc = ""
        if self.post:
            content_desc = f"Post {self.post.id}"
        elif self.topic:
            content_desc = f"Topic {self.topic.id}"
        elif self.reported_user:
            content_desc = f"User {self.reported_user.username}"
        
        return f"{self.get_review_type_display()} - {content_desc} ({self.get_status_display()})"
    
    def calculate_priority_score(self):
        """Calculate priority score based on multiple factors"""
        score = 0.0
        
        # Base priority score
        priority_scores = {1: 100, 2: 75, 3: 50, 4: 25}
        score += priority_scores.get(self.priority, 50)
        
        # Age factor (older items get higher priority)
        if self.created_at:
            age_hours = (timezone.now() - self.created_at).total_seconds() / 3600
            score += min(age_hours * 0.5, 50)  # Cap at 50 points for age
        else:
            # If created_at is None (during creation), assume 0 age
            score += 0
        
        # Community upvotes
        score += self.upvotes * 10
        
        # Trust level of reported user (lower trust = higher priority)
        if self.reported_user:
            try:
                trust_level = self.reported_user.trust_level.level
                score += (4 - trust_level) * 5  # TL0 gets +20, TL4 gets 0
            except:
                score += 20  # No trust level = treat as TL0
        
        # Review type specific scoring
        type_scores = {
            'spam_detection': 30,
            'flagged_post': 25,
            'user_report': 20,
            'new_user_post': 10,
            'edited_post': 5,
            'trust_level_review': 5,
        }
        score += type_scores.get(self.review_type, 10)
        
        return score
    
    def save(self, *args, **kwargs):
        # Update score on save
        self.score = self.calculate_priority_score()
        
        # Set resolved_at when status changes to resolved
        if self.status in ['approved', 'rejected'] and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_resolved(self):
        return self.status in ['approved', 'rejected']
    
    @property
    def age_in_hours(self):
        if self.created_at:
            return (timezone.now() - self.created_at).total_seconds() / 3600
        return 0


class ModerationLog(models.Model):
    """
    Audit trail for all moderation actions.
    """
    ACTION_TYPES = [
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('edit', 'Edited'),
        ('delete', 'Deleted'),
        ('ban_user', 'Banned User'),
        ('trust_level_change', 'Trust Level Changed'),
        ('assign_moderator', 'Assigned Moderator'),
        ('escalate', 'Escalated'),
        ('bulk_action', 'Bulk Action'),
    ]
    
    # Action details
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    moderator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderation_actions')
    
    # Target references
    review_item = models.ForeignKey(ReviewQueue, on_delete=models.CASCADE, null=True, blank=True)
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='moderation_targets')
    target_post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    target_topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True)
    
    # Action details
    reason = models.TextField(help_text="Reason for the moderation action")
    details = models.JSONField(default=dict, blank=True, help_text="Additional action details")
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Moderation Log"
        verbose_name_plural = "Moderation Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['moderator', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['target_user', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        target = ""
        if self.target_user:
            target = f"User: {self.target_user.username}"
        elif self.target_post:
            target = f"Post: {self.target_post.id}"
        elif self.target_topic:
            target = f"Topic: {self.target_topic.subject[:50]}"
        elif self.review_item:
            target = f"Review: {self.review_item.id}"
        
        return f"{self.moderator.username} {self.get_action_type_display()} {target}"


class FlaggedContent(models.Model):
    """
    Track flagged content and flag reasons.
    """
    FLAG_REASONS = [
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('off_topic', 'Off Topic'),
        ('harassment', 'Harassment'),
        ('duplicate', 'Duplicate'),
        ('misinformation', 'Misinformation'),
        ('other', 'Other'),
    ]
    
    # Content reference
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True)
    
    # Flag details
    flagger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flagged_content')
    reason = models.CharField(max_length=20, choices=FLAG_REASONS)
    description = models.TextField(blank=True, help_text="Additional details about the flag")
    
    # Status
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_flags')
    resolution_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Flagged Content"
        verbose_name_plural = "Flagged Content"
        unique_together = ['flagger', 'post', 'reason']  # Prevent duplicate flags
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_resolved', 'created_at']),
            models.Index(fields=['flagger']),
            models.Index(fields=['reason']),
        ]
    
    def __str__(self):
        content = self.post or self.topic
        content_type = "Post" if self.post else "Topic"
        return f"{content_type} flagged by {self.flagger.username} for {self.get_reason_display()}"


# Badge and Gamification Models

class BadgeCategory(models.Model):
    """
    Categories for organizing badges (e.g., Participation, Quality, Moderation, Special)
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-award', help_text="Bootstrap icon class")
    color = models.CharField(max_length=7, default='#0d6efd', help_text="Hex color code")
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Badge Category"
        verbose_name_plural = "Badge Categories"
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class Badge(models.Model):
    """
    Badge definitions with unlock conditions and metadata
    """
    RARITY_CHOICES = [
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]
    
    CONDITION_TYPES = [
        ('posts_created', 'Posts Created'),
        ('topics_created', 'Topics Created'),
        ('likes_received', 'Likes Received'),
        ('likes_given', 'Likes Given'),
        ('days_visited', 'Days Visited'),
        ('reading_time', 'Reading Time'),
        ('first_post', 'First Post'),
        ('first_like', 'First Like Given'),
        ('helpful_posts', 'Helpful Posts'),
        ('consecutive_days', 'Consecutive Days'),
        ('trust_level', 'Trust Level Reached'),
        ('moderation_actions', 'Moderation Actions'),
        ('flags_resolved', 'Flags Resolved'),
        ('special_event', 'Special Event'),
        ('anniversary', 'Anniversary'),
        ('early_adopter', 'Early Adopter'),
    ]
    
    # Basic information
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    category = models.ForeignKey(BadgeCategory, on_delete=models.CASCADE, related_name='badges')
    
    # Visual representation
    icon = models.CharField(max_length=50, default='bi-award', help_text="Bootstrap icon class")
    image = models.ImageField(upload_to='badges/', blank=True, null=True, help_text="Custom badge image")
    color = models.CharField(max_length=7, default='#ffd700', help_text="Badge color (hex)")
    rarity = models.CharField(max_length=10, choices=RARITY_CHOICES, default='common')
    
    # Unlock conditions
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPES)
    condition_value = models.IntegerField(help_text="Threshold value for condition")
    condition_data = models.JSONField(default=dict, blank=True, help_text="Additional condition parameters")
    
    # Badge properties
    is_active = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False, help_text="Hidden until earned")
    points_awarded = models.IntegerField(default=10, help_text="Points given when earned")
    sort_order = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"
        ordering = ['category', 'sort_order', 'name']
        indexes = [
            models.Index(fields=['condition_type', 'is_active']),
            models.Index(fields=['category', 'sort_order']),
            models.Index(fields=['rarity']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()})"
    
    @property
    def rarity_color(self):
        """Get color based on rarity"""
        colors = {
            'common': '#6c757d',
            'uncommon': '#198754',
            'rare': '#0d6efd',
            'epic': '#6f42c1',
            'legendary': '#fd7e14',
        }
        return colors.get(self.rarity, '#6c757d')
    
    def check_condition(self, user):
        """
        Check if user meets the condition for this badge
        """
        try:
            trust_level = user.trust_level
        except TrustLevel.DoesNotExist:
            trust_level = None
        
        if self.condition_type == 'posts_created':
            return trust_level and trust_level.posts_created >= self.condition_value
        
        elif self.condition_type == 'topics_created':
            return trust_level and trust_level.topics_created >= self.condition_value
        
        elif self.condition_type == 'likes_received':
            return trust_level and trust_level.likes_received >= self.condition_value
        
        elif self.condition_type == 'likes_given':
            return trust_level and trust_level.likes_given >= self.condition_value
        
        elif self.condition_type == 'days_visited':
            return trust_level and trust_level.days_visited >= self.condition_value
        
        elif self.condition_type == 'reading_time':
            if trust_level:
                reading_hours = trust_level.time_read.total_seconds() / 3600
                return reading_hours >= self.condition_value
            return False
        
        elif self.condition_type == 'trust_level':
            return trust_level and trust_level.level >= self.condition_value
        
        elif self.condition_type == 'first_post':
            return trust_level and trust_level.posts_created >= 1
        
        elif self.condition_type == 'first_like':
            return trust_level and trust_level.likes_given >= 1
        
        elif self.condition_type == 'consecutive_days':
            # This would require more complex tracking
            return False  # Placeholder for now
        
        elif self.condition_type == 'moderation_actions':
            mod_count = ModerationLog.objects.filter(moderator=user).count()
            return mod_count >= self.condition_value
        
        elif self.condition_type == 'anniversary':
            # Check if user joined X years ago
            years_since_join = (timezone.now() - user.date_joined).days / 365
            return years_since_join >= self.condition_value
        
        elif self.condition_type == 'early_adopter':
            # Check if user joined before a certain date
            cutoff_date = self.condition_data.get('cutoff_date')
            if cutoff_date:
                cutoff = timezone.datetime.fromisoformat(cutoff_date)
                return user.date_joined <= cutoff
            return False
        
        return False
    
    def calculate_progress(self, user):
        """
        Calculate user's progress toward earning this badge
        """
        try:
            trust_level = user.trust_level
        except TrustLevel.DoesNotExist:
            trust_level = None
        
        if self.condition_type == 'posts_created':
            return trust_level.posts_created if trust_level else 0
        
        elif self.condition_type == 'topics_created':
            return trust_level.topics_created if trust_level else 0
        
        elif self.condition_type == 'likes_received':
            return trust_level.likes_received if trust_level else 0
        
        elif self.condition_type == 'likes_given':
            return trust_level.likes_given if trust_level else 0
        
        elif self.condition_type == 'days_visited':
            return trust_level.days_visited if trust_level else 0
        
        elif self.condition_type == 'reading_time':
            if trust_level:
                return int(trust_level.time_read.total_seconds() / 3600)
            return 0
        
        elif self.condition_type == 'trust_level':
            return trust_level.level if trust_level else 0
        
        elif self.condition_type == 'moderation_actions':
            return ModerationLog.objects.filter(moderator=user).count()
        
        elif self.condition_type in ['first_post', 'first_like']:
            # These are binary conditions
            return 1 if self.check_condition(user) else 0
        
        elif self.condition_type == 'anniversary':
            return int((timezone.now() - user.date_joined).days / 365)
        
        return 0


class UserBadge(models.Model):
    """
    Track which badges users have earned
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='earned_by')
    earned_at = models.DateTimeField(auto_now_add=True)
    notification_sent = models.BooleanField(default=False)
    
    # Optional context data
    earned_for_post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True)
    earned_for_topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    context_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "User Badge"
        verbose_name_plural = "User Badges"
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', 'earned_at']),
            models.Index(fields=['badge']),
            models.Index(fields=['notification_sent']),
        ]
    
    def __str__(self):
        return f"{self.user.username} earned {self.badge.name}"


class UserPoints(models.Model):
    """
    Track user points and gamification metrics
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='points')
    
    # Point totals
    total_points = models.IntegerField(default=0)
    monthly_points = models.IntegerField(default=0)
    weekly_points = models.IntegerField(default=0)
    
    # Streaks and achievements
    current_streak = models.IntegerField(default=0, help_text="Current daily activity streak")
    longest_streak = models.IntegerField(default=0, help_text="Longest daily activity streak")
    last_activity_date = models.DateField(null=True, blank=True)
    
    # Leaderboard position caching
    global_rank = models.IntegerField(null=True, blank=True)
    monthly_rank = models.IntegerField(null=True, blank=True)
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Points"
        verbose_name_plural = "User Points"
        ordering = ['-total_points']
        indexes = [
            models.Index(fields=['total_points']),
            models.Index(fields=['monthly_points']),
            models.Index(fields=['current_streak']),
            models.Index(fields=['last_activity_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.total_points} points"
    
    def add_points(self, points, reason=""):
        """Add points to user's total"""
        self.total_points += points
        self.monthly_points += points
        self.weekly_points += points
        self.save()
        
        # Create point history entry
        PointHistory.objects.create(
            user=self.user,
            points_change=points,
            reason=reason,
            new_total=self.total_points
        )
    
    def update_streak(self):
        """Update daily activity streak"""
        today = timezone.now().date()
        yesterday = today - timezone.timedelta(days=1)
        
        if self.last_activity_date == yesterday:
            # Continue streak
            self.current_streak += 1
        elif self.last_activity_date != today:
            # Start new streak
            self.current_streak = 1
        
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.last_activity_date = today
        self.save()


class PointHistory(models.Model):
    """
    History of point changes for transparency and analytics
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_history')
    points_change = models.IntegerField()  # Can be positive or negative
    reason = models.CharField(max_length=200)
    new_total = models.IntegerField()
    
    # Optional references
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Point History"
        verbose_name_plural = "Point History"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        sign = '+' if self.points_change > 0 else ''
        return f"{self.user.username}: {sign}{self.points_change} points - {self.reason}"


class Achievement(models.Model):
    """
    Special achievements that are more complex than simple badges
    """
    ACHIEVEMENT_TYPES = [
        ('milestone', 'Milestone'),
        ('special', 'Special Event'),
        ('community', 'Community Achievement'),
        ('seasonal', 'Seasonal'),
        ('challenge', 'Challenge'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    
    # Visual
    icon = models.CharField(max_length=50, default='bi-trophy')
    color = models.CharField(max_length=7, default='#ffd700')
    
    # Requirements (JSON field for complex conditions)
    requirements = models.JSONField(help_text="Complex achievement requirements")
    
    # Rewards
    points_reward = models.IntegerField(default=50)
    badges_granted = models.ManyToManyField(Badge, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Achievement"
        verbose_name_plural = "Achievements"
        ordering = ['achievement_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_achievement_type_display()})"


class ForumUserAchievement(models.Model):
    """
    Track user forum achievements
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    progress_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Forum User Achievement"
        verbose_name_plural = "Forum User Achievements"
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} earned {self.achievement.name}"


class ForumIndexPage(Page):
    """
    Wagtail page that displays the forum index.
    This page integrates with django-machina to show all forums.
    """
    intro = RichTextField(blank=True, help_text="Introduction text for the forum section")
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]
    
    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]
    
    def get_context(self, request):
        context = super().get_context(request)
        
        # Get root forums from machina
        forums = Forum.objects.filter(parent__isnull=True).order_by('lft')
        context['forums'] = forums
        
        # Get forum statistics
        User = get_user_model()
        context['total_topics'] = Topic.objects.count()
        context['total_posts'] = Post.objects.count()
        context['total_members'] = User.objects.filter(is_active=True).count()
        
        return context
    
    def get_template(self, request, *args, **kwargs):
        # Use our custom forum index template
        return 'forum_integration/forum_index_page.html'
    
    class Meta:
        verbose_name = "Forum Index Page"
        verbose_name_plural = "Forum Index Pages"


class ForumAnnouncementBlock(blocks.StructBlock):
    """Block for forum announcements"""
    title = blocks.CharBlock(required=True)
    content = blocks.RichTextBlock()
    announcement_type = blocks.ChoiceBlock(choices=[
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('danger', 'Important'),
    ], default='info')
    
    class Meta:
        template = 'forum_integration/blocks/announcement.html'
        icon = 'warning'
        label = 'Forum Announcement'


class RecentTopicsBlock(blocks.StructBlock):
    """Block to display recent forum topics"""
    title = blocks.CharBlock(default="Recent Forum Topics")
    num_topics = blocks.IntegerBlock(default=5, min_value=1, max_value=20)
    forum_filter = blocks.ChoiceBlock(
        choices=[],  # Will be populated dynamically
        required=False,
        help_text="Filter topics from specific forum"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Forum choices will be populated dynamically in template context
        self.child_blocks['forum_filter'].field.choices = [('', 'All Forums')]
    
    class Meta:
        template = 'forum_integration/blocks/recent_topics.html'
        icon = 'list-ul'
        label = 'Recent Forum Topics'


class ForumActivityBlock(blocks.StructBlock):
    """Block to display forum activity stats"""
    title = blocks.CharBlock(default="Forum Activity")
    show_topics = blocks.BooleanBlock(default=True)
    show_posts = blocks.BooleanBlock(default=True)
    show_members = blocks.BooleanBlock(default=True)
    show_online = blocks.BooleanBlock(default=True)
    
    class Meta:
        template = 'forum_integration/blocks/forum_activity.html'
        icon = 'group'
        label = 'Forum Activity Stats'


class ForumLandingPage(Page):
    """
    A more detailed forum landing page with StreamField content
    """
    hero_title = models.CharField(max_length=255, default="Community Forum")
    hero_subtitle = models.CharField(
        max_length=500, 
        default="Join our community to discuss Python programming, share knowledge, and get help"
    )
    hero_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    
    content = StreamField([
        ('announcement', ForumAnnouncementBlock()),
        ('recent_topics', RecentTopicsBlock()),
        ('forum_activity', ForumActivityBlock()),
        ('rich_text', blocks.RichTextBlock()),
        ('html', blocks.RawHTMLBlock()),
    ], blank=True, use_json_field=True)
    
    content_panels = Page.content_panels + [
        FieldPanel('hero_title'),
        FieldPanel('hero_subtitle'),
        FieldPanel('hero_image'),
        FieldPanel('content'),
    ]
    
    def get_context(self, request):
        context = super().get_context(request)
        
        # Add forum categories for display
        context['forum_categories'] = Forum.objects.filter(
            parent__isnull=True
        ).order_by('lft')
        
        return context
    
    class Meta:
        verbose_name = "Forum Landing Page"
        verbose_name_plural = "Forum Landing Pages"


# Forum Content Blocks for Rich Posts
class ForumCodeBlock(blocks.StructBlock):
    """Code block with syntax highlighting for forum posts"""
    language = blocks.ChoiceBlock(
        choices=[
            ('python', 'Python'),
            ('javascript', 'JavaScript'),
            ('html', 'HTML'),
            ('css', 'CSS'),
            ('sql', 'SQL'),
            ('bash', 'Bash'),
            ('json', 'JSON'),
            ('yaml', 'YAML'),
            ('cpp', 'C++'),
            ('java', 'Java'),
            ('go', 'Go'),
            ('rust', 'Rust'),
            ('php', 'PHP'),
            ('ruby', 'Ruby'),
        ],
        default='python'
    )
    code = blocks.TextBlock(help_text="Your code here...")
    caption = blocks.CharBlock(required=False, help_text="Optional caption or title")
    
    class Meta:
        template = 'forum_integration/blocks/code_block.html'
        icon = 'code'
        label = 'Code Block'


class ForumVideoBlock(blocks.StructBlock):
    """Video block for embedding videos in forum posts"""
    video_url = blocks.URLBlock(
        help_text="YouTube, Vimeo, or direct video URL. YouTube URLs will be auto-embedded."
    )
    title = blocks.CharBlock(required=False, help_text="Optional video title")
    description = blocks.RichTextBlock(required=False, help_text="Optional video description")
    
    class Meta:
        template = 'forum_integration/blocks/video_block.html'
        icon = 'media'
        label = 'Video'


class ForumQuoteBlock(blocks.StructBlock):
    """Quote block for highlighting quotes or citations"""
    text = blocks.TextBlock(help_text="The quote text")
    source = blocks.CharBlock(required=False, help_text="Source or attribution")
    
    class Meta:
        template = 'forum_integration/blocks/quote_block.html'
        icon = 'openquote'
        label = 'Quote'


class ForumCalloutBlock(blocks.StructBlock):
    """Callout/alert block for important information"""
    type = blocks.ChoiceBlock(
        choices=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('success', 'Success'),
            ('danger', 'Important/Danger'),
            ('tip', 'Tip'),
            ('note', 'Note'),
        ],
        default='info'
    )
    title = blocks.CharBlock(required=False, help_text="Optional title")
    text = blocks.RichTextBlock(help_text="Callout content")
    
    class Meta:
        template = 'forum_integration/blocks/callout_block.html'
        icon = 'warning'
        label = 'Callout/Alert'


class ForumEmbedBlock(blocks.StructBlock):
    """Block for embedding external content"""
    embed_code = blocks.RawHTMLBlock(
        help_text="Paste embed code from YouTube, CodePen, JSFiddle, etc."
    )
    caption = blocks.CharBlock(required=False, help_text="Optional caption")
    
    class Meta:
        template = 'forum_integration/blocks/embed_block.html'
        icon = 'site'
        label = 'Embed Code'


class ForumListBlock(blocks.StructBlock):
    """Numbered or bulleted list block"""
    list_type = blocks.ChoiceBlock(
        choices=[
            ('ul', 'Bulleted List'),
            ('ol', 'Numbered List'),
        ],
        default='ul'
    )
    items = blocks.ListBlock(blocks.CharBlock(label="List item"))
    
    class Meta:
        template = 'forum_integration/blocks/list_block.html'
        icon = 'list-ul'
        label = 'List'


# Define the StreamField blocks available for forum posts
FORUM_CONTENT_BLOCKS = [
    ('paragraph', blocks.RichTextBlock(
        features=['bold', 'italic', 'link', 'ol', 'ul', 'hr', 'code', 'superscript', 'subscript'],
        help_text="Rich text paragraph with basic formatting"
    )),
    ('heading', blocks.CharBlock(
        form_classname="title",
        help_text="Section heading"
    )),
    ('image', ImageChooserBlock(
        help_text="Upload or select an image"
    )),
    ('code', ForumCodeBlock()),
    ('video', ForumVideoBlock()),
    ('quote', ForumQuoteBlock()),
    ('callout', ForumCalloutBlock()),
    ('embed', ForumEmbedBlock()),
    ('list', ForumListBlock()),
]


class RichForumPost(models.Model):
    """
    Model to store rich content for forum posts using StreamField.
    This extends the basic machina Post model with rich content capabilities.
    """
    post = models.OneToOneField(
        Post, 
        on_delete=models.CASCADE, 
        related_name='rich_content'
    )
    content = StreamField(
        FORUM_CONTENT_BLOCKS,
        blank=True,
        use_json_field=True,
        help_text="Rich content for this forum post"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rich Forum Post"
        verbose_name_plural = "Rich Forum Posts"
    
    def __str__(self):
        return f"Rich content for post {self.post.id}"
    
    def render_content(self):
        """Render the StreamField content to HTML"""
        return str(self.content)
    
    @property
    def has_content(self):
        """Check if this post has any rich content"""
        return len(self.content) > 0
