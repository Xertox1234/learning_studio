---
status: pending
priority: p2
issue_id: "028"
tags: [testing, integration, quality-assurance, phase4]
dependencies: [018, 019, 020, 021, 022, 023, 024, 025, 026, 027]
---

# Comprehensive Integration Testing Suite (Phase 4)

## Problem Statement

After implementing 9 critical P1 fixes (security, data integrity, accessibility, performance), we need comprehensive integration testing to verify that all changes work together correctly and no regressions were introduced.

**Category**: Quality Assurance / Testing
**Severity**: High (P2) - Gates production deployment
**Dependencies**: ALL Phase 1-3 todos (018-027) must be complete

## Findings

**Context**: End of Phase 3 (Day 6-7)

**Changes to Validate**:
- ✅ SQL injection fix (.extra() removed)
- ✅ Mutable default JSONField fix
- ✅ Skip navigation link added
- ✅ Forum pagination optimized
- ✅ Enrollment race condition fixed
- ✅ CASCADE deletes changed to SET_NULL
- ✅ Soft delete infrastructure implemented
- ✅ wagtail.py refactored (blog module)
- ✅ Type hints added (90%+ coverage)
- ✅ CodeMirror keyboard navigation added

**Testing Gaps**:
- No end-to-end user flow tests
- No cross-feature integration tests
- No load testing with concurrent users
- No accessibility regression suite
- No security regression suite

## Proposed Solutions

### Option 1: Comprehensive Integration Test Suite (RECOMMENDED)

**Scope**: 5 test suites covering all critical paths

**Pros**:
- Validates all fixes work together
- Catches regressions before production
- Documents expected behavior
- Enables confident deployment

**Cons**: Time-intensive (4 hours)

**Effort**: 4 hours
**Risk**: Low

**Implementation**:

**Test Suite 1: User Lifecycle Integration**
```python
# File: apps/api/tests/test_integration_user_lifecycle.py

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from apps.learning.models import Course, CourseEnrollment
from apps.forum_integration.models import Post, Topic, Forum

User = get_user_model()

class UserLifecycleIntegrationTest(TransactionTestCase):
    """Test complete user lifecycle including soft delete."""

    def test_user_creates_content_then_deletes_account(self):
        """
        End-to-end test:
        1. User signs up
        2. Enrolls in courses
        3. Creates forum posts
        4. Requests account deletion (GDPR)
        5. Content preserved, PII anonymized
        """
        # Step 1: User signs up
        user = User.objects.create_user(
            username='john_doe',
            email='john@example.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )

        # Step 2: Enrolls in courses
        course1 = Course.objects.create(title="Python 101", max_students=10)
        course2 = Course.objects.create(title="Django Basics", max_students=10)

        enrollment1 = CourseEnrollment.objects.create(user=user, course=course1)
        enrollment2 = CourseEnrollment.objects.create(user=user, course=course2)

        # Step 3: Creates forum content
        forum = Forum.objects.create(name="General Discussion")
        topic = Topic.objects.create(
            forum=forum,
            poster=user,
            poster_username=user.username,
            subject="Great course!"
        )
        post = Post.objects.create(
            topic=topic,
            poster=user,
            poster_username=user.username,
            content="I really enjoyed this course!"
        )

        # Step 4: GDPR account deletion
        user.soft_delete(reason='GDPR request')
        user.anonymize_personal_data()

        # Verify: User marked as deleted
        user.refresh_from_db()
        self.assertTrue(user.is_deleted)
        self.assertFalse(user.is_active)
        self.assertIn('deleted_user_', user.username)
        self.assertIn('@deleted.local', user.email)
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')

        # Verify: Enrollments preserved
        self.assertTrue(CourseEnrollment.objects.filter(id=enrollment1.id).exists())
        self.assertTrue(CourseEnrollment.objects.filter(id=enrollment2.id).exists())

        # Verify: Forum content preserved
        topic.refresh_from_db()
        post.refresh_from_db()

        self.assertIsNone(topic.poster)  # FK set to NULL
        self.assertEqual(topic.poster_username, 'john_doe')  # Cached username

        self.assertIsNone(post.poster)
        self.assertEqual(post.poster_username, 'john_doe')
        self.assertEqual(post.content, "I really enjoyed this course!")

        # Verify: User not in default queryset
        self.assertFalse(User.objects.filter(username__contains='john_doe').exists())

        # But exists in all_objects
        self.assertTrue(User.all_objects.filter(id=user.id).exists())
```

