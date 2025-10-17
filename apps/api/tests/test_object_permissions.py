"""
Tests for object-level authorization (IDOR/BOLA prevention).

These tests verify that users cannot access resources belonging to other users
by manipulating object IDs in API requests.

Security Issue: CVE-2024-IDOR-001
OWASP: API1:2023 - Broken Object Level Authorization (BOLA)
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.users.models import UserProfile
from apps.learning.models import CourseReview, Course, PeerReview, CodeReview

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
        self.user_a = User.objects.create_user(
            email='user_a@test.com',
            password='testpass123'
        )
        self.profile_a = UserProfile.objects.create(
            user=self.user_a,
            bio='User A Bio',
            location='City A'
        )

        # Create User B (regular user)
        self.user_b = User.objects.create_user(
            email='user_b@test.com',
            password='testpass123'
        )
        self.profile_b = UserProfile.objects.create(
            user=self.user_b,
            bio='User B Bio',
            location='City B'
        )

        # Create Admin user
        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )
        self.profile_admin = UserProfile.objects.create(
            user=self.admin,
            bio='Admin Bio'
        )

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

        data = {'bio': 'Hacked by User A'}
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
        self.assertEqual(self.profile_b.bio, 'User B Bio')

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
        self.assertEqual(response.data['bio'], 'User A Bio')
        self.assertEqual(response.data['location'], 'City A')

    def test_can_update_own_profile(self):
        """
        Test: User A can update their own profile.

        Expected: 200 OK with updated data
        """
        self.client.force_authenticate(user=self.user_a)

        data = {'bio': 'Updated by User A'}
        response = self.client.patch(
            f'/api/v1/user-profiles/{self.profile_a.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile_a.refresh_from_db()
        self.assertEqual(self.profile_a.bio, 'Updated by User A')

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

        data = {'bio': 'Updated by Admin'}
        response = self.client.patch(
            f'/api/v1/user-profiles/{self.profile_a.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile_a.refresh_from_db()
        self.assertEqual(self.profile_a.bio, 'Updated by Admin')

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


class CourseReviewPermissionTests(APITestCase):
    """
    Test suite for CourseReview object-level authorization.

    Security: Tests verify IDOR/BOLA prevention for course reviews.
    """

    def setUp(self):
        """Set up test users, courses, and reviews."""
        self.client = APIClient()

        # Create users
        self.user_a = User.objects.create_user(
            email='user_a@test.com',
            password='testpass123'
        )
        self.user_b = User.objects.create_user(
            email='user_b@test.com',
            password='testpass123'
        )
        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )

        # Create course
        self.course = Course.objects.create(
            title='Test Course',
            slug='test-course',
            is_published=True
        )

        # Create reviews
        self.review_a = CourseReview.objects.create(
            user=self.user_a,
            course=self.course,
            rating=5,
            comment='Great course!'
        )
        self.review_b = CourseReview.objects.create(
            user=self.user_b,
            course=self.course,
            rating=4,
            comment='Good course'
        )

    def test_cannot_access_other_user_review(self):
        """
        Test: User A cannot access User B's review.

        Security: Prevents IDOR attack
        Expected: 404 Not Found
        """
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f'/api/v1/course-reviews/{self.review_b.id}/')

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
            "User A should not access User B's review"
        )

    def test_can_access_own_review(self):
        """Test: User A can access their own review."""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f'/api/v1/course-reviews/{self.review_a.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 5)

    def test_list_only_shows_own_reviews(self):
        """Test: List endpoint only shows user's own reviews."""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get('/api/v1/course-reviews/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        if isinstance(results, list):
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['id'], self.review_a.id)

    def test_admin_can_access_all_reviews(self):
        """Test: Admin can access all reviews."""
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(f'/api/v1/course-reviews/{self.review_a.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f'/api/v1/course-reviews/{self.review_b.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PeerReviewPermissionTests(APITestCase):
    """
    Test suite for PeerReview object-level authorization.

    Security: Tests verify IDOR/BOLA prevention for peer reviews.
    """

    def setUp(self):
        """Set up test users and peer reviews."""
        self.client = APIClient()

        # Create users
        self.user_a = User.objects.create_user(
            email='user_a@test.com',
            password='testpass123'
        )
        self.user_b = User.objects.create_user(
            email='user_b@test.com',
            password='testpass123'
        )

        # Create peer reviews
        self.peer_review_a = PeerReview.objects.create(
            author=self.user_a,
            reviewee=self.user_b,
            feedback='Good work!'
        )
        self.peer_review_b = PeerReview.objects.create(
            author=self.user_b,
            reviewee=self.user_a,
            feedback='Needs improvement'
        )

    def test_cannot_access_other_user_peer_review(self):
        """Test: User A cannot access User B's peer review."""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f'/api/v1/peer-reviews/{self.peer_review_b.id}/')

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
            "User A should not access User B's peer review"
        )

    def test_can_access_own_peer_review(self):
        """Test: User A can access their own peer review."""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f'/api/v1/peer-reviews/{self.peer_review_a.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CodeReviewPermissionTests(APITestCase):
    """
    Test suite for CodeReview object-level authorization.

    Security: Tests verify IDOR/BOLA prevention for code reviews.
    """

    def setUp(self):
        """Set up test users and code reviews."""
        self.client = APIClient()

        # Create users
        self.user_a = User.objects.create_user(
            email='user_a@test.com',
            password='testpass123'
        )
        self.user_b = User.objects.create_user(
            email='user_b@test.com',
            password='testpass123'
        )

        # Create peer reviews first
        peer_review_a = PeerReview.objects.create(
            author=self.user_a,
            reviewee=self.user_b,
            feedback='Test'
        )
        peer_review_b = PeerReview.objects.create(
            author=self.user_b,
            reviewee=self.user_a,
            feedback='Test'
        )

        # Create code reviews
        self.code_review_a = CodeReview.objects.create(
            reviewer=self.user_a,
            peer_review=peer_review_a,
            comments='Looks good'
        )
        self.code_review_b = CodeReview.objects.create(
            reviewer=self.user_b,
            peer_review=peer_review_b,
            comments='Needs work'
        )

    def test_cannot_access_other_user_code_review(self):
        """Test: User A cannot access User B's code review."""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f'/api/v1/code-reviews/{self.code_review_b.id}/')

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
            "User A should not access User B's code review"
        )

    def test_can_access_own_code_review(self):
        """Test: User A can access their own code review."""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f'/api/v1/code-reviews/{self.code_review_a.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
