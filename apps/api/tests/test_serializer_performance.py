from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection
from rest_framework.test import APIRequestFactory
from apps.api.viewsets.learning import CourseViewSet, LessonViewSet
from apps.learning.models import Course, Enrollment, Lesson
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

            # Add some lessons
            for k in range(3):
                Lesson.objects.create(
                    title=f'Lesson {k} for Course {i}',
                    slug=f'lesson-{i}-{k}',
                    course=course,
                    order=k
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
        # Total: <= 5 queries

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

        # Verify response is valid
        self.assertEqual(response.status_code, 200)
