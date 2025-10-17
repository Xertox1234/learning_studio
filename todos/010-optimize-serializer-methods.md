# Optimize Inefficient Serializer Methods (N+1 Queries)

**Priority**: 🟡 P1 - HIGH
**Category**: Performance
**Effort**: 6-8 hours
**Deadline**: Within 2 weeks

## Problem

Serializer methods trigger database queries for every object in the queryset, causing N+1 problems. This happens when computed fields like `enrollment_count` and `user_enrolled` execute queries per course instead of using annotated values.

## Locations

- `apps/api/serializers.py:71-78` (CourseSerializer)
- `apps/api/serializers.py:301-323` (Other serializers)

## Current Code

```python
# Line 71-78 in serializers.py
class CourseSerializer(serializers.ModelSerializer):
    enrollment_count = serializers.SerializerMethodField()
    user_enrolled = serializers.SerializerMethodField()

    def get_enrollment_count(self, obj):
        return obj.enrollments.count()  # Query per course!

    def get_user_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(
                user=request.user
            ).exists()  # Query per course!
        return False
```

## Performance Impact

### Without Optimization (50 courses)
```
Base query:          1 query
enrollment_count:   50 queries  (1 per course)
user_enrolled:      50 queries  (1 per course)
Total:             101 queries  (~800ms)
```

### With Optimization (50 courses)
```
Annotated query:     1 query
Total:               1 query   (~8ms)
100x improvement!
```

## Solution

Use Django's `annotate()` to compute values in the database, then read them in serializers without additional queries.

## Implementation Steps

### Step 1: Optimize CourseSerializer

```python
# apps/api/serializers.py
from rest_framework import serializers
from apps.learning.models import Course
from django.db.models import Count, Q


class CourseSerializer(serializers.ModelSerializer):
    # Read annotated values (no method field needed)
    enrollment_count = serializers.IntegerField(read_only=True)
    user_enrolled = serializers.BooleanField(read_only=True)

    # Other computed fields
    instructor_name = serializers.CharField(
        source='instructor.get_full_name',
        read_only=True
    )
    category_name = serializers.CharField(
        source='category.name',
        read_only=True
    )

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'instructor',
            'instructor_name',
            'category',
            'category_name',
            'difficulty_level',
            'enrollment_count',    # Annotated
            'user_enrolled',       # Annotated
            'is_published',
            'created_at',
        ]

    # No get_enrollment_count needed - reads from annotation
    # No get_user_enrolled needed - reads from annotation
```

### Step 2: Update CourseViewSet with Annotations

```python
# apps/api/viewsets/learning.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Exists, OuterRef
from apps.learning.models import Course, Enrollment
from apps.api.serializers import CourseSerializer


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Optimize queryset with annotations to avoid N+1 queries.
        """
        user = self.request.user

        # Subquery to check if user is enrolled
        user_enrollment = Enrollment.objects.filter(
            course=OuterRef('pk'),
            user=user,
            is_active=True
        )

        queryset = Course.objects.filter(
            is_published=True
        ).select_related(
            'instructor',
            'category'
        ).prefetch_related(
            'lessons'
        ).annotate(
            # Count total enrollments
            enrollment_count=Count('enrollments', distinct=True),

            # Check if current user is enrolled
            user_enrolled=Exists(user_enrollment)
        )

        return queryset
```

### Step 3: Optimize LessonSerializer

```python
# apps/api/serializers.py
class LessonSerializer(serializers.ModelSerializer):
    # Annotated fields
    completion_count = serializers.IntegerField(read_only=True)
    user_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id',
            'title',
            'order',
            'completion_count',  # Annotated
            'user_completed',    # Annotated
        ]
```

### Step 4: Update LessonViewSet

```python
# apps/api/viewsets/learning.py
from apps.learning.models import Lesson, Progress

class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Subquery for user completion
        user_progress = Progress.objects.filter(
            lesson=OuterRef('pk'),
            user=user,
            is_completed=True
        )

        queryset = Lesson.objects.filter(
            is_published=True
        ).select_related(
            'course'
        ).annotate(
            completion_count=Count(
                'progress',
                filter=Q(progress__is_completed=True),
                distinct=True
            ),
            user_completed=Exists(user_progress)
        )

        return queryset
```

### Step 5: Optimize ExerciseSerializer

```python
# apps/api/serializers.py
class ExerciseSerializer(serializers.ModelSerializer):
    # Annotated fields
    submission_count = serializers.IntegerField(read_only=True)
    user_has_submitted = serializers.BooleanField(read_only=True)
    user_best_score = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Exercise
        fields = [
            'id',
            'title',
            'difficulty_level',
            'submission_count',   # Annotated
            'user_has_submitted', # Annotated
            'user_best_score',    # Annotated
        ]
```

