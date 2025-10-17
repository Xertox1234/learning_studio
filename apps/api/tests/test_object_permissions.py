"""
Tests for object-level authorization (IDOR/BOLA prevention).

These tests verify that users cannot access resources belonging to other users
by manipulating object IDs in API requests.

Security Issue: CVE-2024-IDOR-001
OWASP: API1:2023 - Broken Object Level Authorization (BOLA)
"""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.users.models import UserProfile

User = get_user_model()


class UserProfilePermissionTests(APITestCase):
    """
    Test suite for UserProfile object-level authorization.

    Security: Tests verify IDOR/BOLA prevention for user profiles.
    """

    def setUp(self):
        """Set up test users and profiles."""
        self.client = APIClient()

        # Create User A (regular user)
        # UserProfile is automatically created via signal
        self.user_a = User.objects.create_user(
            username='user_a',
            email='user_a@test.com',
            password='testpass123'
        )
        self.profile_a = self.user_a.profile

        # Create User B (regular user)
        self.user_b = User.objects.create_user(
            username='user_b',
            email='user_b@test.com',
            password='testpass123'
        )
        self.profile_b = self.user_b.profile

        # Create Admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )
        self.profile_admin = self.admin.profile

    def test_cannot_access_other_user_profile_retrieve(self):
        """
        Test: User A cannot retrieve User B's profile.

        Security: Prevents IDOR attack via GET /api/v1/user-profiles/{id}/
        Expected: 404 Not Found (filtered out of queryset)
        """
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f'/api/v1/user-profiles/{self.profile_b.id}/')

        # Should return 404 (filtered out) or 403 (permission denied)
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
            f"User A should not be able to access User B's profile. Got status {response.status_code}"
        )

    def test_cannot_update_other_user_profile(self):
        """
        Test: User A cannot update User B's profile.

        Security: Prevents IDOR attack via PATCH /api/v1/user-profiles/{id}/
        Expected: 404 Not Found or 403 Forbidden
        """
        self.client.force_authenticate(user=self.user_a)

        data = {'skill_level': 'expert'}
        response = self.client.patch(
            f'/api/v1/user-profiles/{self.profile_b.id}/',
            data,
            format='json'
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
            "User A should not be able to update User B's profile"
        )

        # Verify profile was NOT modified
        self.profile_b.refresh_from_db()
        self.assertEqual(self.profile_b.skill_level, 'beginner')

    def test_cannot_delete_other_user_profile(self):
        """
        Test: User A cannot delete User B's profile.

        Security: Prevents IDOR attack via DELETE /api/v1/user-profiles/{id}/
        Expected: 404 Not Found or 403 Forbidden
        """
        self.client.force_authenticate(user=self.user_a)

        response = self.client.delete(f'/api/v1/user-profiles/{self.profile_b.id}/')

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
            "User A should not be able to delete User B's profile"
        )

        # Verify profile still exists
        self.assertTrue(
            UserProfile.objects.filter(id=self.profile_b.id).exists(),
            "Profile should not have been deleted"
        )

    def test_can_access_own_profile(self):
        """
        Test: User A can access their own profile.

        Expected: 200 OK with profile data
        """
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f'/api/v1/user-profiles/{self.profile_a.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.profile_a.id)
        self.assertEqual(response.data['user']['username'], 'user_a')

    def test_can_update_own_profile(self):
        """
        Test: User A can update their own profile.

        Expected: 200 OK with updated data
        """
        self.client.force_authenticate(user=self.user_a)

        data = {'skill_level': 'advanced'}
        response = self.client.patch(
            f'/api/v1/user-profiles/{self.profile_a.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile_a.refresh_from_db()
        self.assertEqual(self.profile_a.skill_level, 'advanced')

    def test_list_only_shows_own_profile(self):
        """
        Test: List endpoint only shows user's own profile.

        Security: Prevents enumeration of all user profiles
        Expected: Only 1 result (user's own profile)
        """
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get('/api/v1/user-profiles/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see own profile
        results = response.data.get('results', response.data)
        if isinstance(results, list):
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['id'], self.profile_a.id)

    def test_admin_can_access_all_profiles(self):
        """
        Test: Admin users can access any profile.

        Expected: 200 OK for any profile
        """
        self.client.force_authenticate(user=self.admin)

        # Admin can access User A's profile
        response_a = self.client.get(f'/api/v1/user-profiles/{self.profile_a.id}/')
        self.assertEqual(response_a.status_code, status.HTTP_200_OK)

        # Admin can access User B's profile
        response_b = self.client.get(f'/api/v1/user-profiles/{self.profile_b.id}/')
        self.assertEqual(response_b.status_code, status.HTTP_200_OK)

    def test_admin_can_update_any_profile(self):
        """
        Test: Admin users can update any profile.

        Expected: 200 OK with updated data
        """
        self.client.force_authenticate(user=self.admin)

        data = {'skill_level': 'expert'}
        response = self.client.patch(
            f'/api/v1/user-profiles/{self.profile_a.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile_a.refresh_from_db()
        self.assertEqual(self.profile_a.skill_level, 'expert')

    def test_admin_list_shows_all_profiles(self):
        """
        Test: Admin list endpoint shows all profiles.

        Expected: 3 results (User A, User B, Admin)
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.get('/api/v1/user-profiles/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        if isinstance(results, list):
            self.assertGreaterEqual(len(results), 3)

    def test_unauthenticated_cannot_access(self):
        """
        Test: Unauthenticated users cannot access profiles.

        Expected: 401 Unauthorized or 403 Forbidden
        """
        # No authentication
        response = self.client.get(f'/api/v1/user-profiles/{self.profile_a.id}/')

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
            "Unauthenticated users should not access profiles"
        )

    def test_sequential_id_enumeration_blocked(self):
        """
        Test: Sequential ID enumeration returns 404 for other users.

        Security: Prevents attacker from enumerating all profiles
        Expected: Only own profile accessible via sequential ID probing
        """
        self.client.force_authenticate(user=self.user_a)

        # Try to access IDs 1-10
        accessible_count = 0
        for profile_id in range(1, 11):
            response = self.client.get(f'/api/v1/user-profiles/{profile_id}/')
            if response.status_code == status.HTTP_200_OK:
                accessible_count += 1

        # Should only access 1 profile (their own)
        self.assertLessEqual(
            accessible_count,
            1,
            f"User should only access 1 profile, got {accessible_count}"
        )
