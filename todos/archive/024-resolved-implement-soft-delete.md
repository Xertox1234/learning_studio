---
status: ready
priority: p1
issue_id: "024"
tags: [data-integrity, gdpr, user-management, foundational]
dependencies: []
---

# Implement Soft Delete for User Accounts

## Problem Statement

No soft delete mechanism exists for user accounts. Hard deleting users triggers 90 CASCADE deletes, destroying all community content. Need soft delete infrastructure to support GDPR compliance while preserving community value.

**Category**: Data Integrity / GDPR Compliance
**Severity**: Critical (P1) - Foundational for Todo #023
**Business Impact**: Enables safe account closure without content loss

## Findings

**Discovered during**: Data integrity review (2025-10-20)

**Current Behavior**:
```python
# ❌ Hard delete destroys everything
user.delete()  # CASCADE deletes 90 related objects
```

**Required Behavior**:
```python
# ✅ Soft delete preserves content, anonymizes PII
user.soft_delete(reason='User request')
# - Marks is_deleted=True
# - Sets deleted_at timestamp
# - Anonymizes personal data (GDPR)
# - Preserves community contributions
# - Prevents login
```

## Proposed Solutions

### Option 1: Add Soft Delete Fields + Custom Manager (RECOMMENDED)

**Pros**:
- Clean separation (deleted users filtered by default)
- Standard Django pattern
- GDPR compliant
- Reversible (can restore if needed)
- Audit trail

**Cons**: Requires model changes, migration

**Effort**: 8 hours
**Risk**: High (foundational change)

**Implementation**:

**Step 1: Add Soft Delete Fields**
```python
# File: apps/users/models.py
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Existing fields...

    # ✅ Soft delete infrastructure
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Soft delete flag - user marked for deletion"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when user was soft deleted"
    )
    deletion_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reason for account deletion (audit trail)"
    )

    # Custom managers
    objects = UserManager()  # Returns non-deleted users
    all_objects = models.Manager()  # Returns all users

    class Meta:
        indexes = [
            models.Index(fields=['is_deleted', 'date_joined']),
            models.Index(fields=['is_deleted', 'username']),
        ]

    def soft_delete(self, reason: str = '') -> None:
        """
        Soft delete user account (GDPR compliant).

        - Marks is_deleted=True
        - Sets deleted_at timestamp
        - Deactivates account (prevents login)
        - Anonymizes PII
        - Preserves community content

        Args:
            reason: Reason for deletion (audit trail)
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deletion_reason = reason
        self.is_active = False  # Prevent login
        self.save()

        # Anonymize personal data (GDPR)
        self.anonymize_personal_data()

    def anonymize_personal_data(self) -> None:
        """
        Remove PII while preserving content attribution.

        GDPR "right to be forgotten" compliance:
        - Removes name, email, personal identifiers
        - Generates anonymous username
        - Preserves user_id for content FK integrity
        """
        from hashlib import sha256

        # Generate anonymous identifier
        anon_id = sha256(f"user_{self.id}".encode()).hexdigest()[:8]

        # Clear PII
        self.first_name = ''
        self.last_name = ''
        self.email = f'deleted_{anon_id}@deleted.local'
        self.username = f'deleted_user_{anon_id}'

        # Clear optional profile data
        if hasattr(self, 'profile'):
            self.profile.bio = ''
            self.profile.avatar = None
            self.profile.save()

        self.save()

    def hard_delete(self) -> None:
        """
        Permanently delete user (GDPR "right to erasure").

        WARNING: This CASCADE deletes all related content.
        Use soft_delete() for normal account closure.
        """
        super().delete()

# Custom manager
class UserManager(models.Manager):
    """Manager that excludes soft-deleted users."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def include_deleted(self):
        """Include soft-deleted users in query."""
        return super().get_queryset()
```

**Step 2: Create Migration**
```python
# apps/users/migrations/0XXX_add_soft_delete.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0XXX_previous'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_deleted',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AddField(
            model_name='user',
            name='deleted_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='deletion_reason',
            field=models.CharField(max_length=255, blank=True, default=''),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(
                fields=['is_deleted', 'date_joined'],
                name='user_del_joined_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(
                fields=['is_deleted', 'username'],
                name='user_del_username_idx'
            ),
        ),
    ]
```

**Step 3: Update API Endpoints**
```python
# File: apps/api/viewsets/user.py

class UserViewSet(viewsets.ModelViewSet):
    """User management with soft delete support."""

    queryset = User.objects.all()  # Uses custom manager (excludes deleted)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def soft_delete(self, request, pk=None):
        """
        Soft delete user account (admin only).

        Request body:
            {
                "reason": "User requested account closure"
            }
        """
        user = self.get_object()
        reason = request.data.get('reason', 'Admin deletion')

        # Perform soft delete
        user.soft_delete(reason=reason)

        return Response({
            'message': f'User {user.username} soft deleted',
            'deleted_at': user.deleted_at,
            'anonymized': True,
            'reason': reason
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def hard_delete(self, request, pk=None):
        """
        Permanently delete user (GDPR "right to erasure").

        WARNING: This CASCADE deletes all user content.

        Requires explicit confirmation:
            {
                "confirm": "DELETE_PERMANENTLY"
            }
        """
        user = self.get_object()
        username = user.username

        # Require explicit confirmation
        if request.data.get('confirm') != 'DELETE_PERMANENTLY':
            return Response({
                'error': 'Must confirm with "confirm": "DELETE_PERMANENTLY"',
                'warning': 'This will CASCADE delete all user content'
            }, status=400)

        # Log the deletion (audit trail)
        import logging
        logger = logging.getLogger('user_management')
        logger.warning(
            f"HARD DELETE: User {username} (ID: {user.id}) permanently deleted by {request.user.username}"
        )

        # Permanent deletion
        user.hard_delete()

        return Response({
            'message': f'User {username} permanently deleted',
            'warning': 'All user content has been deleted'
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def restore(self, request, pk=None):
        """Restore soft-deleted user account."""
        # Use all_objects manager to find deleted users
        user = User.all_objects.get(pk=pk)

        if not user.is_deleted:
            return Response({
                'error': 'User is not deleted'
            }, status=400)

        # Restore user
        user.is_deleted = False
        user.deleted_at = None
        user.is_active = True
        user.save()

        return Response({
            'message': f'User {user.username} restored',
            'note': 'Personal data was anonymized and cannot be recovered'
        })
```

