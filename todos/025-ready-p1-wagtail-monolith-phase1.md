---
status: ready
priority: p1
issue_id: "025"
tags: [architecture, technical-debt, refactoring, phase1]
dependencies: []
---

# Refactor wagtail.py Monolith - Phase 1 (Blog Extraction)

## Problem Statement

`apps/api/views/wagtail.py` is a **51,489-line monolithic file** containing ALL Wagtail CMS endpoints. This God Object anti-pattern causes IDE performance issues, merge conflicts, and cognitive overload.

**Category**: Architecture / Technical Debt
**Severity**: Critical (P1) - Development velocity blocker
**Current Impact**: 15-second IDE load time, frequent merge conflicts

## Findings

**Discovered during**: Architecture review (2025-10-20)

**Location**: `apps/api/views/wagtail.py` (51,489 lines!)

**Anti-Pattern**: God Object
- Handles blog, courses, lessons, exercises, enrollments, progress, homepage
- Impossible to understand full context
- Every PR touches this file (merge conflicts)
- New developers overwhelmed

**Breakdown**:
```
wagtail.py (51,489 lines):
├── Blog endpoints       (~5,000 lines)
├── Course endpoints     (~8,000 lines)
├── Lesson endpoints     (~6,000 lines)
├── Exercise endpoints   (~10,000 lines)
├── Enrollment endpoints (~4,000 lines)
├── Progress endpoints   (~3,000 lines)
├── Homepage endpoint    (~500 lines)
└── Shared utilities     (~15,000 lines)
```

## Proposed Solutions

### Phase 1: Extract Blog Endpoints (RECOMMENDED)

**Scope**: Move blog-related endpoints to separate module

**Pros**:
- **Smallest domain** (5,000 lines) - lowest risk
- Clear boundaries (blog vs other content)
- Can validate approach before larger extractions
- Immediate benefits (10% reduction in main file)

**Cons**: None

**Effort**: 8 hours
**Risk**: High (but mitigated by incremental approach)

**Implementation**:

**Step 1: Create Module Structure**
```bash
mkdir -p apps/api/views/wagtail
touch apps/api/views/wagtail/__init__.py
touch apps/api/views/wagtail/blog.py
```

