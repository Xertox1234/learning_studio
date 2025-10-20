---
status: pending
priority: p1
issue_id: "012"
tags: [code-review, performance, blocker, pr-23]
dependencies: []
source: Code Review PR #23
discovered: 2025-10-19
---

# Fix Blog Category Post Count N+1 Query

## Problem Statement

PR #23 attempts to optimize blog category post counts using `prefetch_related('blogpage_set')`, but this optimization is ineffective because post-prefetch filtering causes Django to discard the cache and execute N+1 queries.

**Location**: `apps/api/views/wagtail.py:215-224`

**Current Code**:
```python
categories = BlogCategory.objects.all().prefetch_related('blogpage_set').order_by('name')

categories_data = [
    {
        'id': cat.id,
        'name': cat.name,
        'slug': cat.slug,
        'description': cat.description,
        'color': cat.color,
        'post_count': cat.blogpage_set.live().public().count()  # ❌ N+1 QUERY!
    }
    for cat in categories
]
```

**Impact**:
- 10 categories = 10 separate COUNT queries
- Expected: ~2 queries total
- Actual: ~12 queries (2 base + 10 counts)
- Performance: 6x slower than claimed

## Findings

**Discovered by**:
- Kieran Python Reviewer (Django ORM analysis)
- Performance Oracle (query pattern detection)
- Data Integrity Guardian (prefetch cache invalidation)

**Why Prefetch Fails**:
1. `prefetch_related('blogpage_set')` loads ALL BlogPage objects for all categories
2. `.live().public()` applies filters AFTER prefetch
3. Django sees new filters, discards prefetch cache
4. Executes separate query for EACH category: `SELECT COUNT(*) WHERE category_id = ? AND live = true`
5. Result: N+1 queries despite prefetch attempt

**Performance Breakdown**:
```
| Step | Queries | Description |
|------|---------|-------------|
| Load categories | 1 | SELECT * FROM blog_category |
| Prefetch posts | 1 | SELECT * FROM blog_blogpage WHERE category IN (...) |
| Count query (cat 1) | 1 | SELECT COUNT(*) WHERE category = 1 AND live = true |
| Count query (cat 2) | 1 | SELECT COUNT(*) WHERE category = 2 AND live = true |
| ... | +8 | One per remaining category |
| **Total** | **12** | Should be ~2 |
```

**Memory Impact**:
- Prefetch loads ALL blog posts (100+ posts × 2KB = 200KB)
- Then discards them without using
- Wasteful memory allocation

## Proposed Solutions

### Option 1: Use Django Annotation (RECOMMENDED)

**Pros**:
- Single efficient query with JOIN + GROUP BY
- Database calculates counts (no Python iteration)
- No wasted memory on unused prefetch
- Standard Django pattern

**Cons**:
- None

**Effort**: Small (10 minutes)
**Risk**: Low

**Implementation**:
```python
from django.db.models import Count, Q

# Remove ineffective prefetch, add annotation
categories = BlogCategory.objects.all().annotate(
    post_count=Count(
        'blogpage_set',
        filter=Q(blogpage_set__live=True) & Q(blogpage_set__show_in_menus=True),
        distinct=True  # Important: prevents double-counting with M2M
    )
).order_by('name')

categories_data = [
    {
        'id': cat.id,
        'name': cat.name,
        'slug': cat.slug,
        'description': cat.description,
        'color': cat.color,
        'post_count': cat.post_count  # ✅ From annotation - no query
    }
    for cat in categories
]
```

**SQL Generated**:
```sql
SELECT
    blog_category.id,
    blog_category.name,
    COUNT(DISTINCT blog_blogpage.id) FILTER (
        WHERE blog_blogpage.live = true
        AND blog_blogpage.show_in_menus = true
    ) as post_count
FROM blog_category
LEFT JOIN blog_blogpage_categories ON ...
LEFT JOIN blog_blogpage ON ...
GROUP BY blog_category.id
ORDER BY blog_category.name
```

### Option 2: Keep Prefetch, Use Python Count

**Pros**:
- Reuses prefetched data
- Works if you need the actual posts elsewhere

**Cons**:
- Loads unnecessary data (only need count, not full objects)
- More memory usage
- Filters must match prefetch exactly