## Recommended Action

✅ **Option 1** - Soft delete infrastructure with custom manager

## Technical Details

**Affected Files**:
- `apps/users/models.py` - User model with soft delete fields
- `apps/api/viewsets/user.py` - Soft delete endpoints
- Migration file - Add soft delete fields

**Database Changes**:
- 3 new fields: is_deleted, deleted_at, deletion_reason
- 2 new indexes for performance

**Breaking Changes**: None (backward compatible)

## Acceptance Criteria

- [ ] Add is_deleted, deleted_at, deletion_reason fields to User model
- [ ] Create custom UserManager that excludes deleted users
- [ ] Implement soft_delete() method
- [ ] Implement anonymize_personal_data() method
- [ ] Add soft_delete API endpoint (admin only)
- [ ] Add hard_delete API endpoint with confirmation (admin only)
- [ ] Add restore API endpoint (admin only)
- [ ] Create and apply migration
- [ ] Add comprehensive tests
- [ ] Update admin interface to show deleted users
- [ ] All existing tests pass

## Testing Strategy

```python
def test_soft_delete_preserves_user():
    """Soft delete marks user but doesn't remove from database."""
    user = User.objects.create(username='testuser', email='test@example.com')
    user_id = user.id

    # Soft delete
    user.soft_delete(reason='Test deletion')

    # User marked as deleted
    user.refresh_from_db()
    assert user.is_deleted is True
    assert user.deleted_at is not None
    assert user.deletion_reason == 'Test deletion'
    assert user.is_active is False

    # User not in default queryset
    assert not User.objects.filter(id=user_id).exists()

    # But exists in all_objects
    assert User.all_objects.filter(id=user_id).exists()

def test_anonymize_personal_data():
    """Anonymization removes PII."""
    user = User.objects.create(
        username='john_doe',
        email='john@example.com',
        first_name='John',
        last_name='Doe'
    )

    user.anonymize_personal_data()
    user.refresh_from_db()

    # PII removed
    assert user.first_name == ''
    assert user.last_name == ''
    assert 'deleted_user_' in user.username
    assert '@deleted.local' in user.email

    # Username is anonymous but consistent
    assert len(user.username) > len('deleted_user_')

def test_soft_delete_preserves_content():
    """Soft deleted users' content remains accessible."""
    user = User.objects.create(username='author')
    post = Post.objects.create(poster=user, content='Important post')

    user.soft_delete()

    # Post still exists
    post.refresh_from_db()
    assert post.content == 'Important post'

def test_soft_delete_prevents_login():
    """Soft deleted users cannot log in."""
    user = User.objects.create(username='testuser')
    user.set_password('testpass')
    user.save()

    # Can log in before deletion
    client = Client()
    response = client.login(username='testuser', password='testpass')
    assert response is True

    # Soft delete
    user.soft_delete()

    # Cannot log in after deletion
    client = Client()
    response = client.login(username='testuser', password='testpass')
    assert response is False

def test_hard_delete_requires_confirmation():
    """Hard delete requires explicit confirmation."""
    user = User.objects.create(username='testuser')

    # Without confirmation
    response = client.post(f'/api/v1/users/{user.id}/hard_delete/', {})
    assert response.status_code == 400
    assert 'confirm' in response.json()['error']

    # With confirmation
    response = client.post(
        f'/api/v1/users/{user.id}/hard_delete/',
        {'confirm': 'DELETE_PERMANENTLY'}
    )
    assert response.status_code == 200

    # User permanently deleted
    assert not User.all_objects.filter(id=user.id).exists()

def test_restore_soft_deleted_user():
    """Soft deleted users can be restored."""
    user = User.objects.create(username='testuser')
    user.soft_delete()

    # Restore
    response = client.post(f'/api/v1/users/{user.id}/restore/')
    assert response.status_code == 200

    # User restored
    user.refresh_from_db()
    assert user.is_deleted is False
    assert user.is_active is True

    # Available in default queryset
    assert User.objects.filter(id=user.id).exists()
```

## Resources

- Soft delete patterns: https://docs.djangoproject.com/en/5.0/topics/db/managers/#custom-managers
- GDPR compliance: https://gdpr.eu/right-to-be-forgotten/
- Django managers: https://docs.djangoproject.com/en/5.0/topics/db/managers/

## Work Log

### 2025-10-20 - Data Integrity Review Discovery
**By:** Claude Code Data Integrity Guardian
**Actions:**
- Identified need for soft delete infrastructure
- Designed GDPR-compliant anonymization strategy
- Created as dependency for Todo #023
- Categorized as P1 foundational

**Learnings:**
- Soft delete is standard pattern for user accounts
- Custom managers enable clean separation
- Anonymization balances GDPR + community value

## Notes

- This is a **foundational** fix for Todo #023
- **GDPR critical** - enables "right to be forgotten"
- High complexity (8 hours)
- High risk (foundational model change)
- **BLOCKS**: Todo #023 (CASCADE delete fix)
- Should be completed in Phase 2 (Day 3)
- Test thoroughly on staging before production
- Consider data retention policies (purge after N days)