**Test Suite 2: Concurrent Enrollment Test**
```python
# File: apps/api/tests/test_integration_concurrency.py

import threading
from django.test import TransactionTestCase, Client
from apps.learning.models import Course, CourseEnrollment

class ConcurrentEnrollmentIntegrationTest(TransactionTestCase):
    """Test enrollment under concurrent load (race condition fix validation)."""

    def test_100_users_enroll_in_limited_course(self):
        """
        100 concurrent users attempt to enroll in course with 10 spots.
        Only 10 should succeed, 90 should fail gracefully.
        """
        course = Course.objects.create(
            title="Limited Course",
            max_students=10
        )

        # Create 100 users
        users = [
            User.objects.create(username=f"user{i}", password="test")
            for i in range(100)
        ]

        results = []
        errors = []

        def enroll(user):
            try:
                client = Client()
                client.force_login(user)
                response = client.post(f'/api/v1/courses/{course.id}/enroll/')
                results.append({
                    'user': user.username,
                    'status': response.status_code,
                    'data': response.json()
                })
            except Exception as e:
                errors.append(str(e))

        # Run 100 concurrent enrollments
        threads = [threading.Thread(target=enroll, args=(u,)) for u in users]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify: Exactly 10 succeeded
        success_count = sum(1 for r in results if r['status'] == 201)
        self.assertEqual(success_count, 10,
            f"Expected 10 enrollments, got {success_count}")

        # Verify: 90 failed with "course full" or "already enrolled"
        failure_count = sum(1 for r in results if r['status'] == 400)
        self.assertEqual(failure_count, 90)

        # Verify: Database state consistent
        actual_enrollments = course.enrollments.count()
        self.assertEqual(actual_enrollments, 10)

        # Verify: No duplicate enrollments
        user_ids = list(course.enrollments.values_list('user_id', flat=True))
        unique_users = set(user_ids)
        self.assertEqual(len(user_ids), len(unique_users),
            "Found duplicate enrollments!")

        # Verify: No errors
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
```

**Test Suite 3: Accessibility Integration**
```javascript
// File: frontend/tests/integration/accessibility.test.js

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility Integration Tests', () => {
  test('skip navigation link works across all pages', async ({ page }) => {
    const pages = [
      '/',
      '/courses',
      '/exercises',
      '/forum',
      '/login'
    ];

    for (const url of pages) {
      await page.goto(url);

      // Press Tab to focus skip link
      await page.keyboard.press('Tab');

      // Skip link should be visible
      const skipLink = page.locator('.skip-link:focus');
      await expect(skipLink).toBeVisible();
      await expect(skipLink).toHaveText('Skip to main content');

      // Press Enter to skip
      await page.keyboard.press('Enter');

      // Main content should be focused
      await expect(page.locator('#main-content')).toBeFocused();
    }
  });

  test('fill-in-blank exercise keyboard navigation', async ({ page }) => {
    await page.goto('/exercises/fill-in-blank-test');

    // Tab through all blanks
    await page.keyboard.press('Tab');  // Skip link
    await page.keyboard.press('Tab');  // First blank

    await expect(page.locator('[data-blank-id="1"]')).toBeFocused();

    // Type answer
    await page.keyboard.type('answer1');

    // Tab to second blank
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-blank-id="2"]')).toBeFocused();

    await page.keyboard.type('answer2');

    // Enter to submit
    await page.keyboard.press('Enter');

    // Should submit
    await expect(page.locator('.success-message')).toBeVisible();
  });

  test('no accessibility violations on key pages', async ({ page }) => {
    const pages = ['/', '/courses', '/exercises', '/forum'];

    for (const url of pages) {
      await page.goto(url);

      const accessibilityScanResults = await new AxeBuilder({ page })
        .analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    }
  });
});
```

