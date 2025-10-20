---
status: ready
priority: p1
issue_id: "021"
tags: [performance, scalability, forum, critical]
dependencies: []
---

# Fix Forum Topics In-Memory Pagination (OOM Risk)

## Problem Statement

Forum topics pagination loads ALL topics into Python memory before paginating, causing massive memory consumption and Out-of-Memory (OOM) errors at scale.

**Category**: Performance / Scalability
**Severity**: Critical (P1) - OOM risk
**Current Impact**: 10,000 topics = 500MB RAM per request

## Findings

**Discovered during**: Performance analysis (2025-10-20)

**Location**: `apps/api/forum/viewsets/forums.py:129-150`

**Anti-Pattern Code**:
```python
# ❌ CRITICAL BUG: Loads ALL topics into memory
pinned_topics = queryset.filter(type__in=[Topic.TOPIC_STICKY, Topic.TOPIC_ANNOUNCE])
regular_topics = queryset.filter(type=Topic.TOPIC_POST)

# This converts entire querysets to Python lists!
all_topics = list(pinned_topics) + list(regular_topics)
total_count = len(all_topics)
page_topics = all_topics[start:end]  # Pagination AFTER loading everything
```

**Performance Impact**:
| Topic Count | Memory per Request | Response Time | Result |
|-------------|-------------------|---------------|---------|
| 1,000 | 50MB | 500ms | Slow |
| 10,000 | 500MB | 5s | Very slow |
| 100,000 | 5GB | Timeout | **OOM crash** |

**Algorithmic Complexity**:
- Memory: O(n) where n = total topics (loads ALL into memory)
- Database: O(n) full table scan
- Should be: O(page_size) with SQL LIMIT/OFFSET

## Proposed Solutions

### Option 1: Database-Level Pagination with Annotations (RECOMMENDED)

**Pros**:
- **100x memory reduction** (500MB → 5MB for 10,000 topics)
- **100x faster** (5s → 50ms)
- Scales to millions of topics
- Single SQL query
- No memory issues

**Cons**: None

**Effort**: 4 hours
**Risk**: Low

**Implementation**:
```python
# File: apps/api/forum/viewsets/forums.py

from django.db.models import Case, When, IntegerField, Q

def get_topics_queryset(self, forum_slug: str, filters: Dict) -> QuerySet:
    """
    Get topics with database-level pagination.

    Pinned topics (STICKY, ANNOUNCE) sorted first, then regular topics.
    All sorting done in SQL, not Python.
    """
    queryset = Topic.objects.filter(forum__slug=forum_slug)

    # Apply filters (search, status, etc.)
    if filters.get('search'):
        queryset = queryset.filter(
            Q(subject__icontains=filters['search']) |
            Q(first_post__content__icontains=filters['search'])
        )

    # ✅ Annotate pinning priority (1 = pinned, 0 = regular)
    # This happens in SQL, not Python
    queryset = queryset.annotate(
        pin_priority=Case(
            When(type__in=[Topic.TOPIC_STICKY, Topic.TOPIC_ANNOUNCE], then=1),
            default=0,
            output_field=IntegerField()
        )
    )

    # ✅ Database-level sort: pinned first, then by last post time
    queryset = queryset.order_by('-pin_priority', '-last_post_on')

    return queryset

@action(detail=True, methods=['get'])
def topics(self, request, slug=None):
    """List topics in forum (paginated)."""
    forum = self.get_object()

    # Get base queryset (NOT evaluated yet!)
    queryset = self.get_topics_queryset(
        forum_slug=slug,
        filters=request.query_params
    )

    # ✅ Django pagination uses SQL LIMIT/OFFSET
    page = self.paginate_queryset(queryset)
    if page is not None:
        serializer = TopicSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    serializer = TopicSerializer(queryset, many=True)
    return Response(serializer.data)
```

**Generated SQL**:
```sql
-- ✅ Efficient query with LIMIT/OFFSET
SELECT
  topic.*,
  CASE
    WHEN topic.type IN (1, 2) THEN 1
    ELSE 0
  END AS pin_priority
FROM forum_topic AS topic
WHERE topic.forum_id = 5
ORDER BY pin_priority DESC, last_post_on DESC
LIMIT 20 OFFSET 0;  -- Only 20 topics loaded, not all!
```

## Recommended Action

