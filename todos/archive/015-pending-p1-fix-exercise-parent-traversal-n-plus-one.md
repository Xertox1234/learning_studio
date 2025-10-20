---
status: pending
priority: p1
issue_id: "015"
tags: [code-review, performance, blocker, pr-23, wagtail]
dependencies: []
source: Code Review PR #23
discovered: 2025-10-19
---

# Fix Exercise Parent Traversal N+1 Query

## Problem Statement

PR #23 optimizes exercise listing queries but introduces N+1 queries when fetching parent (lesson) and grandparent (course) information for each exercise. Multiple calls to `get_parent()` trigger separate database queries for every exercise in the list.

**Location**: `apps/api/views/wagtail.py:755-756, 788-789, 917-918, 1025-1026`

**Current Code**:
```python
# Line 755-756 (exercise_detail function):
'lesson_title': exercise.get_parent().title if exercise.get_parent() else None,
'course_title': exercise.get_parent().get_parent().title if exercise.get_parent() and exercise.get_parent().get_parent() else None,

# Line 788-789 (same pattern):
'lesson_title': exercise.get_parent().title if exercise.get_parent() else None,
'course_title': exercise.get_parent().get_parent().title if exercise.get_parent() and exercise.get_parent().get_parent() else None,

# Lines 917-918, 1025-1026: SAME PATTERN REPEATED
```

**Impact**:
- 20 exercises × 2 queries per exercise = 40 additional queries
- Query 1: `get_parent()` for lesson (1 per exercise)
- Query 2: `get_parent().get_parent()` for course (1 per exercise)
- Expected: ~6 queries total
- Actual: ~46 queries total
- **Regression: 7.6x slower than expected**

## Findings

**Discovered by**:
- Performance Oracle (query pattern analysis)
- Data Integrity Guardian (relationship traversal efficiency)

**Performance Degradation**:
```
| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Base queries | ~4 | ~4 | ✅ |
| Parent lookups | 0 (prefetched) | +40 | 🔴 |
| Total queries | ~6 | ~46 | 🔴 |
| Performance | 15x faster | 1.3x faster | 🔴 |
```

**Root Cause**:
- Wagtail's `get_parent()` executes a database query to traverse page tree
- Called twice per exercise: once for lesson, once for course
- No prefetch or caching of parent relationships
- Repeated calls in defensive None checks

**Code Smell**:
```python
# This pattern calls get_parent() THREE TIMES per exercise!
if exercise.get_parent():  # Query 1
    lesson_title = exercise.get_parent().title  # Query 2 (duplicate)
    if exercise.get_parent().get_parent():  # Query 3 (duplicate)
        course_title = exercise.get_parent().get_parent().title  # Query 4
```

## Proposed Solutions

### Option 1: Prefetch Parent Pages with select_related (RECOMMENDED)

**Pros**:
- Uses Django's select_related for FK relationships
- Single JOIN query for all parents
- No Python caching logic needed
- Most efficient database access

**Cons**:
- Wagtail-specific syntax (`__parent__`)
- May not work if Wagtail page tree uses complex structure

**Effort**: Small (20 minutes)
**Risk**: Low (standard Django pattern)

**Implementation**:
```python
# Optimize exercise queryset
exercises = ExercisePage.objects.live().public().prefetch_related(
    'tags'
).select_related(
    'owner',
    '__parent__',            # Immediate parent (Lesson)
    '__parent____parent__'   # Grandparent (Course)
).order_by('-first_published_at')

# Then in serialization (no additional queries):
'lesson_title': exercise.__parent__.title if exercise.__parent__ else None,
'course_title': exercise.__parent__.__parent__.title if exercise.__parent__ and exercise.__parent__.__parent__ else None,
```

**Note**: If `__parent__` doesn't work, try Wagtail's path notation:
```python
.select_related('path')  # May need to access via page tree path
```

### Option 2: Cache Parent Lookups in Python

**Pros**:
- Guaranteed to work with Wagtail's API
- Explicit caching logic
- Easy to understand

**Cons**:
- Still executes 1-2 queries per unique parent
- More code complexity
- Manual cache management

**Effort**: Medium (30 minutes)
**Risk**: Low

**Implementation**:
```python
# Build parent cache before iteration
parent_cache = {}

for exercise in exercises:
    if exercise.id not in parent_cache:
        parent = exercise.get_parent()  # May trigger query
        if parent:
            grandparent = parent.get_parent()  # May trigger query
            parent_cache[exercise.id] = {
                'lesson': parent,
                'lesson_title': parent.title,
                'course': grandparent,
                'course_title': grandparent.title if grandparent else None
            }
        else:
            parent_cache[exercise.id] = {
                'lesson': None,
                'lesson_title': None,
                'course': None,
                'course_title': None
            }

# Use cache in serialization
for exercise in exercises:
    cached = parent_cache.get(exercise.id, {})
    exercise_data = {
        ...
        'lesson_title': cached.get('lesson_title'),
        'course_title': cached.get('course_title'),
    }
```

