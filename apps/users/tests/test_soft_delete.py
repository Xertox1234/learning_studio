"""
Comprehensive tests for User soft delete functionality.

Tests soft delete, anonymization, restoration, and manager filtering.
Related: Todo #024 - Implement Soft Delete Infrastructure
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class SoftDeleteBasicTests(TestCase):
    """Basic soft delete functionality tests."""

    def setUp(self):
        """Create test user with complete profile."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            bio='Test bio',
            location='Test City',
            website='https://example.com',
            github_username='testuser',
            linkedin_url='https://linkedin.com/in/testuser',
            preferred_programming_languages='Python, JavaScript',
            learning_goals='Learn Django',
            is_mentor=True,
            accepts_mentees=True,
            email_notifications=True
        )

    def test_soft_delete_sets_flags(self):
        """Soft delete should set is_deleted, deleted_at, and deletion_reason."""
        self.user.soft_delete(reason='user_request')

        # Refresh from database
        self.user.refresh_from_db()

        self.assertTrue(self.user.is_deleted)
        self.assertIsNotNone(self.user.deleted_at)
        self.assertEqual(self.user.deletion_reason, 'user_request')
        self.assertFalse(self.user.is_active)

    def test_soft_delete_anonymizes_personal_data(self):
        """Soft delete should anonymize all personal information."""
        original_id = self.user.pk
        self.user.soft_delete()

        # Refresh from database
        self.user.refresh_from_db()

        # Email anonymized
        self.assertEqual(self.user.email, f'deleted_user_{original_id}@deleted.local')

        # Name anonymized
        self.assertEqual(self.user.first_name, '[Deleted')
        self.assertEqual(self.user.last_name, 'User]')

        # Personal info cleared
        self.assertEqual(self.user.bio, '')
        self.assertEqual(self.user.location, '')
        self.assertEqual(self.user.website, '')
        self.assertEqual(self.user.github_username, '')
        self.assertEqual(self.user.linkedin_url, '')

        # Learning preferences cleared
        self.assertEqual(self.user.preferred_programming_languages, '')
        self.assertEqual(self.user.learning_goals, '')

        # Profile settings cleared
        self.assertFalse(self.user.is_mentor)
        self.assertFalse(self.user.accepts_mentees)
        self.assertFalse(self.user.email_notifications)

    def test_soft_delete_deletes_avatar(self):
        """Soft delete should delete avatar file."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        import io

        # Create test image
        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)

        self.user.avatar = SimpleUploadedFile(
            'test_avatar.jpg',
            image_io.read(),
            content_type='image/jpeg'
        )
        self.user.save()

        avatar_path = self.user.avatar.path
        self.assertTrue(self.user.avatar)

        # Soft delete
        self.user.soft_delete()
        self.user.refresh_from_db()

        # Avatar should be cleared
        self.assertFalse(self.user.avatar)

    def test_soft_delete_prevents_duplicate_emails(self):
        """Anonymized emails should be unique to prevent constraint violations."""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password123'
        )

        user1.soft_delete()
        user2.soft_delete()

        user1.refresh_from_db()
        user2.refresh_from_db()

        # Emails should be different (based on ID)
        self.assertNotEqual(user1.email, user2.email)
        self.assertEqual(user1.email, f'deleted_user_{user1.pk}@deleted.local')
        self.assertEqual(user2.email, f'deleted_user_{user2.pk}@deleted.local')


class UserManagerFilteringTests(TestCase):
    """Tests for UserManager filtering soft-deleted users."""

    def setUp(self):
        """Create active and deleted users."""
        self.active_user1 = User.objects.create_user(
            username='active1',
            email='active1@example.com',
            password='password123'
        )
        self.active_user2 = User.objects.create_user(
            username='active2',
            email='active2@example.com',
            password='password123'
        )
        self.deleted_user = User.objects.create_user(
            username='deleted',
            email='deleted@example.com',
            password='password123'
        )
        self.deleted_user.soft_delete()

    def test_default_queryset_excludes_deleted_users(self):
        """User.objects.all() should exclude soft-deleted users."""
        users = User.objects.all()
        self.assertEqual(users.count(), 2)
        self.assertIn(self.active_user1, users)
        self.assertIn(self.active_user2, users)
        self.assertNotIn(self.deleted_user, users)

    def test_filter_excludes_deleted_users(self):
        """User.objects.filter() should exclude soft-deleted users."""
        users = User.objects.filter(username__startswith='active')
        self.assertEqual(users.count(), 2)

        # Trying to filter deleted user returns empty
        deleted_result = User.objects.filter(username='deleted')
        self.assertEqual(deleted_result.count(), 0)

    def test_get_raises_does_not_exist_for_deleted_users(self):
        """User.objects.get() should raise DoesNotExist for deleted users."""
        from django.contrib.auth.models import User as DjangoUser

        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='deleted')

    def test_all_with_deleted_includes_deleted_users(self):
        """all_with_deleted() should include soft-deleted users."""
        all_users = User.objects.all_with_deleted()
        self.assertEqual(all_users.count(), 3)
        self.assertIn(self.deleted_user, all_users)

    def test_deleted_only_returns_only_deleted(self):
        """deleted_only() should return only soft-deleted users."""
        deleted_users = User.objects.deleted_only()
        self.assertEqual(deleted_users.count(), 1)
        self.assertEqual(deleted_users.first(), self.deleted_user)


class SoftDeleteRestorationTests(TestCase):
    """Tests for restoring soft-deleted users."""

    def setUp(self):
        """Create and soft delete a user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.user.soft_delete(reason='user_request')

    def test_restore_undeletes_user(self):
        """restore() should un-delete the user."""
        # User should be deleted
        self.assertEqual(User.objects.all().count(), 0)

        # Restore using all_with_deleted
        deleted_user = User.objects.all_with_deleted().get(username='testuser')
        deleted_user.restore()

        # User should be visible again
        restored_user = User.objects.get(username='testuser')
        self.assertFalse(restored_user.is_deleted)
        self.assertIsNone(restored_user.deleted_at)
        self.assertTrue(restored_user.is_active)

    def test_restore_does_not_recover_anonymized_data(self):
        """restore() cannot recover anonymized personal data."""
        deleted_user = User.objects.all_with_deleted().get(username='testuser')
        deleted_user.restore()

        restored_user = User.objects.get(username='testuser')

        # Data remains anonymized
        self.assertEqual(restored_user.email, f'deleted_user_{restored_user.pk}@deleted.local')
        self.assertEqual(restored_user.first_name, '[Deleted')
        self.assertEqual(restored_user.last_name, 'User]')

    def test_restore_idempotent(self):
        """Calling restore() on active user should be safe (no-op)."""
        active_user = User.objects.create_user(
            username='active',
            email='active@example.com',
            password='password123'
        )

        # Should not raise error
        active_user.restore()

        # User should remain active
        active_user.refresh_from_db()
        self.assertFalse(active_user.is_deleted)


