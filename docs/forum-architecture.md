# Forum Architecture Documentation

## Overview

The Python Learning Studio forum system is built on top of **django-machina 1.3.1**, extended with custom functionality for educational communities. It provides a comprehensive discussion platform with trust levels, gamification, moderation tools, and real-time features.

## Core Components

### 1. Django-Machina Integration

The forum uses django-machina as its foundation, providing:
- **Forum hierarchy**: Categories → Forums → Topics → Posts
- **Permission system**: Fine-grained access control
- **Moderation tools**: Topic locking, pinning, moving
- **User tracking**: Read/unread topics, subscriptions
- **Search functionality**: Built on django-haystack with Whoosh backend

### 2. Trust Level System

Implemented in `apps/forum_integration/models.py:UserTrustLevel`

#### Trust Levels
- **TL0 (New User)**: Default level, posts enter review queue
- **TL1 (Basic)**: Can post without review, basic privileges
- **TL2 (Member)**: Extended privileges, can invite users
- **TL3 (Regular)**: Can recategorize, rename topics, access lounge
- **TL4 (Leader)**: Moderator privileges, can edit posts, close topics

#### Progression Criteria
```python
TRUST_LEVEL_REQUIREMENTS = {
    1: {'days_visited': 5, 'posts_read': 30, 'time_spent_minutes': 60},
    2: {'days_visited': 15, 'posts_read': 100, 'time_spent_minutes': 240, 'likes_received': 5},
    3: {'days_visited': 50, 'posts_read': 500, 'time_spent_minutes': 1440, 'likes_received': 20},
}
```

### 3. Gamification System

Located in `apps/forum_integration/gamification_service.py`

#### Features
- **Point System**: Actions earn points (create_post: 10, receive_like: 5, etc.)
- **Badge System**: 15+ badges for various achievements
- **Leaderboards**: Top contributors by points
- **Activity Tracking**: Comprehensive user engagement metrics

#### Key Badges
- First Post, First Like, Conversation Starter
- Popular (10+ likes), Very Popular (25+ likes), Famous (50+ likes)
- Helpful (5 solutions), Problem Solver (10 solutions), Expert (25 solutions)
- Regular (50 days visited), Devotee (100 days), Fanatic (365 days)

### 4. Review Queue System

Implemented in `apps/forum_integration/review_queue_service.py`

#### Features
- **Automatic Queuing**: TL0 user posts enter review automatically
- **Priority Scoring**: Based on user trust level, keywords, report count
- **Bulk Actions**: Approve/reject multiple items
- **Review History**: Track moderator actions
- **Auto-Approval**: Posts from TL1+ users bypass queue

### 5. Signal-Driven Architecture

Located in `apps/forum_integration/signals.py`

#### Key Signals
- `post_created`: Updates forum/topic trackers, triggers gamification
- `post_updated`: Recalculates statistics
- `topic_created`: Updates forum counters
- `post_approved`: Awards points, updates trust metrics

### 6. API Endpoints

#### Forum Management
- `GET /api/v1/forums/` - List all forums with stats
- `GET /api/v1/forums/{id}/` - Forum details
- `GET /api/v1/forums/{id}/topics/` - Forum topics (paginated)

#### Topic Operations
- `GET /api/v1/topics/` - List topics
- `POST /api/v1/topics/` - Create topic
- `GET /api/v1/topics/{id}/` - Topic details with posts
- `PUT /api/v1/topics/{id}/` - Update topic
- `DELETE /api/v1/topics/{id}/` - Delete topic

#### Post Management
- `GET /api/v1/posts/` - List posts
- `POST /api/v1/posts/` - Create post
- `PUT /api/v1/posts/{id}/` - Update post
- `DELETE /api/v1/posts/{id}/` - Delete post
- `POST /api/v1/posts/{id}/approve/` - Approve post (moderators)
- `POST /api/v1/posts/{id}/like/` - Like/unlike post

#### User Features
- `GET /api/v1/dashboard/forum-stats/` - User's forum statistics
- `GET /api/v1/users/{id}/badges/` - User's badges
- `GET /api/v1/leaderboard/` - Top contributors

## Database Schema

### Custom Models

#### UserTrustLevel
```python
class UserTrustLevel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    level = models.IntegerField(default=0)
    posts_read = models.IntegerField(default=0)
    time_spent_minutes = models.IntegerField(default=0)
    days_visited = models.IntegerField(default=0)
    likes_received = models.IntegerField(default=0)
    likes_given = models.IntegerField(default=0)
    topics_created = models.IntegerField(default=0)
    posts_created = models.IntegerField(default=0)
    last_calculated = models.DateTimeField(auto_now=True)
```

#### Badge
```python
class Badge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    threshold = models.IntegerField(null=True, blank=True)
```

#### UserBadge
```python
class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey('forum.Post', null=True, blank=True)
```

#### ReviewQueue
```python
class ReviewQueue(models.Model):
    post = models.ForeignKey('forum.Post', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True)
    status = models.CharField(max_length=20, choices=REVIEW_STATUSES)
    priority_score = models.IntegerField(default=0)
    rejection_reason = models.TextField(blank=True)
```

## Frontend Integration

