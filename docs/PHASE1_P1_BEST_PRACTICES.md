# Phase 1 P1 Best Practices Research

**Compiled**: 2025-10-20
**Purpose**: Comprehensive best practices documentation for Phase 1 P1 todos
**Scope**: Security, Data Integrity, Accessibility, Performance, Architecture, Code Quality

---

## Table of Contents

1. [Security Best Practices](#1-security-best-practices)
2. [Data Integrity Best Practices](#2-data-integrity-best-practices)
3. [Accessibility Best Practices](#3-accessibility-best-practices)
4. [Performance Best Practices](#4-performance-best-practices)
5. [Architecture Best Practices](#5-architecture-best-practices)
6. [Code Quality Best Practices](#6-code-quality-best-practices)
7. [Testing Strategies](#7-testing-strategies)
8. [Common Pitfalls](#8-common-pitfalls)

---

## 1. Security Best Practices

### 1.1 SQL Injection Prevention

**Authority**: Django Official Documentation, OWASP Foundation
**Severity**: Critical (OWASP A03:2021 - Injection)

#### Official Django Guidance

Django's ORM automatically protects against SQL injection through parameterized queries. However, several legacy APIs bypass this protection and must be avoided.

#### Must-Follow Patterns

**✅ SAFE - Use Django ORM**
```python
# Django ORM uses parameterized queries automatically
User.objects.filter(username=user_input)
Course.objects.get(id=course_id)

# Annotations are safe
from django.db.models.functions import TruncDate
queryset.annotate(date=TruncDate('created_at'))
```

**✅ SAFE - Raw SQL with Parameters**
```python
from django.db import connection

# CORRECT: Parameters passed separately (safe)
with connection.cursor() as cursor:
    cursor.execute("SELECT * FROM users WHERE username = %s", [user_input])

# CORRECT: Using RawSQL with parameters
from django.db.models.expressions import RawSQL
queryset.annotate(
    custom_field=RawSQL("SELECT COUNT(*) FROM table WHERE id = %s", (id,))
)
```

**❌ DANGEROUS - Deprecated .extra() Method**
```python
# NEVER USE: .extra() is deprecated and unsafe
queryset.extra(select={'date': 'date(created_at)'})  # SQL injection vector
queryset.extra(where=['name=%s'], params=[name])      # Still dangerous

# REASON: Django plans to remove .extra() entirely
# SOURCE: Django 5.0+ deprecation timeline
```

**❌ DANGEROUS - String Formatting in SQL**
```python
# NEVER USE: String interpolation in SQL
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # SQL injection!
cursor.execute("SELECT * FROM users WHERE id = '%s'" % user_id)  # Injection!
User.objects.raw("SELECT * FROM users WHERE name = '" + name + "'")  # Unsafe!
```

#### Migration Path: .extra() to Modern ORM

| Old Pattern (.extra()) | Modern Alternative | Performance |
|----------------------|-------------------|-------------|
| `.extra(select={'date': 'date(created_at)'})` | `.annotate(date=TruncDate('created_at'))` | Same or better |
| `.extra(where=['status=%s'], params=['active'])` | `.filter(status='active')` | Better (optimizer aware) |
| `.extra(order_by=['RAND()'])` | `.order_by('?')` | Same |
| `.extra(tables=['other_table'])` | Use explicit JOINs or subqueries | Better (explicit) |

#### Recent Security Updates (October 2025)

**CVE-2025-XXXX**: Django issued security releases (5.2.7, 5.1.13, 4.2.25) for SQL injection in `QuerySet.annotate()`, `alias()`, `aggregate()`, and `extra()` when using dictionary expansion on MySQL/MariaDB.

**Impact**: Dictionary keys can inject SQL on MySQL databases
**Fix**: Update Django immediately, avoid user-controlled dictionary keys

```python
# VULNERABLE (October 2025 CVE)
user_dict = {'malicious': 'injected_sql'}
queryset.annotate(**user_dict)  # SQL injection on MySQL!

# SAFE: Never use user-controlled keys
safe_dict = {'count': Count('id')}  # Hardcoded keys only
queryset.annotate(**safe_dict)
```

#### Resources

- **Django Security**: https://docs.djangoproject.com/en/5.2/topics/security/
- **OWASP SQL Injection**: https://owasp.org/www-community/attacks/SQL_Injection
- **Django Security Releases**: https://www.djangoproject.com/weblog/2025/oct/01/security-releases/

---

### 1.2 Race Conditions & Transaction Management

**Authority**: Django Official Documentation, PostgreSQL Best Practices
**Severity**: High (Data corruption, revenue loss)

#### Understanding Race Conditions

Race conditions occur when multiple concurrent operations access shared data without proper synchronization, leading to:

- **Duplicate records** (same user enrolled twice)
- **Violated constraints** (exceed max_students limit)
- **Lost updates** (counter increments lost)
- **Data inconsistency** (stale reads)

#### Django Transaction Patterns

**Pattern 1: Pessimistic Locking with select_for_update()**

Best for: High-contention scenarios where conflicts are likely

```python
from django.db import transaction
from django.db.models import F

@transaction.atomic
def enroll_in_course(user, course_id):
    """
    Atomic enrollment with pessimistic locking.

    Prevents race conditions by locking the course row until
    transaction completes (COMMIT or ROLLBACK).
    """
    # Lock course row (other transactions wait)
    course = Course.objects.select_for_update().get(id=course_id)

    # Check capacity (safe - we hold the lock)
    if course.enrollments.count() >= course.max_students:
        raise CourseFullError("Course is full")

    # Create enrollment atomically
    enrollment, created = CourseEnrollment.objects.get_or_create(
        user=user,
        course=course,
        defaults={'enrolled_at': timezone.now()}
    )

    if not created:
        raise AlreadyEnrolledError("User already enrolled")

    # Update counter using F() expression (database-level increment)
    course.enrollments_count = F('enrollments_count') + 1
    course.save(update_fields=['enrollments_count'])

    return enrollment
```

**Pattern 2: Optimistic Locking with F() Expressions**

Best for: Low-contention scenarios, better performance

```python
from django.db.models import F

def increment_view_count(article_id):
    """
    Atomic counter increment without locking.

    F() expressions are evaluated at database level,
    preventing race conditions on counter updates.
    """
    # ✅ SAFE: Database-level atomic increment
    Article.objects.filter(id=article_id).update(
        views=F('views') + 1
    )

    # ❌ UNSAFE: Race condition!
    # article = Article.objects.get(id=article_id)
    # article.views += 1  # Lost updates possible!
    # article.save()
```

**Pattern 3: Database Constraints (Defense in Depth)**

```python
# Model definition
class CourseEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Database-level uniqueness constraint
        unique_together = [['user', 'course']]
        indexes = [
            models.Index(fields=['user', 'course']),  # Performance
        ]

# Migration
python manage.py makemigrations
python manage.py migrate

# In view (handle constraint violation)
from django.db import IntegrityError

try:
    enrollment = CourseEnrollment.objects.create(user=user, course=course)
except IntegrityError:
    # Duplicate prevented by database
    return JsonResponse({'error': 'Already enrolled'}, status=400)
```

#### select_for_update() Options

```python
# Default: Block until lock acquired
course = Course.objects.select_for_update().get(id=course_id)

# Skip locked rows (fail fast)
course = Course.objects.select_for_update(skip_locked=True).get(id=course_id)

# Raise exception if locked (don't wait)
course = Course.objects.select_for_update(nowait=True).get(id=course_id)

# Lock related objects too (for foreign keys)
course = Course.objects.select_for_update(of=('self', 'instructor')).get(id=course_id)
```

#### Transaction Isolation Levels

Django defaults to **READ COMMITTED** isolation:

```python
# Change isolation level (if needed)
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
    # ... critical operations ...
```

| Isolation Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads | Use Case |
|----------------|-------------|---------------------|---------------|----------|
| READ UNCOMMITTED | Possible | Possible | Possible | Analytics (unsafe for transactions) |
| READ COMMITTED (Django default) | No | Possible | Possible | Most web applications |
| REPEATABLE READ | No | No | Possible | Financial transactions |
| SERIALIZABLE | No | No | No | Critical operations (slowest) |

#### Common Pitfalls

**Pitfall 1: Transaction Scope Too Small**
```python
# ❌ WRONG: Lock released before operation completes
course = Course.objects.select_for_update().get(id=course_id)
# Lock released here! ⚠️

if course.enrollments.count() >= course.max_students:
    raise Error("Full")  # Race condition - lock already released!
```

```python
# ✅ CORRECT: Lock held until transaction ends
@transaction.atomic
def enroll(user, course_id):
    course = Course.objects.select_for_update().get(id=course_id)
    # Lock held until function returns
    if course.enrollments.count() >= course.max_students:
        raise Error("Full")  # Safe - still holding lock
```

**Pitfall 2: Forgot @transaction.atomic**
```python
# ❌ ERROR: select_for_update() outside transaction
def enroll(user, course_id):
    course = Course.objects.select_for_update().get(id=course_id)
    # TransactionManagementError: select_for_update requires a transaction!
```

**Pitfall 3: Deadlock Risk**
```python
# ⚠️ DEADLOCK RISK: Different lock order in different transactions
# Transaction A:
with transaction.atomic():
    course = Course.objects.select_for_update().get(id=1)
    user = User.objects.select_for_update().get(id=1)

# Transaction B (concurrent):
with transaction.atomic():
    user = User.objects.select_for_update().get(id=1)  # Locks user first
    course = Course.objects.select_for_update().get(id=1)  # Waits for course
    # DEADLOCK! A holds course, waits for user. B holds user, waits for course.

# ✅ SOLUTION: Always lock in same order
# Both transactions:
with transaction.atomic():
    user = User.objects.select_for_update().get(id=1)  # Always lock user first
    course = Course.objects.select_for_update().get(id=1)  # Then course
```

#### Resources

- **Django Transactions**: https://docs.djangoproject.com/en/5.2/topics/db/transactions/
- **select_for_update**: https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update
- **PostgreSQL Locking**: https://www.postgresql.org/docs/current/explicit-locking.html

---

## 2. Data Integrity Best Practices

### 2.1 Mutable Default Arguments

**Authority**: Python Official Documentation, Django Model Best Practices
**Severity**: Critical (Silent data corruption)

#### The Problem

Python evaluates default arguments **once** at function definition time, not at call time. Mutable defaults (lists, dicts) are shared across all function calls.

```python
# ❌ WRONG: Shared mutable default
def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags

print(add_tag('python'))  # ['python']
print(add_tag('django'))  # ['python', 'django'] ⚠️ UNEXPECTED!
print(add_tag('react'))   # ['python', 'django', 'react'] ⚠️ BUG!
```

#### Django Model Pattern

**❌ WRONG: Mutable Default Object**
```python
class Exercise(models.Model):
    # ⚠️ BUG: All instances share same dict/list!
    solutions = models.JSONField(default={})
    tags = models.JSONField(default=[])

# Result: Changes to one instance affect ALL instances
exercise1 = Exercise.objects.create(title="Ex 1")
exercise1.solutions['answer'] = '42'
exercise1.save()

exercise2 = Exercise.objects.create(title="Ex 2")
print(exercise2.solutions)  # {'answer': '42'} ⚠️ SHARED!
```

**✅ CORRECT: Callable Default**
```python
class Exercise(models.Model):
    # ✅ Use callable - returns fresh object each time
    solutions = models.JSONField(default=dict)  # NOT dict()
    tags = models.JSONField(default=list)       # NOT []

    # For complex defaults, use function
    def _default_config():
        return {
            'max_attempts': 3,
            'hints_enabled': True,
            'time_limit': 300
        }

    config = models.JSONField(default=_default_config)
```

#### Django Enforcement (5.0+)

Django 5.0+ includes a system check that raises warnings for non-callable JSONField defaults:

```python
# Django checks this at startup
class Exercise(models.Model):
    solutions = models.JSONField(default={})
    # SystemCheckError: fields.E010
    # JSONField default should be a callable instead of an instance
```

#### Lambda vs Named Function

```python
# ❌ WRONG: Lambda not serializable in migrations
default = models.JSONField(default=lambda: {'key': 'value'})
# Error: Cannot serialize lambda functions

# ✅ CORRECT: Named function (serializable)
def default_settings():
    return {'key': 'value'}

settings = models.JSONField(default=default_settings)
```

#### Testing for Mutable Defaults

```python
def test_no_shared_defaults():
    """Ensure JSONField defaults are not shared between instances."""
    ex1 = Exercise.objects.create(title="Ex 1")
    ex1.solutions['answer'] = 'A'
    ex1.save()

    ex2 = Exercise.objects.create(title="Ex 2")

    # Must be independent
    assert 'answer' not in ex2.solutions, \
        "Mutable default shared between instances!"
```

#### Resources

- **Django JSONField**: https://docs.djangoproject.com/en/5.2/ref/models/fields/#jsonfield
- **Python Mutable Defaults**: https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments
- **Django Ticket #31930**: https://code.djangoproject.com/ticket/31930

---

### 2.2 Soft Delete Implementation

**Authority**: Django Safedelete, Industry Best Practices
**Severity**: High (Data loss prevention, GDPR compliance)

#### Why Soft Delete?

Soft delete marks records as deleted without removing them from the database, enabling:

- **Data recovery** (undo deletions)
- **Audit trails** (who deleted what, when)
- **GDPR compliance** (right to be forgotten tracking)
- **Cascading soft deletes** (preserve referential integrity)

#### Implementation Pattern

**Basic Soft Delete Model**
```python
from django.db import models
from django.utils import timezone

class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet that filters out soft-deleted objects."""

    def delete(self):
        """Soft delete all objects in queryset."""
        return self.update(
            deleted_at=timezone.now(),
            is_deleted=True
        )

    def hard_delete(self):
        """Permanently delete objects (use with caution)."""
        return super().delete()

    def alive(self):
        """Return only non-deleted objects."""
        return self.filter(is_deleted=False)

    def dead(self):
        """Return only deleted objects."""
        return self.filter(is_deleted=True)

    def with_deleted(self):
        """Return all objects (including deleted)."""
        return self


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted objects by default."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted_only(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=True)


class SoftDeleteModel(models.Model):
    """Abstract base class for soft-deletable models."""

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'users.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s_deleted'
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Access to all objects (including deleted)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard=False, deleted_by=None):
        """
        Soft delete by default, with hard delete option.

        Args:
            using: Database alias
            keep_parents: Keep parent records (for multi-table inheritance)
            hard: If True, permanently delete (DANGEROUS)
            deleted_by: User who performed deletion (for audit trail)
        """
        if hard:
            # Permanent deletion
            return super().delete(using=using, keep_parents=keep_parents)

        # Soft delete
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

        # Cascade soft delete to related objects
        self._cascade_soft_delete()

    def restore(self):
        """Restore soft-deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def _cascade_soft_delete(self):
        """
        Cascade soft delete to related objects.

        Finds all ForeignKeys with on_delete=CASCADE pointing to this model
        and soft-deletes them if they inherit from SoftDeleteModel.
        """
        from django.db.models import CASCADE

        for related_object in self._meta.related_objects:
            if related_object.on_delete == CASCADE:
                # Get related objects
                related_name = related_object.get_accessor_name()
                related_manager = getattr(self, related_name, None)

                if related_manager:
                    related_model = related_object.related_model

                    # Only cascade if related model supports soft delete
                    if issubclass(related_model, SoftDeleteModel):
                        related_manager.update(
                            is_deleted=True,
                            deleted_at=timezone.now()
                        )
```

**Usage Example**
```python
class Post(SoftDeleteModel):
    """Blog post with soft delete support."""
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)


class Comment(SoftDeleteModel):
    """Comment with cascading soft delete."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    text = models.TextField()


# Using soft delete
post = Post.objects.get(id=1)
post.delete(deleted_by=request.user)  # Soft delete
# Comments are automatically soft-deleted (CASCADE)

# Query only active posts
active_posts = Post.objects.all()  # Excludes deleted

# Query deleted posts
deleted_posts = Post.deleted_only()

# Query all posts (including deleted)
all_posts = Post.all_objects.all()

# Restore
post.restore()
```

#### CASCADE Behavior

**Django's on_delete Options with Soft Delete**

| on_delete Value | Soft Delete Behavior | Recommendation |
|----------------|---------------------|----------------|
| CASCADE | Soft delete related objects (if SoftDeleteModel) | Recommended for most cases |
| SET_NULL | Set FK to NULL (preserve related record) | Use for optional relationships |
| PROTECT | Prevent deletion if related objects exist | Use for critical data |
| SET_DEFAULT | Set FK to default value | Rarely needed |
| DO_NOTHING | No action (violates referential integrity) | Avoid |

**Example: Mixed CASCADE Behavior**
```python
class Course(SoftDeleteModel):
    """Course with soft delete."""
    title = models.CharField(max_length=200)


class Enrollment(SoftDeleteModel):
    """Enrollment - soft deletes with course."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Payment(models.Model):
    """Payment - preserved when enrollment deleted (audit trail)."""
    enrollment = models.ForeignKey(Enrollment, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)


# Deleting course soft-deletes enrollments, but preserves payments
course.delete()
# Course: is_deleted=True
# Enrollments: is_deleted=True (cascaded)
# Payments: enrollment=NULL (preserved for accounting)
```

#### GDPR Right to Erasure

```python
class User(SoftDeleteModel):
    """User with GDPR compliance."""
    email = models.EmailField(unique=True)

    def anonymize_for_gdpr(self):
        """
        Anonymize user data for GDPR right to erasure.

        Strategy:
        1. Soft delete (preserves database structure)
        2. Anonymize PII (Personally Identifiable Information)
        3. Cascade to related data
        """
        from hashlib import sha256

        # Generate anonymous identifier
        anon_id = sha256(f"user-{self.id}".encode()).hexdigest()[:16]

        # Anonymize PII
        self.email = f"deleted-{anon_id}@anonymized.local"
        self.first_name = "Deleted"
        self.last_name = "User"
        self.phone = None
        self.address = None

        # Soft delete
        self.delete()

        # Cascade anonymization to related data
        self.posts.update(author_name="Anonymous")
        self.comments.delete()  # Soft delete comments

        # Hard delete sensitive data (optional)
        self.profile_images.all().hard_delete()
```

#### Resources

- **django-safedelete**: https://django-safedelete.readthedocs.io/
- **GDPR Right to Erasure**: https://gdpr-info.eu/art-17-gdpr/
- **Soft Delete Pattern**: https://medium.com/@ehsanshafiei82/implementing-soft-delete-in-django-9e9800de0fe3

---

## 3. Accessibility Best Practices

### 3.1 WCAG 2.1 Level A Requirements

**Authority**: W3C Web Accessibility Initiative (WAI)
**Severity**: Critical (Legal compliance, inclusivity)

#### Overview

WCAG 2.1 Level A represents the **minimum** accessibility standard. Failure to meet Level A can exclude users with disabilities and violate laws (ADA in USA, EAA in EU).

#### POUR Principles

1. **Perceivable**: Content must be noticeable
2. **Operable**: Navigable and interactive
3. **Understandable**: Clear and predictable
4. **Robust**: Compatible with assistive technologies

---

### 3.2 Keyboard Navigation (WCAG 2.1.1 Level A)

**Requirement**: All functionality must be operable via keyboard (no mouse required)

**React Implementation**
```jsx
// ✅ CORRECT: Keyboard-accessible button
function AccessibleButton({ onClick, children }) {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick(e);
    }
  };

  return (
    <button
      onClick={onClick}
      onKeyDown={handleKeyPress}
      type="button"
    >
      {children}
    </button>
  );
}

// ❌ WRONG: onClick on div (not keyboard accessible)
function InaccessibleButton({ onClick, children }) {
  return <div onClick={onClick}>{children}</div>;
  // No keyboard support, no focus, no semantics!
}

// ✅ BETTER: If must use div, add ARIA and keyboard support
function AccessibleDiv({ onClick, children }) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick(e);
        }
      }}
      aria-label="Descriptive label"
    >
      {children}
    </div>
  );
}
```

**Focus Management**
```jsx
import { useRef, useEffect } from 'react';

function Modal({ isOpen, onClose, children }) {
  const modalRef = useRef(null);
  const previousFocusRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      // Save current focus
      previousFocusRef.current = document.activeElement;

      // Focus modal
      modalRef.current?.focus();

      // Trap focus inside modal
      const handleTab = (e) => {
        if (e.key !== 'Tab') return;

        const focusableElements = modalRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      };

      document.addEventListener('keydown', handleTab);

      return () => {
        document.removeEventListener('keydown', handleTab);
        // Restore focus when modal closes
        previousFocusRef.current?.focus();
      };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      ref={modalRef}
      role="dialog"
      aria-modal="true"
      tabIndex={-1}
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose();
      }}
    >
      {children}
    </div>
  );
}
```

---

### 3.3 Non-Text Content (WCAG 1.1.1 Level A)

**Requirement**: Provide text alternatives for all non-text content

```jsx
// ✅ CORRECT: Image with alt text
<img
  src="/course-thumbnail.jpg"
  alt="Introduction to Python - Beginner course covering variables, loops, and functions"
/>

// ❌ WRONG: Missing alt text
<img src="/course-thumbnail.jpg" />

// ✅ CORRECT: Decorative image (empty alt)
<img src="/decorative-line.svg" alt="" role="presentation" />

// ✅ CORRECT: Icon button with aria-label
<button aria-label="Close dialog">
  <XIcon />
</button>

// ✅ CORRECT: Complex infographic with long description
<figure>
  <img
    src="/enrollment-stats.png"
    alt="Enrollment statistics for 2025"
    aria-describedby="stats-description"
  />
  <figcaption id="stats-description">
    Enrollment grew from 1,000 students in January to 5,000 in December,
    with the largest increase (2,000 students) occurring in September.
  </figcaption>
</figure>
```

---

### 3.4 Form Accessibility (WCAG 3.3.1, 3.3.2 Level A)

**Requirements**:
- Labels for form controls (3.3.2)
- Error identification (3.3.1)

```jsx
// ✅ CORRECT: Accessible form with labels and error handling
function EnrollmentForm() {
  const [email, setEmail] = useState('');
  const [errors, setErrors] = useState({});

  const handleSubmit = (e) => {
    e.preventDefault();

    const newErrors = {};
    if (!email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Email is invalid';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      // Announce errors to screen readers
      document.getElementById('error-summary')?.focus();
    } else {
      // Submit form
    }
  };

  return (
    <form onSubmit={handleSubmit} aria-label="Course enrollment form">
      {/* Error summary (WCAG 3.3.1) */}
      {Object.keys(errors).length > 0 && (
        <div
          id="error-summary"
          role="alert"
          aria-live="assertive"
          tabIndex={-1}
          className="error-summary"
        >
          <h2>Please correct the following errors:</h2>
          <ul>
            {Object.entries(errors).map(([field, message]) => (
              <li key={field}>
                <a href={`#${field}`}>{message}</a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Form field with label (WCAG 3.3.2) */}
      <div className="form-group">
        <label htmlFor="email">
          Email Address <span aria-label="required">*</span>
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          aria-required="true"
          aria-invalid={errors.email ? 'true' : 'false'}
          aria-describedby={errors.email ? 'email-error' : undefined}
          required
        />
        {errors.email && (
          <span id="email-error" role="alert" className="error-message">
            {errors.email}
          </span>
        )}
      </div>

      <button type="submit">Enroll Now</button>
    </form>
  );
}
```

---

### 3.5 Skip Navigation Link (WCAG 2.4.1 Level A)

**Requirement**: Provide a way to skip repeated content

```jsx
// App.jsx
function App() {
  return (
    <>
      {/* Skip to main content link */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <header>
        <nav>
          {/* Navigation with 20+ links */}
        </nav>
      </header>

      <main id="main-content" tabIndex={-1}>
        {/* Main content */}
      </main>
    </>
  );
}

// styles.css
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: #000;
  color: #fff;
  padding: 8px;
  text-decoration: none;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
```

---

### 3.6 CodeMirror 6 Accessibility

**Challenges**: CodeMirror is a complex editor with custom rendering

```javascript
import { EditorView, keymap } from '@codemirror/view';
import { EditorState } from '@codemirror/state';

// Accessible CodeMirror setup
const editorView = new EditorView({
  state: EditorState.create({
    doc: initialCode,
    extensions: [
      // Keyboard navigation
      keymap.of([
        {
          key: 'Escape',
          run: (view) => {
            // Exit editor, focus next element
            const nextElement = document.querySelector('[data-next-after-editor]');
            nextElement?.focus();
            return true;
          }
        }
      ])
    ]
  }),
  parent: document.getElementById('editor-container')
});

// Add ARIA label
editorView.dom.setAttribute('aria-label', 'Python code editor');

// Add instructions for screen readers
const instructions = document.createElement('div');
instructions.id = 'editor-instructions';
instructions.className = 'sr-only';
instructions.textContent = 'Code editor. Press Escape then Tab to exit.';
editorView.dom.setAttribute('aria-describedby', 'editor-instructions');
editorView.dom.parentElement.prepend(instructions);

// Screen reader only CSS
// .sr-only {
//   position: absolute;
//   width: 1px;
//   height: 1px;
//   padding: 0;
//   margin: -1px;
//   overflow: hidden;
//   clip: rect(0, 0, 0, 0);
//   white-space: nowrap;
//   border-width: 0;
// }
```

**Fill-in-Blank Widget Accessibility**
```javascript
import { WidgetType } from '@codemirror/view';

class BlankWidget extends WidgetType {
  constructor(blankId, value, onUpdate) {
    super();
    this.blankId = blankId;
    this.value = value;
    this.onUpdate = onUpdate;
  }

  toDOM() {
    const input = document.createElement('input');
    input.type = 'text';
    input.value = this.value;
    input.className = 'blank-input';

    // Accessibility attributes
    input.setAttribute('aria-label', `Fill in blank ${this.blankId}`);
    input.setAttribute('role', 'textbox');
    input.id = `blank-${this.blankId}`;

    // Keyboard navigation
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Tab' && !e.shiftKey) {
        // Focus next blank
        const nextBlank = document.getElementById(`blank-${this.blankId + 1}`);
        if (nextBlank) {
          e.preventDefault();
          nextBlank.focus();
        }
      }
    });

    input.addEventListener('input', (e) => {
      this.onUpdate(this.blankId, e.target.value);
    });

    return input;
  }

  ignoreEvent(event) {
    // Allow keyboard events
    return event.type !== 'mousedown';
  }
}
```

---

### 3.7 React ARIA Libraries

**Recommended Libraries** (2025)

| Library | Pros | Cons | Best For |
|---------|------|------|----------|
| **Radix UI** | WAI-ARIA compliant, unstyled primitives, TypeScript | Requires styling | Custom design systems |
| **Headless UI** | Tailwind integration, React + Vue support | Smaller component set | Tailwind projects |
| **React Aria** (Adobe) | Comprehensive, focus management, i18n | Steeper learning curve | Complex applications |

**Example: Radix UI Dialog**
```jsx
import * as Dialog from '@radix-ui/react-dialog';

function EnrollmentDialog({ open, onOpenChange }) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Trigger asChild>
        <button>Enroll Now</button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content">
          <Dialog.Title>Confirm Enrollment</Dialog.Title>
          <Dialog.Description>
            You are about to enroll in "Introduction to Python".
            This will charge your account $49.99.
          </Dialog.Description>

          <div className="dialog-actions">
            <Dialog.Close asChild>
              <button>Cancel</button>
            </Dialog.Close>
            <button onClick={handleEnroll}>Confirm</button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
// Radix handles: focus trap, Escape key, ARIA attributes, keyboard navigation
```

#### Resources

- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/quickref/
- **React Accessibility**: https://react.dev/learn/accessibility
- **Radix UI**: https://www.radix-ui.com/
- **WebAIM**: https://webaim.org/

---

## 4. Performance Best Practices

### 4.1 Django Pagination Optimization

**Authority**: Django Official Documentation, High-Performance Django
**Severity**: High (Memory exhaustion, slow response times)

#### The Problem

Django's default `Paginator` executes expensive `COUNT(*)` queries on large tables:

```python
# ❌ SLOW: COUNT(*) on 1M+ row table
from django.core.paginator import Paginator

posts = Post.objects.all()
paginator = Paginator(posts, 25)  # Executes COUNT(*) immediately
page = paginator.page(1)

# SQL: SELECT COUNT(*) FROM posts;  -- 2-5 seconds on large tables!
# SQL: SELECT * FROM posts LIMIT 25 OFFSET 0;
```

#### Optimization Strategies

**Strategy 1: Disable Count (NoCountPaginator)**

```python
class NoCountPaginator(Paginator):
    """
    Paginator that doesn't execute COUNT queries.

    Use for large datasets where exact count is not critical.
    Shows estimated page count instead.
    """

    @property
    def count(self):
        """Return a large number instead of actual count."""
        return 9999999  # Effectively infinite

    def page(self, number):
        """Return page without validating page number against count."""
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page

        # Fetch one extra to check if there's a next page
        items = list(self.object_list[bottom:top + 1])

        if len(items) > self.per_page:
            # There's a next page
            items = items[:self.per_page]
            has_next = True
        else:
            has_next = False

        return Page(items, number, self, has_next=has_next)


class Page:
    """Custom Page object without count dependency."""

    def __init__(self, object_list, number, paginator, has_next=False):
        self.object_list = object_list
        self.number = number
        self.paginator = paginator
        self._has_next = has_next

    def has_next(self):
        return self._has_next

    def has_previous(self):
        return self.number > 1

    def next_page_number(self):
        return self.number + 1

    def previous_page_number(self):
        return self.number - 1
```

**Strategy 2: Cursor-Based Pagination (Performant)**

```python
# Cursor pagination: O(1) instead of O(n) for OFFSET
from rest_framework.pagination import CursorPagination

class PostCursorPagination(CursorPagination):
    """
    Cursor pagination for infinite scroll.

    Advantages:
    - No OFFSET (constant time)
    - Works with real-time data (stable pagination)
    - No count query

    Disadvantages:
    - Can't jump to arbitrary page
    - Requires ordering by indexed column
    """
    page_size = 25
    ordering = '-created_at'  # Must be indexed!
    cursor_query_param = 'cursor'


# ViewSet
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    pagination_class = PostCursorPagination

# SQL: No COUNT, no OFFSET!
# SELECT * FROM posts WHERE created_at < '2025-10-20' ORDER BY created_at DESC LIMIT 26;
```

**Strategy 3: Limit + Offset with Iterator (Memory Optimization)**

```python
# For large datasets, use iterator() to bypass queryset cache
def export_all_posts():
    """
    Export all posts without loading into memory.

    iterator() prevents Django from caching results,
    reducing memory usage from GB to MB.
    """
    posts = Post.objects.all().iterator(chunk_size=1000)

    for post in posts:
        # Process one at a time (low memory footprint)
        export_to_csv(post)

# Comparison:
# posts = Post.objects.all()  # Loads ALL into memory (1M posts = 2GB RAM!)
# for post in posts: ...      # Out of memory error!

# posts = Post.objects.all().iterator()  # Streams results (50MB RAM)
# for post in posts: ...                 # Memory efficient
```

**Strategy 4: Keyset Pagination (Best Performance)**

```python
# Third-party: performant-pagination package
# GitHub: https://github.com/ross/performant-pagination

from performant_pagination import PerformantPaginator

paginator = PerformantPaginator(
    queryset=Post.objects.all(),
    per_page=25,
    order_by='-id'  # Must be unique and indexed
)

page = paginator.page(after=last_id)  # No OFFSET, uses WHERE id > last_id
```

#### Database Indexing

```python
# Model with pagination-optimized indexes
class Post(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)

    class Meta:
        indexes = [
            # Composite index for common pagination query
            models.Index(fields=['-created_at', 'id']),

            # Cover query for filtering + pagination
            models.Index(fields=['author', '-created_at']),
        ]
```

#### DRF Pagination Settings

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.CursorPagination',
    'PAGE_SIZE': 25,

    # For large datasets
    'MAX_PAGE_SIZE': 100,  # Prevent abuse
}
```

#### Resources

- **Django Pagination**: https://docs.djangoproject.com/en/5.2/topics/pagination/
- **DRF Pagination**: https://www.django-rest-framework.org/api-guide/pagination/
- **Performant Pagination**: https://github.com/ross/performant-pagination

---

## 5. Architecture Best Practices

### 5.1 Incremental Refactoring

**Authority**: Martin Fowler's Refactoring, Working Effectively with Legacy Code
**Severity**: Medium (Technical debt management)

#### The Strangler Fig Pattern

Incrementally replace legacy code without a risky "big rewrite".

**Pattern**:
1. Create new implementation alongside old
2. Route traffic to new implementation (feature flag)
3. Gradually increase traffic to new (0% → 50% → 100%)
4. Remove old implementation

**Django Example: Migrating View to ViewSet**

```python
# Step 1: Old implementation (keep running)
# apps/api/views/legacy_courses.py
@api_view(['GET'])
def course_list(request):
    """Legacy view - DO NOT MODIFY (being replaced)."""
    courses = Course.objects.all()[:20]
    data = [{'id': c.id, 'title': c.title} for c in courses]
    return Response(data)


# Step 2: New implementation (run in parallel)
# apps/api/viewsets/courses.py
class CourseViewSet(viewsets.ModelViewSet):
    """New ViewSet - modern API implementation."""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = CursorPagination


# Step 3: Feature flag routing
# apps/api/urls.py
from django.conf import settings

if settings.USE_NEW_COURSE_API:
    # New implementation
    router.register(r'courses', CourseViewSet)
else:
    # Old implementation
    urlpatterns += [path('courses/', course_list)]


# Step 4: Gradual rollout
# settings.py
import random

def should_use_new_api(request):
    """Gradually increase traffic to new API."""
    rollout_percentage = 50  # Start at 0%, increase to 100%

    # Consistent routing per user (not random each request)
    if hasattr(request, 'user') and request.user.is_authenticated:
        user_hash = hash(request.user.id)
        return (user_hash % 100) < rollout_percentage

    return random.randint(0, 99) < rollout_percentage

USE_NEW_COURSE_API = should_use_new_api(request)


# Step 5: Monitor both implementations
# Monitor error rates, latency, success rates for both
# If new API has issues, roll back to 0% immediately

# Step 6: Remove old implementation (when new = 100% for 2 weeks)
# Delete apps/api/views/legacy_courses.py
```

---

### 5.2 Feature Flags (LaunchDarkly Pattern)

**Authority**: LaunchDarkly Best Practices, Continuous Delivery
**Severity**: Medium (Safe deployments)

#### When to Use Feature Flags

✅ **Use feature flags for:**
- **New features** (gradual rollout)
- **Risky changes** (instant rollback)
- **A/B testing** (experiment with alternatives)
- **Refactoring** (strangler fig pattern)
- **Kill switches** (disable features in production)

❌ **Don't use feature flags for:**
- **Bug fixes** (deploy immediately)
- **Trivial changes** (adds complexity)
- **Permanent variations** (use configuration instead)

#### Implementation Pattern

```python
# Feature flag wrapper (works with LaunchDarkly, Waffle, etc.)
# apps/core/feature_flags.py
from typing import Any, Optional
from django.conf import settings
from django.core.cache import cache

class FeatureFlags:
    """Feature flag abstraction layer."""

    def __init__(self):
        if settings.LAUNCHDARKLY_SDK_KEY:
            import ldclient
            self.client = ldclient.get()
        else:
            self.client = None

    def is_enabled(
        self,
        flag_name: str,
        user: Optional[Any] = None,
        default: bool = False
    ) -> bool:
        """
        Check if feature flag is enabled.

        Args:
            flag_name: Feature flag key
            user: User object for targeting
            default: Default value if flag not found

        Returns:
            True if enabled, False otherwise
        """
        # Development: Use Django settings
        if settings.DEBUG:
            return getattr(settings, f'FEATURE_{flag_name.upper()}', default)

        # Production: Use LaunchDarkly
        if self.client:
            user_context = self._build_user_context(user)
            return self.client.variation(flag_name, user_context, default)

        return default

    def _build_user_context(self, user):
        """Build LaunchDarkly user context."""
        if not user or not hasattr(user, 'id'):
            return {'key': 'anonymous'}

        return {
            'key': str(user.id),
            'email': user.email,
            'custom': {
                'is_staff': user.is_staff,
                'date_joined': user.date_joined.isoformat(),
                'plan': getattr(user, 'subscription_plan', 'free')
            }
        }


# Singleton instance
feature_flags = FeatureFlags()


# Usage in views
from apps.core.feature_flags import feature_flags

def course_detail(request, course_id):
    course = Course.objects.get(id=course_id)

    # Feature flag check
    if feature_flags.is_enabled('new_enrollment_flow', user=request.user):
        # New implementation (being tested)
        return new_enrollment_flow(request, course)
    else:
        # Old implementation (stable)
        return old_enrollment_flow(request, course)
```

#### Flag Lifecycle Management

```python
# Document flags with metadata
# apps/core/feature_flags.py

FLAGS = {
    'new_enrollment_flow': {
        'created': '2025-10-01',
        'type': 'release',  # release | experiment | ops
        'temporary': True,   # Remove after rollout
        'owner': 'platform-team',
        'jira': 'PLAT-123',
        'remove_after': '2025-11-01',  # Cleanup date
    },
    'enrollment_double_opt_in': {
        'created': '2025-09-15',
        'type': 'experiment',
        'temporary': True,
        'owner': 'growth-team',
        'jira': 'GROW-456',
        'remove_after': '2025-10-15',
    },
    'course_recommendations': {
        'created': '2025-08-01',
        'type': 'ops',  # Operational (permanent)
        'temporary': False,
        'owner': 'ml-team',
    }
}

# Automated cleanup check
def check_expired_flags():
    """Alert on flags past removal date."""
    from datetime import date

    for flag_name, meta in FLAGS.items():
        if not meta.get('temporary'):
            continue

        remove_after = date.fromisoformat(meta['remove_after'])
        if date.today() > remove_after:
            print(f"⚠️ Flag '{flag_name}' should be removed (expired {remove_after})")
```

#### Best Practices

1. **Rule of Three**: Don't refactor until code is duplicated 3+ times (especially for temporary flags)
2. **Regular Cleanup**: Quarterly sprint to remove old flags
3. **Naming Convention**: `<team>_<feature>_<variant>` (e.g., `growth_enrollment_v2`)
4. **Default to Safe**: `default=False` for new features, `default=True` for stable
5. **Monitor Both Paths**: Track metrics for flag=on and flag=off

#### Resources

- **LaunchDarkly Best Practices**: https://docs.launchdarkly.com/guides/best-practices/improving-code/
- **Feature Flag Patterns**: https://martinfowler.com/articles/feature-toggles.html

---

## 6. Code Quality Best Practices

### 6.1 Python Type Hints (PEP 484)

**Authority**: Python Enhancement Proposal 484, mypy Documentation
**Severity**: High (Code maintainability, bug prevention)

#### Why Type Hints?

- **IDE autocomplete** (IntelliSense, PyCharm)
- **Static type checking** (mypy catches bugs pre-runtime)
- **Documentation** (function signatures self-documenting)
- **Refactoring safety** (find all usages, prevent breaking changes)

#### Basic Patterns

```python
from typing import Optional, List, Dict, Any, Union, Tuple

# Function signatures
def get_course(course_id: int) -> Optional[Course]:
    """
    Get course by ID.

    Args:
        course_id: Course primary key

    Returns:
        Course instance or None if not found
    """
    try:
        return Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return None


def enroll_user(
    user: User,
    course: Course,
    payment_method: str = 'free'
) -> Tuple[Enrollment, bool]:
    """
    Enroll user in course.

    Args:
        user: User instance
        course: Course instance
        payment_method: Payment method (free, credit_card, paypal)

    Returns:
        (Enrollment instance, created flag)
    """
    return Enrollment.objects.get_or_create(
        user=user,
        course=course,
        defaults={'payment_method': payment_method}
    )


# Class attributes
class CourseService:
    """Service for course operations."""

    cache_timeout: int = 300
    default_page_size: int = 25

    def __init__(self, user: User) -> None:
        self.user = user
        self.cache: Dict[int, Course] = {}

    def get_enrolled_courses(self, active_only: bool = True) -> List[Course]:
        """Get courses user is enrolled in."""
        queryset = self.user.enrolled_courses.all()
        if active_only:
            queryset = queryset.filter(status='active')
        return list(queryset)
```

#### Django-Specific Patterns

```python
from typing import TYPE_CHECKING, TypeVar, Generic
from django.db.models import QuerySet, Model
from django.http import HttpRequest, HttpResponse, JsonResponse

if TYPE_CHECKING:
    # Import for type checking only (avoids circular imports)
    from apps.learning.models import Course, Enrollment

# Generic repository
T = TypeVar('T', bound=Model)

class BaseRepository(Generic[T]):
    """Type-safe repository pattern."""

    def __init__(self, model_class: type[T]) -> None:
        self.model = model_class

    def get_by_id(self, id: int) -> Optional[T]:
        """Get instance by ID."""
        try:
            return self.model.objects.get(pk=id)
        except self.model.DoesNotExist:
            return None

    def filter(self, **kwargs: Any) -> QuerySet[T]:
        """Filter instances."""
        return self.model.objects.filter(**kwargs)

# Usage
course_repo = BaseRepository[Course](Course)
course = course_repo.get_by_id(1)  # Type: Optional[Course]
```

#### DRF ViewSet Type Hints

```python
from rest_framework import viewsets, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import QuerySet

class CourseViewSet(viewsets.ModelViewSet):
    """Course management ViewSet."""

    queryset: QuerySet[Course] = Course.objects.all()
    serializer_class = CourseSerializer

    def get_queryset(self) -> QuerySet[Course]:
        """Get optimized queryset."""
        return super().get_queryset().select_related(
            'instructor'
        ).prefetch_related('tags')

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """List all courses."""
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def enroll(self, request: Request, pk: Optional[int] = None) -> Response:
        """Enroll authenticated user."""
        course: Course = self.get_object()

        # Type checking catches errors
        enrollment: Enrollment = Enrollment.objects.create(
            user=request.user,
            course=course
        )

        return Response({
            'message': 'Enrolled successfully',
            'enrollment_id': enrollment.id
        }, status=status.HTTP_201_CREATED)
```

#### mypy Configuration

```ini
# mypy.ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
show_error_codes = True

# Django plugin
plugins = mypy_django_plugin.main

[mypy.plugins.django-stubs]
django_settings_module = learning_community.settings.development

# Ignore third-party packages without stubs
[mypy-machina.*]
ignore_missing_imports = True

[mypy-wagtail.*]
ignore_missing_imports = True

[mypy-celery.*]
ignore_missing_imports = True
```

```bash
# Install type stubs
pip install mypy django-stubs djangorestframework-stubs types-requests

# Run mypy
mypy apps/

# Check coverage
mypy --html-report mypy-report apps/
# Open mypy-report/index.html
```

#### Common Type Hints

| Python Type | Type Hint | Example |
|------------|-----------|---------|
| Integer | `int` | `user_id: int` |
| String | `str` | `email: str` |
| Boolean | `bool` | `is_active: bool` |
| Optional | `Optional[T]` | `user: Optional[User]` |
| List | `List[T]` | `courses: List[Course]` |
| Dict | `Dict[K, V]` | `config: Dict[str, Any]` |
| Tuple | `Tuple[T1, T2]` | `coords: Tuple[int, int]` |
| Union | `Union[T1, T2]` | `id: Union[int, str]` |
| Any | `Any` | `data: Any` (avoid when possible) |
| QuerySet | `QuerySet[T]` | `qs: QuerySet[Course]` |
| Callable | `Callable[[int], str]` | `func: Callable[[int], str]` |

#### Resources

- **PEP 484**: https://peps.python.org/pep-0484/
- **mypy Documentation**: https://mypy.readthedocs.io/
- **django-stubs**: https://github.com/typeddjango/django-stubs
- **Real Python Type Checking**: https://realpython.com/python-type-checking/

---

## 7. Testing Strategies

### 7.1 Security Testing

```python
# Test SQL injection prevention
def test_no_sql_injection_in_search():
    """Ensure search is safe from SQL injection."""
    malicious_input = "'; DROP TABLE users; --"

    response = client.get(f'/api/v1/search/?q={malicious_input}')

    # Should return safely (not execute SQL)
    assert response.status_code in [200, 400]

    # Verify users table still exists
    assert User.objects.count() > 0


# Test for .extra() usage
def test_no_extra_method_in_codebase():
    """Regression test: Ensure .extra() is not used."""
    import os
    import re

    for root, dirs, files in os.walk('apps/'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path) as f:
                    content = f.read()
                    assert not re.search(r'\.extra\s*\(', content), \
                        f"Found .extra() in {path} (SQL injection vector)"
```

### 7.2 Race Condition Testing

```python
import threading
from django.test import TransactionTestCase

class EnrollmentRaceConditionTest(TransactionTestCase):
    """Use TransactionTestCase for concurrent tests."""

    def test_concurrent_enrollments_no_duplicates(self):
        """Test concurrent enrollments don't create duplicates."""
        course = Course.objects.create(title="Test", max_students=10)
        users = [User.objects.create(username=f"user{i}") for i in range(20)]

        results = []

        def enroll(user):
            from django.test import Client
            client = Client()
            client.force_login(user)
            response = client.post(f'/api/v1/courses/{course.id}/enroll/')
            results.append(response.status_code)

        threads = [threading.Thread(target=enroll, args=(u,)) for u in users]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly 10 should succeed
        success_count = results.count(201)
        assert success_count == 10

        # Database should have exactly 10
        assert course.enrollments.count() == 10
```

### 7.3 Accessibility Testing

```javascript
// Jest + React Testing Library
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('CourseCard has no accessibility violations', async () => {
  const { container } = render(<CourseCard course={mockCourse} />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});

test('Button is keyboard accessible', () => {
  render(<EnrollButton onClick={mockEnroll} />);

  const button = screen.getByRole('button', { name: /enroll/i });

  // Focus via Tab
  button.focus();
  expect(button).toHaveFocus();

  // Activate via Enter
  fireEvent.keyDown(button, { key: 'Enter' });
  expect(mockEnroll).toHaveBeenCalled();
});
```

### 7.4 Performance Testing

```python
from django.test import TestCase
from django.test.utils import override_settings
import time

class PaginationPerformanceTest(TestCase):
    """Test pagination performance on large datasets."""

    @classmethod
    def setUpTestData(cls):
        # Create 10,000 posts
        Post.objects.bulk_create([
            Post(title=f"Post {i}", content="Content")
            for i in range(10000)
        ])

    def test_cursor_pagination_performance(self):
        """Cursor pagination should be O(1)."""
        start = time.time()

        response = self.client.get('/api/v1/posts/?page=1')
        page1_time = time.time() - start

        start = time.time()
        response = self.client.get('/api/v1/posts/?page=100')
        page100_time = time.time() - start

        # Cursor pagination: page 100 should be ~same speed as page 1
        assert page100_time < page1_time * 2, \
            f"Page 100 ({page100_time}s) much slower than page 1 ({page1_time}s)"

    def test_query_count(self):
        """Ensure N+1 queries are avoided."""
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get('/api/v1/courses/')

        # Should be ~3 queries (1 for courses, 1 for prefetch, 1 for count)
        assert len(queries) <= 5, \
            f"Too many queries: {len(queries)} (N+1 problem?)"
```

---

## 8. Common Pitfalls

### 8.1 Security Pitfalls

**Pitfall**: Using f-strings in SQL
```python
# ❌ WRONG
User.objects.raw(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ CORRECT
User.objects.raw("SELECT * FROM users WHERE id = %s", [user_id])
```

**Pitfall**: Trusting user input in .extra()
```python
# ❌ DANGEROUS
queryset.extra(where=[user_input])

# ✅ SAFE
queryset.filter(**safe_filters)
```

---

### 8.2 Data Integrity Pitfalls

**Pitfall**: Mutable default in model
```python
# ❌ WRONG
config = models.JSONField(default={})

# ✅ CORRECT
config = models.JSONField(default=dict)
```

**Pitfall**: Race condition in counter update
```python
# ❌ WRONG
article.views += 1
article.save()

# ✅ CORRECT
Article.objects.filter(id=article.id).update(views=F('views') + 1)
```

---

### 8.3 Accessibility Pitfalls

**Pitfall**: onClick on div
```jsx
// ❌ WRONG (not keyboard accessible)
<div onClick={handleClick}>Click me</div>

// ✅ CORRECT
<button onClick={handleClick}>Click me</button>
```

**Pitfall**: Missing alt text
```jsx
// ❌ WRONG
<img src="/photo.jpg" />

// ✅ CORRECT
<img src="/photo.jpg" alt="Student working on Python exercise" />
```

---

### 8.4 Performance Pitfalls

**Pitfall**: N+1 queries
```python
# ❌ WRONG (N+1 queries)
for course in Course.objects.all():
    print(course.instructor.name)  # Separate query each iteration!

# ✅ CORRECT
for course in Course.objects.select_related('instructor'):
    print(course.instructor.name)  # Single JOIN query
```

**Pitfall**: Large pagination OFFSET
```python
# ❌ SLOW (scans 10,000 rows)
posts = Post.objects.all()[10000:10025]

# ✅ FAST (uses WHERE instead of OFFSET)
last_id = request.GET.get('last_id')
posts = Post.objects.filter(id__lt=last_id).order_by('-id')[:25]
```

---

## Summary Checklist

### Security
- [ ] No `.extra()` usage (use ORM annotations)
- [ ] No string formatting in SQL (use parameterization)
- [ ] All raw SQL uses parameter binding
- [ ] User input never interpolated into queries

### Data Integrity
- [ ] All JSONField defaults are callables
- [ ] Race-prone operations use `@transaction.atomic`
- [ ] Critical operations use `select_for_update()`
- [ ] Counter updates use `F()` expressions
- [ ] Unique constraints for business rules

### Accessibility
- [ ] All images have alt text
- [ ] All forms have labels
- [ ] Skip navigation link present
- [ ] Keyboard navigation works everywhere
- [ ] ARIA attributes for custom widgets
- [ ] Color contrast meets WCAG AA

### Performance
- [ ] No COUNT queries on large tables
- [ ] Cursor pagination for infinite scroll
- [ ] N+1 queries prevented (prefetch_related)
- [ ] Database indexes on filtered/ordered columns
- [ ] iterator() for large exports

### Architecture
- [ ] Feature flags for risky changes
- [ ] Incremental refactoring (strangler fig)
- [ ] Regular flag cleanup (quarterly)
- [ ] Monitoring for both implementations

### Code Quality
- [ ] Type hints on all functions (90%+ coverage)
- [ ] mypy passes with no errors
- [ ] django-stubs installed
- [ ] Pre-commit hook for mypy

---

## Final Resources

### Official Documentation
- **Django 5.2**: https://docs.djangoproject.com/en/5.2/
- **DRF**: https://www.django-rest-framework.org/
- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/quickref/
- **PEP 484**: https://peps.python.org/pep-0484/

### Security
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **Django Security**: https://docs.djangoproject.com/en/5.2/topics/security/

### Performance
- **High Performance Django**: https://highperformancedjango.com/
- **Database Optimization**: https://use-the-index-luke.com/

### Accessibility
- **WebAIM**: https://webaim.org/
- **A11Y Project**: https://www.a11yproject.com/
- **Radix UI**: https://www.radix-ui.com/

---

**Last Updated**: 2025-10-20
**Maintained By**: Python Learning Studio Engineering Team