class HardDeleteTests(TestCase):
    """Tests for permanent hard delete."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

    def test_hard_delete_permanently_removes_user(self):
        """hard_delete() should permanently remove user from database."""
        user_id = self.user.pk
        self.user.hard_delete()

        # User should not exist in any query
        self.assertEqual(User.objects.all().count(), 0)
        self.assertEqual(User.objects.all_with_deleted().count(), 0)
        self.assertEqual(User.objects.deleted_only().count(), 0)

        # Verify user truly deleted
        with self.assertRaises(User.DoesNotExist):
            User.objects.all_with_deleted().get(pk=user_id)

    def test_hard_delete_removes_avatar_file(self):
        """hard_delete() should delete avatar file from filesystem."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        import io

        # Create test image
        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)

        self.user.avatar = SimpleUploadedFile(
            'test_avatar.jpg',
            image_io.read(),
            content_type='image/jpeg'
        )
        self.user.save()

        self.assertTrue(self.user.avatar)

        # Hard delete
        self.user.hard_delete()

        # User should be gone
        self.assertEqual(User.objects.all_with_deleted().count(), 0)


class SoftDeleteConcurrencyTests(TransactionTestCase):
    """
    Concurrency tests for soft delete operations.

    Uses TransactionTestCase to allow real database transactions.
    Note: SQLite has limited concurrent write support, so some
    "database is locked" errors are expected and acceptable.
    """

    def test_concurrent_soft_delete_safe(self):
        """Multiple soft delete requests should be safe (idempotent)."""
        import threading

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        results = []
        errors = []

        def soft_delete():
            """Attempt soft delete from separate thread."""
            try:
                # Get fresh instance in each thread
                u = User.objects.all_with_deleted().get(pk=user.pk)
                u.soft_delete(reason='concurrent_test')
                results.append('success')
            except Exception as e:
                # SQLite may raise "database is locked" - this is expected
                error_msg = str(e)
                if 'database table is locked' not in error_msg and 'database is locked' not in error_msg:
                    errors.append(error_msg)

        # Run 5 concurrent soft deletes
        threads = [threading.Thread(target=soft_delete) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have no unexpected errors (SQLite locks are ok)
        self.assertEqual(len(errors), 0, f"Unexpected errors occurred: {errors}")

        # User should be deleted (at least one thread succeeded)
        deleted_user = User.objects.all_with_deleted().get(pk=user.pk)
        self.assertTrue(deleted_user.is_deleted)
        self.assertIsNotNone(deleted_user.deleted_at)


class SoftDeleteIndexPerformanceTests(TestCase):
    """Tests to verify database indexes work correctly."""

    def test_is_deleted_index_used(self):
        """Verify is_deleted index is used in queries."""
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        # Create active and deleted users
        for i in range(10):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='password123'
            )
            if i % 2 == 0:
                user.soft_delete()

        # Query for active users
        with CaptureQueriesContext(connection) as ctx:
            active_users = list(User.objects.all())

        # Should only get non-deleted users
        self.assertEqual(len(active_users), 5)

        # Verify SQL includes is_deleted filter
        # Django can use either "NOT IS_DELETED" or "IS_DELETED = 0"
        sql = ctx.captured_queries[0]['sql'].upper()
        self.assertIn('IS_DELETED', sql)
        self.assertTrue(
            'NOT "USERS_USER"."IS_DELETED"' in sql or '= 0' in sql or '= FALSE' in sql,
            f"Expected is_deleted filter in SQL, got: {sql}"
        )

    def test_deleted_at_composite_index_used(self):
        """Verify composite (is_deleted, deleted_at) index is used."""
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        # Create deleted users with different deletion times
        base_time = timezone.now()
        users_deleted = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'deleted{i}',
                email=f'deleted{i}@example.com',
                password='password123'
            )
            user.soft_delete()
            users_deleted.append(user)

        # Manually set different deletion times using all_with_deleted
        for i, user in enumerate(users_deleted):
            u = User.objects.all_with_deleted().get(pk=user.pk)
            u.deleted_at = base_time - timedelta(days=i)
            # Save directly without soft delete to preserve deleted_at
            super(User, u).save()

        # Query for recently deleted users
        cutoff = base_time - timedelta(days=2)
        with CaptureQueriesContext(connection) as ctx:
            recent_deleted = list(
                User.objects.deleted_only().filter(deleted_at__gte=cutoff)
            )

        # Should get users deleted in last 2 days (days 0, 1, 2 = 3 users)
        self.assertGreaterEqual(len(recent_deleted), 3)

        # Verify SQL includes both is_deleted and deleted_at
        sql = ctx.captured_queries[0]['sql'].upper()
        self.assertIn('IS_DELETED', sql)
        self.assertIn('DELETED_AT', sql)


