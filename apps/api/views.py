"""
API Views for Python Learning Studio.
Provides REST API endpoints using Django REST Framework ViewSets.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.learning.models import *
from apps.users.models import UserProfile, Achievement, UserFollow
from apps.learning.code_execution import exercise_evaluator, code_executor
from apps.learning.services import learning_ai
from .serializers import *
from .permissions import IsOwnerOrReadOnly, IsInstructorOrReadOnly

User = get_user_model()


# User Management ViewSets
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for User model - read-only public profiles."""
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get or update current user profile."""
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for UserProfile model."""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        if self.action == 'list':
            return UserProfile.objects.filter(user__is_active=True)
        return super().get_queryset()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Learning Management ViewSets
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
    """ViewSet for Course model."""
    queryset = Course.objects.filter(is_published=True)
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsInstructorOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
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
        
        return queryset.select_related('instructor', 'category')
    
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
    """ViewSet for Lesson model."""
    queryset = Lesson.objects.filter(is_published=True)
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsInstructorOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by course
        course = self.request.query_params.get('course')
        if course:
            queryset = queryset.filter(course__slug=course)
        
        return queryset.select_related('course')
    
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
        return CourseEnrollment.objects.filter(user=self.request.user).select_related('course', 'course__instructor')


class UserProgressViewSet(viewsets.ModelViewSet):
    """ViewSet for UserProgress model."""
    serializer_class = UserProgressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user).select_related('lesson', 'lesson__course')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LearningPathViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for LearningPath model."""
    queryset = LearningPath.objects.filter(is_published=True)
    serializer_class = LearningPathSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CourseReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for CourseReview model."""
    serializer_class = CourseReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return CourseReview.objects.filter(user=self.request.user)
        return CourseReview.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Exercise System ViewSets
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
    """ViewSet for Exercise model."""
    queryset = Exercise.objects.filter(is_published=True)
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
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
        
        return queryset.select_related('lesson', 'exercise_type', 'programming_language')
    
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


class SubmissionViewSet(viewsets.ModelViewSet):
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


# Community Features ViewSets
class DiscussionViewSet(viewsets.ModelViewSet):
    """ViewSet for Discussion model."""
    queryset = Discussion.objects.all().order_by('-is_pinned', '-last_activity_at')
    serializer_class = DiscussionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by course, lesson, or exercise
        course = self.request.query_params.get('course')
        if course:
            queryset = queryset.filter(course__slug=course)
        
        lesson = self.request.query_params.get('lesson')
        if lesson:
            queryset = queryset.filter(lesson__slug=lesson)
        
        exercise = self.request.query_params.get('exercise')
        if exercise:
            queryset = queryset.filter(exercise__slug=exercise)
        
        return queryset.select_related('author', 'course', 'lesson', 'exercise')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get replies for this discussion."""
        discussion = self.get_object()
        replies = discussion.replies.filter(parent_reply__isnull=True).order_by('created_at')
        serializer = DiscussionReplySerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)


class DiscussionReplyViewSet(viewsets.ModelViewSet):
    """ViewSet for DiscussionReply model."""
    serializer_class = DiscussionReplySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return DiscussionReply.objects.all().select_related('author', 'discussion')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class StudyGroupViewSet(viewsets.ModelViewSet):
    """ViewSet for StudyGroup model."""
    queryset = StudyGroup.objects.filter(is_active=True, is_public=True)
    serializer_class = StudyGroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join study group."""
        study_group = self.get_object()
        if study_group.is_full:
            return Response({'message': 'Study group is full'}, status=status.HTTP_400_BAD_REQUEST)
        
        membership, created = StudyGroupMembership.objects.get_or_create(
            user=request.user,
            study_group=study_group
        )
        if created:
            return Response({'message': 'Joined study group'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Already a member'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'])
    def leave(self, request, pk=None):
        """Leave study group."""
        study_group = self.get_object()
        try:
            membership = StudyGroupMembership.objects.get(
                user=request.user,
                study_group=study_group
            )
            membership.delete()
            return Response({'message': 'Left study group'}, status=status.HTTP_204_NO_CONTENT)
        except StudyGroupMembership.DoesNotExist:
            return Response({'message': 'Not a member'}, status=status.HTTP_404_NOT_FOUND)


class StudyGroupPostViewSet(viewsets.ModelViewSet):
    """ViewSet for StudyGroupPost model."""
    serializer_class = StudyGroupPostSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        # Only show posts from groups user is a member of
        user_groups = StudyGroup.objects.filter(members=self.request.user)
        return StudyGroupPost.objects.filter(study_group__in=user_groups).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PeerReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for PeerReview model."""
    queryset = PeerReview.objects.all().order_by('-created_at')
    serializer_class = PeerReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CodeReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for CodeReview model."""
    serializer_class = CodeReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return CodeReview.objects.all().select_related('reviewer', 'peer_review')
    
    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


