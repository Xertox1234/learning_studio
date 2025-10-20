# Framework Research Summary - Phase 2 Development

**Date:** 2025-10-20
**Purpose:** Quick reference guide for Phase 2 development framework patterns

---

## Installed Framework Versions

```
Backend:
├─ Django 5.2.7
├─ Wagtail 7.1.1
├─ Django REST Framework 3.16.1
├─ django-machina 1.3.1
├─ PostgreSQL (recommended)
└─ Redis (caching)

Frontend:
├─ React 19.2.0
├─ React Router 6.30.1
├─ TanStack React Query 5.90.3
├─ Zustand 4.5.7
├─ CodeMirror 6.38.5
└─ Vite 5.4.20
```

---

## Quick Reference by Framework

### Django 5.2 - Key Patterns

```python
# Query Optimization (N+1 Prevention)
courses = Course.objects.select_related(
    'instructor',      # FK relationships
    'skill_level'
).prefetch_related(
    'categories',      # M2M relationships
    'tags'
)

# Signal Pattern
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Post)
def update_stats(sender, instance, created, **kwargs):
    if created:
        # Update statistics, invalidate cache
        pass

# Migration Best Practice
def migrate_data(apps, schema_editor):
    # Always use apps.get_model() for historical versions
    User = apps.get_model('users', 'User')
```

### Django REST Framework 3.16 - ViewSet Pattern

```python
from rest_framework import viewsets, permissions
from apps.api.permissions import IsOwnerOrAdmin

class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Layer 1: Filter at database level"""
        queryset = Course.objects.select_related('instructor')
        if not self.request.user.is_staff:
            return queryset.filter(instructor=self.request.user)
        return queryset

    def perform_create(self, serializer):
        """Layer 3: Force ownership"""
        serializer.save(instructor=self.request.user)

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        """Custom action"""
        course = self.get_object()
        # Enrollment logic
        return Response(status=201)
```

### Wagtail 7.1 - Headless CMS Pattern

```python
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.api import APIField

class ExercisePage(Page):
    body = StreamField([
        ('heading', blocks.CharBlock()),
        ('code', CodeBlock()),
    ], use_json_field=True)

    api_fields = [APIField('body')]

# Custom Block API Representation
class CodeBlock(blocks.StructBlock):
    def get_api_representation(self, value, context=None):
        return {
            'type': 'code',
            'language': value['language'],
            'code': value['code'],
        }
```

### React 19 - Modern Hooks

```jsx
import { useState, useEffect, useCallback, useMemo } from 'react'

function Component({ userId }) {
  // useEffect for side effects
  useEffect(() => {
    async function fetchUser() {
      const user = await fetch(`/api/users/${userId}`).then(r => r.json())
      setUser(user)
    }
    fetchUser()
    return () => {
      // Cleanup
    }
  }, [userId])

  // useCallback for stable references
  const handleClick = useCallback(() => {
    // Handler logic
  }, [dependency])

  // useMemo for expensive calculations
  const filtered = useMemo(() => {
    return items.filter(item => item.active)
  }, [items])
}
```

### TanStack React Query 5 - Data Fetching

```javascript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// Query Key Factory
export const courseKeys = {
  all: ['courses'],
  lists: () => [...courseKeys.all, 'list'],
  detail: (id) => [...courseKeys.all, 'detail', id],
}

// Query Hook
export const useCourse = (courseId) => {
  return useQuery({
    queryKey: courseKeys.detail(courseId),
    queryFn: () => fetchCourse(courseId),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!courseId,
  })
}

// Mutation Hook with Optimistic Update
export const useCreatePost = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createPost,

    onMutate: async (newPost) => {
      await queryClient.cancelQueries({ queryKey: postKeys.all })
      const previous = queryClient.getQueryData(postKeys.list())

      queryClient.setQueryData(postKeys.list(), (old) => ({
        ...old,
        results: [...old.results, { ...newPost, id: -Date.now(), _isOptimistic: true }]
      }))

      return { previous }
    },

    onError: (err, newPost, context) => {
      queryClient.setQueryData(postKeys.list(), context.previous)
    },

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: postKeys.all })
    },
  })
}
```

### Zustand 4.5 - State Management

