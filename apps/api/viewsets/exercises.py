"""
Exercise system ViewSets for programming exercises, submissions, and progress tracking.
"""

from django.db.models import Count, Exists, Max, Q, OuterRef
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.learning.models import (
    ProgrammingLanguage, ExerciseType, Exercise,
    Submission, TestCase, StudentProgress, ExerciseHint
)
from apps.learning.code_execution import exercise_evaluator
from ..serializers import (
    ProgrammingLanguageSerializer, ExerciseTypeSerializer,
    ExerciseSerializer, SubmissionSerializer, TestCaseSerializer,
    StudentProgressSerializer, ExerciseHintSerializer
)
from ..permissions import IsOwnerOrReadOnly
from ..mixins import RateLimitMixin


class ProgrammingLanguageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ProgrammingLanguage model."""
    queryset = ProgrammingLanguage.objects.filter(is_active=True)
    serializer_class = ProgrammingLanguageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ExerciseTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ExerciseType model."""
    queryset = ExerciseType.objects.all()
    serializer_class = ExerciseTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Exercise model with optimized annotations."""
    queryset = Exercise.objects.filter(is_published=True)  # For router introspection only
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Optimized queryset with annotations to reduce database queries."""
        user = self.request.user
        queryset = super().get_queryset()

        # Filter by lesson
        lesson = self.request.query_params.get('lesson')
        if lesson:
            queryset = queryset.filter(lesson__slug=lesson)

        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)

        # Filter by programming language
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(programming_language__slug=language)

        # Apply select_related for foreign keys
        queryset = queryset.select_related('lesson', 'exercise_type', 'programming_language')

        # Add annotations for optimized data retrieval
        if user.is_authenticated:
            # Subquery for user submissions
            user_submission = Submission.objects.filter(
                exercise=OuterRef('pk'),
                user=user
            )

            queryset = queryset.annotate(
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
        else:
            # For unauthenticated users, only provide submission count
            queryset = queryset.annotate(
                submission_count=Count('submissions', distinct=True),
                user_has_submitted=False,  # Default value
                user_best_score=None  # Default value
            )

        return queryset
    
    @action(detail=True, methods=['get'])
    def test_cases(self, request, pk=None):
        """Get sample test cases for exercise."""
        exercise = self.get_object()
        test_cases = exercise.test_cases.filter(is_sample=True)
        serializer = TestCaseSerializer(test_cases, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def hints(self, request, pk=None):
        """Get available hints for exercise."""
        exercise = self.get_object()
        hints = exercise.hints.all().order_by('order')
        serializer = ExerciseHintSerializer(hints, many=True, context={'request': request})
        return Response(serializer.data)


class SubmissionViewSet(RateLimitMixin, viewsets.ModelViewSet):
    """ViewSet for Submission model."""
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return Submission.objects.filter(user=self.request.user).select_related('exercise')
    
    def perform_create(self, serializer):
        """Create submission and evaluate code."""
        submission = serializer.save(user=self.request.user)
        
        # Evaluate the submission
        exercise_data = {
            'test_cases': [
                {
                    'name': tc.name,
                    'input': tc.get_input_as_dict(),
                    'expected': tc.expected_output,
                    'timeout': tc.timeout
                }
                for tc in submission.exercise.test_cases.all()
            ],
            'language': submission.exercise.programming_language.slug
        }
        
        evaluation_result = exercise_evaluator.evaluate_submission(
            submission.code, 
            exercise_data
        )
        
        # Update submission with results
        submission.status = evaluation_result['status']
        submission.score = evaluation_result['score']
        submission.passed_tests = evaluation_result.get('passed_tests', 0)
        submission.total_tests = evaluation_result.get('total_tests', 0)
        submission.execution_time = evaluation_result.get('total_execution_time', 0)
        submission.output = evaluation_result.get('message', '')
        submission.processed_at = timezone.now()
        submission.save()
        
        # Generate AI feedback
        if submission.score < 100:
            submission.generate_ai_feedback()
        
        return Response(self.get_serializer(submission).data, status=status.HTTP_201_CREATED)


class TestCaseViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for TestCase model."""
    queryset = TestCase.objects.filter(is_sample=True)
    serializer_class = TestCaseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class StudentProgressViewSet(viewsets.ModelViewSet):
    """ViewSet for StudentProgress model."""
    serializer_class = StudentProgressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return StudentProgress.objects.filter(user=self.request.user).select_related('exercise')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExerciseHintViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ExerciseHint model."""
    queryset = ExerciseHint.objects.all()
    serializer_class = ExerciseHintSerializer
    permission_classes = [permissions.IsAuthenticated]