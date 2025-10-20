---
status: ready
priority: p1
issue_id: "022"
tags: [data-integrity, race-condition, concurrency, transactions]
dependencies: []
---

# Fix Enrollment Race Condition (Duplicate Enrollments)

## Problem Statement

Course enrollment flow lacks atomic transaction safety, allowing multiple concurrent requests to create duplicate enrollments or exceed max_students limit. This causes data inconsistency and potential revenue loss for paid courses.

**Category**: Data Integrity / Concurrency
**Severity**: Critical (P1)
**Business Impact**: Revenue loss, data corruption

## Findings

**Discovered during**: Data integrity review (2025-10-20)

**Location**: `apps/learning/views.py` enrollment endpoints

**Vulnerable Code**:
```python
# ❌ Race condition window between checks and creation
def enroll_in_course(request, course_id):
    course = Course.objects.get(id=course_id)

    # Check 1: Is course full? (NOT atomic)
    if course.enrollments.count() >= course.max_students:
        return error_response("Course is full")

    # Check 2: Already enrolled? (NOT atomic)
    if course.enrollments.filter(user=request.user).exists():
        return error_response("Already enrolled")

    # ⚠️ RACE CONDITION WINDOW HERE ⚠️
    # Multiple requests can pass both checks simultaneously

    # Create enrollment (Race condition!)
    enrollment = CourseEnrollment.objects.create(
        user=request.user,
        course=course
    )
```

**Race Condition Scenario**:
```
Time | Request A (User 1)        | Request B (User 1)        | Database State
-----|---------------------------|---------------------------|----------------
t0   | Check: course.count=9     | Check: course.count=9     | 9 enrollments
t1   | ✓ Not full (max=10)       | ✓ Not full (max=10)       | 9 enrollments
t2   | Check: user not enrolled  | Check: user not enrolled  | 9 enrollments
t3   | ✓ Not enrolled yet        | ✓ Not enrolled yet        | 9 enrollments
t4   | Create enrollment A       |                           | 10 enrollments
t5   |                           | Create enrollment B       | 11 enrollments 🚨
t6   | Return success            | Return success            | DUPLICATE! 🚨
```

**Impact**:
- **Duplicate enrollments** for same user
- **Exceed max_students** limit (overbooking)
- **Data inconsistency** in course statistics
- **Revenue loss** if paid courses (double charging or refunds)

## Proposed Solutions

### Option 1: Atomic Transaction with select_for_update (RECOMMENDED)

**Pros**:
- **Prevents all race conditions** via database row locking
- Standard Django pattern
- Handles concurrent requests safely
- Minimal performance impact
- Works across all databases

**Cons**: Slightly increased latency (10-20ms per lock)

**Effort**: 4 hours
**Risk**: Medium (requires concurrency testing)

**Implementation**:
```python
# File: apps/learning/views.py
from django.db import transaction
from django.utils import timezone
from typing import Tuple

@transaction.atomic
def enroll_in_course(request: HttpRequest, course_id: int) -> JsonResponse:
    """
    Enroll user in course with atomic transaction safety.

    Prevents race conditions using select_for_update() to lock course row.
    """
    try:
        # ✅ Lock course row for update (prevents concurrent modifications)
        course = Course.objects.select_for_update().get(id=course_id)

        # Check capacity with lock held (atomic)
        current_enrollments = course.enrollments.count()
        if course.max_students and current_enrollments >= course.max_students:
            return JsonResponse({
                'error': 'Course is full',
                'code': 'course_full',
                'current': current_enrollments,
                'max': course.max_students
            }, status=400)

        # ✅ Atomic get_or_create (prevents duplicates)
        enrollment, created = CourseEnrollment.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={
                'enrolled_at': timezone.now(),
                'status': 'active',
                'progress_percentage': 0
            }
        )

        if not created:
            return JsonResponse({
                'error': 'Already enrolled',
                'code': 'already_enrolled',
                'enrollment_id': enrollment.id
            }, status=400)

        # ✅ Update course counter atomically using F() expression
        from django.db.models import F
        course.total_enrollments = F('total_enrollments') + 1
        course.save(update_fields=['total_enrollments'])

        # Trigger post-enrollment actions (welcome email, etc.)
        send_enrollment_confirmation.delay(enrollment.id)

        return JsonResponse({
            'message': 'Enrolled successfully',
            'enrollment_id': enrollment.id,
            'enrolled_at': enrollment.enrolled_at.isoformat()
        }, status=201)

    except Course.DoesNotExist:
        return JsonResponse({
            'error': 'Course not found',
            'code': 'not_found'
        }, status=404)
    except Exception as e:
        logger.exception(f"Enrollment failed: {e}")
        return JsonResponse({
            'error': 'Enrollment failed',
            'code': 'internal_error'
        }, status=500)
```

### Option 2: Database Unique Constraint (Defense in Depth)

