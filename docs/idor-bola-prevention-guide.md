# IDOR/BOLA Prevention Guide for Django REST Framework

**Research Date:** October 2025
**Target:** Django REST Framework Applications
**Focus:** Insecure Direct Object Reference (IDOR) & Broken Object-Level Authorization (BOLA)

## Executive Summary

BOLA (Broken Object Level Authorization) is ranked #1 in OWASP API Security Top 10 (2023) as the most critical API security vulnerability. This guide provides industry-standard approaches, code examples, and testing strategies for Django REST Framework applications.

## Table of Contents

1. [Understanding IDOR/BOLA](#understanding-idorbola)
2. [Industry Standards & OWASP Guidelines](#industry-standards--owasp-guidelines)
3. [Django REST Framework Prevention Patterns](#django-rest-framework-prevention-patterns)
4. [Implementation Examples](#implementation-examples)
5. [Testing Strategies](#testing-strategies)
6. [Common Pitfalls](#common-pitfalls)
7. [Additional Resources](#additional-resources)

---

## Understanding IDOR/BOLA

### What is BOLA?

**Broken Object Level Authorization (BOLA)** occurs when an API improperly enforces authorization checks at the object level, allowing users to access or modify resources they don't own by manipulating object identifiers (IDs, GUIDs, tokens) in API requests.

### What is IDOR?

**Insecure Direct Object Reference (IDOR)** is a type of access control vulnerability where an application uses user-supplied input to access objects directly without proper authorization checks.

### Key Distinction

- **BOLA** is the broader vulnerability category (API-focused, OWASP API Top 10)
- **IDOR** is a specific attack pattern (web application-focused, OWASP Top 10)

Both require the same prevention approach: **object-level authorization checks**.

### Real-World Attack Scenarios

From OWASP API Security documentation:

1. **E-commerce Revenue Data**: Attackers identified API patterns like `/shops/{shopName}/revenue_data.json` and systematically replaced shop names to access unauthorized sales data.

2. **Vehicle Remote Access**: A manufacturer's API accepted Vehicle Identification Numbers without validating ownership, allowing attackers to control vehicles they didn't own.

3. **Document Deletion**: A GraphQL mutation deleted documents by ID without permission verification, enabling users to destroy other users' files.

---

## Industry Standards & OWASP Guidelines

### OWASP Prevention Strategies

From the [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/):

1. **Authorization Framework**: Implement a proper authorization mechanism that relies on user policies and hierarchy
2. **Consistent Validation**: Apply authorization checks across ALL functions that access database records using client-supplied input
3. **Unpredictable IDs**: Use random and unpredictable values (UUIDs/GUIDs) for record IDs instead of sequential integers
4. **Robust Testing**: Establish tests evaluating authorization robustness and prevent deploying changes that compromise these tests

### OWASP IDOR Prevention Cheat Sheet

From the [OWASP IDOR Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html):

**Primary Defense:**
- Implement access control checks for each object users try to access
- Determine the currently authenticated user from session information
- Use scoped database queries that filter by the authenticated user

**Defense-in-Depth:**
- Use complex identifiers (UUIDs, random strings) instead of sequential IDs
- Avoid exposing identifiers in URLs and POST bodies when possible
- Pass identifiers in sessions for multi-step flows to prevent tampering

**Vulnerable Pattern (Ruby on Rails example):**
```ruby
# VULNERABLE - searches all projects
@project = Project.find(params[:id])
```

**Secure Pattern:**
```ruby
# SECURE - restricts to user-accessible records
@project = @current_user.projects.find(params[:id])
```

### Django REST Framework OWASP Cheat Sheet

From the [Django REST Framework OWASP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Django_REST_Framework_Cheat_Sheet.html):

**Critical Requirements:**

1. **DO NOT** use `rest_framework.permissions.AllowAny` except for public API endpoints
2. **ALWAYS** change `DEFAULT_PERMISSION_CLASSES` from the permissive default
3. **ALWAYS** call `.check_object_permissions(request, obj)` when implementing object-level permissions
4. **NEVER** override `get_object()` without verifying the requesting user has legitimate access

---

## Django REST Framework Prevention Patterns

### Core Principle

Django provides strong built-in protections against IDOR when developers use the framework's standard access control mechanisms. Vulnerabilities occur when developers bypass these built-ins.

### Three-Layer Defense Strategy

#### Layer 1: Global Permission Configuration

**In `settings.py`:**

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}
```

This ensures:
- All endpoints require authentication by default
- No accidental public endpoints (unless explicitly marked)
- Consistent security baseline across the application

#### Layer 2: QuerySet Filtering (List Views)

**Filter querysets to show only user-accessible objects:**

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return only objects owned by the authenticated user.
        This prevents users from seeing other users' data in list views.
        """
        # For regular users, filter by owner
        if not self.request.user.is_staff:
            return Product.objects.filter(owner=self.request.user)

        # Staff can see all objects
        return Product.objects.all()

    def perform_create(self, serializer):
        """
        Automatically set the owner to the current user on creation.
        """
        serializer.save(owner=self.request.user)
```

**Why this is critical:**

DRF's generic views do NOT automatically apply object-level permissions to each instance in a queryset for performance reasons. You MUST filter the queryset yourself.

#### Layer 3: Object-Level Permissions (Detail Views)

**Custom permission class:**

```python
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.owner == request.user
```

**Apply to ViewSet:**

```python
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # Still filter queryset for list views
        return Product.objects.filter(owner=self.request.user)
```

**Manual `get_object()` override (when needed):**

```python
from django.shortcuts import get_object_or_404

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        """
        Override to add custom object retrieval logic.
        CRITICAL: Must call check_object_permissions!
        """
        # Get the object
        obj = get_object_or_404(
            self.get_queryset(),
            pk=self.kwargs["pk"]
        )

        # REQUIRED: Check object-level permissions
        self.check_object_permissions(self.request, obj)

        return obj
```

---

## Implementation Examples

### Example 1: Simple Owner-Based Access

**Model:**
```python
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Document(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
```

**ViewSet:**
```python
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners to access their documents.
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        Users can only see their own documents.
        """
        return Document.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically assign owner on creation.
        """
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """
        Verify ownership before update (defense-in-depth).
        """
        if serializer.instance.owner != self.request.user:
            raise PermissionDenied("You cannot modify another user's document.")
        serializer.save()

    def perform_destroy(self, instance):
        """
        Verify ownership before deletion (defense-in-depth).
        """
        if instance.owner != self.request.user:
            raise PermissionDenied("You cannot delete another user's document.")
        instance.delete()
```

### Example 2: Role-Based Access with Shared Resources

**Model with multiple access patterns:**
```python
class Project(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    members = models.ManyToManyField(User, related_name='member_projects', blank=True)
    is_public = models.BooleanField(default=False)

    def can_view(self, user):
        """Business logic for view access."""
        return (
            self.is_public or
            self.owner == user or
            user in self.members.all() or
            user.is_staff
        )

    def can_edit(self, user):
        """Business logic for edit access."""
        return (
            self.owner == user or
            user in self.members.all() or
            user.is_staff
        )
```

**Custom permissions:**
```python
class ProjectPermission(permissions.BasePermission):
    """
    Complex permission logic for projects.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions
        if request.method in permissions.SAFE_METHODS:
            return obj.can_view(request.user)

        # Write permissions
        return obj.can_edit(request.user)
```

**ViewSet:**
```python
from django.db.models import Q

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, ProjectPermission]

    def get_queryset(self):
        """
        Filter queryset based on user access:
        - Public projects
        - Projects owned by user
        - Projects where user is a member
        - All projects for staff
        """
        user = self.request.user

        if user.is_staff:
            return Project.objects.all()

        return Project.objects.filter(
            Q(is_public=True) |
            Q(owner=user) |
            Q(members=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
```

### Example 3: Django Guardian Integration (Fine-Grained Object Permissions)

**Installation:**
```bash
pip install django-guardian
```

**Settings:**
```python
INSTALLED_APPS = [
    # ...
    'guardian',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]
```

**Custom permission class:**
```python
from rest_framework import permissions
from guardian.shortcuts import get_objects_for_user

class CustomObjectPermissions(permissions.DjangoObjectPermissions):
    """
    Enhanced permission class using django-guardian.
    """
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def has_object_permission(self, request, view, obj):
        model_cls = obj.__class__
        user = request.user
        perms = self.get_required_object_permissions(request.method, model_cls)

        # Check if user has the required permissions on this specific object
        for perm in perms:
            if not user.has_perm(perm, obj):
                return False

        return True
```

**ViewSet with Guardian:**
```python
from rest_framework import viewsets
from rest_framework_guardian import filters
from guardian.shortcuts import assign_perm, get_objects_for_user

class ArticleViewSet(viewsets.ModelViewSet):
    serializer_class = ArticleSerializer
    permission_classes = [CustomObjectPermissions]
    filter_backends = [filters.ObjectPermissionsFilter]

    def get_queryset(self):
        """
        Guardian's filter returns only objects the user has permission to view.
        """
        return get_objects_for_user(
            self.request.user,
            'articles.view_article',
            klass=Article
        )

    def perform_create(self, serializer):
        """
        Automatically assign permissions to creator.
        """
        article = serializer.save(author=self.request.user)

        # Assign all permissions to the creator
        assign_perm('view_article', self.request.user, article)
        assign_perm('change_article', self.request.user, article)
        assign_perm('delete_article', self.request.user, article)
```

### Example 4: Handling Anonymous Users

**Problem:** `get_queryset()` can fail if it expects authenticated users but DRF calls it during permission checks with anonymous users.

**Solution:**
```python
class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        Handle anonymous users gracefully.
        """
        # Return empty queryset for anonymous users
        if not self.request.user.is_authenticated:
            return Document.objects.none()

        # Return user's documents for authenticated users
        return Document.objects.filter(owner=self.request.user)
```

**Alternative approach - order permissions correctly:**
```python
class DocumentViewSet(viewsets.ModelViewSet):
    # IsAuthenticated first ensures user is authenticated before other checks
    permission_classes = [permissions.IsAuthenticated, IsOwner]
```

### Example 5: Using UUIDs Instead of Sequential IDs

**Model with UUID primary key:**
```python
import uuid
from django.db import models

class SecureDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # Still need authorization checks!
    # UUIDs are defense-in-depth, not primary security
```

**Benefits:**
- Prevents enumeration attacks (can't guess `/api/documents/1/`, `/api/documents/2/`)
- Makes exploitation harder but DOES NOT replace authorization checks

**Important:** UUIDs are a defense-in-depth measure. You MUST still implement proper authorization checks.

---

## Testing Strategies

### Manual Testing for IDOR/BOLA

From OWASP guidelines, the testing approach involves:

1. **Create Test Users:**
   - User A (normal user)
   - User B (normal user)
   - Admin User (optional)

2. **Test Scenario:**
   - Authenticate as User A
   - Retrieve an object owned by User A via API (note the object ID)
   - Modify the object ID in the request to reference an object owned by User B
   - **Expected:** Request should fail with 403 Forbidden or 404 Not Found
   - **Vulnerability:** If request succeeds and returns User B's data, BOLA exists

3. **Test All HTTP Methods:**
   - GET (read access)
   - PUT/PATCH (update access)
   - DELETE (delete access)
   - POST (if object IDs are used in creation)

### Automated Testing with Pytest

**Install dependencies:**
```bash
pip install pytest pytest-django django-rest-framework
```

**Basic IDOR test structure:**

```python
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from myapp.models import Document

User = get_user_model()

@pytest.fixture
def api_client():
    """Provide an API client for testing."""
    return APIClient()

@pytest.fixture
def user_a(db):
    """Create test user A."""
    return User.objects.create_user(
        username='user_a',
        email='user_a@example.com',
        password='testpass123'
    )

@pytest.fixture
def user_b(db):
    """Create test user B."""
    return User.objects.create_user(
        username='user_b',
        email='user_b@example.com',
        password='testpass123'
    )

@pytest.fixture
def document_a(user_a):
    """Create document owned by user A."""
    return Document.objects.create(
        title='User A Document',
        content='Private content',
        owner=user_a
    )

@pytest.fixture
def document_b(user_b):
    """Create document owned by user B."""
    return Document.objects.create(
        title='User B Document',
        content='Private content',
        owner=user_b
    )

@pytest.mark.django_db
class TestDocumentIDOR:
    """Test suite for IDOR vulnerabilities in Document API."""

    def test_user_cannot_read_other_users_document(self, api_client, user_a, document_b):
        """Test that User A cannot read User B's document."""
        # Authenticate as User A
        api_client.force_authenticate(user=user_a)

        # Try to access User B's document
        response = api_client.get(f'/api/documents/{document_b.id}/')

        # Should be denied (403 Forbidden or 404 Not Found)
        assert response.status_code in [403, 404], \
            "User should not be able to access another user's document"

    def test_user_cannot_update_other_users_document(self, api_client, user_a, document_b):
        """Test that User A cannot update User B's document."""
        api_client.force_authenticate(user=user_a)

        response = api_client.patch(
            f'/api/documents/{document_b.id}/',
            {'title': 'Hacked Title'}
        )

        assert response.status_code in [403, 404], \
            "User should not be able to update another user's document"

        # Verify document was not modified
        document_b.refresh_from_db()
        assert document_b.title == 'User B Document'

    def test_user_cannot_delete_other_users_document(self, api_client, user_a, document_b):
        """Test that User A cannot delete User B's document."""
        api_client.force_authenticate(user=user_a)

        response = api_client.delete(f'/api/documents/{document_b.id}/')

        assert response.status_code in [403, 404], \
            "User should not be able to delete another user's document"

        # Verify document still exists
        assert Document.objects.filter(id=document_b.id).exists()

    def test_user_can_access_own_document(self, api_client, user_a, document_a):
        """Test that User A CAN access their own document."""
        api_client.force_authenticate(user=user_a)

        response = api_client.get(f'/api/documents/{document_a.id}/')

        assert response.status_code == 200
        assert response.data['title'] == document_a.title

    def test_user_only_sees_own_documents_in_list(
        self, api_client, user_a, document_a, document_b
    ):
        """Test that list view only shows user's own documents."""
        api_client.force_authenticate(user=user_a)

        response = api_client.get('/api/documents/')

        assert response.status_code == 200

        # Should only see their own document
        document_ids = [doc['id'] for doc in response.data['results']]
        assert str(document_a.id) in document_ids
        assert str(document_b.id) not in document_ids

    def test_unauthenticated_user_cannot_access_documents(
        self, api_client, document_a
    ):
        """Test that anonymous users cannot access documents."""
        # Don't authenticate
        response = api_client.get(f'/api/documents/{document_a.id}/')

        assert response.status_code == 401, \
            "Unauthenticated users should be denied access"
```

### Advanced Testing: Parameter Tampering

```python
@pytest.mark.django_db
class TestParameterTampering:
    """Test for parameter manipulation attacks."""

    def test_cannot_change_owner_on_update(self, api_client, user_a, user_b, document_a):
        """Test that users cannot change document owner via API."""
        api_client.force_authenticate(user=user_a)

        # Try to change owner to User B
        response = api_client.patch(
            f'/api/documents/{document_a.id}/',
            {'owner': user_b.id}  # Attempt to transfer ownership
        )

        # Even if request succeeds, owner should not change
        document_a.refresh_from_db()
        assert document_a.owner == user_a, \
            "Owner field should not be modifiable by users"

    def test_cannot_set_owner_on_create(self, api_client, user_a, user_b):
        """Test that users cannot specify owner on creation."""
        api_client.force_authenticate(user=user_a)

        response = api_client.post(
            '/api/documents/',
            {
                'title': 'New Document',
                'content': 'Content',
                'owner': user_b.id  # Try to create as User B
            }
        )

        if response.status_code == 201:
            document = Document.objects.get(id=response.data['id'])
            assert document.owner == user_a, \
                "Owner should be set to authenticated user, not request parameter"
```

### Security Test Checklist

Create a comprehensive test checklist:

```python
"""
IDOR/BOLA Security Test Checklist
=================================

For each API endpoint that handles objects:

[ ] Test unauthenticated access (should be denied)
[ ] Test authenticated user accessing own object (should succeed)
[ ] Test authenticated user accessing other user's object (should fail)
[ ] Test authenticated user listing objects (should only see own)
[ ] Test authenticated user updating other user's object (should fail)
[ ] Test authenticated user deleting other user's object (should fail)
[ ] Test parameter tampering (owner field, etc.)
[ ] Test role escalation (normal user accessing admin resources)
[ ] Test ID enumeration (sequential ID guessing)
[ ] Test filter bypasses (e.g., ?owner=other_user)
"""
```

---

## Common Pitfalls

### Pitfall 1: Only Checking Permissions at Endpoint Level

**Vulnerable:**
```python
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()  # VULNERABLE - returns ALL documents
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]  # Only checks authentication, not ownership
```

**Secure:**
```python
class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)
```

### Pitfall 2: Forgetting to Filter List Views

**Problem:**
```python
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    permission_classes = [IsOwner]  # Only applies to detail views!
```

DRF does NOT apply `has_object_permission` to list views for performance reasons.

**Solution:**
Always filter the queryset in `get_queryset()`.

### Pitfall 3: Overriding `get_object()` Without Permission Checks

**Vulnerable:**
```python
def get_object(self):
    return Document.objects.get(pk=self.kwargs['pk'])  # NO PERMISSION CHECK
```

**Secure:**
```python
def get_object(self):
    obj = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
    self.check_object_permissions(self.request, obj)  # REQUIRED
    return obj
```

### Pitfall 4: Allowing Owner Field Modification

**Vulnerable serializer:**
```python
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'content', 'owner']  # Owner is writable!
```

**Secure serializer:**
```python
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'content', 'owner']
        read_only_fields = ['owner']  # Prevent modification
```

Or exclude it entirely:
```python
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'content']  # Don't expose owner field
```

### Pitfall 5: Using `AllowAny` Inappropriately

**Vulnerable:**
```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # DANGEROUS DEFAULT
    ],
}
```

**Secure:**
```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Only use AllowAny for specific public endpoints
class PublicContentView(APIView):
    permission_classes = [AllowAny]  # Intentionally public
```

### Pitfall 6: Trusting Client-Provided IDs

**Vulnerable:**
```python
def add_member(self, request, pk=None):
    project = self.get_object()
    user_id = request.data.get('user_id')
    user = User.objects.get(id=user_id)  # Trusts client input
    project.members.add(user)
```

**Secure:**
```python
def add_member(self, request, pk=None):
    project = self.get_object()

    # Verify requester can add members
    if project.owner != request.user:
        raise PermissionDenied("Only owner can add members")

    user_id = request.data.get('user_id')

    # Validate user exists and is eligible
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        raise ValidationError("Invalid user")

    project.members.add(user)
```

### Pitfall 7: Bypassing Built-in Django Security

**Don't do this:**
```python
# Raw SQL queries bypass Django's ORM protections
def get_queryset(self):
    return Document.objects.raw(
        f"SELECT * FROM documents WHERE id = {self.kwargs['pk']}"
    )  # SQL injection risk + no authorization
```

**Use Django ORM:**
```python
def get_queryset(self):
    return Document.objects.filter(owner=self.request.user)
```

---

## Additional Resources

### Official Documentation

1. **Django REST Framework Permissions**
   - URL: https://www.django-rest-framework.org/api-guide/permissions/
   - Coverage: Permission classes, custom permissions, object-level permissions

2. **OWASP API Security Top 10 (2023)**
   - URL: https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/
   - Coverage: BOLA definition, attack scenarios, prevention

3. **OWASP Django REST Framework Cheat Sheet**
   - URL: https://cheatsheetseries.owasp.org/cheatsheets/Django_REST_Framework_Cheat_Sheet.html
   - Coverage: DRF-specific security best practices

4. **OWASP IDOR Prevention Cheat Sheet**
   - URL: https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html
   - Coverage: General IDOR prevention techniques

5. **Django Security Documentation**
   - URL: https://docs.djangoproject.com/en/5.2/topics/security/
   - Coverage: Django's built-in security features

### Testing Resources

6. **TestDriven.io - DRF Permissions**
   - URL: https://testdriven.io/blog/drf-permissions/
   - Coverage: Comprehensive guide to DRF permission testing

7. **OWASP Testing Guide - IDOR**
   - URL: https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References
   - Coverage: Manual testing methodology

8. **Pytest with Django REST Framework**
   - URL: https://pytest-with-eric.com/pytest-advanced/pytest-django-restapi-testing/
   - Coverage: Comprehensive pytest testing guide

### Libraries & Tools

9. **django-guardian**
   - GitHub: https://github.com/django-guardian/django-guardian
   - Docs: https://django-guardian.readthedocs.io/
   - Purpose: Per-object permissions for Django

10. **django-rest-framework-guardian**
    - GitHub: https://github.com/rpkilby/django-rest-framework-guardian
    - Purpose: DRF integration for django-guardian

11. **django-rules**
    - GitHub: https://github.com/dfunckt/django-rules
    - Purpose: Object-level permissions without database overhead

### Security Guides

12. **StackHawk - Django Security**
    - Blog: https://www.stackhawk.com/blog/django-broken-object-level-authorization-guide-examples-and-prevention/
    - Coverage: Django-specific BOLA prevention

13. **Snyk - IDOR in Python**
    - URL: https://snyk.io/blog/insecure-direct-object-references-python/
    - Coverage: Python/Django IDOR patterns

14. **PortSwigger Web Security Academy - IDOR**
    - URL: https://portswigger.net/web-security/access-control/idor
    - Coverage: Interactive labs and examples

### Community Resources

15. **Stack Overflow - DRF Object Permissions**
    - URL: https://stackoverflow.com/questions/18645175/django-rest-framework-object-level-permissions
    - Coverage: Real-world implementation questions

16. **Medium - Best Practices for Securing DRF APIs**
    - URL: https://medium.com/@daniel.doody/best-practices-for-securing-django-rest-framework-apis-9dbb7ba367a8
    - Coverage: Comprehensive security checklist

### Real-World Examples

17. **Open edX Permissions Architecture**
    - URL: https://docs.openedx.org/projects/openedx-proposals/en/latest/archived/oep-0009-bp-permissions.html
    - Coverage: Large-scale Django permission system

### Security Testing Tools

18. **Burp Suite**
    - URL: https://portswigger.net/burp
    - Purpose: Manual security testing, IDOR detection

19. **OWASP ZAP**
    - URL: https://www.zaproxy.org/
    - Purpose: Automated security scanning

20. **Postman/Newman**
    - URL: https://www.postman.com/
    - Purpose: API testing with automated security checks

---

## Summary Checklist

Use this checklist for every API endpoint:

### Configuration
- [ ] `DEFAULT_PERMISSION_CLASSES` set to `IsAuthenticated` or stricter
- [ ] `DEFAULT_AUTHENTICATION_CLASSES` properly configured
- [ ] No `AllowAny` except for intentionally public endpoints

### ViewSet/APIView
- [ ] `get_queryset()` filters by authenticated user
- [ ] Custom permission class implements `has_object_permission()`
- [ ] `perform_create()` automatically sets owner field
- [ ] `perform_update()`/`perform_destroy()` include ownership checks
- [ ] Manual `get_object()` calls `check_object_permissions()`

### Serializer
- [ ] Owner field marked as `read_only` or excluded
- [ ] No sensitive fields exposed unnecessarily
- [ ] Validation prevents unauthorized field modifications

### Testing
- [ ] Unit tests for each permission class
- [ ] Integration tests for IDOR scenarios (cross-user access)
- [ ] Tests for unauthenticated access
- [ ] Tests for parameter tampering
- [ ] Tests for list view filtering

### Defense-in-Depth
- [ ] Consider UUIDs for primary keys (enumeration defense)
- [ ] Rate limiting implemented (prevent brute-force)
- [ ] Logging of access attempts (detection)
- [ ] Consider django-guardian for complex permissions

---

## Conclusion

IDOR/BOLA prevention in Django REST Framework requires a **defense-in-depth approach**:

1. **Global defaults** ensure baseline security
2. **QuerySet filtering** protects list views
3. **Object-level permissions** protect detail views
4. **Comprehensive testing** validates implementation
5. **Code review** catches oversights

Django and DRF provide excellent built-in protections—the key is using them correctly and consistently. When in doubt, **filter by the authenticated user** and **always check object permissions**.

---

**Document Version:** 1.0
**Last Updated:** October 2025
**Maintained By:** Security Team