**Effort**: Medium (20 minutes)
**Risk**: Medium (easy to break)

**Implementation**:
```python
from django.db.models import Prefetch

categories = BlogCategory.objects.all().prefetch_related(
    Prefetch(
        'blogpage_set',
        queryset=BlogPage.objects.live().public(),
        to_attr='published_posts'  # Cache as attribute
    )
).order_by('name')

categories_data = [
    {
        ...
        'post_count': len(cat.published_posts)  # Python len(), not SQL
    }
    for cat in categories
]
```

**Not Recommended** - Over-fetches data just to count.

## Recommended Action

**Use Option 1: Django Annotation**

This is the correct Django pattern for aggregate counts and eliminates both the N+1 queries AND the memory waste from unnecessary prefetching.

## Technical Details

**Affected Files**:
- `apps/api/views/wagtail.py:215-234` (blog_categories function)

**Related Components**:
- BlogCategory model
- BlogPage model (M2M relationship via categories field)
- Wagtail Page queryset methods

**Database Changes**: None required

**Index Requirements**:
- Existing indexes on `blog_blogpage.live` and `blog_blogpage.show_in_menus` sufficient
- M2M join table has default FK indexes

**Test Requirements**:
- Update `apps/api/tests/test_query_performance.py:test_blog_categories_query_count`
- Tighten assertion from `<= 5 queries` to `<= 3 queries`
- Add specific test for post_count annotation:
```python
def test_category_post_count_no_n_plus_one(self):
    """Ensure post_count uses annotation, not per-category queries."""
    # Create 5 categories with varying post counts
    for i in range(5):
        cat = BlogCategory.objects.create(name=f'Category {i}')
        for j in range(i * 2):  # 0, 2, 4, 6, 8 posts
            post = BlogPage.objects.create(...)
            post.categories.add(cat)

    reset_queries()
    response = self.client.get('/api/v1/wagtail/blog/categories/')
    query_count = len(connection.queries)

    # Should be constant regardless of category count
    self.assertLessEqual(query_count, 3)

    # Verify counts are correct
    cats = response.json()['categories']
    self.assertEqual(cats[0]['post_count'], 0)
    self.assertEqual(cats[1]['post_count'], 2)
    self.assertEqual(cats[2]['post_count'], 4)
```

## Acceptance Criteria

- [ ] Post count uses Django annotation instead of per-category query
- [ ] Remove ineffective `prefetch_related('blogpage_set')` line
- [ ] Query count for categories endpoint is <= 3 (down from ~12)
- [ ] Test suite updated with tighter query count assertion
- [ ] New test added for post_count efficiency with varying counts
- [ ] Manual verification with Django Debug Toolbar shows no N+1
- [ ] All existing tests pass
- [ ] Post counts remain accurate (match current behavior)

## Work Log

### 2025-10-19 - Code Review Discovery

**By:** Comprehensive Code Review (8 agents)
**Actions:**
- Discovered during multi-agent review of PR #23
- Analyzed by Kieran Python Reviewer, Performance Oracle, Data Integrity Guardian
- Identified as BLOCKER (P1) - defeats optimization purpose
- Created TODO file for tracking

**Learnings**:
- Prefetch caches are invalidated by post-fetch filtering
- `.filter()`, `.exclude()`, `.count()` on prefetched queryset trigger new queries
- Always use annotation for aggregate calculations
- Prefetch is for accessing relationships, not counting them

## Notes

- This is a common Django anti-pattern (prefetch + filter + count)
- Similar issue exists in course lesson counts (TODO #011)
- Consider adding linter rule to detect `prefetch_related` + `.count()` pattern
- Django Debug Toolbar would have caught this immediately in development

## References

- **PR #23**: Fix N+1 query storm in blog/course/exercise listings
- **Code Review**: Comprehensive multi-agent review on 2025-10-19
- **Django Docs**: [Aggregation](https://docs.djangoproject.com/en/stable/topics/db/aggregation/)
- **Django Docs**: [Prefetch Gotchas](https://docs.djangoproject.com/en/stable/ref/models/querysets/#prefetch-related)
- **Blog Post**: [Prefetch vs Annotate](https://hakibenita.com/django-prefetch-related)