```javascript
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

export const useAuthStore = create(
  devtools(
    persist(
      (set, get) => ({
        user: null,
        token: null,

        login: (user, token) => set({ user, token }),
        logout: () => set({ user: null, token: null }),
      }),
      { name: 'auth-storage' }
    )
  )
)

// Usage
function Header() {
  const user = useAuthStore(state => state.user)
  const logout = useAuthStore(state => state.logout)
  return <button onClick={logout}>{user?.username}</button>
}
```

### CodeMirror 6 - Code Editor

```javascript
import { EditorView } from '@codemirror/view'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'

// React Integration
import CodeMirror from '@uiw/react-codemirror'

function CodeEditor({ value, onChange }) {
  return (
    <CodeMirror
      value={value}
      height="400px"
      theme={oneDark}
      extensions={[python()]}
      onChange={onChange}
    />
  )
}

// Custom Widget (Fill-in-Blank)
class BlankWidget extends WidgetType {
  toDOM() {
    const input = document.createElement('input')
    input.className = 'blank-input'
    return input
  }

  ignoreEvent(event) {
    return event.type !== 'mousedown'
  }
}
```

### django-machina 1.3 + Trust Levels

```python
from machina.core.loading import get_class

PermissionHandler = get_class('forum_permission.handler', 'PermissionHandler')
perm_handler = PermissionHandler()

# Check Permissions
if perm_handler.can_read_forum(forum, user):
    # User can view
    pass

# Trust Level Pattern (Custom)
class TrustLevel(models.Model):
    TRUST_LEVELS = [
        (0, 'New User'),    # Requires moderation
        (1, 'Basic User'),  # Can post images
        (2, 'Member'),      # Extended edit time
        (3, 'Regular'),     # Basic moderation
        (4, 'Leader'),      # Full moderation
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    level = models.IntegerField(default=0, choices=TRUST_LEVELS)

    def check_for_promotion(self):
        # TL0 -> TL1: Read 10 posts, 10 minutes reading
        if self.level == 0:
            if self.posts_read >= 10 and self.time_read >= timedelta(minutes=10):
                return 1
        # ... more levels

# Moderation Pattern
approved = True
if user.trust_level.level == 0:
    approved = False  # TL0 needs review
    review_service.check_new_post(post)
```

---

## Architecture Patterns in Use

### 1. Service Layer Pattern
```
apps/api/
├── viewsets/        # API endpoints
├── services/        # Business logic
│   ├── statistics_service.py
│   ├── review_queue_service.py
│   └── code_execution_service.py
└── repositories/    # Data access (implied)
```

### 2. Dependency Injection
```python
# Container-based DI
from apps.api.services.container import container

stats_service = container.get_statistics_service()
review_service = container.get_review_queue_service()
```

### 3. Query Key Factories
```javascript
// Hierarchical cache keys
export const forumKeys = {
  all: ['forums'],
  lists: () => [...forumKeys.all, 'list'],
  detail: (slug) => [...forumKeys.all, 'detail', slug],
  topics: (slug) => [...forumKeys.detail(slug), 'topics'],
}

// Invalidation strategies
queryClient.invalidateQueries({ queryKey: forumKeys.all })       // All
queryClient.invalidateQueries({ queryKey: forumKeys.lists() })   // Lists
queryClient.invalidateQueries({ queryKey: forumKeys.detail(slug) }) // One
```

### 4. Three-Layer Security
```python
class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        # Layer 1: Database filtering
        if self.request.user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=self.request.user)

    # Layer 2: Object permissions (via IsOwnerOrAdmin)

    def perform_create(self, serializer):
        # Layer 3: Ownership forcing
        serializer.save(user=self.request.user)
```

---

## Testing Patterns

### Backend Testing
```python
from rest_framework.test import APITestCase

class CourseAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """Immutable data - runs once per class"""
        cls.user = User.objects.create_user(username='test')

    def setUp(self):
        """Mutable data - runs before each test"""
        self.client.force_authenticate(user=self.user)

    def test_list_courses(self):
        response = self.client.get('/api/v1/courses/')
        self.assertEqual(response.status_code, 200)
```

### Frontend Testing
```jsx
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

describe('CourseList', () => {
  test('displays courses', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } }
    })

    render(
      <QueryClientProvider client={queryClient}>
        <CourseList />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('Python Basics')).toBeInTheDocument()
    })
  })
})
```

---

## Performance Best Practices

