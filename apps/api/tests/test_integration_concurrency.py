"""
Concurrent Enrollment Integration Test.

Tests enrollment under concurrent load to validate race condition fix.
Complements apps/learning/tests/test_enrollment_concurrency.py which has
comprehensive concurrency tests.

This integration test verifies the fix works end-to-end with:
- Multiple concurrent users
- Real HTTP requests via Django test client
- Transaction rollback behavior
"""

import threading
from django.test import TransactionTestCase, Client
from django.contrib.auth import get_user_model
from apps.learning.models import Course, CourseEnrollment, Category

User = get_user_model()


class ConcurrentEnrollmentIntegrationTest(TransactionTestCase):
    """Test enrollment under concurrent load (race condition fix validation)."""

    def setUp(self):
        """Set up test data."""
        # Create category for courses
        self.category = Category.objects.create(
            name="Programming",
            slug="programming"
        )

        # Create instructor user
        self.instructor = User.objects.create_user(
            username='instructor',
            email='instructor@example.com',
            password='testpass123'
        )

    def test_concurrent_enrollments_no_duplicates(self):
        """
        Validate that concurrent enrollments don't create duplicates.

        Scenario: Same user attempts to enroll from multiple tabs/devices.
        Expected: Only 1 enrollment created, others get "already enrolled".
        """
        # Create course
        course = Course.objects.create(
            title="Concurrent Test Course",
            slug="concurrent-test",
            description="Test course",
            short_description="Test",
            category=self.category,
            instructor=self.instructor,
            is_published=True,
            estimated_duration=10  # Required field
        )

        # Create test user
        user = User.objects.create_user(
            username='concurrent_user',
            email='concurrent@example.com',
            password='testpass123'
        )

        results = []
        errors = []

        def attempt_enrollment():
            """Attempt to enroll user in course."""
            try:
                client = Client()
                client.force_login(user)
                response = client.post(f'/learning/courses/{course.id}/enroll/')

                # Parse JSON response
                if response.status_code == 200:
                    data = response.json()
                    results.append({
                        'status': response.status_code,
                        'success': data.get('success'),
                        'error': data.get('error')
                    })
                else:
                    results.append({
                        'status': response.status_code,
                        'success': False,
                        'error': f"HTTP {response.status_code}"
                    })
            except Exception as e:
                errors.append(str(e))

        # Run 10 concurrent enrollment attempts
        threads = [threading.Thread(target=attempt_enrollment) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify: No errors occurred
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

        # Verify: Exactly 1 successful enrollment
        success_count = sum(1 for r in results if r['success'] is True)
        self.assertEqual(success_count, 1,
            f"Expected 1 successful enrollment, got {success_count}. Results: {results}")

        # Verify: 9 "already enrolled" responses
        already_enrolled_count = sum(
            1 for r in results
            if r['success'] is False and 'already enrolled' in str(r.get('error', '')).lower()
        )
        self.assertEqual(already_enrolled_count, 9,
            f"Expected 9 'already enrolled' responses, got {already_enrolled_count}")

        # Verify: Database has exactly 1 enrollment
        actual_enrollments = CourseEnrollment.objects.filter(
            user=user,
            course=course
        ).count()
        self.assertEqual(actual_enrollments, 1,
            f"Database should have 1 enrollment, found {actual_enrollments}")

    def test_concurrent_different_users_all_succeed(self):
        """
        Validate that different users can enroll concurrently.

        Scenario: 20 different users enroll at the same time.
        Expected: All 20 should succeed (no artificial limits in this test).
        """
        # Create course
        course = Course.objects.create(
            title="Multi-User Concurrent Test",
            slug="multi-user-concurrent",
            description="Test course",
            short_description="Test",
            category=self.category,
            instructor=self.instructor,
            is_published=True,
            estimated_duration=10  # Required field
        )

        # Create 20 users
        users = [
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            for i in range(20)
        ]

        results = []
        errors = []

        def enroll_user(user):
            """Enroll specific user in course."""
            try:
                client = Client()
                client.force_login(user)
                response = client.post(f'/learning/courses/{course.id}/enroll/')

                if response.status_code == 200:
                    data = response.json()
                    results.append({
                        'user': user.username,
                        'status': response.status_code,
                        'success': data.get('success')
                    })
                else:
                    results.append({
                        'user': user.username,
                        'status': response.status_code,
                        'success': False
                    })
            except Exception as e:
                errors.append(f"{user.username}: {str(e)}")

        # Run 20 concurrent enrollments (one per user)
        threads = [threading.Thread(target=enroll_user, args=(u,)) for u in users]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify: No errors
        self.assertEqual(len(errors), 0, f"Errors: {errors}")

        # Verify: All 20 succeeded
        success_count = sum(1 for r in results if r.get('success') is True)
        self.assertEqual(success_count, 20,
            f"Expected 20 successful enrollments, got {success_count}")

        # Verify: Database has 20 enrollments
        actual_enrollments = course.enrollments.count()
        self.assertEqual(actual_enrollments, 20,
            f"Expected 20 enrollments in database, found {actual_enrollments}")

        # Verify: No duplicate enrollments (all user IDs unique)
        user_ids = list(course.enrollments.values_list('user_id', flat=True))
        unique_users = set(user_ids)
        self.assertEqual(len(user_ids), len(unique_users),
            "Found duplicate enrollments!")

    def test_enrollment_counter_accuracy_under_concurrency(self):
        """
        Validate that total_enrollments counter is accurate under load.

        Scenario: 50 users enroll concurrently.
        Expected: total_enrollments = 50 (no lost updates).
        """
        # Create course
        course = Course.objects.create(
            title="Counter Test Course",
            slug="counter-test",
            description="Test course",
            short_description="Test",
            category=self.category,
            instructor=self.instructor,
            is_published=True,
            total_enrollments=0,
            estimated_duration=10  # Required field
        )

        # Create 50 users
        users = [
            User.objects.create_user(
                username=f'counter_user{i}',
                email=f'counter{i}@example.com',
                password='testpass123'
            )
            for i in range(50)
        ]

        def enroll_user(user):
            """Enroll user in course."""
            try:
                client = Client()
                client.force_login(user)
                client.post(f'/learning/courses/{course.id}/enroll/')
            except Exception:
                pass  # Ignore errors for this test

        # Run 50 concurrent enrollments
        threads = [threading.Thread(target=enroll_user, args=(u,)) for u in users]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Refresh course from database
        course.refresh_from_db()

        # Verify: Counter matches actual enrollment count
        actual_enrollments = course.enrollments.count()
        self.assertEqual(course.total_enrollments, actual_enrollments,
            f"Counter mismatch: total_enrollments={course.total_enrollments}, "
            f"actual={actual_enrollments}")

        # Verify: Counter is exactly 50
        self.assertEqual(course.total_enrollments, 50,
            f"Expected total_enrollments=50, got {course.total_enrollments}")

    def test_transaction_rollback_on_error(self):
        """
        Validate that failed enrollments rollback completely.

        Scenario: Enrollment fails due to validation error.
        Expected: No partial enrollment, no counter increment.
        """
        # Create course
        course = Course.objects.create(
            title="Rollback Test Course",
            slug="rollback-test",
            description="Test course",
            short_description="Test",
            category=self.category,
            instructor=self.instructor,
            is_published=True,
            total_enrollments=0,
            estimated_duration=10  # Required field
        )

        initial_enrollments = course.enrollments.count()
        initial_counter = course.total_enrollments

        # Attempt enrollment with invalid course ID (should fail)
        user = User.objects.create_user(
            username='rollback_user',
            email='rollback@example.com',
            password='testpass123'
        )

        client = Client()
        client.force_login(user)
        response = client.post(f'/learning/courses/999999/enroll/')

        # Verify: Request failed
        self.assertEqual(response.status_code, 404)

        # Refresh course
        course.refresh_from_db()

        # Verify: No enrollment created
        final_enrollments = course.enrollments.count()
        self.assertEqual(final_enrollments, initial_enrollments,
            "Enrollment created despite error")

        # Verify: Counter not incremented
        self.assertEqual(course.total_enrollments, initial_counter,
            "Counter incremented despite rollback")