### Option 3: Prefetch with Prefetch Objects

**Pros**:
- Uses Django's Prefetch for explicit control
- Works with complex relationships

**Cons**:
- More verbose
- Still may trigger multiple queries
- Wagtail page tree may not support this pattern

**Effort**: Medium (30 minutes)
**Risk**: Medium

**Implementation**:
```python
from django.db.models import Prefetch

exercises = ExercisePage.objects.live().public().prefetch_related(
    'tags',
    Prefetch(
        'get_parent',  # May not work - get_parent is method, not relation
        queryset=LessonPage.objects.select_related('get_parent')
    )
).select_related('owner')
```

**Not Recommended** - Wagtail's tree structure may not support this.

## Recommended Action

**Use Option 1: select_related with __parent__**

Try Wagtail's `__parent__` notation first. If that doesn't work, fall back to Option 2 (Python caching).

## Technical Details

**Affected Files**:
- `apps/api/views/wagtail.py:704-817` (exercises_list function)
- `apps/api/views/wagtail.py:823-967` (exercise_detail function)
- `apps/api/views/wagtail.py:971-1059` (step_exercise_detail function)

**Affected Lines with get_parent() calls**:
- Line 755-756: exercise_detail lesson/course titles
- Line 788-789: step exercise lesson/course titles
- Line 917-918: exercise body content parent references
- Line 1025-1026: step exercise body content parent references

**Related Components**:
- ExercisePage model (Wagtail Page)
- StepBasedExercisePage model (Wagtail Page)
- LessonPage model (parent)
- CoursePage model (grandparent)
- Wagtail TreeNode / Page tree structure

**Database Changes**: None required

**Wagtail Documentation**:
- Check if `__parent__` works with select_related
- Wagtail may cache get_parent() internally
- Verify with Wagtail version in use

**Test Requirements**:
- Update `apps/api/tests/test_query_performance.py:test_exercise_list_query_count`
- Tighten assertion from `<= 10 queries` to `<= 6 queries`
- Add test for parent prefetch:
```python
def test_exercise_parent_traversal_no_n_plus_one(self):
    """Ensure exercise parent lookups don't trigger N+1 queries."""
    # Create course → lesson → 10 exercises hierarchy
    course = CoursePage.objects.create(...)
    lesson = LessonPage.objects.create(parent=course, ...)
    for i in range(10):
        ExercisePage.objects.create(parent=lesson, ...)

    reset_queries()
    response = self.client.get('/api/v1/wagtail/exercises/')
    query_count = len(connection.queries)

    # Should not increase with number of exercises
    self.assertLessEqual(query_count, 6)

    # Verify parent data is included
    exercises = response.json()['exercises']
    self.assertEqual(exercises[0]['lesson_title'], lesson.title)
    self.assertEqual(exercises[0]['course_title'], course.title)
```

## Acceptance Criteria

- [ ] Exercise parent traversal uses prefetch or caching
- [ ] No `get_parent()` calls inside iteration loops
- [ ] Query count for exercise listing is <= 6 (down from ~46)
- [ ] Test suite updated with tighter query count assertion
- [ ] New test added for parent traversal efficiency
- [ ] Manual verification with Django Debug Toolbar shows no N+1
- [ ] All existing tests pass
- [ ] Lesson and course titles remain accurate

## Work Log

### 2025-10-19 - Code Review Discovery

**By:** Comprehensive Code Review
**Actions:**
- Discovered during multi-agent performance analysis
- Identified by Performance Oracle and Data Integrity Guardian
- Categorized as BLOCKER (P1) - defeats optimization purpose
- Created TODO file for tracking

**Learnings**:
- Wagtail's `get_parent()` is a method that queries the database
- Don't call methods in conditional checks if they trigger queries
- Cache parent lookups or use select_related for FK relationships
- Test with realistic page tree depth (course → lesson → exercise)

**Pattern to Avoid**:
```python
# ❌ BAD: Calls get_parent() multiple times
if obj.get_parent():
    title = obj.get_parent().title  # Duplicate query

# ✅ GOOD: Cache the result
parent = obj.get_parent()
if parent:
    title = parent.title  # No additional query
```

## Notes

- This is the third N+1 query found in PR #23 (lesson counts, post counts, parent traversal)
- Similar pattern in step_exercise_detail function (lines 1025-1026)
- Consider adding Django Debug Toolbar to development by default
- Future: Add query count monitoring to CI/CD pipeline

## References

- **PR #23**: Fix N+1 query storm in blog/course/exercise listings
- **Code Review**: Comprehensive multi-agent review on 2025-10-19
- **Wagtail Docs**: [Page QuerySet](https://docs.wagtail.org/en/stable/reference/pages/queryset_reference.html)
- **Wagtail Docs**: [TreeNode](https://docs.wagtail.org/en/stable/reference/pages/model_reference.html#wagtail.models.Page.get_parent)
- **Django Docs**: [select_related](https://docs.djangoproject.com/en/stable/ref/models/querysets/#select-related)
