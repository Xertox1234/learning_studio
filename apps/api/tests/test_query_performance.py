"""
Query performance tests to ensure N+1 queries are prevented.

These tests verify that our API endpoints use prefetch_related and select_related
appropriately to avoid N+1 query problems.
"""

from datetime import datetime
from django.test import TestCase, override_settings
from django.db import connection, reset_queries
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

User = get_user_model()


@override_settings(DEBUG=True)  # Required for query logging
class QueryPerformanceTests(TestCase):
    """Test query performance for various API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )

        # Import models here to avoid import errors during test discovery
        try:
            from apps.blog.models import (
                BlogPage, BlogCategory, HomePage,
                CoursePage, ExercisePage, SkillLevel
            )
            from wagtail.models import Page, Site

            # Create a root page and site if they don't exist
            root_page = Page.objects.filter(depth=1).first()
            if not root_page:
                root_page = Page.add_root(title="Root", slug="root")

            # Ensure site exists
            site, created = Site.objects.get_or_create(
                is_default_site=True,
                defaults={
                    'hostname': 'localhost',
                    'root_page': root_page,
                    'site_name': 'Test Site'
                }
            )

            # Create or get HomePage
            # Delete any existing home pages to avoid slug conflicts in tests
            HomePage.objects.all().delete()
            homepage = root_page.add_child(instance=HomePage(
                title='Test Home',
                slug='test-home',
                hero_title='Test Homepage',
                hero_subtitle='Testing',
                features_title='Features',
                live=True
            ))

            # Create blog categories
            self.categories = []
            for i in range(3):
                category, created = BlogCategory.objects.get_or_create(
                    name=f'Category {i}',
                    slug=f'category-{i}',
                    defaults={'color': '#3B82F6', 'description': f'Test category {i}'}
                )
                self.categories.append(category)

            # Create blog posts
            self.blog_posts = []
            for i in range(10):
                post = homepage.add_child(instance=BlogPage(
                    title=f'Post {i}',
                    slug=f'post-{i}',
                    intro=f'Introduction for post {i}',
                    author=self.user,
                    date=timezone.now(),
                    live=True
                ))
                # Add categories
                post.categories.add(*self.categories[:2])
                self.blog_posts.append(post)

            # Create skill level
            skill_level, created = SkillLevel.objects.get_or_create(
                name='Beginner',
                slug='beginner',
                defaults={'order': 1, 'color': '#10B981'}
            )

            # Create courses
            self.courses = []
            for i in range(10):
                course = homepage.add_child(instance=CoursePage(
                    title=f'Course {i}',
                    slug=f'course-{i}',
                    course_code=f'CS{i:03d}',
                    short_description=f'Short description for course {i}',
                    detailed_description=f'Detailed description for course {i}',
                    difficulty_level='beginner',
                    estimated_duration=10,
                    is_free=True,
                    instructor=self.user,
                    skill_level=skill_level,
                    live=True
                ))
                # Add categories
                course.categories.add(self.categories[0])
                self.courses.append(course)

            # Create exercises
            self.exercises = []
            for i in range(10):
                exercise = self.courses[0].add_child(instance=ExercisePage(
                    title=f'Exercise {i}',
                    slug=f'exercise-{i}',
                    description=f'Description for exercise {i}',
                    exercise_type='coding',
                    difficulty='easy',
                    points=10,
                    programming_language='python',
                    starter_code='# Write your code here',
                    live=True
                ))
                self.exercises.append(exercise)

            self.models_available = True
        except ImportError:
            self.models_available = False

    def test_blog_list_query_count(self):
        """Ensure blog list endpoint uses optimal number of queries."""
        if not self.models_available:
            self.skipTest("Blog models not available")

        # Reset query log
        reset_queries()

        # Make request
        response = self.client.get('/api/v1/blog/')

        # Count queries
        query_count = len(connection.queries)

        # Should be approximately:
        # 1. Count query for pagination
        # 2. Main posts query
        # 3. Prefetch categories
        # 4. Prefetch tags
        # 5. Select related author
        # Total: ~5 queries regardless of number of posts

        self.assertEqual(response.status_code, 200, "Blog list should return 200 OK")
        self.assertLessEqual(
            query_count,
            10,  # Allow some margin for setup queries
            f"Blog list used {query_count} queries, expected <= 10. "
            f"This indicates N+1 query problem."
        )

        # Verify we got posts in response
        data = response.json()
        self.assertIn('posts', data)
        self.assertGreater(len(data['posts']), 0, "Should return blog posts")

    def test_course_list_query_count(self):
        """Ensure course list endpoint uses optimal number of queries."""
        if not self.models_available:
            self.skipTest("Course models not available")

        # Reset query log
        reset_queries()

        # Make request
        response = self.client.get('/api/v1/learning/courses/')

        # Count queries
        query_count = len(connection.queries)

        # Should be approximately:
        # 1. Count query for pagination
        # 2. Main courses query
        # 3. Prefetch categories
        # 4. Select related instructor
        # 5. Select related skill_level
        # Total: ~5 queries regardless of number of courses (tags removed due to model design issue)

        self.assertEqual(response.status_code, 200, "Course list should return 200 OK")
        self.assertLessEqual(
            query_count,
            12,  # Allow some margin
            f"Course list used {query_count} queries, expected <= 12. "
            f"This indicates N+1 query problem."
        )

        # Verify we got courses in response
        data = response.json()
        self.assertIn('courses', data)

    def test_exercise_list_query_count(self):
        """Ensure exercise list endpoint uses optimal number of queries."""
        if not self.models_available:
            self.skipTest("Exercise models not available")

        # Reset query log
        reset_queries()

        # Make request
        response = self.client.get('/api/v1/wagtail/exercises/')

        # Count queries
        query_count = len(connection.queries)

        # Should be approximately:
        # 1. Main exercises query
        # 2. Select related owner
        # 3. Step-based exercises query (if included)
        # 4. Select related owner for step-based
        # Total: ~4 queries (tags removed - ExercisePage doesn't have tags field)

        self.assertEqual(response.status_code, 200, "Exercise list should return 200 OK")
        self.assertLessEqual(
            query_count,
            10,
            f"Exercise list used {query_count} queries, expected <= 10. "
            f"This indicates N+1 query problem."
        )

        # Verify we got exercises in response
        data = response.json()
        self.assertIn('exercises', data)

    def test_blog_categories_query_count(self):
        """Ensure blog categories endpoint doesn't have N+1 queries."""
        if not self.models_available:
            self.skipTest("Blog models not available")

        # Reset query log
        reset_queries()

        # Make request
        response = self.client.get('/api/v1/blog/categories/')

        # Count queries
        query_count = len(connection.queries)

        # Should be approximately:
        # 1. Main categories query
        # 2. Prefetch blogpage_set
        # Total: ~2 queries

        self.assertEqual(response.status_code, 200, "Categories should return 200 OK")
        self.assertLessEqual(
            query_count,
            5,
            f"Blog categories used {query_count} queries, expected <= 5"
        )

        # Verify we got categories
        data = response.json()
        self.assertIn('categories', data)

    def test_homepage_query_count(self):
        """Ensure homepage endpoint doesn't have N+1 queries."""
        if not self.models_available:
            self.skipTest("Homepage models not available")

        # Reset query log
        reset_queries()

        # Make request
        response = self.client.get('/api/v1/wagtail/homepage/')

        # Count queries
        query_count = len(connection.queries)

        # Should include homepage query + recent posts with prefetch
        self.assertEqual(response.status_code, 200, "Homepage should return 200 OK")
        self.assertLessEqual(
            query_count,
            12,
            f"Homepage used {query_count} queries, expected <= 12"
        )

