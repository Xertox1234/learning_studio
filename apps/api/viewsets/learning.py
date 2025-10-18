"""
Learning management ViewSets for courses, lessons, and progress tracking.
"""

from django.db.models import Q, Count, Exists, OuterRef
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.learning.models import (
    Category, Course, Lesson, CourseEnrollment,
    UserProgress, LearningPath, CourseReview
)
from ..serializers import (
    CategorySerializer, CourseSerializer, LessonSerializer,
    CourseEnrollmentSerializer, UserProgressSerializer,
    LearningPathSerializer, CourseReviewSerializer,
    ExerciseSerializer
)
from ..permissions import IsOwnerOrReadOnly, IsInstructorOrReadOnly, IsOwnerOrAdmin


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Category model."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @action(detail=True, methods=['get'])
    def courses(self, request, pk=None):
        """Get courses in this category."""
        category = self.get_object()
        courses = Course.objects.filter(category=category, is_published=True)
        serializer = CourseSerializer(courses, many=True, context={'request': request})
        return Response(serializer.data)


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet for Course model with optimized queryset annotations."""
    queryset = Course.objects.filter(is_published=True)
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsInstructorOrReadOnly]

    def get_queryset(self):
        """
        Optimize queryset with annotations to avoid N+1 queries.
        """
        user = self.request.user

        # Subquery to check if user is enrolled
        user_enrollment = CourseEnrollment.objects.filter(
            course=OuterRef('pk'),
            user=user
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

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(short_description__icontains=search)
            )

        return queryset
    
    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, pk=None):
        """Enroll user in course."""
        course = self.get_object()
        enrollment, created = CourseEnrollment.objects.get_or_create(
            user=request.user,
            course=course
        )
        if created:
            return Response({'message': 'Enrolled successfully'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Already enrolled'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def unenroll(self, request, pk=None):
        """Unenroll user from course."""
        course = self.get_object()
        try:
            enrollment = CourseEnrollment.objects.get(user=request.user, course=course)
            enrollment.delete()
            return Response({'message': 'Unenrolled successfully'}, status=status.HTTP_204_NO_CONTENT)
        except CourseEnrollment.DoesNotExist:
            return Response({'message': 'Not enrolled'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        """Get lessons for this course."""
        course = self.get_object()
        lessons = course.lessons.filter(is_published=True).order_by('order')
        serializer = LessonSerializer(lessons, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get reviews for this course."""
        course = self.get_object()
        reviews = course.reviews.all().order_by('-created_at')
        serializer = CourseReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    """ViewSet for Lesson model with optimized annotations."""
    queryset = Lesson.objects.filter(is_published=True)
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsInstructorOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filter by course
        course = self.request.query_params.get('course')
        if course:
            queryset = queryset.filter(course__slug=course)

        # Subquery for user completion
        user_progress = UserProgress.objects.filter(
            lesson=OuterRef('pk'),
            user=user,
            completed=True
        )

        # Apply annotations
        queryset = queryset.select_related(
            'course'
        ).annotate(
            completion_count=Count(
                'user_progress',
                filter=Q(user_progress__completed=True),
                distinct=True
            ),
            user_completed=Exists(user_progress)
        )

        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def start(self, request, pk=None):
        """Mark lesson as started."""
        lesson = self.get_object()
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        progress.mark_started()
        return Response({'message': 'Lesson started'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def complete(self, request, pk=None):
        """Mark lesson as completed."""
        lesson = self.get_object()
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        progress.mark_completed()
        return Response({'message': 'Lesson completed'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def exercises(self, request, pk=None):
        """Get exercises for this lesson."""
        lesson = self.get_object()
        exercises = lesson.exercises.filter(is_published=True).order_by('order')
        serializer = ExerciseSerializer(exercises, many=True, context={'request': request})
        return Response(serializer.data)


class CourseEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for CourseEnrollment model."""
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return CourseEnrollment.objects.filter(
            user=self.request.user
        ).select_related('course', 'course__instructor')


class UserProgressViewSet(viewsets.ModelViewSet):
    """ViewSet for UserProgress model."""
    serializer_class = UserProgressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return UserProgress.objects.filter(
            user=self.request.user
        ).select_related('lesson', 'lesson__course')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LearningPathViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for LearningPath model."""
    queryset = LearningPath.objects.filter(is_published=True)
    serializer_class = LearningPathSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CourseReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CourseReview model with object-level authorization.

    Security:
        - Users can only view/edit their own reviews
        - Staff can view/edit all reviews
        - Implements IDOR/BOLA prevention

    Permissions:
        - IsAuthenticated: Requires user to be logged in
        - IsOwnerOrAdmin: Checks ownership at object level
    """
    queryset = CourseReview.objects.all()  # For router introspection only
    serializer_class = CourseReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """
        Filter queryset to only user's own reviews.
        Staff can see all reviews.

        Security: Prevents IDOR attacks by filtering at queryset level.
        """
        user = self.request.user

        if user.is_staff or user.is_superuser:
            # Staff can see all reviews
            return CourseReview.objects.all()

        # Regular users can only see their own reviews
        return CourseReview.objects.filter(user=user)

    def perform_create(self, serializer):
        """
        Force ownership to authenticated user.

        Security: Prevents ownership hijacking
        """
        serializer.save(user=self.request.user)