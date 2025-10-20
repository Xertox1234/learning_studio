# Framework Documentation Research for Phase 2 Development (2025)

**Generated:** 2025-10-20
**Purpose:** Comprehensive framework documentation and best practices for Python Learning Studio Phase 2 development
**Target Frameworks:** Django 5.2.7, Wagtail 7.1.1, DRF 3.16.1, React 19.2.0, TanStack Query 5.90.3

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Django 5.2.7 - Backend Patterns](#django-527-backend-patterns)
3. [Django REST Framework 3.16.1 - API Patterns](#django-rest-framework-3161-api-patterns)
4. [Wagtail 7.1.1 - Headless CMS](#wagtail-711-headless-cms)
5. [React 19 - Modern Frontend Patterns](#react-19-modern-frontend-patterns)
6. [TanStack React Query 5.90 - Data Fetching](#tanstack-react-query-590-data-fetching)
7. [Zustand 4.5 - State Management](#zustand-45-state-management)
8. [CodeMirror 6 - Educational Code Editor](#codemirror-6-educational-code-editor)
9. [django-machina 1.3 - Forum Integration](#django-machina-13-forum-integration)
10. [Testing Patterns](#testing-patterns)
11. [Implementation Recommendations](#implementation-recommendations)

---

## Executive Summary

### Installed Versions

```
Backend:
- Django: 5.2.7
- Wagtail: 7.1.1
- Django REST Framework: 3.16.1
- django-machina: 1.3.1

Frontend:
- React: 19.2.0
- React Router: 6.30.1
- TanStack React Query: 5.90.3
- Zustand: 4.5.7
- CodeMirror: 6.38.5
- Vite: 5.4.20
```

### Key Architectural Patterns in Use

1. **Service Layer Pattern** - Business logic extracted to `/apps/api/services/`
2. **Repository Pattern** - Data access abstraction with N+1 query prevention
3. **Dependency Injection** - Container-based service management
4. **React Query Hooks** - Custom hooks for data fetching with caching
5. **Optimistic Updates** - UI updates before server confirmation
6. **Query Key Factories** - Hierarchical cache key structure

---

## Django 5.2.7 - Backend Patterns

### Official Documentation
- **URL:** https://docs.djangoproject.com/en/5.2/
- **Migration Docs:** https://docs.djangoproject.com/en/5.2/topics/migrations/
- **Model Relationships:** https://docs.djangoproject.com/en/5.2/topics/db/models/

### Key Features in 5.2

#### 1. Composite Primary Keys (New in 5.2)
Django 5.2 introduced composite primary key support with limitations:
- Cannot migrate to/from composite PKs
- Relationship fields (ForeignKey, OneToOneField, ManyToManyField) cannot point to models with composite PKs
- Workaround available using internal API `ForeignObject`

**Recommendation:** Avoid composite PKs for now due to migration limitations. Use traditional single-column PKs with unique constraints instead.

#### 2. Stricter Validation
Django 5.2 enforces that unsaved model instances cannot be used in related filters - raises `ValueError` consistently.

```python
# This now raises ValueError in 5.2
user = User()  # Not saved yet
Course.objects.filter(instructor=user)  # ERROR!

# Correct pattern
user = User.objects.create(username='instructor')
Course.objects.filter(instructor=user)  # OK
```

### Model Relationships Best Practices

#### Using `select_related` (ForeignKey, OneToOne)
For reducing N+1 queries on forward FK and OneToOne relationships:

```python
# Bad - N+1 queries (1 + N for each course's instructor)
courses = Course.objects.all()
for course in courses:
    print(course.instructor.name)  # Separate query per course

# Good - Single JOIN query
courses = Course.objects.select_related('instructor').all()
for course in courses:
    print(course.instructor.name)  # No additional queries
```

**Project Pattern (from `/apps/api/views/wagtail.py`):**
```python
# Current implementation in project
courses = CoursePage.objects.live().prefetch_related(
    'categories',  # M2M relationships
    'tags'
).select_related(
    'instructor',  # FK relationships
    'skill_level'
)
```

#### Using `prefetch_related` (ManyToMany, Reverse FK)
For reducing N+1 queries on M2M and reverse relationships:

```python
# Bad - N+1 queries
courses = Course.objects.all()
for course in courses:
    print(course.categories.all())  # Separate query per course

# Good - Separate query with IN clause
courses = Course.objects.prefetch_related('categories').all()
for course in courses:
    print(course.categories.all())  # Prefetched, no query
```

#### Combining Both Methods
```python
from django.db.models import Prefetch

# Advanced pattern with custom prefetch queryset
courses = Course.objects.select_related(
    'instructor',
    'skill_level'
).prefetch_related(
    Prefetch(
        'lessons',
        queryset=Lesson.objects.select_related('author').order_by('order')
    ),
    'categories',
    'tags'
)
```

**Key Rule:**
- ✅ `select_related` for ForeignKey and OneToOne (SQL JOIN)
- ✅ `prefetch_related` for ManyToMany and reverse FK (separate query with IN)
- ✅ Apply optimizations inline in views for clarity (YAGNI principle)
- ✅ Test with `apps/api/tests/test_query_performance.py`

### Migration Best Practices

#### 1. Use Historical Models
```python
def migrate_data(apps, schema_editor):
    # Always use apps.get_model() for historical versions
    User = apps.get_model('users', 'User')
    TrustLevel = apps.get_model('forum_integration', 'TrustLevel')

    for user in User.objects.all():
        TrustLevel.objects.create(user=user, level=0)
```

#### 2. Handle ManyToManyField Changes Carefully
```python
from django.db import migrations

class Migration(migrations.Migration):
    operations = [
        migrations.SeparateDatabaseAndState(
            # Database operation - rename table
            database_operations=[
                migrations.RunSQL(
                    "ALTER TABLE old_m2m_table RENAME TO new_m2m_table;",
                    reverse_sql="ALTER TABLE new_m2m_table RENAME TO old_m2m_table;"
                )
            ],
            # State operation - update Django's knowledge
            state_operations=[
                migrations.AlterField(
                    model_name='course',
                    name='tags',
                    field=models.ManyToManyField(through='CourseTag')
                )
            ]
        )
    ]
```

#### 3. PostgreSQL for Production
PostgreSQL provides the most complete schema support, including:
- Transactional DDL (schema changes in transactions)
- Advanced constraint support
- Efficient indexing strategies

MySQL lacks transaction support for schema changes, requiring manual rollback on failed migrations.

### Django Signals Best Practices

#### When to Use Signals
✅ **Good use cases:**
- Cross-app communication (decoupling apps)
- Audit logging (tracking changes)
- Cache invalidation
- Background task triggering

❌ **Avoid signals for:**
- Logic that belongs in model methods
- Business logic that should be in services
- Cases where explicit method calls are clearer

#### Signal Pattern (from project)
```python
# apps/forum_integration/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Post)
def update_topic_stats(sender, instance, created, **kwargs):
    """Update topic statistics when a post is created."""
    if created and instance.approved:
        topic = instance.topic
        topic.posts_count += 1
        topic.last_post = instance
        topic.save()

        # Invalidate cache
        from apps.api.services.container import container
        stats_service = container.get_statistics_service()
        stats_service.invalidate_cache(forum_id=topic.forum_id)
```

#### Alternative: Django Lifecycle Hooks
Consider `django-lifecycle` for cleaner model lifecycle behaviors:

```python
from django_lifecycle import LifecycleModel, hook, AFTER_CREATE

class Post(LifecycleModel):
    # ... fields ...

    @hook(AFTER_CREATE, when='approved', is_now=True)
    def on_approved(self):
        """Logic when post is approved."""
        self.topic.posts_count += 1
        self.topic.save()
```

**Advantage:** Keeps logic closer to the model, supports conditions natively.

### Database Indexing Strategy

Based on project's trust level model:

```python
class Meta:
    indexes = [
        # Single column indexes
        models.Index(fields=['level']),
        models.Index(fields=['last_visit_date']),

        # Composite indexes for common query patterns
        models.Index(
            fields=['level', '-posts_created'],
            name='trustlevel_level_posts_idx'
        ),
        models.Index(
            fields=['level', '-likes_received'],
            name='trustlevel_level_likes_idx'
        ),
    ]
```

**Index Design Principles:**
1. Index fields used in WHERE clauses
2. Composite indexes for multi-field queries (leaderboards, filtering)
3. Order matters: most selective field first
4. Consider query frequency vs. write overhead

---

## Django REST Framework 3.16.1 - API Patterns

### Official Documentation
- **URL:** https://www.django-rest-framework.org/
- **ViewSets:** https://www.django-rest-framework.org/api-guide/viewsets/
- **Serializers:** https://www.django-rest-framework.org/api-guide/serializers/

### ViewSet Patterns (Current Project Architecture)

#### Modular ViewSet Structure
```
apps/api/
├── viewsets/
│   ├── user.py           # User management ViewSets
│   ├── learning.py       # Course/lesson ViewSets
│   ├── exercises.py      # Exercise system ViewSets
│   └── community.py      # Discussion/forum ViewSets
├── views/
│   ├── code_execution.py # Function-based views
│   └── wagtail.py        # Wagtail CMS endpoints
└── services/
    └── code_execution_service.py  # Business logic
```

#### ViewSet Best Practices

**1. Standard ViewSet with Optimizations:**
```python
from rest_framework import viewsets, permissions
from apps.api.permissions import IsOwnerOrAdmin

class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for courses.

    Implements:
    - Queryset filtering (Layer 1 security)
    - Object permissions (Layer 2 security)
    - Query optimization (prefetch/select)
    """
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    queryset = Course.objects.all()  # For router introspection only

    def get_queryset(self):
        """Layer 1: Filter at database level."""
        queryset = Course.objects.select_related(
            'instructor',
            'skill_level'
        ).prefetch_related(
            'categories',
            'tags'
        )

        if self.request.user.is_staff:
            return queryset
        return queryset.filter(instructor=self.request.user)

    def perform_create(self, serializer):
        """Layer 3: Force ownership."""
        serializer.save(instructor=self.request.user)
```

**2. Dynamic Serializer Selection:**
```python
class CourseViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        """Use different serializers based on action."""
        if self.action == 'list':
            return CourseListSerializer  # Minimal fields
        elif self.action == 'retrieve':
            return CourseDetailSerializer  # All fields + nested
        return CourseSerializer  # Default
```

**3. Custom Actions:**
```python
from rest_framework.decorators import action

class CourseViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        """Custom endpoint: POST /courses/{id}/enroll/"""
        course = self.get_object()
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course
        )
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Custom endpoint: GET /courses/trending/"""
        trending_courses = self.get_queryset().annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:10]
        serializer = self.get_serializer(trending_courses, many=True)
        return Response(serializer.data)
```

### Serializer Patterns

#### 1. Context-Aware Serialization
```python
class CourseSerializer(serializers.ModelSerializer):
    instructor_name = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'instructor_name', 'is_enrolled']

    def get_instructor_name(self, obj):
        """Access object data."""
        return obj.instructor.get_full_name()

    def get_is_enrolled(self, obj):
        """Access request context."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(student=request.user).exists()
        return False
```

#### 2. Nested Serializers with Optimization
```python
class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'order']

class CourseDetailSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'lessons']

    # In ViewSet, prefetch to avoid N+1:
    # Course.objects.prefetch_related('lessons')
```

#### 3. Write vs Read Serializers
```python
class CourseCreateSerializer(serializers.ModelSerializer):
    """For POST requests - validation only."""
    class Meta:
        model = Course
        fields = ['title', 'description', 'category']

class CourseReadSerializer(serializers.ModelSerializer):
    """For GET requests - computed fields."""
    instructor = UserSerializer(read_only=True)
    enrollment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'instructor', 'enrollment_count']

class CourseViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return CourseCreateSerializer
        return CourseReadSerializer
```

### Response Patterns

#### Consistent Error Format
```python
from rest_framework.response import Response
from rest_framework import status

# Error response
return Response({
    'error': 'Course not found',
    'details': {'course_id': course_id}
}, status=status.HTTP_404_NOT_FOUND)

# Success response
return Response({
    'message': 'Course created successfully',
    'course': serializer.data
}, status=status.HTTP_201_CREATED)
```

#### Paginated Responses
```python
from rest_framework.pagination import CursorPagination

class CoursePagination(CursorPagination):
    page_size = 20
    ordering = '-created_at'

class CourseViewSet(viewsets.ModelViewSet):
    pagination_class = CoursePagination

    # Response format:
    # {
    #   "next": "http://api/courses/?cursor=xyz",
    #   "previous": null,
    #   "results": [...]
    # }
```

### Testing DRF APIs

#### APITestCase Pattern
```python
from rest_framework.test import APITestCase
from rest_framework import status

class CourseAPITests(APITestCase):
    fixtures = ['users.json', 'courses.json']

    def setUp(self):
        """Run before each test method."""
        self.user = User.objects.get(username='testuser')
        self.client.force_authenticate(user=self.user)

    @classmethod
    def setUpTestData(cls):
        """Run once per test class - for immutable data."""
        cls.test_course = Course.objects.create(
            title='Test Course',
            instructor=User.objects.get(username='instructor')
        )

    def test_list_courses(self):
        """Test GET /api/courses/"""
        response = self.client.get('/api/v1/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_create_course_unauthorized(self):
        """Test POST /api/courses/ without auth."""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/v1/courses/', {
            'title': 'New Course'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

---

## Wagtail 7.1.1 - Headless CMS

### Official Documentation
- **URL:** https://docs.wagtail.org/en/stable/
- **API v2:** https://docs.wagtail.org/en/stable/advanced_topics/api/v2/configuration.html
- **StreamField:** https://docs.wagtail.org/en/stable/topics/streamfield.html

### Wagtail 7.1 New Features

#### 1. Improved Headless Preview
Wagtail 7.1 refactored live preview and user bar features to work better in headless setups:
- Preview panel can now load cross-domain headless frontends
- Integration with `wagtail-headless-preview` package
- Wagtail user bar refactored as independent template component

#### 2. StreamField Enhancements
- `form_attrs` support added to all StreamField blocks
- Better API extraction for preview content

### StreamField API Serialization

#### Basic StreamField Setup
```python
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.api import APIField

class BlogPage(Page):
    body = StreamField([
        ('heading', blocks.CharBlock()),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ], use_json_field=True)

    # Expose in API
    api_fields = [
        APIField('body'),
    ]
```

#### Custom Block API Representation
```python
from wagtail.images.blocks import ImageChooserBlock
from rest_framework import serializers

class CustomImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['title', 'url', 'thumbnail', 'width', 'height']

    def get_url(self, obj):
        return obj.get_rendition('fill-1200x630|jpegquality-85').url

    def get_thumbnail(self, obj):
        return obj.get_rendition('fill-300x200').url

class APIImageChooserBlock(ImageChooserBlock):
    """Custom image block with optimized API output."""

    def get_api_representation(self, value, context=None):
        """
        Override default serialization.
        Called by StreamField serializer.
        """
        if value:
            return CustomImageSerializer(context=context).to_representation(value)
        return None

# Use in StreamField
class BlogPage(Page):
    body = StreamField([
        ('image', APIImageChooserBlock()),
        ('paragraph', blocks.RichTextBlock()),
    ], use_json_field=True)
```

### Page Model Patterns (from project)

```python
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.api import APIField

class ExercisePage(Page):
    """Exercise page with fill-in-blank support."""

    # Fields
    description = RichTextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    template_code = models.TextField(help_text='Code template with {{BLANK_N}} syntax')
    solutions = models.JSONField(
        default=dict,
        help_text='Solutions dict: {"1": "answer", "2": "answer"}'
    )

    # Admin panels
    content_panels = Page.content_panels + [
        FieldPanel('description'),
        FieldPanel('difficulty'),
        FieldPanel('template_code'),
        FieldPanel('solutions'),
    ]

    # API configuration
    api_fields = [
        APIField('description'),
        APIField('difficulty'),
        APIField('template_code'),
        APIField('solutions'),
    ]

    # Parent/child page rules
    parent_page_types = ['exercises.ExerciseIndexPage']
    subpage_types = []
```

### Wagtail API Endpoints

#### Project Pattern
```python
# apps/api/views/wagtail.py
from wagtail.models import Page
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def list_exercises(request):
    """GET /api/v1/wagtail/exercises/"""
    exercises = ExercisePage.objects.live().prefetch_related(
        'tags'
    ).select_related(
        'owner'
    ).order_by('-first_published_at')

    # Paginate
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(exercises, request)

    # Serialize
    data = []
    for exercise in page:
        data.append({
            'id': exercise.id,
            'title': exercise.title,
            'slug': exercise.slug,
            'difficulty': exercise.difficulty,
            'description': exercise.description,
            'url': exercise.get_url(request),
        })

    return paginator.get_paginated_response(data)
```

#### Slug-Based Routing
```python
# Wagtail uses slugs, not IDs
GET /api/v1/wagtail/exercises/python-variables/
GET /api/v1/wagtail/courses/intro-to-python/

# Django models use IDs
GET /api/v1/exercises/123/submit/
GET /api/v1/courses/45/
```

### Wagtail + React Integration

#### React Component Example
```jsx
import { useQuery } from '@tanstack/react-query'
import { sanitize } from '@/utils/sanitize'

function ExercisePage({ slug }) {
  const { data, isLoading } = useQuery({
    queryKey: ['exercise', slug],
    queryFn: () => fetch(`/api/v1/wagtail/exercises/${slug}/`).then(r => r.json()),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  if (isLoading) return <div>Loading...</div>

  return (
    <div>
      <h1>{data.title}</h1>
      <div dangerouslySetInnerHTML={{
        __html: sanitize.rich(data.description)
      }} />
      {/* CodeMirror editor for template_code */}
    </div>
  )
}
```

---

## React 19 - Modern Frontend Patterns

### Official Documentation
- **URL:** https://react.dev/
- **Hooks Reference:** https://react.dev/reference/react
- **New Features:** https://react.dev/blog/2025/04/25/react-19

### React 19 Key Features

#### 1. Automatic Optimizations via Compiler
React 19 introduces a compiler that automatically optimizes components:
- **No more manual `useCallback`/`useMemo` in many cases**
- Compiler handles memoization behind the scenes
- Focus on clean code, let React optimize

**However:** Still use hooks when:
- Integrating with third-party libraries expecting stable references
- Passing callbacks to custom hooks with internal effects
- Explicit performance optimization for heavy computations

#### 2. Modern Hooks Patterns

**useEffect Best Practices:**
```jsx
import { useEffect, useState } from 'react'

function UserProfile({ userId }) {
  const [user, setUser] = useState(null)

  useEffect(() => {
    // Good: Async function inside effect
    async function fetchUser() {
      const response = await fetch(`/api/users/${userId}`)
      const data = await response.json()
      setUser(data)
    }

    fetchUser()

    // Cleanup function
    return () => {
      // Cancel requests, clear timers, etc.
    }
  }, [userId]) // Dependencies: re-run when userId changes

  return <div>{user?.name}</div>
}
```

**useCallback for Stable References:**
```jsx
import { useCallback } from 'react'

function SearchInput({ onSearch }) {
  const [query, setQuery] = useState('')

  // Wrap in useCallback for stable reference
  const handleSubmit = useCallback((e) => {
    e.preventDefault()
    onSearch(query)
  }, [query, onSearch])

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
    </form>
  )
}
```

**useMemo for Expensive Calculations:**
```jsx
import { useMemo } from 'react'

function CourseList({ courses, filters }) {
  // Expensive filtering/sorting only runs when dependencies change
  const filteredCourses = useMemo(() => {
    return courses
      .filter(c => filters.difficulty.includes(c.difficulty))
      .sort((a, b) => b.rating - a.rating)
  }, [courses, filters.difficulty])

  return (
    <ul>
      {filteredCourses.map(course => (
        <li key={course.id}>{course.title}</li>
      ))}
    </ul>
  )
}
```

### React Router 6.30 Patterns

#### Code Splitting with Lazy Loading
```jsx
import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

// Lazy load routes
const Home = lazy(() => import('./pages/Home'))
const Courses = lazy(() => import('./pages/Courses'))
const Exercise = lazy(() => import('./pages/Exercise'))

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/courses" element={<Courses />} />
          <Route path="/exercises/:slug" element={<Exercise />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
```

#### Data Router with Loaders (React Router 6.4+)
```jsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom'

const router = createBrowserRouter([
  {
    path: '/courses/:id',
    element: <CoursePage />,
    loader: async ({ params }) => {
      // Data loads in parallel with code splitting
      const response = await fetch(`/api/v1/courses/${params.id}`)
      return response.json()
    },
  },
])

function App() {
  return <RouterProvider router={router} />
}

// In component
import { useLoaderData } from 'react-router-dom'

function CoursePage() {
  const course = useLoaderData() // Data from loader
  return <h1>{course.title}</h1>
}
```

### Error Boundaries
```jsx
import { Component } from 'react'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    // Log to error tracking service
  }

  render() {
    if (this.state.hasError) {
      return (
        <div>
          <h1>Something went wrong</h1>
          <p>{this.state.error?.message}</p>
        </div>
      )
    }

    return this.props.children
  }
}

// Usage
<ErrorBoundary>
  <Suspense fallback={<Loading />}>
    <Routes>...</Routes>
  </Suspense>
</ErrorBoundary>
```

---

## TanStack React Query 5.90 - Data Fetching

### Official Documentation
- **URL:** https://tanstack.com/query/latest
- **Queries:** https://tanstack.com/query/v5/docs/framework/react/guides/queries
- **Mutations:** https://tanstack.com/query/v5/docs/framework/react/guides/mutations

### Project Implementation Pattern

From `/frontend/src/hooks/useForumQuery.js`:

#### Query Key Factories
```javascript
// Hierarchical cache key structure
export const forumKeys = {
  all: ['forums'],
  lists: () => [...forumKeys.all, 'list'],
  list: () => [...forumKeys.lists()],
  details: () => [...forumKeys.all, 'detail'],
  detail: (slug) => [...forumKeys.details(), slug],
  topics: (slug) => [...forumKeys.detail(slug), 'topics'],
  stats: (slug) => [...forumKeys.detail(slug), 'stats'],
}

// Benefits:
// - Invalidate all forums: forumKeys.all
// - Invalidate forum lists: forumKeys.lists()
// - Invalidate specific forum: forumKeys.detail(slug)
```

#### Basic Query Hook
```javascript
export const useForums = (options = {}) => {
  return useQuery({
    queryKey: forumKeys.list(),
    queryFn: forumApi.getForums,
    staleTime: 5 * 60 * 1000, // 5 minutes - data considered fresh
    gcTime: 10 * 60 * 1000,   // 10 minutes - cache garbage collection
    ...options, // Allow overrides
  })
}

// Usage in component
function ForumList() {
  const { data, isLoading, error, refetch } = useForums()

  if (isLoading) return <Spinner />
  if (error) return <Error error={error} />

  return (
    <div>
      {data.forums.map(forum => (
        <ForumCard key={forum.id} forum={forum} />
      ))}
    </div>
  )
}
```

#### Mutation with Optimistic Updates
```javascript
export const useCreatePost = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: forumApi.createPost,

    // 1. Before request (optimistic update)
    onMutate: async (newPost) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: topicKeys.posts(newPost.topic)
      })

      // Snapshot previous value
      const previousPosts = queryClient.getQueryData(
        topicKeys.posts(newPost.topic)
      )

      // Optimistically add new post
      queryClient.setQueryData(topicKeys.posts(newPost.topic), (old) => {
        if (!old) return old
        return {
          ...old,
          results: [
            ...old.results,
            {
              ...newPost,
              id: -Date.now(), // Temporary negative ID
              created_at: new Date().toISOString(),
              _isOptimistic: true, // Flag for UI
            },
          ],
        }
      })

      return { previousPosts } // Context for rollback
    },

    // 2. On error (rollback)
    onError: (err, newPost, context) => {
      if (context?.previousPosts) {
        queryClient.setQueryData(
          topicKeys.posts(newPost.topic),
          context.previousPosts
        )
      }
      toast.error('Failed to create post')
    },

    // 3. On success (update with real data)
    onSuccess: (newPost) => {
      queryClient.invalidateQueries({
        queryKey: topicKeys.posts(newPost.topic)
      })
      toast.success('Post created!')
    },
  })
}
```

#### Infinite Queries (Cursor Pagination)
```javascript
export const useInfiniteTopicPosts = (topicId, options = {}) => {
  return useInfiniteQuery({
    queryKey: topicKeys.posts(topicId),

    queryFn: async ({ pageParam = null }) => {
      const params = {}
      if (pageParam) {
        params.cursor = pageParam
      }
      return forumApi.getTopicPosts(topicId, params)
    },

    getNextPageParam: (lastPage) => {
      // Extract cursor from 'next' URL
      if (lastPage.next) {
        const url = new URL(lastPage.next, window.location.origin)
        return url.searchParams.get('cursor')
      }
      return undefined // No more pages
    },

    enabled: !!topicId,
    staleTime: 30 * 1000, // 30 seconds
    ...options,
  })
}

// Usage
function PostList({ topicId }) {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteTopicPosts(topicId)

  return (
    <div>
      {data.pages.map((page, i) => (
        <React.Fragment key={i}>
          {page.results.map(post => (
            <PostCard key={post.id} post={post} />
          ))}
        </React.Fragment>
      ))}

      {hasNextPage && (
        <button
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
        >
          {isFetchingNextPage ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  )
}
```

### Cache Invalidation Strategies

#### 1. Invalidate Specific Query
```javascript
// Invalidate and refetch
queryClient.invalidateQueries({
  queryKey: forumKeys.detail('python-help')
})
```

#### 2. Invalidate Multiple Queries
```javascript
// Invalidate all forum-related queries
queryClient.invalidateQueries({
  queryKey: forumKeys.all
})

// Invalidate all topic lists
queryClient.invalidateQueries({
  queryKey: topicKeys.lists()
})
```

#### 3. Remove Query from Cache
```javascript
// Remove specific query
queryClient.removeQueries({
  queryKey: topicKeys.detail(topicId)
})
```

#### 4. Set Query Data Directly
```javascript
// Update cache directly without refetch
queryClient.setQueryData(
  forumKeys.detail('python-help'),
  (oldData) => ({
    ...oldData,
    posts_count: oldData.posts_count + 1
  })
)
```

### Stale Time vs Cache Time

```javascript
useQuery({
  queryKey: ['data'],
  queryFn: fetchData,
  staleTime: 5 * 60 * 1000,  // 5 minutes - "fresh" period
  gcTime: 10 * 60 * 1000,    // 10 minutes - cache lifetime
})

// Timeline:
// 0-5min:  Data is "fresh", no refetch on mount
// 5-10min: Data is "stale", refetch on mount if component remounts
// 10min+:  Data garbage collected, fresh fetch required
```

**Recommendations:**
- **Stale time:** How long data is considered fresh (no refetch)
  - Static content: 10-30 minutes
  - Dynamic content: 1-5 minutes
  - Real-time data: 0-30 seconds
- **Cache time:** How long unused data stays in memory
  - Usually 2-3x stale time

---

## Zustand 4.5 - State Management

### Official Documentation
- **URL:** https://github.com/pmndrs/zustand
- **Middleware:** https://github.com/pmndrs/zustand#middleware

### When to Use Zustand vs React Query

**Use React Query for:**
- Server state (API data)
- Caching, background refetching
- Optimistic updates
- Request deduplication

**Use Zustand for:**
- Client-only state (UI state)
- Authentication state
- Theme preferences
- Form state (complex forms)

### Basic Store Pattern

```javascript
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

// Simple store
export const useAuthStore = create((set) => ({
  user: null,
  token: null,

  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),

  logout: () => set({ user: null, token: null }),
}))

// Usage in component
function Header() {
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)

  return (
    <div>
      <span>{user?.username}</span>
      <button onClick={logout}>Logout</button>
    </div>
  )
}
```

### Store with Middleware

```javascript
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

export const useSettingsStore = create(
  devtools(
    persist(
      (set, get) => ({
        theme: 'light',
        language: 'en',
        notifications: true,

        toggleTheme: () => set((state) => ({
          theme: state.theme === 'light' ? 'dark' : 'light'
        })),

        setLanguage: (language) => set({ language }),

        toggleNotifications: () => set((state) => ({
          notifications: !state.notifications
        })),
      }),
      {
        name: 'settings-storage', // localStorage key
        partialize: (state) => ({
          // Only persist these fields
          theme: state.theme,
          language: state.language,
        }),
      }
    )
  )
)
```

### Slice Pattern (Large Apps)

```javascript
// authSlice.js
export const createAuthSlice = (set) => ({
  user: null,
  token: null,
  login: (user, token) => set({ user, token }),
  logout: () => set({ user: null, token: null }),
})

// settingsSlice.js
export const createSettingsSlice = (set) => ({
  theme: 'light',
  toggleTheme: () => set((state) => ({
    theme: state.theme === 'light' ? 'dark' : 'light'
  })),
})

// Combined store
import { create } from 'zustand'

export const useAppStore = create((set, get) => ({
  ...createAuthSlice(set, get),
  ...createSettingsSlice(set, get),
}))
```

### Zustand + React Query Integration

```javascript
import { create } from 'zustand'
import { useQuery } from '@tanstack/react-query'

// Client state in Zustand
export const useUIStore = create((set) => ({
  sidebarOpen: true,
  modalOpen: false,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  openModal: () => set({ modalOpen: true }),
  closeModal: () => set({ modalOpen: false }),
}))

// Server state in React Query
function CourseList() {
  const { data: courses } = useQuery({
    queryKey: ['courses'],
    queryFn: fetchCourses,
  })

  const sidebarOpen = useUIStore((state) => state.sidebarOpen)
  const toggleSidebar = useUIStore((state) => state.toggleSidebar)

  return (
    <div className={sidebarOpen ? 'with-sidebar' : ''}>
      {/* Render courses from React Query */}
    </div>
  )
}
```

---

## CodeMirror 6 - Educational Code Editor

### Official Documentation
- **URL:** https://codemirror.net/
- **System Guide:** https://codemirror.net/docs/guide/
- **Extensions:** https://codemirror.net/docs/extensions/

### CodeMirror 6 Architecture

CodeMirror 6 is built around:
- **State:** Immutable document state
- **View:** DOM representation
- **Extensions:** Plugins that add functionality
- **Transactions:** State changes

### Project Usage (Fill-in-Blank Widgets)

From `CLAUDE.md`:

```javascript
import { EditorView, WidgetType } from '@codemirror/view'

// Custom widget for fill-in-blank exercises
class BlankWidget extends WidgetType {
  constructor(blankId, solution) {
    super()
    this.blankId = blankId
    this.solution = solution
  }

  toDOM() {
    const input = document.createElement('input')
    input.type = 'text'
    input.className = 'blank-input'
    input.dataset.blankId = this.blankId
    input.placeholder = `Blank ${this.blankId}`

    // Add validation on blur
    input.addEventListener('blur', () => {
      const userAnswer = input.value.trim()
      if (userAnswer === this.solution) {
        input.classList.add('correct')
        input.classList.remove('incorrect')
      } else {
        input.classList.add('incorrect')
        input.classList.remove('correct')
      }
    })

    return input
  }

  ignoreEvent(event) {
    // Allow all events on the input (typing, focus, etc.)
    return event.type !== 'mousedown'
  }
}

// Replace {{BLANK_N}} with widgets
function createBlankDecorations(view, solutions) {
  const decorations = []
  const text = view.state.doc.toString()
  const regex = /\{\{BLANK_(\d+)\}\}/g

  let match
  while ((match = regex.exec(text)) !== null) {
    const blankId = match[1]
    const solution = solutions[blankId]
    const from = match.index
    const to = from + match[0].length

    decorations.push(
      Decoration.replace({
        widget: new BlankWidget(blankId, solution)
      }).range(from, to)
    )
  }

  return Decoration.set(decorations)
}
```

### Basic CodeMirror Setup

```javascript
import { EditorView, basicSetup } from 'codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'

const editor = new EditorView({
  doc: 'print("Hello World")',
  extensions: [
    basicSetup,
    python(),
    oneDark,
  ],
  parent: document.getElementById('editor'),
})
```

### React Integration with @uiw/react-codemirror

```jsx
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'

function CodeEditor({ value, onChange, readOnly = false }) {
  return (
    <CodeMirror
      value={value}
      height="400px"
      theme={oneDark}
      extensions={[python()]}
      onChange={onChange}
      editable={!readOnly}
      basicSetup={{
        lineNumbers: true,
        highlightActiveLineGutter: true,
        highlightSpecialChars: true,
        foldGutter: true,
        drawSelection: true,
        dropCursor: true,
        allowMultipleSelections: true,
        indentOnInput: true,
        syntaxHighlighting: true,
        bracketMatching: true,
        closeBrackets: true,
        autocompletion: true,
        rectangularSelection: true,
        crosshairCursor: true,
        highlightActiveLine: true,
        highlightSelectionMatches: true,
        closeBracketsKeymap: true,
        searchKeymap: true,
        foldKeymap: true,
        completionKeymap: true,
        lintKeymap: true,
      }}
    />
  )
}
```

### Custom Extensions

```javascript
import { ViewPlugin, Decoration, EditorView } from '@codemirror/view'
import { StateField, StateEffect } from '@codemirror/state'

// Extension to highlight errors
const highlightErrors = StateField.define({
  create() {
    return Decoration.none
  },

  update(decorations, tr) {
    // Update decorations based on transaction
    const effects = tr.effects.filter(e => e.is(addErrorEffect))

    if (effects.length === 0) return decorations

    const newDecorations = []
    for (const effect of effects) {
      const { line, message } = effect.value
      const lineStart = tr.state.doc.line(line).from

      newDecorations.push(
        Decoration.line({
          attributes: { class: 'error-line' }
        }).range(lineStart)
      )
    }

    return Decoration.set(newDecorations)
  },

  provide: f => EditorView.decorations.from(f)
})

// Effect to add errors
const addErrorEffect = StateEffect.define()

// Function to highlight errors
function highlightError(view, line, message) {
  view.dispatch({
    effects: addErrorEffect.of({ line, message })
  })
}
```

---

## django-machina 1.3 - Forum Integration

### Official Documentation
- **URL:** https://django-machina.readthedocs.io/en/stable/
- **Permissions:** https://django-machina.readthedocs.io/en/stable/forum_permissions.html
- **Moderation:** https://django-machina.readthedocs.io/en/stable/machina_apps_reference/forum_moderation.html

### Permission System

#### Per-Forum Permissions
django-machina uses per-forum permissions (not trust levels):
- Permissions can be granted to users (anonymous, specific user, all registered users)
- Permissions can be granted to groups
- Some permissions can be global (all forums)

```python
from machina.core.loading import get_class

PermissionHandler = get_class('forum_permission.handler', 'PermissionHandler')
perm_handler = PermissionHandler()

# Check forum access
if perm_handler.can_read_forum(forum, user):
    # User can view forum
    pass

# Check moderation permissions
if perm_handler.can_lock_topics(forum, user):
    # User can lock topics in this forum
    pass

# Check posting permissions
if perm_handler.can_create_topics(forum, user):
    # User can create topics
    pass
```

### Project's Trust Level System

The project implements a **custom trust level system** on top of machina:

```python
# apps/forum_integration/models.py
class TrustLevel(models.Model):
    TRUST_LEVELS = [
        (0, 'New User'),     # TL0: Requires moderation
        (1, 'Basic User'),   # TL1: Can post images
        (2, 'Member'),       # TL2: Extended edit, wiki posts
        (3, 'Regular'),      # TL3: Basic moderation
        (4, 'Leader'),       # TL4: Full moderation
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    level = models.IntegerField(default=0, choices=TRUST_LEVELS)

    # Metrics for promotion
    posts_read = models.IntegerField(default=0)
    topics_viewed = models.IntegerField(default=0)
    time_read = models.DurationField(default=timedelta())
    posts_created = models.IntegerField(default=0)
    likes_given = models.IntegerField(default=0)
    likes_received = models.IntegerField(default=0)
    days_visited = models.IntegerField(default=0)

    def check_for_promotion(self):
        """Check if user qualifies for promotion."""
        # TL0 -> TL1: Read 10 posts, spend 10 minutes
        if self.level == 0:
            if self.posts_read >= 10 and self.time_read >= timedelta(minutes=10):
                return 1

        # TL1 -> TL2: Visit 15 days, read 100 posts, receive 1 like
        elif self.level == 1:
            if (self.days_visited >= 15 and
                self.posts_read >= 100 and
                self.likes_received >= 1):
                return 2

        # TL2 -> TL3: Visit 50 days, read 500 posts, receive 10 likes
        elif self.level == 2:
            if (self.days_visited >= 50 and
                self.posts_read >= 500 and
                self.likes_received >= 10 and
                self.likes_given >= 30):
                return 3

        # TL3 -> TL4: Manual promotion by admins
        return None
```

#### Trust Level + Moderation Pattern

```python
# Check if post needs moderation
user = request.user
approved = True

if not user.is_staff and not user.is_superuser:
    if hasattr(user, 'trust_level'):
        # TL0 users need moderation
        if user.trust_level.level == 0:
            approved = False
            # Add to review queue
            from apps.api.services.container import container
            review_service = container.get_review_queue_service()
            review_service.check_new_post(post)
    else:
        # Users without trust level need moderation
        approved = False

post = Post.objects.create(
    topic=topic,
    poster=user,
    content=content,
    approved=approved
)
```

### Forum Statistics Service Pattern

From `/apps/api/services/statistics_service.py`:

```python
class ForumStatisticsService:
    """
    Service for calculating and caching forum statistics.
    Uses dependency injection for repositories and cache backend.
    """

    CACHE_TIMEOUT_SHORT = 60   # 1 minute
    CACHE_TIMEOUT_MEDIUM = 300 # 5 minutes
    CACHE_VERSION = 'v1'

    def __init__(self, user_repo, topic_repo, post_repo, forum_repo, cache):
        self.user_repo = user_repo
        self.topic_repo = topic_repo
        self.post_repo = post_repo
        self.forum_repo = forum_repo
        self.cache = cache

    def get_forum_statistics(self) -> Dict[str, Any]:
        """Get overall forum statistics with caching."""
        cache_key = f'{self.CACHE_VERSION}:forum:stats:all'

        stats = self.cache.get(cache_key)
        if stats is not None:
            return stats

        stats = {
            'total_topics': self.topic_repo.count_approved(),
            'total_posts': self.post_repo.count_approved(),
            'total_users': self.user_repo.count(is_active=True),
            'online_users': self._get_online_users_count(),
        }

        self.cache.set(cache_key, stats, timeout=self.CACHE_TIMEOUT_SHORT)
        return stats

    def invalidate_cache(self, forum_id=None, user_id=None):
        """Invalidate statistics caches."""
        if forum_id:
            self.cache.delete(f'{self.CACHE_VERSION}:forum:stats:{forum_id}')
        if user_id:
            self.cache.delete(f'{self.CACHE_VERSION}:forum:user_stats:{user_id}')

        self.cache.delete(f'{self.CACHE_VERSION}:forum:stats:all')
```

### Review Queue System

```python
# apps/forum_integration/models.py
class ReviewQueue(models.Model):
    REVIEW_TYPES = [
        ('flagged_post', 'Flagged Post'),
        ('new_user_post', 'New User Post'),
        ('spam_detection', 'Spam Detection'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    PRIORITY_CHOICES = [
        (1, 'Critical'),
        (2, 'High'),
        (3, 'Medium'),
        (4, 'Low'),
    ]

    review_type = models.CharField(max_length=20, choices=REVIEW_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=3)

    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True)

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_reports_made')
    assigned_moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    reason = models.TextField()
    resolution_notes = models.TextField(blank=True)
    score = models.FloatField(default=0.0)  # Priority score

    def calculate_priority_score(self):
        """Calculate priority score based on multiple factors."""
        score = 0.0

        # Base priority
        priority_scores = {1: 100, 2: 75, 3: 50, 4: 25}
        score += priority_scores.get(self.priority, 50)

        # Age factor (older = higher priority)
        age_hours = (timezone.now() - self.created_at).total_seconds() / 3600
        score += min(age_hours * 0.5, 50)

        # Trust level of reported user
        if self.reported_user and hasattr(self.reported_user, 'trust_level'):
            score += (4 - self.reported_user.trust_level.level) * 5

        return score
```

---

## Testing Patterns

### Backend Testing with Django

#### APITestCase Setup
```python
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class ForumAPITests(APITestCase):
    fixtures = ['forums.json', 'users.json']

    @classmethod
    def setUpTestData(cls):
        """Run once per test class - immutable data."""
        cls.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        cls.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='user123'
        )

    def setUp(self):
        """Run before each test method - mutable data."""
        self.client.force_authenticate(user=self.regular_user)

    def test_create_topic_authenticated(self):
        """Test POST /api/v1/topics/"""
        response = self.client.post('/api/v1/topics/', {
            'forum': 1,
            'subject': 'Test Topic',
            'content': 'Test content'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['subject'], 'Test Topic')

    def test_create_topic_unauthenticated(self):
        """Test POST /api/v1/topics/ without auth."""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/v1/topics/', {
            'forum': 1,
            'subject': 'Test Topic'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_topics_with_n_plus_one_check(self):
        """Test GET /api/v1/topics/ doesn't have N+1 queries."""
        from django.test.utils import override_settings
        from django.db import connection
        from django.test import RequestFactory

        with self.assertNumQueries(3):  # Should be <= 3 queries
            response = self.client.get('/api/v1/topics/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
```

#### Testing Services
```python
from django.test import TestCase
from django.core.cache import cache
from apps.api.services.statistics_service import ForumStatisticsService
from apps.api.services.repositories import (
    UserRepository, TopicRepository, PostRepository, ForumRepository
)

class ForumStatisticsServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.service = ForumStatisticsService(
            user_repo=UserRepository(),
            topic_repo=TopicRepository(),
            post_repo=PostRepository(),
            forum_repo=ForumRepository(),
            cache=cache
        )

    def test_get_forum_statistics_caching(self):
        """Test that statistics are cached."""
        # First call - should hit database
        stats1 = self.service.get_forum_statistics()

        # Second call - should hit cache
        stats2 = self.service.get_forum_statistics()

        self.assertEqual(stats1, stats2)
        # Verify cache hit by checking cache directly
        cache_key = f'{self.service.CACHE_VERSION}:forum:stats:all'
        self.assertIsNotNone(cache.get(cache_key))

    def test_invalidate_cache(self):
        """Test cache invalidation."""
        self.service.get_forum_statistics()
        self.service.invalidate_cache()

        cache_key = f'{self.service.CACHE_VERSION}:forum:stats:all'
        self.assertIsNone(cache.get(cache_key))
```

### Frontend Testing with Vitest + Testing Library

#### Component Testing
```jsx
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import ForumList from './ForumList'
import * as forumApi from '../api/forumApi'

describe('ForumList', () => {
  let queryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })
  })

  afterEach(() => {
    queryClient.clear()
  })

  function renderWithQuery(ui) {
    return render(
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    )
  }

  test('displays forums after loading', async () => {
    // Mock API call
    vi.spyOn(forumApi, 'getForums').mockResolvedValue({
      forums: [
        { id: 1, name: 'Python Help', slug: 'python-help' },
        { id: 2, name: 'General Discussion', slug: 'general' },
      ],
    })

    renderWithQuery(<ForumList />)

    // Loading state
    expect(screen.getByText(/loading/i)).toBeInTheDocument()

    // Loaded state
    await waitFor(() => {
      expect(screen.getByText('Python Help')).toBeInTheDocument()
    })
    expect(screen.getByText('General Discussion')).toBeInTheDocument()
  })

  test('handles error state', async () => {
    vi.spyOn(forumApi, 'getForums').mockRejectedValue(
      new Error('Failed to fetch')
    )

    renderWithQuery(<ForumList />)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  test('clicking forum navigates to detail', async () => {
    const user = userEvent.setup()

    vi.spyOn(forumApi, 'getForums').mockResolvedValue({
      forums: [{ id: 1, name: 'Python Help', slug: 'python-help' }],
    })

    renderWithQuery(<ForumList />)

    await waitFor(() => {
      expect(screen.getByText('Python Help')).toBeInTheDocument()
    })

    const forumLink = screen.getByRole('link', { name: /python help/i })
    await user.click(forumLink)

    // Verify navigation (with React Router testing)
    expect(window.location.pathname).toBe('/forums/python-help')
  })
})
```

#### Hook Testing
```jsx
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi } from 'vitest'
import { useForums } from './useForumQuery'
import * as forumApi from '../api/forumApi'

describe('useForums', () => {
  let queryClient

  function wrapper({ children }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    })
  })

  test('fetches and returns forums', async () => {
    vi.spyOn(forumApi, 'getForums').mockResolvedValue({
      forums: [{ id: 1, name: 'Test Forum' }],
    })

    const { result } = renderHook(() => useForums(), { wrapper })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data.forums).toHaveLength(1)
    expect(result.current.data.forums[0].name).toBe('Test Forum')
  })
})
```

---

## Implementation Recommendations

### Phase 2 Development Priorities

#### 1. Backend Development

**Service Layer Pattern:**
- ✅ Continue using service layer for business logic
- ✅ Use dependency injection via container
- ✅ Repository pattern for data access
- ✅ Redis caching for hot paths

**Query Optimization:**
- ✅ Apply `select_related` for FK/OneToOne
- ✅ Apply `prefetch_related` for M2M/reverse FK
- ✅ Test query counts with performance tests
- ✅ Inline optimizations in views (YAGNI)

**Security:**
- ✅ Three-layer authorization (queryset filter, permissions, ownership forcing)
- ✅ Validate all user input
- ✅ Sanitize all output (DOMPurify on frontend)
- ✅ Test cross-user access scenarios

#### 2. Frontend Development

**React Patterns:**
- ✅ Use React 19's compiler for auto-optimization
- ✅ Lazy load routes with React.lazy + Suspense
- ✅ Error boundaries around route components
- ✅ Code splitting at route level

**Data Fetching:**
- ✅ TanStack Query for all server state
- ✅ Zustand for client-only UI state
- ✅ Query key factories for cache management
- ✅ Optimistic updates for better UX

**Code Editor:**
- ✅ CodeMirror 6 for exercises
- ✅ Custom widgets for fill-in-blank
- ✅ Syntax highlighting per language
- ✅ Read-only mode for solutions

#### 3. Wagtail CMS

**Headless API:**
- ✅ Use slug-based routing for pages
- ✅ Custom `get_api_representation` for blocks
- ✅ Optimize queries with prefetch/select
- ✅ Cache API responses (5-15 minutes)

**StreamField:**
- ✅ Rich content blocks for educational content
- ✅ Code blocks with syntax highlighting
- ✅ Video/image embeds with optimized renditions
- ✅ Callout/quote blocks for emphasis

#### 4. Forum Integration

**Trust Levels:**
- ✅ Automatic promotion based on metrics
- ✅ TL0 requires moderation
- ✅ TL1+ auto-approved posts
- ✅ TL3+ basic moderation powers

**Moderation:**
- ✅ Review queue with priority scoring
- ✅ Edit history tracking
- ✅ Moderation statistics
- ✅ Forum customization (icons, colors)

#### 5. Testing Strategy

**Backend:**
- ✅ APITestCase for endpoint testing
- ✅ Service tests with cache mocking
- ✅ N+1 query performance tests
- ✅ Security tests (cross-user access)

**Frontend:**
- ✅ Vitest + Testing Library
- ✅ Component integration tests
- ✅ Hook tests
- ✅ E2E tests with Playwright

---

## Version-Specific Gotchas

### Django 5.2
- ⚠️ Cannot migrate to/from composite PKs
- ⚠️ Unsaved instances raise ValueError in filters
- ✅ PostgreSQL recommended for production

### React 19
- ⚠️ Compiler auto-optimizes, but still use hooks for:
  - Third-party library integrations
  - Custom hooks with effects
  - Heavy computations
- ✅ New Suspense improvements
- ✅ Better error handling

### TanStack Query 5
- ⚠️ `cacheTime` renamed to `gcTime`
- ⚠️ Different cache invalidation API
- ✅ Better TypeScript support
- ✅ Improved devtools

### Wagtail 7.1
- ✅ Improved headless support
- ✅ Better live preview
- ✅ StreamField enhancements
- ⚠️ Use `use_json_field=True` for new StreamFields

---

## Additional Resources

### Django
- Official Docs: https://docs.djangoproject.com/en/5.2/
- DRF Docs: https://www.django-rest-framework.org/
- Classy DRF: https://www.cdrf.co/

### Wagtail
- Official Docs: https://docs.wagtail.org/
- LearnWagtail Tutorials: https://learnwagtail.com/

### React
- Official Docs: https://react.dev/
- React Router: https://reactrouter.com/
- TanStack Query: https://tanstack.com/query/

### Testing
- Django Testing: https://docs.djangoproject.com/en/5.2/topics/testing/
- Testing Library: https://testing-library.com/
- Vitest: https://vitest.dev/

---

## Conclusion

This documentation research provides a comprehensive foundation for Phase 2 development of the Python Learning Studio platform. The frameworks and patterns documented here are all actively in use in the current codebase and have been validated against official documentation and community best practices.

**Key Takeaways:**
1. Service layer + Repository pattern working well for business logic
2. React Query + Zustand provides excellent state management
3. Query optimization critical for performance (select_related/prefetch_related)
4. Trust level system successfully extends django-machina
5. CodeMirror 6 ideal for educational code editors
6. Three-layer security prevents IDOR/BOLA vulnerabilities

Continue following these patterns for consistency and maintainability in Phase 2 development.
