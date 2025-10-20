"""
Concurrency tests for course enrollment race condition fix.

Tests atomic transaction safety and prevents duplicate enrollments.
Related: Todo #022 - Fix Enrollment Race Condition
"""

import threading
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from apps.learning.models import Course, CourseEnrollment, Category

User = get_user_model()


class EnrollmentConcurrencyTests(TransactionTestCase):
    """
    Use TransactionTestCase (not TestCase) to allow real database transactions.

    Regular TestCase runs in a single transaction and doesn't support
    concurrent threads accessing the database.
    """

    def setUp(self):
        """Set up test data."""
        # Create category for courses
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category"
        )

    def test_concurrent_same_user_enrollment_no_duplicates(self):
        """
        Test that same user can't enroll twice concurrently.

        Verifies that select_for_update() and get_or_create() prevent
        duplicate enrollments when same user makes concurrent requests.
        """
        # Create course
        course = Course.objects.create(
            title="Test Course",
            slug="test-course",
            description="Test",
            short_description="Test",
            category=self.category,
            instructor=User.objects.create_user(
                username='instructor',
                email='instructor@test.com',
                password='password123'
            ),
            estimated_duration=10,
            is_published=True
        )

        # Create user
        user = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='password123'
        )

        results = []
        errors = []

        def enroll():
            """Attempt enrollment from separate thread."""
            from django.test import Client
            try:
                client = Client()
                client.force_login(user)
                response = client.post(f'/learning/courses/{course.id}/enroll/')
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Run 10 concurrent enrollment attempts for same user
        threads = [threading.Thread(target=enroll) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify no errors occurred
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")

        # Exactly 1 should succeed (200), rest should get "already enrolled"
        success_count = results.count(200)
        self.assertEqual(
            success_count,
            1,
            f"Expected exactly 1 successful enrollment, got {success_count}. "
            f"Results: {results}"
        )

        # Database should have exactly 1 enrollment
        enrollment_count = CourseEnrollment.objects.filter(
            user=user,
            course=course
        ).count()

        self.assertEqual(
            enrollment_count,
            1,
            f"Expected 1 enrollment in database, found {enrollment_count}. "
            f"Race condition detected!"
        )

    def test_concurrent_different_users_no_overbooking(self):
        """
        Test that course with max_students doesn't get overbooked.

        This is currently NOT implemented (no max_students check in view),
        but tests the infrastructure for future implementation.
        """
        # Create course
        instructor = User.objects.create_user(
            username='instructor',
            email='instructor@test.com',
            password='password123'
        )

        course = Course.objects.create(
            title="Limited Course",
            slug="limited-course",
            description="Test",
            short_description="Test",
            category=self.category,
            instructor=instructor,
            estimated_duration=10,
            is_published=True
        )

        # Create 20 users
        users = []
        for i in range(20):
            users.append(User.objects.create_user(
                username=f'student{i}',
                email=f'student{i}@test.com',
                password='password123'
            ))

        results = []
        errors = []

        def enroll(user):
            """Enroll from separate thread."""
            from django.test import Client
            try:
                client = Client()
                client.force_login(user)
                response = client.post(f'/learning/courses/{course.id}/enroll/')
                results.append({
                    'user': user.username,
                    'status': response.status_code
                })
            except Exception as e:
                errors.append({'user': user.username, 'error': str(e)})

        # Run enrollments in parallel
        threads = [threading.Thread(target=enroll, args=(u,)) for u in users]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify no errors
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")

        # All 20 should succeed (no max_students check currently)
        success_count = sum(1 for r in results if r['status'] == 200)
        self.assertEqual(
            success_count,
            20,
            f"Expected all 20 enrollments to succeed, got {success_count}"
        )

        # Verify database state - should have exactly 20 unique enrollments
        actual_count = CourseEnrollment.objects.filter(course=course).count()
        self.assertEqual(
            actual_count,
            20,
            f"Expected 20 enrollments in database, found {actual_count}"
        )

        # Verify no duplicate enrollments (unique_together constraint)
        enrollments = CourseEnrollment.objects.filter(course=course)
        user_ids = list(enrollments.values_list('user_id', flat=True))
        unique_user_ids = set(user_ids)

        self.assertEqual(
            len(user_ids),
            len(unique_user_ids),
            f"Found duplicate enrollments! {len(user_ids)} enrollments for {len(unique_user_ids)} users"
        )

    def test_get_or_create_atomicity(self):
        """
        Test that get_or_create is truly atomic at database level.

        Directly tests the ORM method without going through views.
        """
        course = Course.objects.create(
            title="Atomic Test Course",
            slug="atomic-test",
            description="Test",
            short_description="Test",
            category=self.category,
            instructor=User.objects.create_user(
                username='instructor',
                email='instructor@test.com',
                password='password123'
            ),
            estimated_duration=10,
            is_published=True
        )

        user = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='password123'
        )

        created_flags = []
        enrollment_ids = []

        def try_create():
            """Try to create enrollment."""
            enrollment, created = CourseEnrollment.objects.get_or_create(
                user=user,
                course=course,
                defaults={'progress_percentage': 0}
            )
            created_flags.append(created)
            enrollment_ids.append(enrollment.id)

        # Run 10 concurrent get_or_create attempts
        threads = [threading.Thread(target=try_create) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly 1 should have created=True
        create_count = created_flags.count(True)
        self.assertEqual(
            create_count,
            1,
            f"Expected 1 creation, got {create_count}. "
            f"get_or_create is not atomic!"
        )

        # All enrollment IDs should be the same (same object)
        unique_ids = set(enrollment_ids)
        self.assertEqual(
            len(unique_ids),
            1,
            f"Expected same enrollment ID for all attempts, got {len(unique_ids)} different IDs"
        )

        # Database should have exactly 1 enrollment
        db_count = CourseEnrollment.objects.filter(user=user, course=course).count()
        self.assertEqual(db_count, 1, f"Database has {db_count} enrollments, expected 1")

    def test_unique_constraint_enforced(self):
        """
        Test that database unique_together constraint prevents duplicates.

        This is defense in depth - even if app code fails, database enforces uniqueness.
        """
        from django.db import IntegrityError

        course = Course.objects.create(
            title="Constraint Test Course",
            slug="constraint-test",
            description="Test",
            short_description="Test",
            category=self.category,
            instructor=User.objects.create_user(
                username='instructor',
                email='instructor@test.com',
                password='password123'
            ),
            estimated_duration=10,
            is_published=True
        )

        user = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='password123'
        )

        # First enrollment succeeds
        enrollment1 = CourseEnrollment.objects.create(
            user=user,
            course=course,
            progress_percentage=0
        )
        self.assertIsNotNone(enrollment1.id)

        # Second enrollment should raise IntegrityError
        with self.assertRaises(IntegrityError):
            CourseEnrollment.objects.create(
                user=user,
                course=course,
                progress_percentage=0
            )

    def test_f_expression_counter_safety(self):
        """
        Test that F() expressions prevent counter race conditions.

        Verifies that concurrent counter updates don't lose increments.
        """
        from django.db.models import F

        course = Course.objects.create(
            title="Counter Test Course",
            slug="counter-test",
            description="Test",
            short_description="Test",
            category=self.category,
            instructor=User.objects.create_user(
                username='instructor',
                email='instructor@test.com',
                password='password123'
            ),
            estimated_duration=10,
            is_published=True,
            total_enrollments=0
        )

        def increment_counter():
            """Increment counter using F() expression."""
            Course.objects.filter(id=course.id).update(
                total_enrollments=F('total_enrollments') + 1
            )

        # Run 100 concurrent increments
        threads = [threading.Thread(target=increment_counter) for _ in range(100)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Refresh from database
        course.refresh_from_db()

        # Counter should be exactly 100 (no lost updates)
        self.assertEqual(
            course.total_enrollments,
            100,
            f"Expected counter=100, got {course.total_enrollments}. "
            f"Race condition in counter updates!"
        )