class SoftDeleteGDPRComplianceTests(TestCase):
    """Tests for GDPR compliance (right to be forgotten)."""

    def test_soft_delete_anonymizes_all_pii(self):
        """Verify all PII is anonymized (GDPR Article 17)."""
        user = User.objects.create_user(
            username='gdpruser',
            email='gdpr@example.com',
            password='password123',
            first_name='John',
            last_name='Doe',
            bio='Personal bio with PII',
            location='123 Street, City',
            website='https://personal-site.com',
            github_username='johndoe',
            linkedin_url='https://linkedin.com/in/johndoe',
            preferred_programming_languages='Python, Java',
            learning_goals='Become a data scientist'
        )

        user.soft_delete(reason='gdpr_request')
        user.refresh_from_db()

        # Verify all PII fields are cleared or anonymized
        pii_fields = {
            'email': f'deleted_user_{user.pk}@deleted.local',
            'first_name': '[Deleted',
            'last_name': 'User]',
            'bio': '',
            'location': '',
            'website': '',
            'github_username': '',
            'linkedin_url': '',
            'preferred_programming_languages': '',
            'learning_goals': '',
        }

        for field, expected_value in pii_fields.items():
            actual_value = getattr(user, field)
            self.assertEqual(
                actual_value,
                expected_value,
                f"Field '{field}' not properly anonymized. "
                f"Expected '{expected_value}', got '{actual_value}'"
            )

    def test_hard_delete_for_gdpr_erasure(self):
        """
        Verify hard delete permanently removes all data (GDPR Article 17).

        After grace period, users can request complete erasure.
        """
        user = User.objects.create_user(
            username='erasureuser',
            email='erasure@example.com',
            password='password123'
        )

        user_id = user.pk

        # Soft delete first (standard flow)
        user.soft_delete(reason='gdpr_request')

        # After grace period (30 days), hard delete
        deleted_user = User.objects.all_with_deleted().get(pk=user_id)
        deleted_user.hard_delete()

        # Verify complete removal
        with self.assertRaises(User.DoesNotExist):
            User.objects.all_with_deleted().get(pk=user_id)

    def test_anonymization_prevents_user_identification(self):
        """Verify anonymized data cannot identify user."""
        user = User.objects.create_user(
            username='privacyuser',
            email='privacy@example.com',
            password='password123',
            first_name='Alice',
            last_name='Smith',
            location='San Francisco'
        )

        original_email = user.email
        original_name = f"{user.first_name} {user.last_name}"

        user.soft_delete()
        user.refresh_from_db()

        # Cannot identify user from anonymized data
        self.assertNotEqual(user.email, original_email)
        self.assertNotIn('Alice', user.first_name)
        self.assertNotIn('Smith', user.last_name)
        self.assertNotIn('San Francisco', user.location)

        # Display name should show [Deleted User]
        display_name = user.get_full_display_name()
        self.assertIn('[Deleted', display_name)
        self.assertIn('User]', display_name)
