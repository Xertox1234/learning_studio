"""
ReviewQueueService with dependency injection and caching.

Refactored from apps/forum_integration/review_queue_service.py
to use repository pattern, dependency injection, and Redis caching.
"""

from __future__ import annotations
import re
from typing import TYPE_CHECKING, Optional, Dict, Any, List
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache as django_cache

if TYPE_CHECKING:
    from apps.api.repositories.review_queue_repository import ReviewQueueRepository
    from apps.api.repositories.post_repository import PostRepository
    from apps.api.repositories.topic_repository import TopicRepository
    from apps.api.repositories.user_repository import UserRepository
    from django.core.cache import BaseCache
    from machina.apps.forum_conversation.models import Post, Topic
    from django.contrib.auth import get_user_model
    User = get_user_model()


class ReviewQueueService:
    """
    Service for managing the review queue with automatic moderation triggers.

    Uses dependency injection for testability and Redis caching for performance.
    """

    # Cache configuration
    CACHE_VERSION = 'v1'
    SPAM_PATTERN_VERSION = '1'  # Increment when spam patterns change
    CACHE_TIMEOUT_SHORT = 300  # 5 minutes - spam scores (content can be edited)
    CACHE_TIMEOUT_MEDIUM = 900  # 15 minutes - duplicate checks

    # Spam detection patterns (could be moved to Django settings)
    SPAM_PATTERNS = [
        r'(?i)\b(buy|sell|cheap|discount|offer|deal)\s+(viagra|cialis|pills|medication)',
        r'(?i)\b(casino|poker|gambling|lottery|winner|prize)\b',
        r'(?i)\b(make\s+money|earn\s+\$|guaranteed\s+income|work\s+from\s+home)',
        r'(?i)\b(click\s+here|visit\s+now|limited\s+time|act\s+now)',
        r'(?i)\b(free\s+download|no\s+cost|absolutely\s+free)',
        r'(?i)\b(weight\s+loss|lose\s+weight|diet\s+pills)',
    ]

    # Suspicious link patterns
    SUSPICIOUS_LINK_PATTERNS = [
        r'bit\.ly|tinyurl|short\.link|t\.co',  # URL shorteners
        r'\.tk|\.ml|\.ga|\.cf',  # Free domains
        r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+',  # IP addresses
    ]

    def __init__(
        self,
        review_queue_repo: ReviewQueueRepository,
        post_repo: PostRepository,
        topic_repo: TopicRepository,
        user_repo: UserRepository,
        cache: BaseCache
    ):
        """
        Initialize with injected dependencies.

        Args:
            review_queue_repo: ReviewQueue repository
            post_repo: Post repository
            topic_repo: Topic repository
            user_repo: User repository
            cache: Cache backend
        """
        self.review_queue_repo = review_queue_repo
        self.post_repo = post_repo
        self.topic_repo = topic_repo
        self.user_repo = user_repo
        self.cache = cache

    # ========================================
    # Content Checking Methods
    # ========================================

    def check_new_post(self, post: Post) -> None:
        """
        Check if a new post should be added to the review queue.

        Args:
            post: Post instance to check
        """
        user = post.poster
        if not user:
            return

        # Get user's trust level
        trust_level = self._get_user_trust_level(user.id)

        # Check if post needs review based on trust level
        if trust_level == 0:  # TL0 users - all posts reviewed
            self.add_to_queue(
                post=post,
                review_type='new_user_post',
                reason=f'Post by new user (TL{trust_level}) requires review',
                priority=3,
                reporter=None
            )

        # Check for spam indicators
        spam_score = self.calculate_spam_score(post)
        if spam_score > 0.7:  # High spam probability
            self.add_to_queue(
                post=post,
                review_type='spam_detection',
                reason=f'Automatic spam detection (score: {spam_score:.2f})',
                priority=2,
                reporter=None
            )
        elif spam_score > 0.4:  # Medium spam probability
            self.add_to_queue(
                post=post,
                review_type='spam_detection',
                reason=f'Possible spam content (score: {spam_score:.2f})',
                priority=3,
                reporter=None
            )

        # Check for duplicate content
        if self.is_duplicate_content(post):
            self.add_to_queue(
                post=post,
                review_type='edited_post',
                reason='Potential duplicate content detected',
                priority=4,
                reporter=None
            )

    def check_edited_post(self, post: Post, user: User) -> None:
        """
        Check if an edited post should be reviewed.

        Args:
            post: Post instance that was edited
            user: User who edited the post
        """
        trust_level = self._get_user_trust_level(user.id)

        # Low trust users' edits need review
        if trust_level <= 1:
            self.add_to_queue(
                post=post,
                review_type='edited_post',
                reason=f'Post edited by TL{trust_level} user',
                priority=4,
                reporter=None
            )

        # Check if edit introduces spam patterns
        spam_score = self.calculate_spam_score(post)
        if spam_score > 0.5:
            self.add_to_queue(
                post=post,
                review_type='spam_detection',
                reason=f'Spam patterns detected in edit (score: {spam_score:.2f})',
                priority=2,
                reporter=None
            )

        # Invalidate spam score cache after edit
        self.invalidate_cache(post_id=post.id)

    def check_new_topic(self, topic: Topic) -> None:
        """
        Check if a new topic should be reviewed.

        Args:
            topic: Topic instance to check
        """
        user = topic.poster
        if not user:
            return

        trust_level = self._get_user_trust_level(user.id)

        # New users' topics are always reviewed
        if trust_level == 0:
            self.add_to_queue(
                topic=topic,
                review_type='new_user_post',
                reason=f'Topic by new user (TL{trust_level}) requires review',
                priority=3,
                reporter=None
            )

        # Check topic title for spam
        title_spam_score = self.calculate_text_spam_score(topic.subject)
        if title_spam_score > 0.6:
            self.add_to_queue(
                topic=topic,
                review_type='spam_detection',
                reason=f'Spam detected in topic title (score: {title_spam_score:.2f})',
                priority=2,
                reporter=None
            )

    def check_user_behavior(self, user_id: int) -> None:
        """
        Check if a user's behavior pattern warrants review.

        Args:
            user_id: User ID to check
        """
        trust_level = self._get_user_trust_level(user_id)

        # Check for suspicious posting patterns
        day_ago = timezone.now() - timedelta(hours=24)
        recent_posts = self.post_repo.count(
            poster_id=user_id,
            created__gte=day_ago
        )

        # Too many posts in short time (potential spam)
        if recent_posts > 20 and trust_level <= 1:
            self.add_to_queue(
                reported_user_id=user_id,
                review_type='trust_level_review',
                reason=f'User posted {recent_posts} times in 24 hours',
                priority=3,
                reporter=None
            )

        # Check for multiple flags
        active_flags = self.review_queue_repo.count(
            reported_user_id=user_id,
            status='pending'
        )

        if active_flags >= 3:
            self.add_to_queue(
                reported_user_id=user_id,
                review_type='user_report',
                reason=f'User has {active_flags} pending moderation reviews',
                priority=2,
                reporter=None
            )

    # ========================================
    # Queue Management Methods
    # ========================================

    def add_to_queue(
        self,
        review_type: str,
        reason: str,
        priority: int = 3,
        reporter: Optional[User] = None,
        post: Optional[Post] = None,
        topic: Optional[Topic] = None,
        reported_user: Optional[User] = None,
        reported_user_id: Optional[int] = None
    ) -> Any:
        """
        Add an item to the review queue.

        Args:
            review_type: Type of review needed
            reason: Reason for review
            priority: Priority level (1=highest, 5=lowest)
            reporter: User who reported (if user-reported)
            post: Post to review (optional)
            topic: Topic to review (optional)
            reported_user: User being reported (optional)
            reported_user_id: User ID being reported (optional)

        Returns:
            ReviewQueue instance
        """
        from apps.forum_integration.models import ReviewQueue

        # Extract IDs
        post_id = post.id if post else None
        topic_id = topic.id if topic else None
        reporter_id = reporter.id if reporter else None
        if reported_user:
            reported_user_id = reported_user.id

        # Check if similar item already exists (use repository)
        filters = {
            'review_type': review_type,
            'status': 'pending'
        }
        if post_id:
            filters['post_id'] = post_id
        if topic_id:
            filters['topic_id'] = topic_id
        if reported_user_id:
            filters['reported_user_id'] = reported_user_id

        existing_items = self.review_queue_repo.filter(**filters)
        if existing_items:
            existing = existing_items[0]
            # Update existing item's priority if this is more urgent
            if priority < existing.priority:
                self.review_queue_repo.update(existing.id, priority=priority)
            return existing

        # Create new review item using ORM (repository doesn't have create method)
        review_item = ReviewQueue.objects.create(
            review_type=review_type,
            post=post,
            topic=topic,
            reported_user_id=reported_user_id,
            reporter_id=reporter_id,
            reason=reason,
            priority=priority
        )

        return review_item

    def review_item(
        self,
        item_id: int,
        reviewer: User,
        action: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Review and approve/reject an item.

        Also invalidates cached spam scores and duplicate checks for reviewed content.

        Args:
            item_id: ReviewQueue item ID
            reviewer: User performing the review
            action: 'approve' or 'reject'
            notes: Optional moderator notes

        Returns:
            True if successful
        """
        # Get the item to find what to invalidate
        item = self.review_queue_repo.get_by_id(item_id)
        if not item:
            return False

        success = False
        if action == 'approve':
            success = self.review_queue_repo.approve_item(
                item_id=item_id,
                moderator_id=reviewer.id,
                reason=notes
            )
        elif action == 'reject':
            success = self.review_queue_repo.reject_item(
                item_id=item_id,
                moderator_id=reviewer.id,
                reason=notes
            )

        # Invalidate cache for reviewed content
        if success:
            if item.post:
                self.invalidate_cache(post_id=item.post.id)
            if item.topic:
                self.invalidate_cache(topic_id=item.topic.id)

        return success

    def get_pending_queue(
        self,
        review_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get pending review items with pagination.

        Args:
            review_type: Optional filter by review type
            page: Page number
            page_size: Items per page

        Returns:
            Dict with results and pagination info
        """
        return self.review_queue_repo.get_pending_queue(
            review_type=review_type,
            page=page,
            page_size=page_size
        )

    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get moderation queue statistics.

        Returns:
            Dict with queue statistics
        """
        return self.review_queue_repo.get_queue_stats()

    # ========================================
    # Spam Detection Methods (with caching)
    # ========================================

    def calculate_spam_score(self, post: Post) -> float:
        """
        Calculate spam probability score for a post.
        Uses caching to avoid recalculating for same post.

        Cache key includes spam pattern version to ensure cache is invalidated
        when detection rules are updated.

        Args:
            post: Post instance

        Returns:
            Float between 0 and 1 (1 = definitely spam)
        """
        # Include pattern version in cache key to auto-invalidate when patterns change
        cache_key = f'{self.CACHE_VERSION}:spam:v{self.SPAM_PATTERN_VERSION}:post:{post.id}'

        # Try cache first
        cached_score = self.cache.get(cache_key)
        if cached_score is not None:
            return cached_score

        # Calculate score
        content = str(post.content) if post.content else ""
        score = self._calculate_content_spam_score(content)

        # Cache result (5 minutes - content could be edited)
        self.cache.set(cache_key, score, timeout=self.CACHE_TIMEOUT_SHORT)

        return score

    def calculate_text_spam_score(self, text: str) -> float:
        """
        Calculate spam score for plain text (like topic titles).

        Args:
            text: Text to analyze

        Returns:
            Float between 0 and 1 (1 = definitely spam)
        """
        if not text:
            return 0.0

        score = 0.0

        # Check against spam patterns
        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, text):
                score += 0.4

        # Check for excessive capitalization
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
        if caps_ratio > 0.7:
            score += 0.3

        # Check for excessive punctuation
        punct_ratio = sum(1 for c in text if c in '!?') / len(text)
        if punct_ratio > 0.2:
            score += 0.3

        return min(score, 1.0)

    def _calculate_content_spam_score(self, content: str) -> float:
        """
        Internal method to calculate spam score for post content.

        Args:
            content: Post content text

        Returns:
            Float between 0 and 1
        """
        score = 0.0

        # Check against spam patterns
        pattern_matches = 0
        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, content):
                pattern_matches += 1

        if pattern_matches > 0:
            score += min(0.3 + (pattern_matches * 0.2), 0.8)

        # Check for suspicious links
        link_matches = 0
        for pattern in self.SUSPICIOUS_LINK_PATTERNS:
            if re.search(pattern, content):
                link_matches += 1

        if link_matches > 0:
            score += min(0.2 + (link_matches * 0.15), 0.5)

        # Check for excessive capitalization
        if content:
            caps_ratio = sum(1 for c in content if c.isupper()) / len(content)
            if caps_ratio > 0.5 and len(content) > 20:
                score += 0.3

        # Check for excessive punctuation
        if content:
            punct_ratio = sum(1 for c in content if c in '!?') / max(len(content), 1)
            if punct_ratio > 0.1:
                score += 0.2

        # Check for very short posts with links
        if content and len(content.strip()) < 50 and re.search(r'http', content):
            score += 0.4

        return min(score, 1.0)

    # ========================================
    # Duplicate Detection (optimized)
    # ========================================

    def is_duplicate_content(self, post: Post) -> bool:
        """
        Check if post content is similar to existing posts.
        Optimized to avoid N+1 queries by limiting posts checked.

        Args:
            post: Post instance to check

        Returns:
            True if duplicate detected
        """
        if not post.content:
            return False

        content = str(post.content).strip()
        if len(content) < 50:  # Too short to be meaningful duplicate
            return False

        # Check cache first
        cache_key = f'{self.CACHE_VERSION}:duplicate:post:{post.id}'
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Optimize: Only check recent posts by same user or in same topic/forum
        # This prevents loading thousands of posts on active forums
        week_ago = timezone.now() - timedelta(days=7)

        # Build efficient query: same user OR same topic, limited to 100 recent posts
        from machina.apps.forum_conversation.models import Post as PostModel
        from django.db.models import Q

        query = Q(poster_id=post.poster_id) | Q(topic_id=post.topic_id)
        recent_posts = PostModel.objects.filter(
            query,
            created__gte=week_ago
        ).exclude(
            id=post.id
        ).order_by('-created')[:100]  # Hard limit to prevent unbounded queries

        is_duplicate = False
        for recent_post in recent_posts:
            if not recent_post.content:
                continue

            recent_content = str(recent_post.content).strip()

            # Simple similarity check (exact match)
            if content == recent_content:
                is_duplicate = True
                break

            # Check for near-duplicates (90% similarity)
            if self.calculate_similarity(content, recent_content) > 0.9:
                is_duplicate = True
                break

        # Cache result (15 minutes)
        self.cache.set(cache_key, is_duplicate, timeout=self.CACHE_TIMEOUT_MEDIUM)

        return is_duplicate

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0

        # Simple word-based similarity (Jaccard index)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    # ========================================
    # Utility Methods
    # ========================================

    def _get_user_trust_level(self, user_id: int) -> int:
        """
        Get user's trust level.

        Args:
            user_id: User ID

        Returns:
            Trust level (0-4)
        """
        try:
            from apps.forum_integration.models import TrustLevel
            trust_level_obj = TrustLevel.objects.filter(user_id=user_id).first()
            return trust_level_obj.level if trust_level_obj else 0
        except (AttributeError, ValueError, ImportError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Trust level lookup failed for user {user_id}: {e}")
            return 0

    def cleanup_old_items(self, days: int = 30) -> int:
        """
        Clean up old resolved review queue items.

        Args:
            days: Age threshold in days

        Returns:
            Number of items deleted
        """
        return self.review_queue_repo.cleanup_old_items(days=days)

    def recalculate_priorities(self) -> None:
        """
        Recalculate priority scores for all pending items.
        """
        from apps.forum_integration.models import ReviewQueue, ModerationLog

        pending_items = ReviewQueue.objects.filter(status='pending')

        for item in pending_items:
            old_score = item.score
            item.save()  # This triggers score recalculation in model

            if abs(item.score - old_score) > 10:  # Significant change
                ModerationLog.objects.create(
                    action_type='escalate' if item.score > old_score else 'de_escalate',
                    moderator=None,  # System action
                    review_item=item,
                    reason=f'Priority score updated: {old_score:.1f} → {item.score:.1f}',
                    details={'old_score': old_score, 'new_score': item.score}
                )

    # ========================================
    # Cache Invalidation
    # ========================================

    def invalidate_cache(
        self,
        post_id: Optional[int] = None,
        topic_id: Optional[int] = None
    ) -> None:
        """
        Invalidate cached spam scores and duplicate checks.

        Args:
            post_id: Post ID to invalidate
            topic_id: Topic ID to invalidate
        """
        if post_id:
            # Include spam pattern version in key
            spam_key = f'{self.CACHE_VERSION}:spam:v{self.SPAM_PATTERN_VERSION}:post:{post_id}'
            dup_key = f'{self.CACHE_VERSION}:duplicate:post:{post_id}'
            self.cache.delete(spam_key)
            self.cache.delete(dup_key)

        if topic_id:
            topic_key = f'{self.CACHE_VERSION}:spam:v{self.SPAM_PATTERN_VERSION}:topic:{topic_id}'
            self.cache.delete(topic_key)