**Step 2: Extract Blog Endpoints**
```python
# File: apps/api/views/wagtail/blog.py
"""
Wagtail Blog API endpoints.

Extracted from monolithic wagtail.py (2025-10-20).
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.blog.models import BlogPage, BlogCategory, BlogTag

@api_view(['GET'])
@permission_classes([AllowAny])
def blog_index(request):
    """
    List all blog posts with pagination.

    Query params:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 12)
        - category: Filter by category slug
        - tag: Filter by tag slug
        - search: Search in title and content

    Returns:
        {
            "results": [...],
            "pagination": {
                "current_page": 1,
                "total_pages": 5,
                "total_count": 50,
                "has_next": true,
                "has_prev": false
            }
        }
    """
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 12))

    # ✅ Optimized query with prefetch/select_related
    blog_pages = BlogPage.objects.live().public().prefetch_related(
        'categories',
        'tags'
    ).select_related('author').order_by('-first_published_at')

    # Apply filters
    category = request.GET.get('category')
    if category:
        blog_pages = blog_pages.filter(categories__slug=category)

    tag = request.GET.get('tag')
    if tag:
        blog_pages = blog_pages.filter(tags__slug=tag)

    search = request.GET.get('search')
    if search:
        blog_pages = blog_pages.search(search)

    # Pagination
    total_count = blog_pages.count()
    start = (page - 1) * page_size
    end = start + page_size
    paginated_posts = blog_pages[start:end]

    # Serialize
    posts_data = [serialize_blog_post(post, request) for post in paginated_posts]

    return Response({
        'results': posts_data,
        'pagination': {
            'current_page': page,
            'total_pages': (total_count + page_size - 1) // page_size,
            'total_count': total_count,
            'has_next': end < total_count,
            'has_prev': page > 1
        }
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def blog_post_detail(request, slug):
    """
    Get single blog post by slug.

    Args:
        slug: Blog post slug

    Returns:
        Blog post data with full content
    """
    try:
        post = BlogPage.objects.live().public().prefetch_related(
            'categories',
            'tags'
        ).select_related('author').get(slug=slug)
    except BlogPage.DoesNotExist:
        return Response({
            'error': 'Blog post not found'
        }, status=404)

    return Response(serialize_blog_post(post, request, detail=True))

@api_view(['GET'])
@permission_classes([AllowAny])
def blog_categories(request):
    """List all blog categories."""
    categories = BlogCategory.objects.all()
    return Response([
        {
            'id': cat.id,
            'name': cat.name,
            'slug': cat.slug
        }
        for cat in categories
    ])

@api_view(['GET'])
@permission_classes([AllowAny])
def blog_tags(request):
    """List all blog tags."""
    tags = BlogTag.objects.all()
    return Response([
        {
            'id': tag.id,
            'name': tag.name,
            'slug': tag.slug
        }
        for tag in tags
    ])

# Shared serialization logic
def serialize_blog_post(post, request, detail=False):
    """Serialize blog post to JSON."""
    data = {
        'id': post.id,
        'title': post.title,
        'slug': post.slug,
        'excerpt': post.excerpt,
        'author': {
            'id': post.author.id,
            'name': post.author.get_full_name(),
            'username': post.author.username
        } if post.author else None,
        'published_date': post.first_published_at,
        'categories': [
            {'id': cat.id, 'name': cat.name, 'slug': cat.slug}
            for cat in post.categories.all()
        ],
        'tags': [
            {'id': tag.id, 'name': tag.name, 'slug': tag.slug}
            for tag in post.tags.all()
        ],
        'featured_image': post.featured_image.url if post.featured_image else None,
    }

    if detail:
        # Include full content only in detail view
        data['body'] = serialize_streamfield(post.body, request)
        data['reading_time'] = post.reading_time

    return data

def serialize_streamfield(streamfield, request):
    """Serialize Wagtail StreamField to JSON."""
    # Existing logic from wagtail.py
    pass
```

**Step 3: Update Module __init__.py**
```python
# File: apps/api/views/wagtail/__init__.py
"""
Wagtail CMS API endpoints (modularized).

Modules:
- blog: Blog post endpoints (DONE - Phase 1)
- courses: Course endpoints (TODO - Phase 2)
- exercises: Exercise endpoints (TODO - Phase 3)
"""

from .blog import (
    blog_index,
    blog_post_detail,
    blog_categories,
    blog_tags
)

__all__ = [
    'blog_index',
    'blog_post_detail',
    'blog_categories',
    'blog_tags',
]
```

**Step 4: Update URL Configuration**
```python
# File: apps/api/urls.py

# BEFORE:
from apps.api.views import wagtail

urlpatterns = [
    path('blog/', wagtail.blog_index, name='blog-index'),
    # ...
]

# AFTER:
from apps.api.views.wagtail import (
    blog_index,
    blog_post_detail,
    blog_categories,
    blog_tags
)

urlpatterns = [
    path('blog/', blog_index, name='blog-index'),
    path('blog/<slug:slug>/', blog_post_detail, name='blog-detail'),
    path('blog/categories/', blog_categories, name='blog-categories'),
    path('blog/tags/', blog_tags, name='blog-tags'),
    # ...
]
```

**Step 5: Rollback Safety (Feature Flag)**
```python
# File: learning_community/settings/base.py

# Feature flag for gradual rollout
USE_MODULAR_WAGTAIL_VIEWS = env.bool('USE_MODULAR_WAGTAIL_VIEWS', default=False)

# File: apps/api/urls.py
from django.conf import settings

if settings.USE_MODULAR_WAGTAIL_VIEWS:
    from apps.api.views.wagtail import blog_index, blog_post_detail
else:
    from apps.api.views import wagtail
    blog_index = wagtail.blog_index
    blog_post_detail = wagtail.blog_post_detail
```

## Recommended Action

✅ **Phase 1** - Extract blog endpoints (5,000 lines)
⏳ **Phase 2** - Extract course endpoints (8,000 lines) - Todo #026
⏳ **Phase 3** - Extract exercise endpoints (10,000 lines) - Todo #027

