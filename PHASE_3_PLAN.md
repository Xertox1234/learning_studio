# Phase 3: Service Layer Refactoring - Implementation Plan

**Created:** 2025-10-15
**Status:** 📋 Planning
**Estimated Duration:** 8-12 hours
**Complexity:** High

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Current Architecture Analysis](#current-architecture-analysis)
3. [Problems Identified](#problems-identified)
4. [Proposed Architecture](#proposed-architecture)
5. [Implementation Plan](#implementation-plan)
6. [Risk Assessment](#risk-assessment)
7. [Success Metrics](#success-metrics)

---

## Executive Summary

**Objective:** Refactor Django service layer to implement:
- Dependency injection pattern
- Redis caching layer
- Query optimization (solve N+1 problems)
- Clear separation of concerns
- Testable, maintainable architecture

**Current State:** Services exist but inconsistent patterns, no DI, limited caching, potential N+1 queries

**Target State:** Professional-grade service layer with:
- Unified dependency injection container
- Redis caching for hot paths
- Optimized database queries (select_related, prefetch_related)
- Comprehensive service layer tests
- 50%+ performance improvement on key endpoints

---

## Current Architecture Analysis

### Existing Services

#### 1. **ForumStatisticsService** (apps/forum_integration/statistics_service.py)
**Lines:** 126
**Pattern:** Class-based with @classmethod decorators
**Caching:** Django cache (1-5 min timeout)
**Dependencies:** Hardcoded Django models

**Current Issues:**
- ❌ No dependency injection - direct model imports
- ⚠️ Limited caching strategy (only static data cached)
- ⚠️ Potential N+1 queries in `get_forum_specific_stats()`
- ❌ No unit tests possible (tightly coupled to ORM)

**Good Practices:**
- ✅ Centralized statistics logic
- ✅ Clear cache key naming
- ✅ Appropriate cache timeouts

#### 2. **ReviewQueueService** (apps/forum_integration/review_queue_service.py)
**Lines:** 392
**Pattern:** Class-based with @classmethod decorators
**Caching:** None
**Dependencies:** Hardcoded Django models

**Current Issues:**
- ❌ No dependency injection
- ❌ No caching (spam score calculated every time)
- ⚠️ Potential N+1 query in `is_duplicate_content()` (line 321)
- ❌ Regex patterns hardcoded (should be configurable)
- ❌ Difficult to test (tightly coupled)

**Good Practices:**
- ✅ Comprehensive spam detection logic
- ✅ Configurable priority system
- ✅ Good documentation

#### 3. **CodeExecutionService** (apps/api/services/code_execution_service.py)
**Status:** Already refactored (Phase 1)
**Pattern:** Instance-based with dependency injection
**Caching:** None (not needed - execution is stateful)

**Good Practices:**
- ✅ Dependency injection implemented
- ✅ Testable architecture
- ✅ Docker fallback pattern

#### 4. **ForumContentService** (apps/api/services/forum_content_service.py)
**Status:** New service (needs review)

---

### Database Query Analysis

**Potential N+1 Problems Identified:**

#### Location 1: ForumStatisticsService.get_forum_specific_stats()
**File:** apps/forum_integration/statistics_service.py:62-97

**Issue:**
```python
# Line 69-73: Queries all posts for the week (OK)
weekly_posts = Post.objects.filter(
    topic__forum=forum,
    approved=True,
    created__gte=week_ago
).count()

# Line 76-81: Potential N+1 on user->post relationship
forum_online_users = User.objects.filter(
    is_active=True,
    post__topic__forum=forum,  # JOIN through post table
    post__created__gte=online_threshold
).distinct().count()
```

**Fix Required:** Add select_related/prefetch_related

#### Location 2: ReviewQueueService.is_duplicate_content()
**File:** apps/forum_integration/review_queue_service.py:305-335

**Issue:**
```python
# Line 317-320: Fetches all recent posts
recent_posts = Post.objects.filter(
    created__gte=timezone.now() - timezone.timedelta(days=7)
).exclude(id=post.id)

# Line 321-333: Iterates and accesses post.content (potential N+1)
for recent_post in recent_posts:
    if not recent_post.content:  # Accessing content field
        continue
```

**Fix Required:** Add `.only('content', 'id')` or `.values_list()`

#### Location 3: API Views (need analysis)
**Files:** apps/api/views/*.py

**Requires:** Full query analysis with Django Debug Toolbar

---

### Caching Strategy Analysis

**Current Caching:**

| Service | Cache Backend | Keys | Timeout | Coverage |
|---------|---------------|------|---------|----------|
| ForumStatisticsService | Django Cache | `forum:static_stats`, `forum:user_stats:{id}` | 1-5 min | ~30% |
| ReviewQueueService | None | N/A | N/A | 0% |
| Other Services | None | N/A | N/A | 0% |

**Issues:**
- ❌ No Redis integration (using default Django cache)
- ❌ No cache warming strategies
- ❌ No distributed caching (multi-server issues)
- ❌ Cache keys not prefixed properly for multi-environment
- ❌ No cache versioning (invalidation on code changes)

---

## Problems Identified

### 1. **Tight Coupling** (Priority: HIGH)
**Impact:** Cannot test services, difficult to mock dependencies

**Example:**
```python
# Current (COUPLED):
class ForumStatisticsService:
    @classmethod
    def get_forum_statistics(cls):
        total_users = User.objects.filter(is_active=True).count()
        # Direct ORM dependency - cannot mock in tests
```

**Desired:**
```python
# Refactored (TESTABLE):
class ForumStatisticsService:
    def __init__(self, user_repository, topic_repository, post_repository, cache):
        self.user_repo = user_repository
        self.topic_repo = topic_repository
        self.post_repo = post_repository
        self.cache = cache

    def get_forum_statistics(self):
        total_users = self.user_repo.count_active_users()
        # Repository can be mocked in tests
```

### 2. **No Redis Caching** (Priority: HIGH)
**Impact:** Poor performance on hot paths, no distributed caching

**Hot Paths Identified:**
1. `/api/v1/forums/` - Forum list (called frequently)
2. `/api/v1/topics/{id}/` - Topic detail (called on every page load)
3. `/api/v1/moderation/queue/` - Moderation queue (real-time data)
4. `/api/v1/moderation/analytics/` - Analytics (complex aggregations)

**Proposed Cache Strategy:**
- Forum list: 10 min (invalidate on forum creation)
- Topic detail: 2 min (invalidate on post creation/edit)
- User stats: 5 min (invalidate on user activity)
- Moderation analytics: 1 min (near real-time)

### 3. **N+1 Query Problems** (Priority: MEDIUM)
**Impact:** Slow API responses, high database load

**Identified Locations:**
- ForumStatisticsService.get_forum_specific_stats()
- ReviewQueueService.is_duplicate_content()
- Potential in API views (needs analysis)

### 4. **No Unit Tests for Services** (Priority: MEDIUM)
**Impact:** Risky refactoring, difficult to maintain

**Current Test Coverage:**
- ForumStatisticsService: 0%
- ReviewQueueService: 0%
- CodeExecutionService: 80%+ (already refactored)

### 5. **Inconsistent Patterns** (Priority: LOW)
**Impact:** Confusing for new developers, harder to maintain

**Observations:**
- Some services use @classmethod (ForumStatisticsService)
- Some use instance methods (CodeExecutionService)
- No clear pattern for dependency management
- Singleton instance created manually (line 126 in statistics_service.py)

---

## Proposed Architecture

### 1. **Repository Pattern**

**Purpose:** Abstract database access, enable testing

**Structure:**
```python
# apps/api/repositories/base.py
class BaseRepository:
    """Abstract base repository"""
    def __init__(self, model):
        self.model = model

    def get_by_id(self, id):
        return self.model.objects.get(pk=id)

    def filter(self, **kwargs):
        return self.model.objects.filter(**kwargs)

    def count(self, **kwargs):
        return self.model.objects.filter(**kwargs).count()

# apps/api/repositories/user_repository.py
class UserRepository(BaseRepository):
    def __init__(self):
        from django.contrib.auth import get_user_model
        super().__init__(get_user_model())

    def count_active_users(self):
        return self.count(is_active=True)

    def get_online_users(self, threshold):
        return self.filter(
            is_active=True,
            last_login__gte=threshold
        )

# apps/api/repositories/forum_repository.py
class ForumRepository(BaseRepository):
    def __init__(self):
        from machina.apps.forum.models import Forum
        super().__init__(Forum)

    def get_with_stats(self, forum_id):
        """Optimized query with select_related/prefetch_related"""
        return self.model.objects.select_related(
            'parent'
        ).prefetch_related(
            'topics', 'topics__posts'
        ).get(pk=forum_id)
```

### 2. **Dependency Injection Container**

**Purpose:** Centralized dependency management, testable services

**Structure:**
```python
# apps/api/services/container.py
class ServiceContainer:
    """Dependency injection container for services"""

    _instance = None
    _services = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, name, factory):
        """Register a service factory"""
        self._services[name] = factory

    def get(self, name):
        """Get or create service instance"""
        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered")

        factory = self._services[name]
        return factory()

    def get_cache(self):
        """Get cache backend (Redis or fallback)"""
        from django.core.cache import caches
        return caches['default']  # Will be Redis

    def get_user_repository(self):
        from apps.api.repositories import UserRepository
        return UserRepository()

    def get_forum_repository(self):
        from apps.api.repositories import ForumRepository
        return ForumRepository()

    def get_statistics_service(self):
        from apps.api.services import ForumStatisticsService
        return ForumStatisticsService(
            user_repo=self.get_user_repository(),
            topic_repo=self.get_topic_repository(),
            post_repo=self.get_post_repository(),
            cache=self.get_cache()
        )

# Initialize container
container = ServiceContainer()

# Usage in views:
def forum_stats_view(request):
    stats_service = container.get_statistics_service()
    stats = stats_service.get_forum_statistics()
    return Response(stats)
```

### 3. **Redis Integration**

**Purpose:** Fast, distributed caching

**Configuration:**
```python
# settings/base.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'PICKLE_VERSION': -1,  # Use latest pickle protocol
        },
        'KEY_PREFIX': 'learning_studio',
        'VERSION': 1,  # Increment to invalidate all caches
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Optional: Separate cache for sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

**Cache Key Patterns:**
```python
# Prefix: learning_studio:v1:
# Pattern: {namespace}:{resource}:{id}:{variant}

# Examples:
cache_key = 'forum:list:all'                    # All forums
cache_key = 'forum:detail:5'                    # Forum ID 5
cache_key = 'forum:detail:5:stats'              # Forum 5 stats
cache_key = 'topic:detail:123'                  # Topic ID 123
cache_key = 'topic:detail:123:posts:page:1'     # Topic posts page 1
cache_key = 'user:stats:456'                    # User ID 456 stats
cache_key = 'moderation:queue:pending'          # Pending queue
cache_key = 'moderation:analytics:7d'           # 7-day analytics
```

### 4. **Service Layer with DI**

**Refactored Service Example:**
```python
# apps/api/services/statistics_service.py
class ForumStatisticsService:
    """Refactored with dependency injection"""

    CACHE_VERSION = 1  # Increment to invalidate all stat caches

    def __init__(self, user_repo, topic_repo, post_repo, cache):
        self.user_repo = user_repo
        self.topic_repo = topic_repo
        self.post_repo = post_repo
        self.cache = cache
        self.online_threshold_minutes = 15

    def get_forum_statistics(self):
        """Get overall forum statistics with Redis caching"""
        cache_key = self._make_cache_key('forum:stats:all')

        stats = self.cache.get(cache_key)
        if stats is not None:
            return stats

        # Calculate stats
        stats = {
            'total_users': self.user_repo.count_active_users(),
            'total_topics': self.topic_repo.count_approved(),
            'total_posts': self.post_repo.count_approved(),
            'online_users': self._get_online_users_count(),
            'latest_member': self.user_repo.get_latest_member()
        }

        # Cache for 5 minutes
        self.cache.set(cache_key, stats, timeout=300)
        return stats

    def get_forum_specific_stats(self, forum_id):
        """OPTIMIZED: Removed N+1 query"""
        cache_key = self._make_cache_key(f'forum:stats:{forum_id}')

        stats = self.cache.get(cache_key)
        if stats is not None:
            return stats

        # FIXED: Use optimized repository method
        forum = self.forum_repo.get_with_stats(forum_id)

        # Calculate with optimized queries
        week_ago = timezone.now() - timedelta(days=7)
        weekly_posts = self.post_repo.count_for_forum_since(
            forum_id, week_ago
        )

        stats = {
            'topics_count': forum.direct_topics_count,
            'posts_count': forum.direct_posts_count,
            'weekly_posts': weekly_posts,
            'online_users': self._get_forum_online_users(forum_id),
            'trending': weekly_posts > 5
        }

        # Cache for 2 minutes (more volatile)
        self.cache.set(cache_key, stats, timeout=120)
        return stats

    def invalidate_cache(self, scope='all'):
        """Invalidate caches with pattern matching (Redis feature)"""
        if scope == 'all':
            pattern = self._make_cache_key('forum:stats:*')
        else:
            pattern = self._make_cache_key(f'forum:stats:{scope}:*')

        # Redis SCAN command for pattern deletion
        self.cache.delete_pattern(pattern)

    def _make_cache_key(self, key):
        """Generate versioned cache key"""
        return f'v{self.CACHE_VERSION}:{key}'

    def _get_online_users_count(self):
        """Cached online user count"""
        cache_key = self._make_cache_key('users:online:count')

        count = self.cache.get(cache_key)
        if count is not None:
            return count

        threshold = timezone.now() - timedelta(minutes=self.online_threshold_minutes)
        count = self.user_repo.count_online(threshold)

        # Cache for 30 seconds (very volatile)
        self.cache.set(cache_key, count, timeout=30)
        return count
```

---

## Implementation Plan

### Phase 3.1: Infrastructure Setup (Est. 2 hours)

**Tasks:**
1. ✅ Install Redis and django-redis
2. ✅ Configure Redis in settings (dev, staging, prod)
3. ✅ Create base repository pattern
4. ✅ Create dependency injection container
5. ✅ Add Redis to docker-compose.yml
6. ✅ Test Redis connection

**Files to Create:**
- `apps/api/repositories/base.py`
- `apps/api/repositories/__init__.py`
- `apps/api/services/container.py`
- `docker-compose.yml` (update)
- `requirements.txt` (update)

**Redis Installation:**
```bash
pip install redis django-redis hiredis
```

### Phase 3.2: Repository Layer (Est. 3 hours)

**Tasks:**
1. ✅ Create UserRepository with optimized queries
2. ✅ Create ForumRepository with select_related/prefetch_related
3. ✅ Create TopicRepository with optimized queries
4. ✅ Create PostRepository with optimized queries
5. ✅ Create ReviewQueueRepository
6. ✅ Add unit tests for repositories

**Files to Create:**
- `apps/api/repositories/user_repository.py`
- `apps/api/repositories/forum_repository.py`
- `apps/api/repositories/topic_repository.py`
- `apps/api/repositories/post_repository.py`
- `apps/api/repositories/review_queue_repository.py`
- `apps/api/tests/test_repositories.py`

**Optimization Examples:**
```python
# BEFORE (N+1):
forums = Forum.objects.all()
for forum in forums:
    topic_count = forum.topics.count()  # N+1 query

# AFTER (Optimized):
forums = Forum.objects.annotate(
    topic_count=Count('topics')
).all()
for forum in forums:
    topic_count = forum.topic_count  # No extra query
```

### Phase 3.3: Refactor ForumStatisticsService (Est. 2 hours)

**Tasks:**
1. ✅ Refactor to use dependency injection
2. ✅ Integrate Redis caching
3. ✅ Fix N+1 queries
4. ✅ Add cache invalidation logic
5. ✅ Add unit tests (80%+ coverage)
6. ✅ Update views to use new service

**Files to Modify:**
- `apps/forum_integration/statistics_service.py` → `apps/api/services/statistics_service.py`
- `apps/api/views/forum_api.py` (update to use container)

### Phase 3.4: Refactor ReviewQueueService (Est. 2 hours)

**Tasks:**
1. ✅ Refactor to use dependency injection
2. ✅ Add Redis caching for spam scores
3. ✅ Fix N+1 in duplicate detection
4. ✅ Make regex patterns configurable
5. ✅ Add unit tests (80%+ coverage)
6. ✅ Update views to use new service

**Files to Modify:**
- `apps/forum_integration/review_queue_service.py` → `apps/api/services/review_queue_service.py`

### Phase 3.5: Optimize API Views (Est. 2 hours)

**Tasks:**
1. ✅ Audit all API views for N+1 queries
2. ✅ Add select_related/prefetch_related
3. ✅ Update views to use DI container
4. ✅ Add query count monitoring
5. ✅ Run Django Debug Toolbar analysis

**Files to Modify:**
- `apps/api/viewsets/*.py`
- `apps/api/views/*.py`

### Phase 3.6: Testing & Validation (Est. 2 hours)

**Tasks:**
1. ✅ Write comprehensive service tests
2. ✅ Write repository tests
3. ✅ Performance benchmarking (before/after)
4. ✅ Load testing with Redis
5. ✅ Cache hit rate monitoring
6. ✅ Query count verification

**Files to Create:**
- `apps/api/tests/test_statistics_service.py`
- `apps/api/tests/test_review_queue_service.py`
- `apps/api/tests/test_repositories.py`
- `apps/api/tests/test_container.py`

---

## Risk Assessment

### High Risk Areas

#### 1. **Redis Downtime** (Probability: Medium, Impact: High)
**Risk:** Redis failure breaks application

**Mitigation:**
- Implement Redis fallback to Django cache backend
- Add health check endpoint for Redis
- Configure Redis persistence (RDB snapshots)
- Add Redis monitoring (memory, connections)

**Fallback Code:**
```python
def get_cache():
    try:
        cache = caches['default']
        cache.get('health_check')
        return cache
    except Exception:
        logger.warning('Redis unavailable, falling back to in-memory cache')
        return caches['fallback']
```

#### 2. **Cache Invalidation Bugs** (Probability: Medium, Impact: Medium)
**Risk:** Stale data shown to users

**Mitigation:**
- Comprehensive invalidation tests
- Short cache timeouts initially (1-2 min)
- Add cache version bump mechanism
- Monitor cache hit/miss rates

**Versioning Strategy:**
```python
# Increment CACHE_VERSION on code changes that affect cached data
CACHE_VERSION = 2  # Changed data structure - invalidates all caches
```

#### 3. **Query Optimization Errors** (Probability: Low, Impact: High)
**Risk:** Optimizations break functionality or cause different bugs

**Mitigation:**
- Comprehensive before/after testing
- Use Django Debug Toolbar to verify query counts
- Add query count assertions in tests
- Gradual rollout with feature flags

**Test Example:**
```python
def test_query_count_optimized(self):
    with self.assertNumQueries(3):  # Should be exactly 3 queries
        forums = forum_service.get_forum_list()
        assert len(forums) > 0
```

### Medium Risk Areas

#### 4. **Dependency Injection Complexity** (Probability: Low, Impact: Medium)
**Risk:** Team unfamiliar with DI pattern, harder to debug

**Mitigation:**
- Comprehensive documentation
- Team training session
- Clear examples in code
- Gradual adoption (not big bang)

#### 5. **Redis Memory Management** (Probability: Medium, Impact: Low)
**Risk:** Redis runs out of memory

**Mitigation:**
- Set maxmemory policy (allkeys-lru)
- Monitor memory usage
- Use appropriate TTLs
- Implement cache warming selectively

**Redis Configuration:**
```
maxmemory 256mb
maxmemory-policy allkeys-lru
```

---

## Success Metrics

### Performance Targets

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Forum list API response time | 800ms | 200ms | Django Debug Toolbar |
| Topic detail API response time | 600ms | 150ms | Django Debug Toolbar |
| Moderation queue response time | 900ms | 300ms | Django Debug Toolbar |
| Database queries per request | 15-30 | 5-10 | assertNumQueries |
| Cache hit rate | 0% | 60%+ | Redis INFO stats |

### Code Quality Targets

| Metric | Target |
|--------|--------|
| Service test coverage | 80%+ |
| Repository test coverage | 90%+ |
| Documented DI patterns | 100% |
| N+1 queries eliminated | 100% |

### Operational Targets

| Metric | Target |
|--------|--------|
| Redis uptime | 99.9% |
| Redis memory usage | <256MB |
| Redis connection count | <50 |
| Cache invalidation errors | <0.1% |

---

## Implementation Timeline

**Day 1 (4 hours):**
- Setup Redis infrastructure
- Create base repository pattern
- Create DI container
- Basic testing

**Day 2 (4 hours):**
- Implement all repositories
- Write repository tests
- Integrate with services

**Day 3 (4 hours):**
- Refactor ForumStatisticsService
- Refactor ReviewQueueService
- Add service tests

**Day 4 (2 hours):**
- Optimize API views
- Performance benchmarking
- Final testing and validation

**Total:** 14 hours (8-12 estimated + buffer)

---

## Rollback Plan

If Phase 3 causes issues in production:

1. **Immediate Rollback:**
   - Disable Redis caching via environment variable
   - Services fall back to direct ORM calls
   - No data loss (Redis is cache only)

2. **Partial Rollback:**
   - Disable specific cache keys via configuration
   - Roll back specific service refactors
   - Keep repository layer (backwards compatible)

3. **Monitoring:**
   - Add logging for all cache operations
   - Track cache hit/miss rates
   - Monitor Redis memory and connections
   - Alert on cache-related errors

---

## Next Steps

**Approval Required:** Yes

**After Approval:**
1. Start with Phase 3.1 (Infrastructure Setup)
2. Create feature branch: `feature/phase-3-service-layer`
3. Implement incrementally with tests
4. Code review before merging
5. Deploy to staging for validation
6. Production deployment with monitoring

---

**Ready to proceed with Phase 3.1: Infrastructure Setup?**

**Estimated Time:** 2 hours
**Risk Level:** Low
**Files Changed:** ~5 new files, 2 modified files
**Reversible:** Yes (feature flag controlled)
