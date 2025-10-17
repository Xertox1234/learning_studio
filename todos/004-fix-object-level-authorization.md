# Fix Missing Object-Level Authorization

**Priority**: 🔴 P1 - CRITICAL
**Category**: Security
**Effort**: 20-30 hours
**Deadline**: Within 2 weeks

## Problem

Many ViewSets check if a user is authenticated but not if they have permission to access specific objects. This allows users to view, modify, or delete resources they shouldn't have access to (IDOR/BOLA vulnerability).

## Locations

Multiple files in `apps/api/viewsets/*.py`

## Current Vulnerable Pattern

```python
# apps/api/viewsets/user.py
class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]  # Only checks authentication!

    def retrieve(self, request, pk=None):
        profile = get_object_or_404(UserProfile, pk=pk)
        # No check if request.user owns this profile!
        return Response(serializer.data)
```

## Attack Vector

```bash
# User A (ID 123) logged in
# Can access User B's (ID 456) private profile:
GET /api/v1/users/456/profile/
Authorization: Bearer <user_a_token>

# Returns User B's private data!
```

## Impact

- Users can view other users' private profiles
- Users can modify other users' exercise submissions
- Users can delete other users' content
- Users can access admin-only resources
- Privilege escalation opportunities

## Affected ViewSets

1. `UserProfileViewSet` - Profile access
2. `ExerciseSubmissionViewSet` - Submissions
3. `EnrollmentViewSet` - Course enrollments
4. `UserProgressViewSet` - Learning progress
5. `UserAchievementViewSet` - Achievements
6. `DiscussionViewSet` - Partial (needs review)

## Solution

Implement proper object-level authorization using custom permission classes and filtered querysets.

## Implementation Steps

### Step 1: Create custom permission classes

```python
# apps/api/permissions.py
from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners to view/edit.
    """
    def has_object_permission(self, request, view, obj):
        # Assumes the model instance has an attribute `user`
        return obj.user == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to allow read to anyone,
    but write only to owners.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions (GET, HEAD, OPTIONS) allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for owner
        return obj.user == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission for owner or admin.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access anything
        if request.user.is_staff:
            return True

        # Owner can access their own
        return obj.user == request.user


class IsEnrolledOrAdmin(permissions.BasePermission):
    """
    Permission for course-related resources.
    Users can only access if enrolled or if they're admin.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access anything
        if request.user.is_staff:
            return True

        # Check if user is enrolled in the course
        if hasattr(obj, 'course'):
            from apps.learning.models import Enrollment
            return Enrollment.objects.filter(
                user=request.user,
                course=obj.course,
                is_active=True
            ).exists()

        return False
```

### Step 2: Fix UserProfileViewSet

```python
# apps/api/viewsets/user.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.api.permissions import IsOwnerOrAdmin

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """
        Filter queryset to only user's own profile.
        Admins can see all.
        """
        user = self.request.user

        if user.is_staff:
            return UserProfile.objects.all()

        # Regular users can only see their own profile
        return UserProfile.objects.filter(user=user)

    def retrieve(self, request, pk=None):
        """Get specific profile with permission check"""
        # get_object() automatically calls has_object_permission
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def update(self, request, pk=None):
        """Update profile with permission check"""
        profile = self.get_object()  # Permission check here

        serializer = self.get_serializer(
            profile,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def list(self, request):
        """List only accessible profiles"""
        # Queryset already filtered by get_queryset()
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```

### Step 3: Fix ExerciseSubmissionViewSet