Add database-level constraint as additional safety:
```python
# File: apps/learning/models.py
class CourseEnrollment(models.Model):
    class Meta:
        unique_together = [['user', 'course']]
        # This enforces uniqueness at database level
```

## Recommended Action

✅ **Option 1** - Atomic transaction with select_for_update
✅ **Option 2** - Add unique_together constraint (defense in depth)

## Technical Details

**Affected Files**:
- `apps/learning/views.py` - Enrollment endpoints
- `apps/learning/models.py` - CourseEnrollment model (add unique constraint)

**Database Changes**:
- Migration to add unique_together constraint
- No data migration needed (duplicates should not exist yet)

**Performance Impact**:
- Row locking adds 10-20ms per enrollment
- Prevents expensive duplicate cleanup
- Net positive for system health

## Acceptance Criteria

- [ ] Wrap enrollment in @transaction.atomic decorator
- [ ] Use select_for_update() to lock course row
- [ ] Use get_or_create() for atomic enrollment creation
- [ ] Use F() expression for counter updates
- [ ] Add unique_together constraint to CourseEnrollment
- [ ] Create migration for unique constraint
- [ ] Add concurrency test (20 simultaneous enrollments)
- [ ] All existing tests pass
- [ ] No performance regression (P95 < 200ms)

## Testing Strategy

```python
# Concurrency test - CRITICAL
import threading
from django.test import TransactionTestCase, Client

class EnrollmentConcurrencyTest(TransactionTestCase):
    """Use TransactionTestCase to allow concurrent threads."""

    def test_concurrent_enrollment_no_duplicates(self):
        """Test that concurrent enrollments don't create duplicates."""
        course = Course.objects.create(
            title="Test Course",
            max_students=10
        )

        # Create 20 users
        users = [User.objects.create(username=f"user{i}") for i in range(20)]

        results = []

        def enroll(user):
            """Enroll in separate thread."""
            client = Client()
            client.force_login(user)
            response = client.post(f'/api/v1/courses/{course.id}/enroll/')
            results.append({
                'status': response.status_code,
                'user': user.username
            })

        # Run enrollments in parallel threads
        threads = [threading.Thread(target=enroll, args=(u,)) for u in users]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify only 10 succeeded (201), rest failed (400)
        success_count = sum(1 for r in results if r['status'] == 201)
        self.assertEqual(success_count, 10,
            f"Expected 10 enrollments, got {success_count}")

        # Verify database state
        actual_count = course.enrollments.count()
        self.assertEqual(actual_count, 10,
            f"Database has {actual_count} enrollments, expected 10")

        # Verify no duplicates
        user_ids = course.enrollments.values_list('user_id', flat=True)
        unique_users = set(user_ids)
        self.assertEqual(len(user_ids), len(unique_users),
            "Found duplicate enrollments for same user")

    def test_same_user_concurrent_enrollment(self):
        """Test that same user can't enroll twice concurrently."""
        course = Course.objects.create(title="Test Course")
        user = User.objects.create(username="testuser")

        results = []

        def enroll():
            client = Client()
            client.force_login(user)
            response = client.post(f'/api/v1/courses/{course.id}/enroll/')
            results.append(response.status_code)

        # Same user, 10 concurrent enrollment attempts
        threads = [threading.Thread(target=enroll) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly 1 should succeed
        success_count = results.count(201)
        self.assertEqual(success_count, 1,
            f"Expected 1 success, got {success_count}")

        # Database should have exactly 1 enrollment
        self.assertEqual(course.enrollments.count(), 1)

# Unique constraint test
def test_unique_constraint_enforced():
    """Database should reject duplicate enrollments."""
    from django.db import IntegrityError

    course = Course.objects.create(title="Test")
    user = User.objects.create(username="test")

    # First enrollment succeeds
    enrollment1 = CourseEnrollment.objects.create(user=user, course=course)

    # Second enrollment raises IntegrityError
    with pytest.raises(IntegrityError):
        CourseEnrollment.objects.create(user=user, course=course)
```

## Resources

- Django transactions: https://docs.djangoproject.com/en/5.0/topics/db/transactions/
- select_for_update: https://docs.djangoproject.com/en/5.0/ref/models/querysets/#select-for-update
- Concurrency testing: https://docs.djangoproject.com/en/5.0/topics/testing/tools/#transactiontestcase

## Work Log

### 2025-10-20 - Data Integrity Review Discovery
**By:** Claude Code Data Integrity Guardian
**Actions:**
- Discovered during data integrity review
- Identified race condition in enrollment flow
- Categorized as P1 (revenue impact, data corruption)

**Learnings:**
- Always use transactions for multi-step operations
- select_for_update() prevents race conditions
- get_or_create() is atomic by design
- F() expressions for safe counter updates

## Notes

- This is a **data integrity critical** fix
- **Revenue impact** for paid courses
- Moderate complexity (4 hours)
- Medium risk (requires concurrency testing)
- Should be completed in Phase 1 (Day 2)
- Load testing recommended before production