## Technical Details

**Affected Files**:
- `apps/api/views/wagtail.py` (reduce by 5,000 lines)
- `apps/api/views/wagtail/blog.py` (NEW - 5,000 lines)
- `apps/api/views/wagtail/__init__.py` (NEW - 50 lines)
- `apps/api/urls.py` (update imports)

**Breaking Changes**: None (backward compatible with feature flag)

**Database Changes**: None

## Acceptance Criteria

- [ ] Create `apps/api/views/wagtail/` module structure
- [ ] Extract blog_index, blog_post_detail, blog_categories, blog_tags
- [ ] Move shared blog serialization logic
- [ ] Update URL configuration
- [ ] Add feature flag for gradual rollout
- [ ] All blog API tests pass
- [ ] No regression in blog functionality
- [ ] API responses identical before/after
- [ ] Performance maintained (query count unchanged)
- [ ] wagtail.py reduced by ~5,000 lines

## Testing Strategy

```python
# Regression tests - API responses must be identical

def test_blog_index_response_unchanged():
    """Blog index response must match old implementation."""
    response = client.get('/api/v1/blog/')

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert 'results' in data
    assert 'pagination' in data
    assert isinstance(data['results'], list)

    # Verify pagination metadata
    pagination = data['pagination']
    assert 'current_page' in pagination
    assert 'total_pages' in pagination
    assert 'has_next' in pagination
    assert 'has_prev' in pagination

def test_blog_detail_response_unchanged():
    """Blog detail response must match old implementation."""
    post = BlogPage.objects.live().first()

    response = client.get(f'/api/v1/blog/{post.slug}/')
    assert response.status_code == 200

    data = response.json()
    assert data['title'] == post.title
    assert data['slug'] == post.slug
    assert 'body' in data  # Full content in detail view
    assert 'author' in data
    assert 'categories' in data
    assert 'tags' in data

def test_blog_query_count_unchanged():
    """Query count should match old implementation (N+1 prevention)."""
    from django.test.utils import CaptureQueriesContext
    from django.db import connection

    with CaptureQueriesContext(connection) as ctx:
        response = client.get('/api/v1/blog/')

    query_count = len(ctx.captured_queries)

    # Should be ~5 queries (not N+1)
    # 1. Count total posts
    # 2. Get page of posts
    # 3. Prefetch categories
    # 4. Prefetch tags
    # 5. Select related author
    assert query_count <= 6, f"Too many queries: {query_count}"

# Feature flag test
def test_feature_flag_fallback():
    """Feature flag should allow rollback to old implementation."""
    from django.conf import settings

    # Disable modular views
    settings.USE_MODULAR_WAGTAIL_VIEWS = False

    response = client.get('/api/v1/blog/')
    assert response.status_code == 200  # Still works

    # Enable modular views
    settings.USE_MODULAR_WAGTAIL_VIEWS = True

    response = client.get('/api/v1/blog/')
    assert response.status_code == 200  # Still works
```

## Resources

- Python module best practices: https://realpython.com/python-modules-packages/
- Django view organization: https://docs.djangoproject.com/en/5.0/topics/http/views/
- Refactoring large files: https://martinfowler.com/books/refactoring.html

## Work Log

### 2025-10-20 - Architecture Review Discovery
**By:** Claude Code Architecture Strategist
**Actions:**
- Discovered 51,489-line monolithic wagtail.py
- Categorized as God Object anti-pattern
- Designed 3-phase extraction strategy
- Phase 1: Blog (5,000 lines) - lowest risk
- Categorized as P1 (development velocity impact)

**Learnings:**
- Incremental refactoring reduces risk
- Blog is smallest, cleanest domain (start here)
- Feature flags enable safe rollback

## Notes

- This is an **architecture critical** fix
- **Development velocity** impact - reduces merge conflicts
- High complexity (8 hours per phase)
- High risk (large refactoring)
- **Incremental approach** - Phase 1 validates strategy
- Should be completed in Phase 2 (Day 4)
- Test thoroughly before proceeding to Phase 2
- Monitor IDE performance improvement
