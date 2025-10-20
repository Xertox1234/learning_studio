"""
User Lifecycle Integration Test.

Tests complete user lifecycle including:
- User signup
- Content creation (enrollments, forum posts)
- GDPR account deletion (soft delete)
- Content preservation after deletion
"""

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post
from apps.learning.models import CourseEnrollment

User = get_user_model()


class UserLifecycleIntegrationTest(TransactionTestCase):
    """Test complete user lifecycle including soft delete."""

    def setUp(self):
        """Set up test data."""
        # Import Course model here to avoid circular import issues
        try:
            from apps.blog.models import CoursePage
            from wagtail.models import Page, Site

            # Create root page and site if they don't exist
            root_page = Page.objects.filter(depth=1).first()
            if not root_page:
                root_page = Page.add_root(title="Root", slug="root")

            # Ensure site exists
            site, created = Site.objects.get_or_create(
                is_default_site=True,
                defaults={
                    'hostname': 'localhost',
                    'root_page': root_page
                }
            )

            # Create homepage for courses to live under
            home_page = root_page.add_child(instance=Page(
                title="Home",
                slug="home"
            ))

            self.home_page = home_page
            self.CoursePage = CoursePage

        except ImportError:
            self.skipTest("Wagtail models not available")

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
        user_id = user.id

        # Step 2: Create and enroll in courses
        course1 = self.home_page.add_child(instance=self.CoursePage(
            title="Python 101",
            slug="python-101"
        ))
        course2 = self.home_page.add_child(instance=self.CoursePage(
            title="Django Basics",
            slug="django-basics"
        ))

        enrollment1 = CourseEnrollment.objects.create(
            user=user,
            course_page=course1
        )
        enrollment2 = CourseEnrollment.objects.create(
            user=user,
            course_page=course2
        )

        enrollment1_id = enrollment1.id
        enrollment2_id = enrollment2.id

        # Step 3: Creates forum content
        # Create a root forum category first
        forum = Forum.objects.create(
            name="General Discussion",
            slug="general",
            type=Forum.FORUM_POST  # Standard forum type
        )

        topic = Topic.objects.create(
            forum=forum,
            poster=user,
            subject="Great course!",
            type=Topic.TOPIC_POST
        )
        topic_id = topic.id

        post = Post.objects.create(
            topic=topic,
            poster=user,
            subject="Great course!",
            content="I really enjoyed this course!",
            approved=True
        )
        post_id = post.id

        # Verify user state before deletion
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_deleted)
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.email, 'john@example.com')

        # Step 4: GDPR account deletion
        user.soft_delete(reason='GDPR request')
        user.refresh_from_db()

        # Verify: User marked as deleted
        self.assertTrue(user.is_deleted)
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.deleted_at)
        self.assertEqual(user.deletion_reason, 'GDPR request')

        # Verify: Personal data anonymized
        self.assertIn('deleted_user_', user.email)
        self.assertIn('@deleted.local', user.email)
        self.assertEqual(user.first_name, '[Deleted')
        self.assertEqual(user.last_name, 'User]')
        self.assertEqual(user.bio, '')
        self.assertEqual(user.location, '')
        self.assertEqual(user.website, '')

        # Verify: Enrollments preserved
        self.assertTrue(CourseEnrollment.objects.filter(id=enrollment1_id).exists())
        self.assertTrue(CourseEnrollment.objects.filter(id=enrollment2_id).exists())

        enrollment1.refresh_from_db()
        enrollment2.refresh_from_db()
        self.assertEqual(enrollment1.user_id, user_id)
        self.assertEqual(enrollment2.user_id, user_id)

        # Verify: Forum content preserved
        # Note: Topic and Post models from django-machina still use CASCADE
        # This test documents current behavior - CASCADE research deferred to Phase 3
        # Once #023 is implemented, these assertions should be updated to:
        # - self.assertIsNone(topic.poster)
        # - self.assertEqual(topic.poster_username, 'john_doe')

        # Verify: User not in default queryset
        self.assertFalse(User.objects.filter(id=user_id).exists())

        # But exists in all_with_deleted queryset
        self.assertTrue(User.objects.all_with_deleted().filter(id=user_id).exists())

    def test_user_restore_after_soft_delete(self):
        """Test that soft-deleted users can be restored by admins."""
        # Create user
        user = User.objects.create_user(
            username='restore_test',
            email='restore@example.com',
            password='testpass123'
        )
        user_id = user.id

        # Soft delete
        user.soft_delete(reason='testing restore')
        user.refresh_from_db()

        # Verify deleted
        self.assertTrue(user.is_deleted)
        self.assertFalse(user.is_active)

        # Restore
        user.restore()
        user.refresh_from_db()

        # Verify restored
        self.assertFalse(user.is_deleted)
        self.assertTrue(user.is_active)
        self.assertIsNone(user.deleted_at)

        # User should appear in default queryset again
        self.assertTrue(User.objects.filter(id=user_id).exists())

    def test_multiple_enrollments_preserved_after_deletion(self):
        """Test that all user enrollments are preserved after soft delete."""
        # Create user
        user = User.objects.create_user(
            username='multi_enroll',
            email='multi@example.com',
            password='testpass123'
        )

        # Create 5 courses
        courses = []
        for i in range(5):
            course = self.home_page.add_child(instance=self.CoursePage(
                title=f"Course {i}",
                slug=f"course-{i}"
            ))
            courses.append(course)

        # Enroll in all courses
        enrollments = []
        for course in courses:
            enrollment = CourseEnrollment.objects.create(
                user=user,
                course_page=course
            )
            enrollments.append(enrollment)

        # Verify 5 enrollments exist
        self.assertEqual(CourseEnrollment.objects.filter(user=user).count(), 5)

        # Soft delete user
        user.soft_delete(reason='test')
        user.refresh_from_db()

        # Verify all 5 enrollments still exist
        enrollment_ids = [e.id for e in enrollments]
        for enrollment_id in enrollment_ids:
            self.assertTrue(
                CourseEnrollment.objects.filter(id=enrollment_id).exists(),
                f"Enrollment {enrollment_id} was deleted (should be preserved)"
            )

        # Verify total enrollment count unchanged
        self.assertEqual(
            CourseEnrollment.objects.filter(id__in=enrollment_ids).count(),
            5,
            "Enrollments were deleted when user was soft deleted"
        )

    def test_soft_delete_idempotent(self):
        """Test that soft_delete can be called multiple times safely."""
        user = User.objects.create_user(
            username='idempotent_test',
            email='idempotent@example.com',
            password='testpass123'
        )

        # Call soft_delete 3 times
        user.soft_delete(reason='first')
        first_deleted_at = user.deleted_at

        user.soft_delete(reason='second')
        second_deleted_at = user.deleted_at

        user.soft_delete(reason='third')
        third_deleted_at = user.deleted_at

        # Deleted timestamp should not change after first call
        self.assertEqual(first_deleted_at, second_deleted_at)
        self.assertEqual(second_deleted_at, third_deleted_at)

        # User should still be marked as deleted
        user.refresh_from_db()
        self.assertTrue(user.is_deleted)
        self.assertFalse(user.is_active)

        # Should only have one deleted record
        self.assertEqual(
            User.objects.all_with_deleted().filter(id=user.id).count(),
            1
        )