```python
# apps/api/viewsets/exercises.py
from apps.api.permissions import IsOwnerOrAdmin

class ExerciseSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSubmissionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Users can only see their own submissions"""
        user = self.request.user

        if user.is_staff:
            # Admins see all submissions
            return ExerciseSubmission.objects.all().select_related(
                'user', 'exercise'
            )

        # Regular users see only their submissions
        return ExerciseSubmission.objects.filter(
            user=user
        ).select_related('exercise')

    def create(self, request):
        """Create submission for current user only"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Force user to be request.user (can't submit for others)
        serializer.save(user=request.user)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, pk=None):
        """Users can only update their own submissions"""
        submission = self.get_object()  # Permission check

        # Additional check: Can only update if not already graded
        if submission.is_graded:
            return Response(
                {'error': 'Cannot update graded submission'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(
            submission,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def destroy(self, request, pk=None):
        """Users can only delete their own submissions"""
        submission = self.get_object()  # Permission check

        # Additional check: Can only delete if not graded
        if submission.is_graded:
            return Response(
                {'error': 'Cannot delete graded submission'},
                status=status.HTTP_403_FORBIDDEN
            )

        submission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

### Step 4: Fix EnrollmentViewSet

```python
# apps/api/viewsets/learning.py
from apps.api.permissions import IsOwnerOrAdmin

