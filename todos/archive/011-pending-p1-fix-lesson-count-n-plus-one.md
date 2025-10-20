---
status: pending
priority: p1
issue_id: "011"
tags: [code-review, performance, blocker, pr-23]
dependencies: []
source: Code Review PR #23
discovered: 2025-10-19
---

# Fix Lesson Count N+1 Query in Course Listing

## Problem Statement

PR #23 claims to fix N+1 queries in course listings, but introduces a NEW N+1 query pattern when calculating lesson counts. For each course displayed, a separate database query is executed to count lessons.

**Location**: `apps/api/views/wagtail.py:477`

**Current Code**:
```python
for course in paginated_courses:
    lesson_count = course.get_children().live().public().count()  # ❌ N+1 QUERY!
```

**Impact**:
- 12 courses per page = 12 additional queries (default pagination)
- 100 courses total = 100 queries across all pages
- Defeats the purpose of the N+1 optimization PR
- Query count: Expected ~6, Actual ~18 (3x regression)

## Findings

**Discovered by**:
- Kieran Python Reviewer (performance analysis)
- Performance Oracle (query pattern analysis)
- Data Integrity Guardian (query correctness verification)

**Performance Degradation**:
```
| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Base queries | ~6 | ~6 | ✅ |
| Lesson counts | 0 (annotated) | +12 | 🔴 |
| Total queries | ~6 | ~18 | 🔴 |
| Performance | 6.7x faster | 2.2x faster | 🔴 |
```

**Root Cause**:
- `get_children()` method executes a new query for each course iteration
- `.live().public()` filters applied per course, not in bulk
- No annotation or prefetch for lesson counts

## Proposed Solutions

### Option 1: Use Django Annotation (RECOMMENDED)

**Pros**:
- Single query with COUNT aggregation
- No code complexity increase
- Standard Django ORM pattern
- Scales to any number of courses

**Cons**:
- Requires understanding of Wagtail's TreeNode structure

**Effort**: Small (15 minutes)
**Risk**: Low (well-tested pattern)

**Implementation**:
```python
from django.db.models import Count, Q

courses = CoursePage.objects.live().public().annotate(
    lesson_count=Count(
        'get_children',
        filter=Q(get_children__live=True) & Q(get_children__show_in_menus=True)
    )
).prefetch_related(
    'categories',
    'tags'
).select_related(
    'instructor',
    'skill_level'
).order_by('-first_published_at')

# Then in serialization:
'lesson_count': course.lesson_count  # ✅ From annotation - no query
```

### Option 2: Prefetch Children

**Pros**:
- Explicit about loading children
- Works with complex filtering

**Cons**:
- Loads ALL lesson data (not just count)
- More memory overhead
- Still requires .count() in Python

**Effort**: Medium (30 minutes)
**Risk**: Medium (memory usage)

**Implementation**:
```python
from django.db.models import Prefetch

courses = CoursePage.objects.live().public().prefetch_related(
    Prefetch(
        'get_children',
        queryset=LessonPage.objects.live().public()
    ),
    'categories',
    'tags'
).select_related('instructor', 'skill_level')

# Then in serialization:
lesson_count = course.get_children().filter(live=True).count()  # Uses prefetched cache
```

### Option 3: Cache Lesson Count on Model

**Pros**:
- Extremely fast (no query)
- Simple to use

**Cons**:
- Requires database migration
- Cache invalidation complexity
- Stale data risk

**Effort**: Large (2 hours)
**Risk**: High (cache consistency)

**Not Recommended** - Over-engineering for this use case

## Recommended Action

**Use Option 1: Django Annotation**

This is the standard Django pattern for aggregate calculations and aligns with the existing optimization strategy used elsewhere in the codebase.

## Technical Details

**Affected Files**:
- `apps/api/views/wagtail.py:442-521` (courses_list function)
- `apps/api/views/wagtail.py:477` (specific line with N+1 query)

**Related Components**:
- CoursePage model (Wagtail Page)
- LessonPage model (child pages in tree structure)
- Wagtail TreeNode queryset methods

**Database Changes**: None required

**Test Requirements**:
- Update `apps/api/tests/test_query_performance.py:test_course_list_query_count`
- Tighten assertion from `<= 12 queries` to `<= 8 queries`
- Add specific test for lesson_count annotation:
```python
def test_course_lesson_count_no_n_plus_one(self):
    """Ensure lesson_count uses annotation, not per-course queries."""
    # Create course with 5 lessons
    course = CoursePage.objects.create(...)
    for i in range(5):
        LessonPage.objects.create(parent=course, ...)

    reset_queries()
    response = self.client.get('/api/v1/wagtail/courses/')
    query_count = len(connection.queries)

    # Should not increase with number of lessons
    self.assertLessEqual(query_count, 8)
    self.assertEqual(response.json()['courses'][0]['lesson_count'], 5)
```

## Acceptance Criteria

- [ ] Lesson count uses Django annotation instead of per-course query
- [ ] Query count for course listing is <= 8 (down from ~18)
- [ ] Test suite updated with tighter query count assertion
- [ ] New test added specifically for lesson_count efficiency
- [ ] Manual verification with Django Debug Toolbar shows no N+1
- [ ] Performance metrics confirm 6-7x improvement (not 2x)
- [ ] All existing tests pass
- [ ] No functional regression (lesson counts remain accurate)

## Work Log

### 2025-10-19 - Code Review Discovery

**By:** Comprehensive Code Review (8 agents)
**Actions:**
- Discovered during multi-agent review of PR #23
- Analyzed by Kieran Python Reviewer, Performance Oracle, Data Integrity Guardian
- Categorized as BLOCKER (P1) - must fix before merge
- Created TODO file for tracking

**Learnings:**
- N+1 queries can hide in aggregate calculations (count, sum, avg)
- Always test query counts with realistic data (10+ related objects)
- Annotations are preferred over post-fetch aggregation

## Notes

- This issue was introduced in PR #23 (new code, not pre-existing)
- Blocks PR #23 from merging until resolved
- Similar pattern may exist in other endpoints (check exercises, blog)
- Consider adding CI query count threshold to prevent future regressions

## References

- **PR #23**: Fix N+1 query storm in blog/course/exercise listings
- **Code Review**: Comprehensive multi-agent review on 2025-10-19
- **Django Docs**: [Aggregation](https://docs.djangoproject.com/en/stable/topics/db/aggregation/)
- **Wagtail Docs**: [TreeNode API](https://docs.wagtail.org/en/stable/reference/pages/model_reference.html)
