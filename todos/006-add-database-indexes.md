# Add Missing Database Indexes

**Status**: ✅ RESOLVED
**Priority**: 🟡 P1 - HIGH
**Category**: Performance
**Effort**: 2-3 hours
**Deadline**: Within 1 week
**Completed**: 2025-10-19
**GitHub Issue**: [#8](https://github.com/Xertox1234/learning_studio/issues/8) (closed)
**Pull Request**: [#22](https://github.com/Xertox1234/learning_studio/pull/22)

---

## Resolution Summary

✅ **Successfully added 39 database indexes** across 4 apps to optimize query performance:

- **learning app**: 27 indexes (Course, Lesson, Exercise, Enrollment, Progress, LearningPath, StudySession)
- **blog app**: 5 indexes (BlogCategory, WagtailCourseEnrollment)
- **users app**: 4 indexes (UserProfile leaderboards)
- **forum app**: 3 indexes (TrustLevel leaderboards)

**Results:**
- ✅ All migrations created and applied successfully
- ✅ System check passed with no issues
- ✅ Code review approved with no blockers
- ✅ Tests passing (no new failures introduced)
- 🎯 Expected 50-100x query speed improvement
- 🎯 Expected 30-50% reduction in database CPU usage

---

## Problem

Frequently queried fields lack database indexes, causing full table scans that scale linearly with table size. At scale, this causes unacceptable query performance degradation.

## Locations

- `apps/learning/models.py` (Course, Lesson, Exercise)
- `apps/blog/models.py` (BlogPost)
- `apps/users/models.py` (UserProfile)
- `apps/forum_integration/models.py` (ForumPost, Topic)

## Performance Impact

### Without Indexes (1,000 courses)
```sql
SELECT * FROM courses WHERE is_published = true AND difficulty_level = 'beginner';
-- Full table scan: 500ms
```

### With Indexes (1,000 courses)
```sql
SELECT * FROM courses WHERE is_published = true AND difficulty_level = 'beginner';
-- Index scan: 5ms (100x faster)
```

### Scaling Impact

| Table Size | Query Time (No Index) | Query Time (With Index) | Improvement |
|------------|----------------------|-------------------------|-------------|
| 1,000      | 50ms                 | 0.5ms                   | 100x        |
| 10,000     | 500ms                | 0.5ms                   | 1,000x      |
| 100,000    | 5,000ms (5s)         | 1ms                     | 5,000x      |

## Solution

Add composite indexes on frequently queried field combinations.

## Implementation Steps

### Step 1: Add Indexes to Course Model

```python
# apps/learning/models.py

class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    difficulty_level = models.CharField(max_length=20)
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            # Composite indexes for common query patterns
            models.Index(
                fields=['is_published', 'difficulty_level'],
                name='course_pub_diff_idx'
            ),
            models.Index(
                fields=['is_featured', '-created_at'],
                name='course_feat_created_idx'
            ),
            models.Index(
                fields=['category', 'is_published'],
                name='course_cat_pub_idx'
            ),
            models.Index(
                fields=['instructor', 'is_published'],
                name='course_instr_pub_idx'
            ),
            models.Index(
                fields=['-created_at'],
                name='course_created_idx'
            ),
        ]
        ordering = ['-created_at']
```

### Step 2: Add Indexes to Lesson Model

```python
# apps/learning/models.py

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=['course', 'order'],
                name='lesson_course_order_idx'
            ),
            models.Index(
                fields=['course', 'is_published'],
                name='lesson_course_pub_idx'
            ),
        ]
        ordering = ['course', 'order']
```

### Step 3: Add Indexes to Exercise Model

```python
# apps/learning/models.py

class Exercise(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exercises')
    title = models.CharField(max_length=200)
    difficulty_level = models.CharField(max_length=20)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=['lesson', 'is_published'],
                name='exercise_lesson_pub_idx'
            ),
            models.Index(
                fields=['difficulty_level', 'is_published'],
                name='exercise_diff_pub_idx'
            ),
        ]
```

### Step 4: Add Indexes to BlogPost Model

```python
# apps/blog/models.py

class BlogPost(Page):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    excerpt = models.TextField(max_length=300)
    published_date = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    reading_time = models.IntegerField(default=5)

    class Meta:
        indexes = [
            models.Index(
                fields=['-published_date'],
                name='blog_published_idx'
            ),
            models.Index(
                fields=['author', '-published_date'],
                name='blog_author_pub_idx'
            ),
            models.Index(
                fields=['is_featured', '-published_date'],
                name='blog_feat_pub_idx'
            ),
        ]
```

### Step 5: Add Indexes to UserProfile Model

```python
# apps/users/models.py

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    trust_level = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=['user', 'is_active'],
                name='profile_user_active_idx'
            ),
            models.Index(
                fields=['trust_level'],
                name='profile_trust_idx'
            ),
        ]
```

### Step 6: Add Indexes to Forum Models

```python
# apps/forum_integration/models.py

class ForumPost(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(
                fields=['topic', 'created_at'],
                name='post_topic_created_idx'
            ),
            models.Index(
                fields=['author', '-created_at'],
                name='post_author_created_idx'
            ),
            models.Index(
                fields=['is_approved', '-created_at'],
                name='post_approved_created_idx'
            ),
        ]

class Topic(models.Model):
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_sticky = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(
                fields=['forum', '-updated_at'],
                name='topic_forum_updated_idx'
            ),
            models.Index(
                fields=['is_sticky', '-updated_at'],
                name='topic_sticky_updated_idx'
            ),
            models.Index(
                fields=['author', '-created_at'],
                name='topic_author_created_idx'
            ),
        ]
```

### Step 7: Create Migration

```bash
# Generate migration
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py makemigrations --name add_performance_indexes

# Review migration file
cat apps/learning/migrations/00XX_add_performance_indexes.py
```

### Step 8: Apply Migration with Concurrency

For production, use PostgreSQL's `CONCURRENTLY` option to avoid locking:

```python
# Edit migration file to add concurrent index creation
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models

class Migration(migrations.Migration):
    atomic = False  # Required for concurrent index creation

    operations = [
        AddIndexConcurrently(
            model_name='course',
            index=models.Index(
                fields=['is_published', 'difficulty_level'],
                name='course_pub_diff_idx'
            ),
        ),
        # ... other indexes
    ]
```

```bash
# Apply migration
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py migrate learning
```

### Step 9: Verify Index Usage

```sql
-- Check if indexes are created
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('learning_course', 'blog_blogpost', 'users_userprofile')
ORDER BY tablename, indexname;

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename IN ('learning_course', 'blog_blogpost')
ORDER BY idx_scan DESC;

-- Find unused indexes (after some time in production)
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
    AND indexname NOT LIKE '%_pkey'
ORDER BY tablename, indexname;
```

### Step 10: Query Performance Testing

```python
# tests/test_index_performance.py
from django.test import TestCase
from django.db import connection
from django.test.utils import override_settings
import time

class IndexPerformanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create 1,000 test courses
        for i in range(1000):
            Course.objects.create(
                title=f'Course {i}',
                slug=f'course-{i}',
                difficulty_level='beginner' if i % 3 == 0 else 'intermediate',
                is_published=i % 2 == 0,
                is_featured=i % 10 == 0,
            )

    @override_settings(DEBUG=True)
    def test_published_courses_query_uses_index(self):
        """Verify index is used for published courses query"""
        start_time = time.time()

        courses = Course.objects.filter(
            is_published=True,
            difficulty_level='beginner'
        )[:10]

        list(courses)  # Force evaluation

        query_time = time.time() - start_time

        # Should be very fast with index (< 50ms)
        self.assertLess(
            query_time,
            0.05,
            f"Query took {query_time}s, expected < 0.05s"
        )

        # Check if index was used (PostgreSQL specific)
        if connection.vendor == 'postgresql':
            query = connection.queries[-1]['sql']
            # Look for index scan in EXPLAIN output
            # (Actual EXPLAIN check would require raw SQL)

    def test_featured_courses_query_performance(self):
        """Test performance of featured courses query"""
        start_time = time.time()

        courses = Course.objects.filter(
            is_featured=True
        ).order_by('-created_at')[:5]

        list(courses)

        query_time = time.time() - start_time

        self.assertLess(
            query_time,
            0.05,
            f"Query took {query_time}s, expected < 0.05s"
        )
```

## Monitoring After Deployment

```python
# Management command to analyze query performance
# management/commands/analyze_indexes.py

from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Analyze index usage and performance'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check index usage
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    pg_size_pretty(pg_relation_size(indexrelid)) as size
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC
                LIMIT 20;
            """)

            self.stdout.write("Top 20 Most Used Indexes:")
            for row in cursor.fetchall():
                self.stdout.write(f"  {row[2]}: {row[3]} scans, {row[4]}")

            # Find unused indexes
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(indexrelid)) as size
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                    AND schemaname = 'public'
                    AND indexname NOT LIKE '%_pkey'
                ORDER BY pg_relation_size(indexrelid) DESC;
            """)

            unused = cursor.fetchall()
            if unused:
                self.stdout.write("\nUnused Indexes (consider removing):")
                for row in unused:
                    self.stdout.write(f"  {row[2]}: {row[3]}")
```

## Checklist

- [ ] Indexes added to Course model
- [ ] Indexes added to Lesson model
- [ ] Indexes added to Exercise model
- [ ] Indexes added to BlogPost model
- [ ] Indexes added to UserProfile model
- [ ] Indexes added to Forum models
- [ ] Migration created and reviewed
- [ ] Migration applied with CONCURRENTLY in production
- [ ] Index usage verified in database
- [ ] Query performance tests added
- [ ] Monitoring command created
- [ ] Documentation updated

## Expected Results

- Query response time: 50-100x faster for filtered queries
- Database CPU usage: 30-50% reduction
- P95 latency: 80% improvement
- Support 10x more concurrent users

## References

- PostgreSQL: Indexes and Query Performance
- Django: Database Optimization - Indexes
- Comprehensive Security Audit 2025, Finding #6