### React Components (if implemented)
- `PostCreateForm.jsx` - Create new posts/topics
- `ForumList.jsx` - Display forum hierarchy
- `TopicList.jsx` - Show topics with pagination
- `PostThread.jsx` - Display posts in a topic
- `UserBadges.jsx` - Show user achievements
- `TrustLevelIndicator.jsx` - Display user trust level

### Templates (Django)
Located in `templates/machina/` with custom overrides:
- `board_base.html` - Base template integrating with site theme
- `forum/forum_detail.html` - Forum page with topics
- `forum_conversation/topic_detail.html` - Topic with posts
- `forum_member/user_detail.html` - User profile with badges

## Security Considerations

### Current Implementation
1. **Permission Checks**: Django-machina's permission system
2. **CSRF Protection**: Currently EXEMPTED (needs fixing)
3. **Rate Limiting**: Not implemented (recommended)
4. **Input Validation**: Basic Django form validation
5. **XSS Protection**: Django's template escaping

### Recommended Improvements
1. Remove CSRF exemptions from API endpoints
2. Implement rate limiting for post creation
3. Add content filtering for spam/inappropriate content
4. Implement IP-based restrictions for suspicious activity
5. Add honeypot fields to prevent bot submissions

## Performance Optimizations

### Current State
- Basic database indexes on foreign keys
- N+1 query issues in topic/post listings
- No caching implementation
- Real-time features may impact performance

### Recommended Optimizations
1. **Database Indexes**:
   ```python
   class Meta:
       indexes = [
           models.Index(fields=['status', 'priority_score']),
           models.Index(fields=['user', 'created_at']),
       ]
   ```

2. **Query Optimization**:
   ```python
   topics = Topic.objects.select_related('poster', 'forum')\
                         .prefetch_related('posts')\
                         .annotate(post_count=Count('posts'))
   ```

3. **Caching Strategy**:
   - Cache forum statistics (update on write)
   - Cache user trust levels (TTL: 1 hour)
   - Cache badge calculations

4. **Pagination**: Implement cursor-based pagination for large datasets

## Maintenance Commands

### Trust Level Management
```bash
python manage.py create_trust_levels          # Initialize trust levels
python manage.py calculate_trust_levels       # Update all user levels
python manage.py trust_level_stats           # Show statistics
```

### Forum Maintenance
```bash
python manage.py rebuild_forum_trackers      # Fix forum statistics
python manage.py rebuild_topic_trackers      # Fix topic metadata
python manage.py setup_forum_permissions     # Configure permissions
```

### Badge Management
```bash
python manage.py create_default_badges       # Create badge definitions
python manage.py award_badges               # Check and award badges
```

## Configuration

### Settings
```python
# learning_community/settings/base.py

MACHINA_FORUM_NAME = 'Python Learning Studio Forums'

MACHINA_DEFAULT_AUTHENTICATED_USER_FORUM_PERMISSIONS = [
    'can_see_forum',
    'can_read_forum',
    'can_start_new_topics',
    'can_reply_to_topics',
    'can_edit_own_posts',
    'can_post_without_approval',  # TL1+ only
]

# Trust level thresholds
TRUST_LEVEL_POST_THRESHOLD = 1  # Minimum TL to post without review
TRUST_LEVEL_MODERATE_THRESHOLD = 4  # Minimum TL to moderate

# Gamification settings
POINTS_FOR_POST = 10
POINTS_FOR_TOPIC = 15
POINTS_FOR_LIKE_RECEIVED = 5
POINTS_FOR_SOLUTION = 25
```

## Real-time Features (Planned)

### WebSocket Integration
- Live post updates in topics
- Real-time notifications
- Online user presence
- Typing indicators

### Implementation with Django Channels
```python
# consumers.py
class ForumConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.forum_id = self.scope['url_route']['kwargs']['forum_id']
        self.forum_group = f'forum_{self.forum_id}'
        
        await self.channel_layer.group_add(
            self.forum_group,
            self.channel_name
        )
```

## Testing

### Unit Tests
Located in `apps/forum_integration/tests/`:
- `test_models.py` - Model functionality
- `test_signals.py` - Signal handlers
- `test_services.py` - Service layer
- `test_api.py` - API endpoints

### Integration Tests
- Trust level progression
- Gamification triggers
- Review queue workflow
- Permission enforcement

### Performance Tests
- Load testing for concurrent users
- Database query optimization
- Caching effectiveness

## Monitoring and Analytics

### Metrics to Track
1. **User Engagement**:
   - Daily active users
   - Posts per day
   - Average session duration
   - Topic views

2. **Content Quality**:
   - Review queue approval rate
   - Reported posts
   - Solution rate
   - Like/post ratio

3. **System Performance**:
   - API response times
   - Database query performance
   - Cache hit rates
   - WebSocket connections

### Recommended Tools
- Django Debug Toolbar (development)
- Sentry (error tracking)
- Prometheus + Grafana (metrics)
- ELK Stack (logs)

## Future Enhancements

1. **AI-Powered Features**:
   - Auto-tagging topics
   - Content suggestions
   - Spam detection
   - Sentiment analysis

2. **Advanced Moderation**:
   - Automated content filtering
   - User reputation system
   - Shadow banning
   - IP blocking

3. **Enhanced Gamification**:
   - Streaks and challenges
   - Team competitions
   - Custom badges
   - Virtual rewards

4. **Mobile Optimization**:
   - Progressive Web App
   - Push notifications
   - Offline support
   - Native app integration