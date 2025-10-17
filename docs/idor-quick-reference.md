# IDOR/BOLA Quick Reference Guide

**Quick access security patterns for Django REST Framework developers**

## The Three-Layer Defense Pattern

### Layer 1: Global Settings (settings.py)

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # No AllowAny!
    ],
}
```

### Layer 2: Filter QuerySets (List Views)

```python
def get_queryset(self):
    # Regular users see only their objects
    if not self.request.user.is_staff:
        return MyModel.objects.filter(owner=self.request.user)
    return MyModel.objects.all()
```

### Layer 3: Object Permissions (Detail Views)

```python
from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
```

## Common ViewSet Pattern

```python
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class MyModelViewSet(viewsets.ModelViewSet):
    serializer_class = MyModelSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """Filter to user's objects only."""
        return MyModel.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """Auto-assign owner on creation."""
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """Verify ownership before update."""
        if serializer.instance.owner != self.request.user:
            raise PermissionDenied("Cannot modify another user's object")
        serializer.save()
```

## Read-Only Owner Field in Serializer

```python
class MyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = ['id', 'title', 'content', 'owner']
        read_only_fields = ['owner']  # Prevent client modification
```

## Custom get_object() Pattern

```python
from django.shortcuts import get_object_or_404

def get_object(self):
    obj = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
    self.check_object_permissions(self.request, obj)  # REQUIRED
    return obj
```

## Testing Pattern

```python
import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_user_cannot_access_other_users_object(api_client, user_a, object_b):
    """User A should NOT access User B's object."""
    api_client.force_authenticate(user=user_a)
    response = api_client.get(f'/api/objects/{object_b.id}/')
    assert response.status_code in [403, 404]

@pytest.mark.django_db
def test_user_only_sees_own_objects_in_list(api_client, user_a, object_a, object_b):
    """List view should only show user's objects."""
    api_client.force_authenticate(user=user_a)
    response = api_client.get('/api/objects/')
    ids = [obj['id'] for obj in response.data['results']]
    assert str(object_a.id) in ids
    assert str(object_b.id) not in ids
```

## Security Checklist

### Every ViewSet Must Have:
- ✅ Authentication required (no `AllowAny` by default)
- ✅ `get_queryset()` filters by user
- ✅ Object-level permission class
- ✅ Auto-assign owner in `perform_create()`
- ✅ Owner field read-only in serializer

### Every Endpoint Must Be Tested:
- ✅ Unauthenticated access (should fail)
- ✅ User accessing own object (should succeed)
- ✅ User accessing other user's object (should fail)
- ✅ List view filtering (should only show own)
- ✅ Update/delete other user's object (should fail)

## Common Mistakes to Avoid

### ❌ DON'T: Use AllowAny as default
```python
# WRONG
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
}
```

### ❌ DON'T: Forget to filter querysets
```python
# WRONG - returns ALL objects
queryset = MyModel.objects.all()
```

### ❌ DON'T: Override get_object() without permission check
```python
# WRONG
def get_object(self):
    return MyModel.objects.get(pk=self.kwargs['pk'])  # No permission check!
```

### ❌ DON'T: Allow owner field modification
```python
# WRONG
class MySerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = ['id', 'owner']  # Owner is writable!
```

### ❌ DON'T: Trust client-provided user IDs
```python
# WRONG
user_id = request.data.get('user_id')
user = User.objects.get(id=user_id)  # Trusts client input
```

## Quick Security Review Questions

When reviewing code, ask:

1. **Can an unauthenticated user access this endpoint?**
   - If yes, is that intentional?

2. **Does get_queryset() filter by the authenticated user?**
   - If no, users can see others' data in list views

3. **Is there an object-level permission class?**
   - If no, users can access others' objects directly

4. **Is the owner field read-only or excluded?**
   - If no, users can hijack objects

5. **Are there tests for cross-user access attempts?**
   - If no, vulnerabilities won't be caught

## Resources

- **Full Guide:** `/docs/idor-bola-prevention-guide.md`
- **OWASP DRF Cheat Sheet:** https://cheatsheetseries.owasp.org/cheatsheets/Django_REST_Framework_Cheat_Sheet.html
- **DRF Permissions Docs:** https://www.django-rest-framework.org/api-guide/permissions/
- **OWASP API Security Top 10:** https://owasp.org/API-Security/

---

**When in doubt:** Filter by the authenticated user and check object permissions.