### Backend
- ✅ Use `select_related` for FK/OneToOne
- ✅ Use `prefetch_related` for M2M/reverse FK
- ✅ Apply optimizations inline in views
- ✅ Test query counts: `assertNumQueries(3)`
- ✅ Redis caching with versioned keys
- ✅ Cache invalidation on mutations

### Frontend
- ✅ Lazy load routes with React.lazy
- ✅ Code splitting at route level
- ✅ TanStack Query caching (staleTime/gcTime)
- ✅ Optimistic updates for better UX
- ✅ Error boundaries around routes
- ✅ Suspense for loading states

---

## Security Checklist

### Backend
- ✅ Three-layer authorization
- ✅ Queryset filtering by user
- ✅ Object permissions on retrieve/update/destroy
- ✅ Ownership forcing on create
- ✅ Rate limiting on sensitive endpoints
- ✅ Input validation (serializers)

### Frontend
- ✅ Sanitize all HTML with DOMPurify
- ✅ Use `sanitize.strict()` for user input
- ✅ Use `sanitize.rich()` for trusted content
- ✅ Never use raw `dangerouslySetInnerHTML`
- ✅ CSRF tokens on mutations
- ✅ Authentication checks in components

---

## Common Pitfalls & Solutions

### Django 5.2
❌ **Problem:** Using unsaved instances in filters
```python
user = User()  # Not saved
Course.objects.filter(instructor=user)  # ValueError in 5.2
```

✅ **Solution:** Always save before filtering
```python
user = User.objects.create(username='test')
Course.objects.filter(instructor=user)  # OK
```

### React Query
❌ **Problem:** `cacheTime` no longer exists in v5
```javascript
useQuery({ cacheTime: 300000 })  // Removed in v5
```

✅ **Solution:** Use `gcTime` instead
```javascript
useQuery({ gcTime: 300000 })  // Correct in v5
```

### N+1 Queries
❌ **Problem:** Missing prefetch/select
```python
courses = Course.objects.all()
for course in courses:
    print(course.instructor.name)  # N+1 queries
```

✅ **Solution:** Optimize queryset
```python
courses = Course.objects.select_related('instructor')
for course in courses:
    print(course.instructor.name)  # 1 query
```

---

## Phase 2 Development Checklist

### Before Starting New Feature
- [ ] Review existing patterns in `/apps/api/viewsets/`
- [ ] Check security patterns in `/docs/idor-quick-reference.md`
- [ ] Review query optimization in `/docs/security/PR-23-N-PLUS-ONE-AUDIT.md`
- [ ] Check React patterns in `/frontend/src/hooks/`

### During Development
- [ ] Use service layer for business logic
- [ ] Optimize queries with select/prefetch
- [ ] Implement three-layer security
- [ ] Use TanStack Query for server state
- [ ] Use Zustand for UI state only
- [ ] Add optimistic updates for mutations

### Before Submitting PR
- [ ] Write tests (backend + frontend)
- [ ] Check query counts (assertNumQueries)
- [ ] Test cross-user access scenarios
- [ ] Sanitize all HTML output
- [ ] Update documentation
- [ ] Run full test suite

---

## Documentation Links

**Full Documentation:**
- `/docs/research/framework-documentation-phase2-2025.md` - Complete framework guide

**Project Documentation:**
- `/CLAUDE.md` - Development workflow and patterns
- `/docs/idor-quick-reference.md` - Security patterns
- `/docs/security/PR-23-N-PLUS-ONE-AUDIT.md` - Query optimization

**External Resources:**
- Django: https://docs.djangoproject.com/en/5.2/
- DRF: https://www.django-rest-framework.org/
- Wagtail: https://docs.wagtail.org/
- React: https://react.dev/
- TanStack Query: https://tanstack.com/query/

---

## Quick Command Reference

### Backend
```bash
# Run tests
python manage.py test apps.api
python manage.py test apps.forum_integration

# Check queries
python manage.py test apps.api.tests.test_query_performance

# Create migration
python manage.py makemigrations

# Apply migration
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py migrate
```

### Frontend
```bash
# Run dev server
cd frontend && npm run dev

# Run tests
cd frontend && npm test

# Build production
cd frontend && npm run build

# Run linter
cd frontend && npm run lint
```

---

**Last Updated:** 2025-10-20
**Next Review:** Before Phase 2 kickoff