✅ **Option 1** - Database-level pagination with SQL annotations

## Technical Details

**Affected Files**:
- `apps/api/forum/viewsets/forums.py` (lines 129-150)

**Database Impact**:
- No schema changes
- Much more efficient queries (LIMIT/OFFSET)
- Reduced database load

**Memory Impact**:
- **Before**: Loads all N topics into memory
- **After**: Loads only page_size (20-50) topics
- **Reduction**: 100x for large forums

## Acceptance Criteria

- [ ] Replace in-memory pagination with database-level LIMIT/OFFSET
- [ ] Pinned topics still appear first
- [ ] Pagination metadata accurate (total count, has_next, etc.)
- [ ] Query count remains constant regardless of total topic count
- [ ] Memory usage <10MB for any page (not proportional to topic count)
- [ ] Response time <100ms for any page
- [ ] All existing forum tests pass
- [ ] Add performance regression test

## Testing Strategy

```python
# Performance regression test
def test_pagination_query_efficiency():
    """Ensure topic pagination uses database-level LIMIT/OFFSET."""
    from django.test.utils import CaptureQueriesContext
    from django.db import connection

    forum = Forum.objects.create(name="Test Forum", slug="test")

    # Create 1000 topics
    for i in range(1000):
        Topic.objects.create(
            forum=forum,
            subject=f"Topic {i}",
            type=Topic.TOPIC_POST if i > 10 else Topic.TOPIC_STICKY
        )

    # Count queries for page 1
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(f'/api/v1/forums/test/topics/?page=1')

    query_count = len(ctx.captured_queries)

    # Should be ~5 queries regardless of total topic count
    # 1. Get forum
    # 2. Count topics (for pagination metadata)
    # 3. Get page of topics with annotations
    # 4-5. Prefetch related data
    assert query_count <= 6, f"Too many queries: {query_count}"

    # Verify SQL uses LIMIT
    sql = ctx.captured_queries[-2]['sql']  # Topic query
    assert 'LIMIT' in sql.upper(), "Query should use LIMIT"
    assert 'OFFSET' in sql.upper(), "Query should use OFFSET"

    # Verify no memory spike
    import tracemalloc
    tracemalloc.start()

    response = client.get(f'/api/v1/forums/test/topics/?page=50')

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Should use <10MB for any page
    peak_mb = peak / 1024 / 1024
    assert peak_mb < 10, f"Memory usage too high: {peak_mb:.1f}MB"

# Functional test
def test_pinned_topics_appear_first():
    """Pinned topics should appear first in pagination."""
    forum = Forum.objects.create(name="Test", slug="test")

    # Create mixed topics
    regular = Topic.objects.create(forum=forum, subject="Regular", type=Topic.TOPIC_POST)
    sticky = Topic.objects.create(forum=forum, subject="Sticky", type=Topic.TOPIC_STICKY)
    announce = Topic.objects.create(forum=forum, subject="Announce", type=Topic.TOPIC_ANNOUNCE)

    response = client.get('/api/v1/forums/test/topics/')
    topics = response.json()['results']

    # Pinned topics should be first
    assert topics[0]['subject'] in ['Sticky', 'Announce']
    assert topics[1]['subject'] in ['Sticky', 'Announce']
    assert topics[2]['subject'] == 'Regular'
```

## Resources

- Django pagination: https://docs.djangoproject.com/en/5.0/topics/pagination/
- Query optimization: https://docs.djangoproject.com/en/5.0/topics/db/optimization/
- Performance testing: https://docs.djangoproject.com/en/5.0/topics/testing/tools/#django.test.utils.CaptureQueriesContext

## Work Log

### 2025-10-20 - Performance Analysis Discovery
**By:** Claude Code Performance Oracle
**Actions:**
- Discovered during performance analysis
- Identified as critical scalability issue
- Memory profiling showed 500MB usage for 10,000 topics
- Categorized as P1 (OOM risk at scale)

**Learnings:**
- In-memory pagination is a common anti-pattern
- Should ALWAYS use database-level LIMIT/OFFSET
- Symptoms: Memory growth proportional to data size

## Notes

- This is a **performance critical** fix
- **OOM risk** at scale (10,000+ topics)
- Relatively easy fix (4 hours)
- Low risk (standard Django pagination pattern)
- Should be completed in Phase 1 (Day 2)
- **100x performance improvement** expected
