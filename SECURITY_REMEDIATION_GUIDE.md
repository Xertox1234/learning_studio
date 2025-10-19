# Security Remediation Guide - PR #23 Follow-Up

Quick reference for addressing the two LOW severity findings from the PR #23 security audit.

---

## Issue #24: Remove Instructor Email from Public API

**Priority**: P2
**Effort**: 30 minutes
**Severity**: 🟡 LOW (Privacy/Information Disclosure)

### Current Code (3 locations to fix)

**Location 1**: `apps/api/views/wagtail.py:382-385`
```python
'instructor': {
    'name': course.instructor.get_full_name(),
    'email': course.instructor.email  # ❌ REMOVE
} if course.instructor else None,
```

**Location 2**: `apps/api/views/wagtail.py:497-500`
```python
'instructor': {
    'name': course.instructor.get_full_name(),
    'email': course.instructor.email  # ❌ REMOVE
} if course.instructor else None,
```

**Location 3**: `apps/api/views/wagtail.py:571-575`
```python
'instructor': {
    'id': course.instructor.id,
    'name': course.instructor.get_full_name() or course.instructor.username,
    'email': course.instructor.email,  # ❌ REMOVE
} if course.instructor else None,
```

### Recommended Fix (Option 1 - Simple)

Remove the email field entirely:

```python
# apps/api/views/wagtail.py

# Location 1 (line ~382-385) - learning_index()
'instructor': {
    'id': course.instructor.id,
    'name': course.instructor.get_full_name(),
    # email removed - not needed by frontend
} if course.instructor else None,

# Location 2 (line ~497-500) - courses_list()
'instructor': {
    'id': course.instructor.id,
    'name': course.instructor.get_full_name(),
    # email removed - not needed by frontend
} if course.instructor else None,

# Location 3 (line ~571-575) - course_detail()
'instructor': {
    'id': course.instructor.id,
    'name': course.instructor.get_full_name() or course.instructor.username,
    # email removed - not needed by frontend
} if course.instructor else None,
```

### Recommended Fix (Option 2 - Auth-Gated)

Only show email to authenticated users:

```python
# apps/api/views/wagtail.py

instructor_data = {
    'id': course.instructor.id,
    'name': course.instructor.get_full_name() or course.instructor.username,
}

# Only expose email to authenticated users
if request.user.is_authenticated:
    instructor_data['email'] = course.instructor.email

featured_courses_data.append({
    # ... other fields ...
    'instructor': instructor_data if course.instructor else None,
})
```

### Verification Test

```bash
# Test as anonymous user
curl http://localhost:8000/api/v1/wagtail/courses/ | jq '.courses[0].instructor'

# Expected (after fix):
{
  "id": 1,
  "name": "John Doe"
  # No email field
}

# Before fix (current):
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com"  # ❌ Should not be exposed
}
```

### Frontend Impact

Check if frontend uses instructor email anywhere:

```bash
# Search frontend code
grep -r "instructor.email" frontend/src/

# If found, update to use alternative (e.g., contact form instead of direct email)
```

---

## Issue #25: Add Pagination Limits

**Priority**: P2
**Effort**: 1 hour
**Severity**: 🟡 LOW (DoS/Resource Exhaustion)

### Current Code (3 vulnerable locations)

**Location 1**: `apps/api/views/wagtail.py:24-25` - blog_index()
```python
page = int(request.GET.get('page', 1))
page_size = int(request.GET.get('page_size', 9))  # ❌ No upper limit
```

**Location 2**: `apps/api/views/wagtail.py:438-439` - courses_list()
```python
page_num = int(request.GET.get('page', 1))
page_size = int(request.GET.get('page_size', 12))  # ❌ No upper limit
```

**Location 3**: `apps/api/views/wagtail.py:714-715` - exercises_list()
```python
page_num = int(request.GET.get('page', 1))
page_size = int(request.GET.get('page_size', 12))  # ❌ No upper limit
```

### Recommended Fix (Add Validation Utility)

**Step 1**: Add utility function at top of file

```python
# apps/api/views/wagtail.py (add near imports)

# Security: Maximum page size to prevent DoS
MAX_PAGE_SIZE = 100  # Allow reasonable batch sizes but prevent abuse

def get_validated_pagination(request, default_page_size=9):
    """
    Safely extract and validate pagination parameters.

    Args:
        request: Django request object
        default_page_size: Default items per page

    Returns:
        tuple: (page_num, page_size) both validated and safe

    Security:
        - Enforces maximum page size to prevent resource exhaustion
        - Validates numeric inputs
        - Returns safe defaults on invalid input
    """
    # Validate page number
    try:
        page = int(request.GET.get('page', 1))
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1

    # Validate page size with security limit
    try:
        page_size = int(request.GET.get('page_size', default_page_size))
        if page_size < 1:
            page_size = default_page_size
        elif page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE  # ✅ Enforce security limit
    except (ValueError, TypeError):
        page_size = default_page_size

    return page, page_size
```

