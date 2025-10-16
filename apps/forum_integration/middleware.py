"""
Middleware for tracking user activity and trust level progression
"""
from datetime import timedelta
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from .models import TrustLevel, UserActivity

User = get_user_model()


class TrustLevelTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track user activity for trust level calculations.
    This middleware runs on every request to track daily visits and activity.
    """
    
    def process_request(self, request):
        """Track user activity on each request"""
        # Only track activity for forum-related pages to avoid database writes on every request
        # This prevents unnecessary writes for admin, API, static files, etc.
        if not self._should_track_activity(request):
            return None

        if request.user.is_authenticated:
            self.track_daily_visit(request.user)
        return None

    def _should_track_activity(self, request):
        """
        Determine if we should track activity for this request.
        Only track for actual forum page views, not API calls or static files.
        """
        path = request.path

        # Skip API endpoints (they don't represent user engagement in the same way)
        if path.startswith('/api/'):
            return False

        # Skip admin pages
        if path.startswith('/admin/') or path.startswith('/django-admin/'):
            return False

        # Skip static and media files
        if path.startswith('/static/') or path.startswith('/media/'):
            return False

        # Skip authentication pages
        if path.startswith('/accounts/') or path in ['/login/', '/logout/', '/register/']:
            return False

        # Track everything else (forum pages, dashboard, etc.)
        return True
    
    def track_daily_visit(self, user):
        """
        Track that a user has visited today and update their activity metrics
        """
        today = timezone.now().date()
        
        # Get or create trust level for user
        trust_level, created = TrustLevel.objects.get_or_create(
            user=user,
            defaults={
                'level': 0,
                'last_visit_date': today
            }
        )
        
        # Get or create daily activity record
        activity, activity_created = UserActivity.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'first_visit_time': timezone.now(),
                'last_activity_time': timezone.now()
            }
        )
        
        # Update activity timestamp
        activity.last_activity_time = timezone.now()
        activity.save(update_fields=['last_activity_time'])
        
        # If this is a new day for the user, increment days_visited
        if trust_level.last_visit_date != today:
            trust_level.days_visited += 1
            trust_level.last_visit_date = today
            trust_level.save(update_fields=['days_visited', 'last_visit_date'])
            
            # Check for promotion opportunity (but don't auto-promote)
            # This will be handled by a background task or management command
            if trust_level.check_for_promotion():
                # Log promotion opportunity or trigger background task
                pass


class ForumActivityTracker:
    """
    Helper class to track specific forum activities.
    This should be called from forum views and signals.
    """
    
    @staticmethod
    def track_post_read(user, post):
        """Track when a user reads a post"""
        if not user.is_authenticated:
            return
            
        today = timezone.now().date()
        
        # Update trust level metrics
        trust_level, _ = TrustLevel.objects.get_or_create(
            user=user,
            defaults={'level': 0}
        )
        trust_level.posts_read += 1
        trust_level.save(update_fields=['posts_read'])
        
        # Update daily activity
        activity, _ = UserActivity.objects.get_or_create(
            user=user,
            date=today,
            defaults={}
        )
        activity.posts_read_today += 1
        activity.save(update_fields=['posts_read_today'])
    
    @staticmethod
    def track_topic_viewed(user, topic):
        """Track when a user views a topic"""
        if not user.is_authenticated:
            return
            
        today = timezone.now().date()
        
        # Update trust level metrics
        trust_level, _ = TrustLevel.objects.get_or_create(
            user=user,
            defaults={'level': 0}
        )
        trust_level.topics_viewed += 1
        trust_level.save(update_fields=['topics_viewed'])
        
        # Update daily activity
        activity, _ = UserActivity.objects.get_or_create(
            user=user,
            date=today,
            defaults={}
        )
        activity.topics_viewed_today += 1
        activity.save(update_fields=['topics_viewed_today'])
    
    @staticmethod
    def track_post_created(user, post):
        """Track when a user creates a post"""
        if not user.is_authenticated:
            return
            
        today = timezone.now().date()
        
        # Update trust level metrics
        trust_level, _ = TrustLevel.objects.get_or_create(
            user=user,
            defaults={'level': 0}
        )
        trust_level.posts_created += 1
        trust_level.save(update_fields=['posts_created'])
        
        # Update daily activity
        activity, _ = UserActivity.objects.get_or_create(
            user=user,
            date=today,
            defaults={}
        )
        activity.posts_created_today += 1
        activity.save(update_fields=['posts_created_today'])
    
    @staticmethod
    def track_topic_created(user, topic):
        """Track when a user creates a topic"""
        if not user.is_authenticated:
            return
            
        trust_level, _ = TrustLevel.objects.get_or_create(
            user=user,
            defaults={'level': 0}
        )
        trust_level.topics_created += 1
        trust_level.save(update_fields=['topics_created'])
    
    @staticmethod
    def track_like_given(user, target_post):
        """Track when a user gives a like"""
        if not user.is_authenticated:
            return
            
        today = timezone.now().date()
        
        # Update trust level metrics for like giver
        trust_level, _ = TrustLevel.objects.get_or_create(
            user=user,
            defaults={'level': 0}
        )
        trust_level.likes_given += 1
        trust_level.save(update_fields=['likes_given'])
        
        # Update daily activity for like giver
        activity, _ = UserActivity.objects.get_or_create(
            user=user,
            date=today,
            defaults={}
        )
        activity.likes_given_today += 1
        activity.save(update_fields=['likes_given_today'])
        
        # Update trust level metrics for like receiver
        if target_post.poster:
            receiver_trust_level, _ = TrustLevel.objects.get_or_create(
                user=target_post.poster,
                defaults={'level': 0}
            )
            receiver_trust_level.likes_received += 1
            receiver_trust_level.save(update_fields=['likes_received'])
    
    @staticmethod
    def track_reading_time(user, topic, time_spent, scroll_depth=None):
        """Track time spent reading a topic"""
        if not user.is_authenticated:
            return
            
        from .models import ReadingProgress
        
        # Update reading progress for the topic
        progress, created = ReadingProgress.objects.get_or_create(
            user=user,
            topic=topic,
            defaults={'time_spent': timedelta()}
        )
        
        progress.time_spent += time_spent
        if scroll_depth is not None:
            progress.scroll_depth = max(progress.scroll_depth, scroll_depth)
            if scroll_depth >= 0.95:  # Consider 95% as completed
                progress.completed = True
        
        progress.save()
        
        # Update trust level total reading time
        trust_level, _ = TrustLevel.objects.get_or_create(
            user=user,
            defaults={'level': 0}
        )
        trust_level.time_read += time_spent
        trust_level.save(update_fields=['time_read'])
        
        # Update daily activity
        today = timezone.now().date()
        activity, _ = UserActivity.objects.get_or_create(
            user=user,
            date=today,
            defaults={}
        )
        activity.time_spent_reading += time_spent
        activity.save(update_fields=['time_spent_reading'])