class LearningBuddyViewSet(viewsets.ModelViewSet):
    """ViewSet for LearningBuddy model."""
    serializer_class = LearningBuddySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return LearningBuddy.objects.filter(
            Q(user1=self.request.user) | Q(user2=self.request.user),
            is_active=True
        )
    
    def perform_create(self, serializer):
        serializer.save(user1=self.request.user)


class LearningSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for LearningSession model."""
    queryset = LearningSession.objects.filter(is_public=True).order_by('scheduled_at')
    serializer_class = LearningSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for Notification model."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'message': 'Notification marked as read'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read'}, status=status.HTTP_200_OK)


# Custom API Views
class CodeExecutionView(APIView):
    """API view for code execution."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CodeExecutionRequestSerializer(data=request.data)
        if serializer.is_valid():
            result = code_executor.execute_python_code(
                code=serializer.validated_data['code'],
                test_inputs=serializer.validated_data.get('test_inputs', []),
                timeout=serializer.validated_data.get('timeout', 10)
            )
            
            response_serializer = CodeExecutionResponseSerializer({
                'success': result.success,
                'output': result.output,
                'error': result.error,
                'execution_time': result.execution_time,
                'memory_used': result.memory_used
            })
            
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIAssistanceView(APIView):
    """API view for AI-powered assistance."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = AIAssistanceRequestSerializer(data=request.data)
        if serializer.is_valid():
            assistance_type = serializer.validated_data['assistance_type']
            content = serializer.validated_data['content']
            context = serializer.validated_data.get('context', '')
            difficulty = serializer.validated_data.get('difficulty_level', 'beginner')
            
            try:
                if assistance_type == 'code_explanation':
                    response = learning_ai.generate_exercise_explanation(content)
                elif assistance_type == 'error_help':
                    response = learning_ai.explain_error_message(content, context)
                elif assistance_type == 'hint_generation':
                    response = learning_ai.generate_hints_for_exercise(content, context)
                elif assistance_type == 'code_review':
                    response = learning_ai.review_student_code(content, context)
                elif assistance_type == 'exercise_generation':
                    response = learning_ai.create_exercise_from_concept(content, difficulty)
                else:
                    return Response({'error': 'Invalid assistance type'}, status=status.HTTP_400_BAD_REQUEST)
                
                response_serializer = AIAssistanceResponseSerializer({
                    'assistance_type': assistance_type,
                    'response': response,
                    'success': True
                })
                
                return Response(response_serializer.data)
                
            except Exception as e:
                response_serializer = AIAssistanceResponseSerializer({
                    'assistance_type': assistance_type,
                    'response': '',
                    'success': False,
                    'error_message': str(e)
                })
                return Response(response_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseEvaluationView(APIView):
    """API view for exercise evaluation."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        exercise_id = request.data.get('exercise_id')
        code = request.data.get('code')
        
        if not exercise_id or not code:
            return Response({'error': 'exercise_id and code are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            exercise = Exercise.objects.get(id=exercise_id)
            
            # Create submission
            submission = Submission.objects.create(
                user=request.user,
                exercise=exercise,
                code=code,
                attempt_number=Submission.objects.filter(user=request.user, exercise=exercise).count() + 1
            )
            
            # Evaluate submission
            exercise_data = {
                'test_cases': [
                    {
                        'name': tc.name,
                        'input': tc.get_input_as_dict(),
                        'expected': tc.expected_output,
                        'timeout': tc.timeout
                    }
                    for tc in exercise.test_cases.all()
                ],
                'language': exercise.programming_language.slug
            }
            
            evaluation_result = exercise_evaluator.evaluate_submission(code, exercise_data)
            
            # Update submission
            submission.status = evaluation_result['status']
            submission.score = evaluation_result['score']
            submission.passed_tests = evaluation_result.get('passed_tests', 0)
            submission.total_tests = evaluation_result.get('total_tests', 0)
            submission.execution_time = evaluation_result.get('total_execution_time', 0)
            submission.output = evaluation_result.get('message', '')
            submission.processed_at = timezone.now()
            submission.save()
            
            # Update exercise statistics
            exercise.total_submissions += 1
            if submission.score >= 80:
                exercise.successful_submissions += 1
            exercise.save()
            
            # Update student progress
            progress, created = StudentProgress.objects.get_or_create(
                user=request.user,
                exercise=exercise
            )
            progress.total_attempts += 1
            if not progress.started:
                progress.started = True
                progress.started_at = timezone.now()
            if submission.score > progress.best_score:
                progress.best_score = submission.score
            if submission.score >= 80 and not progress.completed:
                progress.mark_completed(submission.score)
            progress.save()
            
            return Response({
                'submission_id': submission.submission_id,
                'score': submission.score,
                'status': submission.status,
                'passed_tests': submission.passed_tests,
                'total_tests': submission.total_tests,
                'execution_time': submission.execution_time,
                'message': submission.output,
                'test_results': evaluation_result.get('test_results', [])
            })
            
        except Exercise.DoesNotExist:
            return Response({'error': 'Exercise not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# New Docker-based Code Execution Endpoints
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_code(request):
    """Execute Python code in a secure Docker environment."""
    try:
        from ..learning.docker_executor import get_code_executor
        
        data = request.data
        code = data.get('code', '')
        test_cases = data.get('test_cases', [])
        time_limit = min(int(data.get('time_limit', 30)), 60)  # Max 60 seconds
        memory_limit = min(int(data.get('memory_limit', 256)), 512)  # Max 512MB
        
        if not code.strip():
            return Response({
                'success': False,
                'error': 'No code provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use the Docker executor
        try:
            docker_executor = get_code_executor()
            result = docker_executor.execute_code(
                code=code,
                test_cases=test_cases,
                time_limit=time_limit,
                memory_limit=f"{memory_limit}m",
                use_cache=True
            )
        except Exception as e:
            logger.warning(f"Docker executor failed, using fallback: {e}")
            # Fallback to basic executor
            execution_result = code_executor.execute_python_code(
                code=code,
                timeout=time_limit,
                memory_limit=memory_limit
            )
            result = {
                'success': execution_result.success,
                'stdout': execution_result.output,
                'stderr': execution_result.error,
                'execution_time': execution_result.execution_time,
                'memory_used': execution_result.memory_used * 1024 * 1024,  # Convert to bytes
                'timeout': execution_result.timeout,
                'from_cache': False
            }
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Code execution error: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error during code execution'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_exercise_code(request, exercise_id):
    """Submit code for an exercise using Docker executor."""
    try:
        from ..learning.models import Exercise, ExerciseSubmission
        from ..learning.docker_executor import get_code_executor
        
        exercise = get_object_or_404(Exercise, id=exercise_id, is_published=True)
        data = request.data
        code = data.get('code', '')
        
        if not code.strip():
            return Response({
                'success': False,
                'error': 'No code provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get test cases for the exercise
        test_cases = []
        for test_case in exercise.test_cases.all():
            test_cases.append({
                'name': test_case.name,
                'test_code': f'result = {test_case.input_data}; print(result)',
                'expected_output': test_case.expected_output,
                'input_data': test_case.input_data
            })
        
        # Execute code with Docker
        docker_executor = get_code_executor()
        result = docker_executor.execute_code(
            code=code,
            test_cases=test_cases,
            time_limit=30,
            memory_limit="256m",
            use_cache=False  # Don't cache exercise submissions
        )
        
        # Calculate score based on test results
        test_results = result.get('test_results', [])
        passed_tests = sum(1 for test in test_results if test.get('passed', False))
        total_tests = len(test_results)
        score = int((passed_tests / total_tests) * 100) if total_tests > 0 else 0
        
        # Create submission record
        submission = ExerciseSubmission.objects.create(
            student=request.user,
            exercise=exercise,
            code=code,
            score=score,
            is_correct=score >= 80,
            feedback=f"Passed {passed_tests}/{total_tests} test cases",
            execution_time=result.get('execution_time', 0),
            output=result.get('stdout', ''),
            error=result.get('stderr', '') or result.get('error', '')
        )
        
        return Response({
            'success': True,
            'submission_id': submission.id,
            'score': score,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'test_results': test_results,
            'execution_time': result.get('execution_time', 0),
            'output': result.get('stdout', ''),
            'error': result.get('stderr', '') or result.get('error', ''),
            'from_cache': result.get('from_cache', False)
        })
        
    except Exercise.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Exercise not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Exercise submission error: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error during submission evaluation'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def docker_status(request):
    """Get Docker system status and information."""
    try:
        from ..learning.docker_executor import get_code_executor
        
        docker_executor = get_code_executor()
        system_info = docker_executor.executor.get_system_info()
        
        return Response({
            'docker_available': True,
            'system_info': system_info,
            'executor_type': 'docker'
        })
        
    except Exception as e:
        return Response({
            'docker_available': False,
            'error': str(e),
            'executor_type': 'fallback'
        })
