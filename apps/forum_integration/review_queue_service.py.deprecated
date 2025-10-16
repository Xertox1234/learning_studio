"""
Service functions for automatically populating and managing the review queue.
"""

import re
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ReviewQueue, TrustLevel, ModerationLog
from machina.apps.forum_conversation.models import Post, Topic

User = get_user_model()


class ReviewQueueService:
    """
    Service class for managing the review queue and automatic moderation triggers.
    """
    
    # Spam detection patterns
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
    
    @classmethod
    def check_new_post(cls, post):
        """
        Check if a new post should be added to the review queue.
        """
        user = post.poster
        if not user:
            return
        
        # Get user's trust level
        try:
            trust_level = user.trust_level.level
        except TrustLevel.DoesNotExist:
            trust_level = 0
        
        # Check if post needs review based on trust level
        if trust_level == 0:  # TL0 users - all posts reviewed
            cls.add_to_queue(
                post=post,
                review_type='new_user_post',
                reason=f'Post by new user (TL{trust_level}) requires review',
                priority=3,
                reporter=None
            )
        
        # Check for spam indicators
        spam_score = cls.calculate_spam_score(post)
        if spam_score > 0.7:  # High spam probability
            cls.add_to_queue(
                post=post,
                review_type='spam_detection',
                reason=f'Automatic spam detection (score: {spam_score:.2f})',
                priority=2,
                reporter=None
            )
        elif spam_score > 0.4:  # Medium spam probability
            cls.add_to_queue(
                post=post,
                review_type='spam_detection',
                reason=f'Possible spam content (score: {spam_score:.2f})',
                priority=3,
                reporter=None
            )
        
        # Check for duplicate content
        if cls.is_duplicate_content(post):
            cls.add_to_queue(
                post=post,
                review_type='edited_post',
                reason='Potential duplicate content detected',
                priority=4,
                reporter=None
            )
    
    @classmethod
    def check_edited_post(cls, post, user):
        """
        Check if an edited post should be reviewed.
        """
        try:
            trust_level = user.trust_level.level
        except TrustLevel.DoesNotExist:
            trust_level = 0
        
        # Low trust users' edits need review
        if trust_level <= 1:
            cls.add_to_queue(
                post=post,
                review_type='edited_post',
                reason=f'Post edited by TL{trust_level} user',
                priority=4,
                reporter=None
            )
        
        # Check if edit introduces spam patterns
        spam_score = cls.calculate_spam_score(post)
        if spam_score > 0.5:
            cls.add_to_queue(
                post=post,
                review_type='spam_detection',
                reason=f'Spam patterns detected in edit (score: {spam_score:.2f})',
                priority=2,
                reporter=None
            )
    
    @classmethod
    def check_new_topic(cls, topic):
        """
        Check if a new topic should be reviewed.
        """
        user = topic.poster
        if not user:
            return
        
        try:
            trust_level = user.trust_level.level
        except TrustLevel.DoesNotExist:
            trust_level = 0
        
        # New users' topics are always reviewed
        if trust_level == 0:
            cls.add_to_queue(
                topic=topic,
                review_type='new_user_post',
                reason=f'Topic by new user (TL{trust_level}) requires review',
                priority=3,
                reporter=None
            )
        
        # Check topic title for spam
        title_spam_score = cls.calculate_text_spam_score(topic.subject)
        if title_spam_score > 0.6:
            cls.add_to_queue(
                topic=topic,
                review_type='spam_detection',
                reason=f'Spam detected in topic title (score: {title_spam_score:.2f})',
                priority=2,
                reporter=None
            )
    
    @classmethod
    def check_user_behavior(cls, user):
        """
        Check if a user's behavior pattern warrants review.
        """
        try:
            trust_level = user.trust_level.level
        except TrustLevel.DoesNotExist:
            trust_level = 0
        
        # Check for suspicious posting patterns
        recent_posts = Post.objects.filter(
            poster=user,
            created__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()
        
        # Too many posts in short time (potential spam)
        if recent_posts > 20 and trust_level <= 1:
            cls.add_to_queue(
                reported_user=user,
                review_type='trust_level_review',
                reason=f'User posted {recent_posts} times in 24 hours',
                priority=3,
                reporter=None
            )
        
        # Check for multiple flags
        active_flags = ReviewQueue.objects.filter(
            reported_user=user,
            status='pending'
        ).count()
        
        if active_flags >= 3:
            cls.add_to_queue(
                reported_user=user,
                review_type='user_report',
                reason=f'User has {active_flags} pending moderation reviews',
                priority=2,
                reporter=None
            )
    
    @classmethod
    def add_to_queue(cls, review_type, reason, priority=3, reporter=None, 
                     post=None, topic=None, reported_user=None):
        """
        Add an item to the review queue.
        """
        # Check if similar item already exists
        existing = ReviewQueue.objects.filter(
            review_type=review_type,
            post=post,
            topic=topic,
            reported_user=reported_user,
            status='pending'
        ).first()
        
        if existing:
            # Update existing item's priority if this is more urgent
            if priority < existing.priority:
                existing.priority = priority
                existing.save()
            return existing
        
        # Create new review item
        review_item = ReviewQueue.objects.create(
            review_type=review_type,
            post=post,
            topic=topic,
            reported_user=reported_user,
            reporter=reporter,
            reason=reason,
            priority=priority
        )
        
        return review_item
    
    @classmethod
    def calculate_spam_score(cls, post):
        """
        Calculate spam probability score for a post.
        Returns float between 0 and 1 (1 = definitely spam).
        """
        content = str(post.content) if post.content else ""
        score = 0.0
        
        # Check against spam patterns
        pattern_matches = 0
        for pattern in cls.SPAM_PATTERNS:
            if re.search(pattern, content):
                pattern_matches += 1
        
        if pattern_matches > 0:
            score += min(0.3 + (pattern_matches * 0.2), 0.8)
        
        # Check for suspicious links
        link_matches = 0
        for pattern in cls.SUSPICIOUS_LINK_PATTERNS:
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
    
    @classmethod
    def calculate_text_spam_score(cls, text):
        """
        Calculate spam score for plain text (like topic titles).
        """
        if not text:
            return 0.0
        
        score = 0.0
        
        # Check against spam patterns
        for pattern in cls.SPAM_PATTERNS:
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
    
    @classmethod
    def is_duplicate_content(cls, post):
        """
        Check if post content is similar to existing posts.
        """
        if not post.content:
            return False
        
        content = str(post.content).strip()
        if len(content) < 50:  # Too short to be meaningful duplicate
            return False
        
        # Check for exact duplicates in recent posts
        recent_posts = Post.objects.filter(
            created__gte=timezone.now() - timezone.timedelta(days=7)
        ).exclude(id=post.id)
        
        for recent_post in recent_posts:
            if not recent_post.content:
                continue
            
            recent_content = str(recent_post.content).strip()
            
            # Simple similarity check (exact match)
            if content == recent_content:
                return True
            
            # Check for near-duplicates (90% similarity)
            if cls.calculate_similarity(content, recent_content) > 0.9:
                return True
        
        return False
    
    @classmethod
    def calculate_similarity(cls, text1, text2):
        """
        Calculate simple similarity between two texts.
        """
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    @classmethod
    def cleanup_old_items(cls, days=30):
        """
        Clean up old resolved review queue items.
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        old_items = ReviewQueue.objects.filter(
            status__in=['approved', 'rejected'],
            resolved_at__lt=cutoff_date
        )
        
        count = old_items.count()
        old_items.delete()
        
        return count
    
    @classmethod
    def recalculate_priorities(cls):
        """
        Recalculate priority scores for all pending items.
        """
        pending_items = ReviewQueue.objects.filter(status='pending')
        
        for item in pending_items:
            old_score = item.score
            item.save()  # This triggers score recalculation
            
            if abs(item.score - old_score) > 10:  # Significant change
                ModerationLog.objects.create(
                    action_type='escalate' if item.score > old_score else 'de_escalate',
                    moderator=None,  # System action
                    review_item=item,
                    reason=f'Priority score updated: {old_score:.1f} → {item.score:.1f}',
                    details={'old_score': old_score, 'new_score': item.score}
                )