**Step 2**: Update blog_index()

```python
# apps/api/views/wagtail.py:blog_index() (around line 24-25)

# OLD CODE:
# page = int(request.GET.get('page', 1))
# page_size = int(request.GET.get('page_size', 9))

# NEW CODE:
page, page_size = get_validated_pagination(request, default_page_size=9)
```

**Step 3**: Update courses_list()

```python
# apps/api/views/wagtail.py:courses_list() (around line 438-439)

# OLD CODE:
# page_num = int(request.GET.get('page', 1))
# page_size = int(request.GET.get('page_size', 12))

# NEW CODE:
page_num, page_size = get_validated_pagination(request, default_page_size=12)
```

**Step 4**: Update exercises_list()

```python
# apps/api/views/wagtail.py:exercises_list() (around line 714-715)

# OLD CODE:
# page_num = int(request.GET.get('page', 1))
# page_size = int(request.GET.get('page_size', 12))

# NEW CODE:
page_num, page_size = get_validated_pagination(request, default_page_size=12)
```

### Alternative: Django REST Framework Pagination

If using DRF more extensively:

```python
# apps/api/pagination.py (new file)
from rest_framework.pagination import PageNumberPagination

class SecurePagination(PageNumberPagination):
    """
    Pagination class with security limits.

    Security:
        - max_page_size prevents DoS via large page_size values
        - page_size_query_param allows client customization (within limits)
    """
    page_size = 9
    page_size_query_param = 'page_size'
    max_page_size = 100  # Hard security limit

    def get_paginated_response(self, data):
        """Add security headers to paginated responses."""
        response = super().get_paginated_response(data)
        # Add cache control for public endpoints
        response['Cache-Control'] = 'public, max-age=300'  # 5 minutes
        return response
```

### Verification Tests

**Manual Testing:**
```bash
# Test 1: Normal pagination (should work)
curl "http://localhost:8000/api/v1/wagtail/blog/?page=1&page_size=10" | jq '.posts | length'
# Expected: 10 (or fewer if less content)

# Test 2: Attempt DoS with huge page_size (should be capped)
curl "http://localhost:8000/api/v1/wagtail/blog/?page_size=99999" | jq '.posts | length'
# Expected: 100 (MAX_PAGE_SIZE enforced)

# Test 3: Invalid page_size (should use default)
curl "http://localhost:8000/api/v1/wagtail/blog/?page_size=abc" | jq '.posts | length'
# Expected: 9 (default for blog)

# Test 4: Negative page_size (should use default)
curl "http://localhost:8000/api/v1/wagtail/blog/?page_size=-50" | jq '.posts | length'
# Expected: 9 (default for blog)
```

**Automated Test:**
```python
# apps/api/tests/test_security.py (new file or add to existing)

from django.test import TestCase
from rest_framework.test import APIClient

class PaginationSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create 200 test posts
        for i in range(200):
            # Create test data
            pass

    def test_pagination_limit_enforced_blog(self):
        """Verify page_size cannot exceed MAX_PAGE_SIZE for blog endpoint."""
        response = self.client.get('/api/v1/wagtail/blog/?page_size=99999')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(
            len(data['posts']),
            100,
            "page_size should be capped at MAX_PAGE_SIZE (100)"
        )

    def test_pagination_limit_enforced_courses(self):
        """Verify page_size cannot exceed MAX_PAGE_SIZE for courses endpoint."""
        response = self.client.get('/api/v1/wagtail/courses/?page_size=99999')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(
            len(data['courses']),
            100,
            "page_size should be capped at MAX_PAGE_SIZE (100)"
        )

    def test_pagination_invalid_input_handled(self):
        """Verify invalid page_size values handled gracefully."""
        # Test with non-numeric value
        response = self.client.get('/api/v1/wagtail/blog/?page_size=abc')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            len(data['posts']),
            9,  # Should use default
            "Invalid page_size should default to 9"
        )

        # Test with negative value
        response = self.client.get('/api/v1/wagtail/blog/?page_size=-50')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            len(data['posts']),
            9,  # Should use default
            "Negative page_size should default to 9"
        )
```

### Performance Testing