### Step 6: Update ExerciseViewSet

```python
# apps/api/viewsets/exercises.py
from apps.learning.models import Exercise, ExerciseSubmission
from django.db.models import Count, Exists, Max, Q

class ExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Subquery for user submissions
        user_submission = ExerciseSubmission.objects.filter(
            exercise=OuterRef('pk'),
            user=user
        )

        queryset = Exercise.objects.filter(
            is_published=True
        ).annotate(
            # Total submissions across all users
            submission_count=Count('submissions', distinct=True),

            # Check if current user has submitted
            user_has_submitted=Exists(user_submission),

            # User's best score
            user_best_score=Max(
                'submissions__score',
                filter=Q(submissions__user=user)
            )
        )

        return queryset
```

### Step 7: Optimize BlogPostSerializer

```python
# apps/api/serializers.py
class BlogPostSerializer(serializers.ModelSerializer):
    # Annotated fields
    comment_count = serializers.IntegerField(read_only=True)

    # Use source for FK relationships (no extra query with select_related)
    author_name = serializers.CharField(
        source='author.get_full_name',
        read_only=True
    )

    class Meta:
        model = BlogPost
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'author',
            'author_name',
            'comment_count',  # Annotated
            'published_date',
        ]
```

### Step 8: Create Reusable Annotation Utilities

```python
# apps/api/utils/queryset_annotations.py
"""
Reusable query annotations for common patterns.
"""
from django.db.models import Count, Exists, Max, Q, OuterRef


def annotate_enrollment_data(queryset, user):
    """
    Add enrollment-related annotations to course queryset.

    Args:
        queryset: Course queryset
        user: Current user

    Returns:
        Annotated queryset
    """
    from apps.learning.models import Enrollment

    user_enrollment = Enrollment.objects.filter(
        course=OuterRef('pk'),
        user=user,
        is_active=True
    )

    return queryset.annotate(
        enrollment_count=Count('enrollments', distinct=True),
        user_enrolled=Exists(user_enrollment)
    )


def annotate_lesson_progress(queryset, user):
    """
    Add progress annotations to lesson queryset.
    """
    from apps.learning.models import Progress

    user_progress = Progress.objects.filter(
        lesson=OuterRef('pk'),
        user=user,
        is_completed=True
    )

    return queryset.annotate(
        completion_count=Count(
            'progress',
            filter=Q(progress__is_completed=True),
            distinct=True
        ),
        user_completed=Exists(user_progress)
    )


def annotate_exercise_stats(queryset, user):
    """
    Add submission statistics to exercise queryset.
    """
    from apps.learning.models import ExerciseSubmission

    user_submission = ExerciseSubmission.objects.filter(
        exercise=OuterRef('pk'),
        user=user
    )

    return queryset.annotate(
        submission_count=Count('submissions', distinct=True),
        user_has_submitted=Exists(user_submission),
        user_best_score=Max(
            'submissions__score',
            filter=Q(submissions__user=user)
        )
    )
```

Usage:
```python
# In ViewSet
from apps.api.utils.queryset_annotations import annotate_enrollment_data

def get_queryset(self):
    queryset = Course.objects.filter(is_published=True)
    return annotate_enrollment_data(queryset, self.request.user)
```

### Step 9: Add Query Performance Tests

```python
# tests/test_serializer_performance.py
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection
from rest_framework.test import APIRequestFactory
from apps.api.viewsets.learning import CourseViewSet
from apps.learning.models import Course, Enrollment
from apps.users.models import User


class SerializerPerformanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test user
        cls.user = User.objects.create_user(
            email='test@test.com',
            password='password123'
        )

        # Create 50 courses
        for i in range(50):
            course = Course.objects.create(
                title=f'Course {i}',
                slug=f'course-{i}',
                is_published=True
            )

            # Add some enrollments
            for j in range(5):
                other_user = User.objects.create_user(
                    email=f'user{i}_{j}@test.com',
                    password='password123'
                )
                Enrollment.objects.create(
                    user=other_user,
                    course=course
                )

    @override_settings(DEBUG=True)
    def test_course_list_query_count(self):
        """
        Ensure course list endpoint uses minimal queries.
        """
        # Clear query log
        connection.queries_log.clear()

        # Create API request
        factory = APIRequestFactory()
        request = factory.get('/api/v1/learning/courses/')
        request.user = self.user

        # Get viewset response
        viewset = CourseViewSet.as_view({'get': 'list'})
        response = viewset(request)

        # Count queries
        query_count = len(connection.queries)

        # Should be:
        # 1. Main courses query with annotations
        # 2. Possible: select_related for instructor
        # Total: <= 3 queries

        self.assertLessEqual(
            query_count,
            5,
            f"Course list used {query_count} queries, expected <= 5"
        )

        # Verify data is correct
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 50)

        # Verify annotation fields present
        first_course = response.data[0]
        self.assertIn('enrollment_count', first_course)
        self.assertIn('user_enrolled', first_course)

    @override_settings(DEBUG=True)
    def test_lesson_list_query_count(self):
        """Ensure lesson list uses minimal queries"""
        connection.queries_log.clear()

        factory = APIRequestFactory()
        request = factory.get('/api/v1/learning/lessons/')
        request.user = self.user

        viewset = LessonViewSet.as_view({'get': 'list'})
        response = viewset(request)

        query_count = len(connection.queries)

        self.assertLessEqual(
            query_count,
            5,
            f"Lesson list used {query_count} queries, expected <= 5"
        )
```