**Test Suite 4: Performance Integration**
```python
# File: apps/api/tests/test_integration_performance.py

from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from apps.forum_integration.models import Forum, Topic

class PerformanceIntegrationTest(TestCase):
    """Validate performance fixes (N+1, pagination)."""

    def test_forum_pagination_query_count(self):
        """Forum pagination should use constant queries regardless of topic count."""
        forum = Forum.objects.create(name="Test Forum", slug="test")

        # Create 1000 topics
        for i in range(1000):
            Topic.objects.create(
                forum=forum,
                subject=f"Topic {i}",
                type=Topic.TOPIC_POST if i > 10 else Topic.TOPIC_STICKY
            )

        # Test page 1
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get('/api/v1/forums/test/topics/?page=1')

        page1_queries = len(ctx.captured_queries)

        # Test page 50
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get('/api/v1/forums/test/topics/?page=50')

        page50_queries = len(ctx.captured_queries)

        # Query count should be constant
        self.assertEqual(page1_queries, page50_queries,
            "Query count varies by page number (pagination broken)")

        # Should be ~5 queries max
        self.assertLessEqual(page1_queries, 6,
            f"Too many queries: {page1_queries}")

        # Verify SQL uses LIMIT
        sql = ctx.captured_queries[-2]['sql']
        self.assertIn('LIMIT', sql.upper())
        self.assertIn('OFFSET', sql.upper())
```

**Test Suite 5: Security Regression**
```python
# File: apps/api/tests/test_integration_security.py

class SecurityRegressionTest(TestCase):
    """Ensure security fixes remain in place."""

    def test_no_extra_method_usage(self):
        """Verify .extra() is not used (SQL injection vector)."""
        import os
        import re

        violations = []

        for root, dirs, files in os.walk('apps/'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath) as f:
                        content = f.read()
                        if re.search(r'\.extra\s*\(', content):
                            violations.append(filepath)

        self.assertEqual(violations, [],
            f"Found .extra() usage in: {violations}")

    def test_no_mutable_defaults(self):
        """Scan models for mutable default anti-pattern."""
        from django.apps import apps

        violations = []

        for model in apps.get_models():
            for field in model._meta.get_fields():
                if hasattr(field, 'default') and field.default is not None:
                    # Check if default is mutable object (not callable)
                    if isinstance(field.default, (list, dict, set)):
                        violations.append(
                            f"{model.__name__}.{field.name}"
                        )

        self.assertEqual(violations, [],
            f"Found mutable defaults: {violations}")
```

## Recommended Action

✅ **Option 1** - Comprehensive 5-suite integration testing

## Technical Details

**Test Files to Create**:
- `apps/api/tests/test_integration_user_lifecycle.py` (NEW)
- `apps/api/tests/test_integration_concurrency.py` (NEW)
- `apps/api/tests/test_integration_performance.py` (NEW)
- `apps/api/tests/test_integration_security.py` (NEW)
- `frontend/tests/integration/accessibility.test.js` (NEW)

**Dependencies**: Requires Playwright for frontend tests

## Acceptance Criteria

- [ ] User lifecycle integration test passes
- [ ] Concurrent enrollment test passes (100 users, 10 spots)
- [ ] Accessibility tests pass all key pages
- [ ] Performance tests validate query count
- [ ] Security regression tests pass
- [ ] All 5 test suites execute in CI/CD
- [ ] 100% pass rate required for deployment

## Testing Strategy

```bash
# Run all integration tests
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py test apps.api.tests.test_integration_*

# Run accessibility tests
cd frontend && npx playwright test integration/accessibility.test.js

# Run in CI/CD pipeline
# .github/workflows/integration-tests.yml
name: Integration Tests
on: [pull_request]
jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Django integration tests
        run: |
          python manage.py test apps.api.tests.test_integration_*
      - name: Run Playwright accessibility tests
        run: |
          cd frontend
          npm install
          npx playwright install
          npx playwright test integration/
```

## Resources

- Django testing: https://docs.djangoproject.com/en/5.0/topics/testing/
- Playwright: https://playwright.dev/
- axe-core: https://github.com/dequelabs/axe-core

## Work Log

### 2025-10-20 - Phase 4 Planning
**By:** Claude Code Review System
**Actions:**
- Designed 5-suite integration testing strategy
- Categorized as P2 (gates deployment)
- Estimated 4 hours effort

**Learnings:**
- Integration tests catch regressions
- Concurrency tests validate race condition fixes
- Accessibility tests ensure compliance

## Notes

- This is a **quality assurance** task
- **Gates production deployment** - must pass
- Moderate complexity (4 hours)
- Low risk (testing only)
- Should be completed in Phase 4 (Day 7)
- ALL Phase 1-3 todos must be complete first