class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Users can only see their own enrollments"""
        user = self.request.user

        if user.is_staff:
            return Enrollment.objects.all().select_related(
                'user', 'course'
            )

        return Enrollment.objects.filter(
            user=user
        ).select_related('course')

    def create(self, request):
        """Enroll current user in a course"""
        course_id = request.data.get('course')

        # Check if already enrolled
        if Enrollment.objects.filter(
            user=request.user,
            course_id=course_id,
            is_active=True
        ).exists():
            return Response(
                {'error': 'Already enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Force user to be request.user
        serializer.save(user=request.user)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
```

### Step 5: Fix UserProgressViewSet

```python
# apps/api/viewsets/learning.py
from apps.api.permissions import IsOwnerOrAdmin

class UserProgressViewSet(viewsets.ModelViewSet):
    serializer_class = UserProgressSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Users can only see their own progress"""
        user = self.request.user

        if user.is_staff:
            return Progress.objects.all().select_related(
                'user', 'course', 'lesson'
            )

        return Progress.objects.filter(
            user=user
        ).select_related('course', 'lesson')

    def create(self, request):
        """Record progress for current user"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Force user to be request.user
        serializer.save(user=request.user)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, pk=None):
        """Update progress with permission check"""
        progress = self.get_object()  # Permission check

        serializer = self.get_serializer(
            progress,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
```

### Step 6: Fix UserAchievementViewSet

```python
# apps/api/viewsets/achievements.py
from apps.api.permissions import IsOwnerOrReadOnly

class UserAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for user achievements.
    Achievements are awarded by the system, users can only view.
    """
    serializer_class = UserAchievementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users can only see their own achievements"""
        user = self.request.user

        if user.is_staff:
            return UserAchievement.objects.all().select_related(
                'user', 'achievement'
            )

        return UserAchievement.objects.filter(
            user=user
        ).select_related('achievement')
```

### Step 7: Review DiscussionViewSet

```python
# apps/api/viewsets/community.py
from apps.api.permissions import IsOwnerOrReadOnly

class DiscussionViewSet(viewsets.ModelViewSet):
    serializer_class = DiscussionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """All users can see discussions"""
        return Discussion.objects.all().select_related(
            'author', 'course'
        )

    def create(self, request):
        """Create discussion for current user"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Force author to be request.user
        serializer.save(author=request.user)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, pk=None):
        """Only author can update discussion"""
        discussion = self.get_object()  # Permission check

        # Additional time-based check: Can only edit within 1 hour
        from django.utils import timezone
        from datetime import timedelta

        time_limit = timezone.now() - timedelta(hours=1)
        if discussion.created_at < time_limit:
            return Response(
                {'error': 'Cannot edit discussion after 1 hour'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(
            discussion,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def destroy(self, request, pk=None):
        """Only author or admin can delete"""
        discussion = self.get_object()  # Permission check
        discussion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

## Testing

```python
# tests/test_object_permissions.py

class ObjectLevelPermissionTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            email='user_a@test.com',
            password='password123'
        )
        self.user_b = User.objects.create_user(
            email='user_b@test.com',
            password='password123'
        )

        self.profile_a = UserProfile.objects.create(user=self.user_a)
        self.profile_b = UserProfile.objects.create(user=self.user_b)

    def test_cannot_access_other_user_profile(self):
        """User A cannot access User B's profile"""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(
            f'/api/v1/users/profiles/{self.profile_b.id}/'
        )

        # Should return 404 (filtered out) or 403 (permission denied)
        self.assertIn(response.status_code, [403, 404])

    def test_can_access_own_profile(self):
        """User A can access their own profile"""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(
            f'/api/v1/users/profiles/{self.profile_a.id}/'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.profile_a.id)

    def test_cannot_update_other_user_profile(self):
        """User A cannot update User B's profile"""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.patch(
            f'/api/v1/users/profiles/{self.profile_b.id}/',
            {'bio': 'Hacked!'}
        )

        self.assertIn(response.status_code, [403, 404])

    def test_cannot_view_other_user_submissions(self):
        """User A cannot view User B's submissions"""
        submission_b = ExerciseSubmission.objects.create(
            user=self.user_b,
            exercise=self.exercise,
            code='print("B")'
        )

        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(
            f'/api/v1/submissions/{submission_b.id}/'
        )

        self.assertIn(response.status_code, [403, 404])

    def test_list_only_shows_own_items(self):
        """List endpoints only show user's own items"""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get('/api/v1/users/profiles/')

        self.assertEqual(response.status_code, 200)
        # Should only see own profile
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.profile_a.id)

    def test_admin_can_access_all(self):
        """Admins can access all resources"""
        admin = User.objects.create_superuser(
            email='admin@test.com',
            password='admin123'
        )
        self.client.force_authenticate(user=admin)

        response = self.client.get(
            f'/api/v1/users/profiles/{self.profile_b.id}/'
        )

        self.assertEqual(response.status_code, 200)

    def test_cannot_submit_for_other_user(self):
        """Users cannot create submissions for others"""
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post('/api/v1/submissions/', {
            'user': self.user_b.id,  # Try to submit for User B
            'exercise': self.exercise.id,
            'code': 'print("hack")'
        })

        # Should create for user_a, not user_b
        if response.status_code == 201:
            submission = ExerciseSubmission.objects.get(
                id=response.data['id']
            )
            self.assertEqual(submission.user, self.user_a)
```

## Verification Checklist

- [ ] Custom permission classes created
- [ ] All affected ViewSets updated with permissions
- [ ] get_queryset() filters by user
- [ ] create() methods force user=request.user
- [ ] Comprehensive permission tests added
- [ ] Manual testing with different users
- [ ] Admin access tested and working
- [ ] List endpoints filter correctly
- [ ] 404 vs 403 responses considered

## Manual Testing

1. Create two test users
2. Log in as User A
3. Try to access User B's resources:
   - Profile: `/api/v1/users/profiles/{user_b_id}/`
   - Submissions: `/api/v1/submissions/{user_b_submission_id}/`
   - Progress: `/api/v1/progress/{user_b_progress_id}/`
4. All should return 403 or 404
5. Access own resources - should work
6. List endpoints - should only show own items

## Notes

- This is a large refactoring across multiple ViewSets
- Consider doing in phases: most critical first
- Priority order:
  1. UserProfileViewSet (PII exposure)
  2. ExerciseSubmissionViewSet (academic integrity)
  3. EnrollmentViewSet (payment/access bypass)
  4. UserProgressViewSet (data privacy)
  5. Others

## References

- OWASP API Security Top 10: Broken Object Level Authorization (BOLA)
- OWASP: Insecure Direct Object References (IDOR)
- CWE-639: Authorization Bypass Through User-Controlled Key
- Django REST Framework Permissions: https://www.django-rest-framework.org/api-guide/permissions/
- Comprehensive Security Audit 2025, Finding #4