### Step 10: Add Performance Monitoring

```python
# middleware/query_count_middleware.py
import time
from django.db import connection
from django.conf import settings


class QueryCountMiddleware:
    """
    Log slow requests with high query counts.
    Only active in development or with DEBUG=True.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start timer
        start_time = time.time()

        # Track queries
        if settings.DEBUG:
            start_queries = len(connection.queries)

        response = self.get_response(request)

        # Calculate metrics
        duration = time.time() - start_time

        if settings.DEBUG:
            query_count = len(connection.queries) - start_queries

            # Log if slow or high query count
            if duration > 1.0 or query_count > 20:
                print(f"\n⚠️  Slow request detected:")
                print(f"  Path: {request.path}")
                print(f"  Duration: {duration:.2f}s")
                print(f"  Queries: {query_count}")

                if query_count > 20:
                    print(f"  ⚠️  High query count! Consider optimization.")

        return response
```

Add to settings:
```python
# learning_community/settings/development.py
MIDDLEWARE += ['middleware.query_count_middleware.QueryCountMiddleware']
```

## Verification

### Before Fix (50 courses):
```python
# Django shell
from apps.api.viewsets.learning import CourseViewSet
from django.db import connection
from django.test.utils import override_settings

with override_settings(DEBUG=True):
    connection.queries_log.clear()
    # Make request
    # ...
    print(f"Queries: {len(connection.queries)}")
    # Output: Queries: 101
```

### After Fix (50 courses):
```python
# Same test
# Output: Queries: 3
```

## Checklist

- [ ] CourseSerializer optimized with annotations
- [ ] LessonSerializer optimized with annotations
- [ ] ExerciseSerializer optimized with annotations
- [ ] BlogPostSerializer optimized with annotations
- [ ] All ViewSets updated with annotated querysets
- [ ] Reusable annotation utilities created
- [ ] Query performance tests added
- [ ] Performance monitoring middleware added
- [ ] Manual testing confirms query reduction
- [ ] Documentation updated

## Expected Results

| Endpoint | Objects | Before | After | Improvement |
|----------|---------|--------|-------|-------------|
| /courses/ | 50 | 101 queries | 3 queries | 97% reduction |
| /lessons/ | 100 | 201 queries | 4 queries | 98% reduction |
| /exercises/ | 50 | 151 queries | 3 queries | 98% reduction |

**Response Time**: 800ms → 8ms (100x faster)

## Monitoring After Deployment

```python
# Management command to find N+1 issues
# management/commands/detect_n_plus_one.py

from django.core.management.base import BaseCommand
from django.test.utils import override_settings
from django.db import connection
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Detect potential N+1 query issues'

    @override_settings(DEBUG=True)
    def handle(self, *args, **options):
        test_user = User.objects.first()

        endpoints = [
            ('/api/v1/learning/courses/', 'GET'),
            ('/api/v1/learning/lessons/', 'GET'),
            ('/api/v1/exercises/', 'GET'),
        ]

        for path, method in endpoints:
            connection.queries_log.clear()

            # Make request (simplified)
            # In reality, use test client
            # client.get(path, user=test_user)

            query_count = len(connection.queries)

            if query_count > 20:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  {path}: {query_count} queries (potential N+1)"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ {path}: {query_count} queries"
                    )
                )
```

## References

- Django: Aggregation
- Django: Subquery and OuterRef
- Django: select_related and prefetch_related
- DRF: Serializer Performance
- Comprehensive Security Audit 2025, Finding #10