```bash
# Before fix: DoS possible
time curl "http://localhost:8000/api/v1/wagtail/blog/?page_size=99999" > /dev/null
# Expected: Very slow (5-30 seconds), high memory usage

# After fix: DoS mitigated
time curl "http://localhost:8000/api/v1/wagtail/blog/?page_size=99999" > /dev/null
# Expected: Fast (< 1 second), returns max 100 items
```

---

## Issue #26: Add Security-Focused Tests

**Priority**: P3
**Effort**: 2 hours
**Severity**: N/A (Test Coverage Improvement)

### Recommended Tests

Create `apps/api/tests/test_security.py`:

```python
"""
Security-focused tests for API endpoints.

Tests cover:
- Authorization bypass attempts
- Information disclosure
- Resource exhaustion (DoS)
- Input validation
"""

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class APISecurityTests(TestCase):
    """Security tests for Wagtail API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            username='user2',
            password='testpass123'
        )

    def test_enrollment_authorization_user_scoped(self):
        """Verify users can only access their own enrollments."""
        # Create course and enroll both users
        # ... setup code ...

        # User1 should only see their enrollment
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/v1/wagtail/courses/{course.slug}/enrollment/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Verify user1's enrollment data is returned
        # Verify user2's enrollment data is NOT returned

    def test_instructor_email_not_exposed_to_anonymous(self):
        """Verify instructor email is not exposed to anonymous users."""
        response = self.client.get('/api/v1/wagtail/courses/')
        self.assertEqual(response.status_code, 200)
        data = response.json()

        for course in data['courses']:
            if course.get('instructor'):
                self.assertNotIn(
                    'email',
                    course['instructor'],
                    "Instructor email should not be exposed to anonymous users"
                )

    def test_pagination_dos_protection(self):
        """Verify pagination limits prevent DoS attacks."""
        # Test covered in Issue #25 tests above
        pass

    def test_sql_injection_search_parameter(self):
        """Verify search parameter is safe from SQL injection."""
        # SQLi payload
        malicious_search = "'; DROP TABLE blog_blogpage; --"

        response = self.client.get(
            f'/api/v1/wagtail/courses/?search={malicious_search}'
        )

        # Should return normally (not execute SQL)
        self.assertEqual(response.status_code, 200)

        # Verify no database corruption
        # (tables should still exist)
        from apps.blog.models import BlogPage
        self.assertTrue(BlogPage.objects.model._meta.db_table)

    def test_enrollment_requires_authentication(self):
        """Verify enrollment endpoints require authentication."""
        # Attempt enrollment without auth
        response = self.client.post(
            f'/api/v1/wagtail/courses/test-course/enroll/'
        )

        # Should return 401 or 403
        self.assertIn(response.status_code, [401, 403])

    def test_xss_prevention_in_responses(self):
        """Verify HTML in content is properly escaped."""
        # Create content with potential XSS
        # ... test XSS prevention ...
        pass
```

---

## Deployment Checklist

### Before Deploying Issue #24 (Email Removal)

- [ ] Review frontend code for uses of `instructor.email`
- [ ] Update frontend to use contact forms instead of direct email links
- [ ] Test all course listing pages
- [ ] Verify API documentation updated
- [ ] Add to changelog

### Before Deploying Issue #25 (Pagination Limits)

- [ ] Verify MAX_PAGE_SIZE (100) is appropriate for use case
- [ ] Test with maximum page size (100 items)
- [ ] Monitor API response times in staging
- [ ] Update API documentation with new limits
- [ ] Add rate limiting if not already present
- [ ] Add to changelog

### Before Deploying Issue #26 (Tests)

- [ ] All new tests passing
- [ ] Code coverage maintained or improved
- [ ] CI/CD pipeline includes new tests
- [ ] Add to test documentation

---

## Monitoring After Deployment

### Metrics to Track

```python
# Add logging to track potential abuse

import logging
logger = logging.getLogger('security')

def get_validated_pagination(request, default_page_size=9):
    page, page_size = # ... validation code ...

    # Log when security limit is enforced
    requested_size = request.GET.get('page_size')
    if requested_size and int(requested_size) > MAX_PAGE_SIZE:
        logger.warning(
            f"Pagination limit enforced: user requested {requested_size}, "
            f"capped to {MAX_PAGE_SIZE}",
            extra={
                'ip': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT'),
                'endpoint': request.path,
            }
        )

    return page, page_size
```

### Alerting Rules

Set up alerts for:
1. **Repeated MAX_PAGE_SIZE hits** - May indicate scraping/abuse
2. **High query counts** - Monitor for regression in query optimization
3. **Error rate increases** - Watch for issues with pagination validation

---

## Questions?

Contact the security team or reference the full audit report:
**`docs/security/PR-23-N-PLUS-ONE-AUDIT.md`**
