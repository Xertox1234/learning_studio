"""
API Views for Python Learning Studio.
Provides REST API endpoints using Django REST Framework ViewSets.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from django.conf import settings
from django.utils.decorators import method_decorator

from apps.learning.models import *
from apps.users.models import UserProfile, Achievement, UserFollow
from apps.learning.code_execution import exercise_evaluator, code_executor
from apps.learning.services import learning_ai
from .serializers import *
from .permissions import IsOwnerOrReadOnly, IsInstructorOrReadOnly
from .utils import serialize_tags, get_featured_image_url

User = get_user_model()

# Rate Limiting Utilities (defined early to avoid import errors)

def get_client_ip(request):
    """Get the client IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_or_ip(request):
    """Get user ID if authenticated, otherwise use IP address for rate limiting."""
    if request.user.is_authenticated:
        return f"user_{request.user.id}"
    return f"ip_{get_client_ip(request)}"


class RateLimitMixin:
    """
    Mixin to add rate limiting to ViewSets.
    Apply different rate limits based on action type.
    """
    
    @method_decorator(ratelimit(key=get_user_or_ip, rate=settings.RATE_LIMIT_SETTINGS['API_CALLS'], method=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], block=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


def ratelimited(request, exception):
    """
    Custom view for handling rate limit exceeded responses.
    Returns a user-friendly error message and appropriate HTTP status.
    """
    if request.content_type == 'application/json' or request.path.startswith('/api/'):
        from django.http import JsonResponse
        return JsonResponse({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'retry_after': getattr(exception, 'time_left', 60)
        }, status=429)
    else:
        # For non-API requests, render a template
        return render(request, 'errors/rate_limited.html', {
            'retry_after': getattr(exception, 'time_left', 60)
        }, status=429)


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


# Community Features ViewSets
class DiscussionViewSet(RateLimitMixin, viewsets.ModelViewSet):
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


class DiscussionReplyViewSet(RateLimitMixin, viewsets.ModelViewSet):
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


@method_decorator(ratelimit(key='user', rate=settings.RATE_LIMIT_SETTINGS['AI_REQUESTS'], method='POST', block=True), name='post')
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
                elif assistance_type == 'contextual_chat':
                    # Parse context for contextual chat
                    import json
                    try:
                        context_data = json.loads(context) if context else {}
                        exercise_context = context_data.get('exercise', {})
                        student_code = context_data.get('student_code', '')
                        conversation_history = context_data.get('conversation_history', [])
                        response = learning_ai.contextual_chat_response(
                            content, exercise_context, student_code, conversation_history
                        )
                    except json.JSONDecodeError:
                        response = learning_ai.contextual_chat_response(content)
                elif assistance_type == 'real_world_examples':
                    industry_focus = serializer.validated_data.get('industry_focus', 'general')
                    response = learning_ai.generate_real_world_examples(content, industry_focus)
                elif assistance_type == 'debugging_guidance':
                    response = learning_ai.generate_debugging_guidance(content, context, difficulty)
                elif assistance_type == 'struggle_analysis':
                    # Parse context for struggle analysis
                    import json
                    try:
                        context_data = json.loads(context) if context else {}
                        time_spent = context_data.get('time_spent', 0)
                        wrong_attempts = context_data.get('wrong_attempts', 0)
                        code_attempts = context_data.get('code_attempts', [])
                        exercise_data = context_data.get('exercise_data', {})
                        response = learning_ai.analyze_student_struggle(
                            exercise_data, time_spent, wrong_attempts, code_attempts
                        )
                    except json.JSONDecodeError:
                        response = "I'd be happy to help, but I need more information about what you're working on."
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
@ratelimit(key='user', rate=settings.RATE_LIMIT_SETTINGS['CODE_EXECUTION'], method='POST', block=True)
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


# Forum API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forum_list(request):
    """Get forum data for React frontend."""
    try:
        from machina.apps.forum.models import Forum
        from machina.apps.forum_conversation.models import Topic, Post
        from django.contrib.auth import get_user_model
        from apps.api.services.container import container

        User = get_user_model()
        stats_service = container.get_statistics_service()
        
        # Get forum categories and their children
        forum_categories = Forum.objects.filter(type=Forum.FORUM_CAT)
        
        forums_data = []
        for category in forum_categories:
            category_data = {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': str(category.description) if category.description else '',
                'type': 'category',
                'forums': []
            }
            
            # Get child forums
            for forum in category.get_children():
                if forum.type == Forum.FORUM_POST:
                    # Get latest topic for this forum
                    latest_topic = Topic.objects.filter(
                        forum=forum, approved=True
                    ).select_related('poster', 'last_post', 'last_post__poster').order_by('-last_post_on').first()
                    
                    last_post_data = None
                    if latest_topic and latest_topic.last_post:
                        last_post_data = {
                            'id': latest_topic.last_post.id,
                            'title': latest_topic.subject,
                            'author': {
                                'username': latest_topic.last_post.poster.username,
                                'avatar': None,
                                'trust_level': 1  # Default trust level
                            },
                            'created_at': latest_topic.last_post_on.isoformat() if latest_topic.last_post_on else None
                        }
                    
                    # Get real statistics for this forum
                    forum_stats = stats_service.get_forum_specific_stats(forum.id)
                    
                    forum_data = {
                        'id': forum.id,
                        'name': forum.name,
                        'slug': forum.slug,
                        'description': str(forum.description) if forum.description else '',
                        'icon': '💬',  # Default icon
                        'topics_count': forum.direct_topics_count,
                        'posts_count': forum.direct_posts_count,
                        'last_post': last_post_data,
                        'stats': {
                            'online_users': forum_stats['online_users'],
                            'weekly_posts': forum_stats['weekly_posts'],
                            'trending': forum_stats['trending']
                        },
                        'color': 'bg-blue-500'  # Default color
                    }
                    category_data['forums'].append(forum_data)
            
            if category_data['forums']:  # Only include categories that have forums
                forums_data.append(category_data)
        
        # Get overall stats using the statistics service
        overall_stats = stats_service.get_forum_statistics()
        
        return Response({
            'categories': forums_data,
            'stats': {
                'total_topics': overall_stats['total_topics'],
                'total_posts': overall_stats['total_posts'],
                'total_users': overall_stats['total_users'],
                'online_users': overall_stats['online_users']
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch forum data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forum_topic_detail(request, forum_slug, forum_id, topic_slug, topic_id):
    """Get topic detail with posts for React frontend."""
    try:
        from machina.apps.forum.models import Forum
        from machina.apps.forum_conversation.models import Topic, Post
        
        # Get the topic
        topic = Topic.objects.select_related('poster', 'forum').get(
            id=topic_id,
            forum_id=forum_id,
            approved=True
        )
        
        # Get posts for this topic
        posts = Post.objects.select_related('poster').filter(
            topic=topic,
            approved=True
        ).order_by('created')
        
        # Format posts data
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post.id,
                'content': str(post.content),
                'created': post.created.isoformat(),
                'updated': post.updated.isoformat() if post.updated else None,
                'poster': {
                    'id': post.poster.id,
                    'username': post.poster.username,
                    'first_name': post.poster.first_name,
                    'last_name': post.poster.last_name,
                    'avatar': None,  # Could add avatar logic here
                },
                'position': posts_data.__len__() + 1
            })
        
        # Format topic data
        topic_data = {
            'id': topic.id,
            'subject': topic.subject,
            'slug': topic.slug,
            'created': topic.created.isoformat(),
            'updated': topic.updated.isoformat(),
            'posts_count': topic.posts_count,
            'views_count': topic.views_count,
            'poster': {
                'id': topic.poster.id,
                'username': topic.poster.username,
                'first_name': topic.poster.first_name,
                'last_name': topic.poster.last_name,
                'avatar': None,
            },
            'forum': {
                'id': topic.forum.id,
                'name': topic.forum.name,
                'slug': topic.forum.slug,
                'description': str(topic.forum.description) if topic.forum.description else '',
            },
            'posts': posts_data
        }
        
        return Response(topic_data)
        
    except Topic.DoesNotExist:
        return Response({
            'error': 'Topic not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to fetch topic: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forum_detail(request, forum_slug, forum_id):
    """Get forum detail with topics list for React frontend."""
    try:
        from machina.apps.forum.models import Forum
        from machina.apps.forum_conversation.models import Topic
        
        # Get the forum
        forum = Forum.objects.get(id=forum_id, slug=forum_slug)
        
        # Get topics for this forum
        topics = Topic.objects.select_related('poster', 'last_post', 'last_post__poster').filter(
            forum=forum,
            approved=True
        ).order_by('-last_post_on')[:20]  # Limit to 20 most recent topics
        
        # Format topics data
        topics_data = []
        for topic in topics:
            last_post_data = None
            if topic.last_post:
                last_post_data = {
                    'id': topic.last_post.id,
                    'created': topic.last_post.created.isoformat(),
                    'poster': {
                        'username': topic.last_post.poster.username,
                        'display_name': topic.last_post.poster.get_display_name() if hasattr(topic.last_post.poster, 'get_display_name') else topic.last_post.poster.username
                    }
                }
            
            topics_data.append({
                'id': topic.id,
                'subject': topic.subject,
                'slug': topic.slug,
                'created': topic.created.isoformat(),
                'posts_count': topic.posts_count,
                'views_count': topic.views_count,
                'last_post_on': topic.last_post_on.isoformat() if topic.last_post_on else None,
                'poster': {
                    'id': topic.poster.id,
                    'username': topic.poster.username,
                    'display_name': topic.poster.get_display_name() if hasattr(topic.poster, 'get_display_name') else topic.poster.username
                },
                'last_post': last_post_data
            })
        
        # Format forum data
        forum_data = {
            'id': forum.id,
            'name': forum.name,
            'slug': forum.slug,
            'description': str(forum.description) if forum.description else '',
            'topics_count': forum.direct_topics_count,
            'posts_count': forum.direct_posts_count,
            'topics': topics_data
        }
        
        return Response(forum_data)
        
    except Forum.DoesNotExist:
        return Response({
            'error': 'Forum not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to fetch forum: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Forum Topic CRUD API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def topic_create(request):
    """Create a new forum topic."""
    try:
        from machina.apps.forum.models import Forum
        from machina.apps.forum_conversation.models import Topic, Post
        from django.utils import timezone
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"Topic creation request from user {request.user.id}: {request.data}")
        
        # Get forum
        forum_id = request.data.get('forum_id')
        if not forum_id:
            return Response({
                'error': 'Forum ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            forum = Forum.objects.get(id=forum_id)
            logger.info(f"Found forum: {forum.name} (ID: {forum.id}, Type: {forum.type})")
        except Forum.DoesNotExist:
            return Response({
                'error': 'Forum not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if forum allows posting
        if forum.type != Forum.FORUM_POST:
            return Response({
                'error': 'Cannot create topics in this forum type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate required fields
        subject = request.data.get('subject', '').strip()
        content = request.data.get('content', '').strip()
        
        if not subject:
            return Response({
                'error': 'Subject is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not content:
            return Response({
                'error': 'Content is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create topic
        logger.info("Creating topic...")
        topic = Topic.objects.create(
            forum=forum,
            subject=subject,
            poster=request.user,
            type=request.data.get('topic_type', Topic.TOPIC_POST),
            status=Topic.TOPIC_UNLOCKED,
            approved=True,
            created=timezone.now(),
            updated=timezone.now()
        )
        logger.info(f"Created topic {topic.id}: {topic.subject}")
        
        # Create the first post
        logger.info("Creating first post...")
        post = Post.objects.create(
            topic=topic,
            poster=request.user,
            subject=subject,
            content=content,
            approved=True,
            enable_signature=request.data.get('enable_signature', False),
            created=timezone.now(),
            updated=timezone.now()
        )
        logger.info(f"Created post {post.id} for topic {topic.id}")
        
        # Update topic references
        topic.first_post = post
        topic.last_post = post
        topic.last_post_on = post.created
        topic.posts_count = 1
        topic.save()
        
        # Update forum statistics
        forum.refresh_from_db()
        
        # Return successful response
        topic_data = {
            'id': topic.id,
            'subject': topic.subject,
            'slug': topic.slug,
            'created': topic.created.isoformat(),
            'posts_count': topic.posts_count,
            'views_count': getattr(topic, 'views_count', 0),
            'forum': {
                'id': forum.id,
                'name': forum.name,
                'slug': forum.slug,
            },
            'poster': {
                'id': request.user.id,
                'username': request.user.username,
                'display_name': request.user.get_display_name() if hasattr(request.user, 'get_display_name') else request.user.username
            }
        }
        
        return Response({
            'success': True,
            'topic': topic_data,
            'message': 'Topic created successfully'
        }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Failed to create topic: {str(e)}")
        return Response({
            'error': f'Failed to create topic: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def topic_edit(request, topic_id):
    """Edit an existing forum topic."""
    try:
        from machina.apps.forum_conversation.models import Topic
        from machina.apps.forum_conversation.forms import TopicForm
        
        # Get the topic
        try:
            topic = Topic.objects.select_related('forum', 'first_post').get(
                id=topic_id,
                approved=True
            )
        except Topic.DoesNotExist:
            return Response({
                'error': 'Topic not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions - user must be topic creator or have moderation permissions
        if topic.poster != request.user:
            # Check if user has moderation permissions for this forum
            # This would need to be implemented based on your permission system
            return Response({
                'error': 'You do not have permission to edit this topic'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get the first post (topic post)
        first_post = topic.first_post
        if not first_post:
            return Response({
                'error': 'Topic post not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update fields
        subject = request.data.get('subject', '').strip()
        content = request.data.get('content', '').strip()
        
        if not subject:
            return Response({
                'error': 'Subject is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not content:
            return Response({
                'error': 'Content is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare form data
        form_data = {
            'subject': subject,
            'content': content,
            'topic_type': request.data.get('topic_type', topic.type),
            'enable_signature': request.data.get('enable_signature', first_post.enable_signature),
            'update_reason': request.data.get('update_reason', ''),
        }
        
        # Use TopicForm for validation and update
        form = TopicForm(
            data=form_data,
            instance=first_post,
            user=request.user,
            forum=topic.forum,
            topic=topic
        )
        
        if form.is_valid():
            # Save the updated post and topic
            post = form.save()
            updated_topic = post.topic
            
            # Return updated topic data
            topic_data = {
                'id': updated_topic.id,
                'subject': updated_topic.subject,
                'slug': updated_topic.slug,
                'updated': updated_topic.updated.isoformat(),
                'posts_count': updated_topic.posts_count,
                'views_count': updated_topic.views_count,
                'forum': {
                    'id': updated_topic.forum.id,
                    'name': updated_topic.forum.name,
                    'slug': updated_topic.forum.slug,
                },
                'poster': {
                    'id': updated_topic.poster.id,
                    'username': updated_topic.poster.username,
                    'display_name': updated_topic.poster.get_display_name() if hasattr(updated_topic.poster, 'get_display_name') else updated_topic.poster.username
                }
            }
            
            return Response({
                'success': True,
                'topic': topic_data,
                'message': 'Topic updated successfully'
            })
        else:
            return Response({
                'error': 'Validation failed',
                'errors': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'error': f'Failed to update topic: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def topic_delete(request, topic_id):
    """Delete a forum topic."""
    try:
        from machina.apps.forum_conversation.models import Topic
        
        # Get the topic
        try:
            topic = Topic.objects.select_related('forum', 'first_post').get(
                id=topic_id,
                approved=True
            )
        except Topic.DoesNotExist:
            return Response({
                'error': 'Topic not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions - user must be topic creator or have moderation permissions
        if topic.poster != request.user:
            # Check if user has moderation permissions for this forum
            # This would need to be implemented based on your permission system
            return Response({
                'error': 'You do not have permission to delete this topic'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Store forum info for response
        forum_data = {
            'id': topic.forum.id,
            'name': topic.forum.name,
            'slug': topic.forum.slug,
        }
        
        # Delete the topic (this will cascade to delete all posts)
        topic_subject = topic.subject
        topic.delete()
        
        return Response({
            'success': True,
            'message': f'Topic "{topic_subject}" deleted successfully',
            'forum': forum_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to delete topic: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Forum Post CRUD API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate=settings.RATE_LIMIT_SETTINGS['FORUM_POSTS'], method='POST', block=True)
@csrf_exempt
def post_create(request):
    """Create a new forum post (reply to a topic)."""
    try:
        from machina.apps.forum_conversation.models import Topic, Post
        from django.utils import timezone
        
        # Get topic ID from request data
        topic_id = request.data.get('topic_id')
        if not topic_id:
            return Response({
                'error': 'Topic ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get content
        content = request.data.get('content', '').strip()
        if not content:
            return Response({
                'error': 'Content is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the topic
        try:
            topic = Topic.objects.get(id=topic_id)
        except Topic.DoesNotExist:
            return Response({
                'error': 'Topic not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create the post using the same pattern as topic_create
        # Use explicit timestamps to avoid signal issues
        post = Post.objects.create(
            topic=topic,
            poster=request.user,
            subject=f'Re: {topic.subject}',
            content=content,
            approved=True,
            enable_signature=request.data.get('enable_signature', True),
            created=timezone.now(),
            updated=timezone.now()
        )
        
        # Update topic statistics
        topic.posts_count = topic.posts.filter(approved=True).count()
        topic.last_post = post
        topic.last_post_on = post.created
        topic.save()
        
        # Update forum statistics
        forum = topic.forum
        forum.posts_count = Post.objects.filter(topic__forum=forum, approved=True).count()
        forum.last_post = post
        forum.save()
        
        # Calculate position safely
        post_position = topic.posts.filter(approved=True).count()
        
        # Return success response
        return Response({
            'success': True,
            'message': 'Post created successfully',
            'post': {
                'id': post.id,
                'content': str(post.content),
                'created': post.created.isoformat() if post.created else timezone.now().isoformat(),
                'updated': post.updated.isoformat() if post.updated else None,
                'poster': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                },
                'position': post_position,
                'topic': {
                    'id': topic.id,
                    'subject': topic.subject,
                    'slug': topic.slug,
                }
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating post: {str(e)}")
        return Response({
            'error': f'Failed to create post: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_reply(request, topic_id):
    """Create a reply post to a topic."""
    try:
        from machina.apps.forum_conversation.models import Topic, Post
        from machina.apps.forum_conversation.forms import PostForm
        
        # Get the topic
        try:
            topic = Topic.objects.select_related('forum').get(
                id=topic_id,
                approved=True
            )
        except Topic.DoesNotExist:
            return Response({
                'error': 'Topic not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if topic is locked
        if topic.status == Topic.TOPIC_LOCKED:
            return Response({
                'error': 'Topic is locked'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate required fields
        content = request.data.get('content', '').strip()
        
        if not content:
            return Response({
                'error': 'Content is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare form data
        form_data = {
            'subject': f"Re: {topic.subject}",
            'content': content,
            'enable_signature': request.data.get('enable_signature', False),
        }
        
        # Use PostForm for validation and creation
        form = PostForm(
            data=form_data,
            user=request.user,
            forum=topic.forum,
            topic=topic
        )
        
        if form.is_valid():
            # Save the post
            post = form.save()
            
            # Return post data
            post_data = {
                'id': post.id,
                'content': str(post.content),
                'created': post.created.isoformat(),
                'poster': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'display_name': request.user.get_display_name() if hasattr(request.user, 'get_display_name') else request.user.username
                },
                'topic': {
                    'id': topic.id,
                    'subject': topic.subject,
                    'slug': topic.slug,
                },
                'position': topic.posts.count()
            }
            
            return Response({
                'success': True,
                'post': post_data,
                'message': 'Reply posted successfully'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Validation failed',
                'errors': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'error': f'Failed to create reply: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def post_edit(request, post_id):
    """Edit an existing forum post."""
    try:
        from machina.apps.forum_conversation.models import Post
        from machina.apps.forum_conversation.forms import PostForm
        
        # Get the post
        try:
            post = Post.objects.select_related('topic', 'topic__forum', 'poster').get(
                id=post_id,
                approved=True
            )
        except Post.DoesNotExist:
            return Response({
                'error': 'Post not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions - user must be post creator or have moderation permissions
        if post.poster != request.user:
            return Response({
                'error': 'You do not have permission to edit this post'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate required fields
        content = request.data.get('content', '').strip()
        
        if not content:
            return Response({
                'error': 'Content is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare form data
        form_data = {
            'subject': request.data.get('subject', post.subject),
            'content': content,
            'enable_signature': request.data.get('enable_signature', post.enable_signature),
            'update_reason': request.data.get('update_reason', ''),
        }
        
        # Use PostForm for validation and update
        form = PostForm(
            data=form_data,
            instance=post,
            user=request.user,
            forum=post.topic.forum,
            topic=post.topic
        )
        
        if form.is_valid():
            # Save the updated post
            updated_post = form.save()
            
            # Return updated post data
            post_data = {
                'id': updated_post.id,
                'subject': updated_post.subject,
                'content': str(updated_post.content),
                'updated': updated_post.updated.isoformat(),
                'updates_count': updated_post.updates_count,
                'poster': {
                    'id': updated_post.poster.id,
                    'username': updated_post.poster.username,
                    'display_name': updated_post.poster.get_display_name() if hasattr(updated_post.poster, 'get_display_name') else updated_post.poster.username
                },
                'updated_by': {
                    'id': updated_post.updated_by.id,
                    'username': updated_post.updated_by.username,
                } if updated_post.updated_by else None
            }
            
            return Response({
                'success': True,
                'post': post_data,
                'message': 'Post updated successfully'
            })
        else:
            return Response({
                'error': 'Validation failed',
                'errors': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'error': f'Failed to update post: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def post_delete(request, post_id):
    """Delete a forum post."""
    try:
        from machina.apps.forum_conversation.models import Post
        
        # Get the post
        try:
            post = Post.objects.select_related('topic', 'topic__forum', 'poster').get(
                id=post_id,
                approved=True
            )
        except Post.DoesNotExist:
            return Response({
                'error': 'Post not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions - user must be post creator or have moderation permissions
        if post.poster != request.user:
            return Response({
                'error': 'You do not have permission to delete this post'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if this is the first post of a topic (can't delete topic starter post without deleting topic)
        if post.is_topic_head:
            return Response({
                'error': 'Cannot delete the first post of a topic. Delete the topic instead.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Store topic info for response
        topic_data = {
            'id': post.topic.id,
            'subject': post.topic.subject,
            'slug': post.topic.slug,
        }
        
        # Delete the post
        post_id_deleted = post.id
        post.delete()
        
        return Response({
            'success': True,
            'message': f'Post #{post_id_deleted} deleted successfully',
            'topic': topic_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to delete post: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_quote(request, post_id):
    """Get a post for quoting."""
    try:
        from machina.apps.forum_conversation.models import Post
        
        # Get the post
        try:
            post = Post.objects.select_related('topic', 'poster').get(
                id=post_id,
                approved=True
            )
        except Post.DoesNotExist:
            return Response({
                'error': 'Post not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Format quoted content
        quoted_content = f"""[quote="{post.poster.username}"]
{str(post.content)}
[/quote]

"""
        
        # Return quoted content for use in new post
        return Response({
            'success': True,
            'quoted_content': quoted_content,
            'original_post': {
                'id': post.id,
                'poster': {
                    'username': post.poster.username,
                    'display_name': post.poster.get_display_name() if hasattr(post.poster, 'get_display_name') else post.poster.username
                },
                'created': post.created.isoformat(),
                'content': str(post.content)[:200] + '...' if len(str(post.content)) > 200 else str(post.content)
            },
            'topic': {
                'id': post.topic.id,
                'subject': post.topic.subject,
                'slug': post.topic.slug,
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to quote post: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Dashboard Forum Stats API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_forum_stats(request):
    """Get forum statistics for the user dashboard."""
    try:
        from machina.apps.forum.models import Forum
        from machina.apps.forum_conversation.models import Topic, Post
        from django.contrib.auth import get_user_model
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta
        
        User = get_user_model()
        
        # Get user's recent activity
        user_recent_posts = Post.objects.filter(
            poster=request.user,
            approved=True
        ).select_related('topic', 'topic__forum').order_by('-created')[:5]
        
        user_recent_topics = Topic.objects.filter(
            poster=request.user,
            approved=True
        ).select_related('forum').order_by('-created')[:5]
        
        # Get recent activity data
        recent_posts_data = []
        for post in user_recent_posts:
            recent_posts_data.append({
                'id': post.id,
                'content': str(post.content)[:150] + '...' if len(str(post.content)) > 150 else str(post.content),
                'created': post.created.isoformat(),
                'topic': {
                    'id': post.topic.id,
                    'subject': post.topic.subject,
                    'slug': post.topic.slug,
                },
                'forum': {
                    'id': post.topic.forum.id,
                    'name': post.topic.forum.name,
                    'slug': post.topic.forum.slug,
                }
            })
        
        recent_topics_data = []
        for topic in user_recent_topics:
            recent_topics_data.append({
                'id': topic.id,
                'subject': topic.subject,
                'slug': topic.slug,
                'created': topic.created.isoformat(),
                'posts_count': topic.posts_count,
                'views_count': topic.views_count,
                'forum': {
                    'id': topic.forum.id,
                    'name': topic.forum.name,
                    'slug': topic.forum.slug,
                }
            })
        
        # Get overall forum statistics using the centralized service
        from apps.api.services.container import container
        stats_service = container.get_statistics_service()
        overall_stats = stats_service.get_forum_statistics()
        total_forums = Forum.objects.filter(type=Forum.FORUM_POST).count()
        
        # Get recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_topics_count = Topic.objects.filter(
            created__gte=week_ago,
            approved=True
        ).count()
        recent_posts_count = Post.objects.filter(
            created__gte=week_ago,
            approved=True
        ).count()
        
        # Get user's forum stats
        user_topics_count = Topic.objects.filter(
            poster=request.user,
            approved=True
        ).count()
        user_posts_count = Post.objects.filter(
            poster=request.user,
            approved=True
        ).count()
        
        # Get most active forums (by posts in last week)
        active_forums = Forum.objects.filter(
            type=Forum.FORUM_POST
        ).annotate(
            recent_posts=Count(
                'topics__posts',
                filter=Q(
                    topics__posts__created__gte=week_ago,
                    topics__posts__approved=True
                )
            )
        ).order_by('-recent_posts')[:5]
        
        active_forums_data = []
        for forum in active_forums:
            # Get latest topic for this forum
            latest_topic = Topic.objects.filter(
                forum=forum,
                approved=True
            ).select_related('poster').order_by('-last_post_on').first()
            
            latest_topic_data = None
            if latest_topic:
                latest_topic_data = {
                    'id': latest_topic.id,
                    'subject': latest_topic.subject,
                    'slug': latest_topic.slug,
                    'last_post_on': latest_topic.last_post_on.isoformat() if latest_topic.last_post_on else None,
                    'poster': {
                        'username': latest_topic.poster.username,
                    }
                }
            
            active_forums_data.append({
                'id': forum.id,
                'name': forum.name,
                'slug': forum.slug,
                'description': str(forum.description) if forum.description else '',
                'topics_count': forum.direct_topics_count,
                'posts_count': forum.direct_posts_count,
                'recent_posts': forum.recent_posts,
                'latest_topic': latest_topic_data
            })
        
        return Response({
            'user_stats': {
                'topics_created': user_topics_count,
                'posts_made': user_posts_count,
                'recent_posts': recent_posts_data,
                'recent_topics': recent_topics_data
            },
            'forum_stats': {
                'total_topics': overall_stats['total_topics'],
                'total_posts': overall_stats['total_posts'],
                'total_users': overall_stats['total_users'],
                'online_users': overall_stats['online_users'],
                'total_forums': total_forums,
                'recent_topics': recent_topics_count,
                'recent_posts': recent_posts_count
            },
            'active_forums': active_forums_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch dashboard stats: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Blog/Wagtail API Views

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def blog_index(request):
    """Get blog posts for React frontend."""
    try:
        from apps.blog.models import BlogPage, BlogCategory
        
        # Get query parameters
        category_slug = request.GET.get('category')
        tag = request.GET.get('tag')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 9))
        
        # Get all published blog pages
        blog_pages = BlogPage.objects.live().public().order_by('-first_published_at')
        
        # Filter by category if provided
        if category_slug:
            blog_pages = blog_pages.filter(categories__slug=category_slug)
        
        # Filter by tag if provided
        if tag:
            blog_pages = blog_pages.filter(tags__name=tag)
        
        # Calculate pagination
        total_count = blog_pages.count()
        start = (page - 1) * page_size
        end = start + page_size
        paginated_posts = blog_pages[start:end]
        
        # Serialize blog posts
        posts_data = []
        for post in paginated_posts:
            # Get categories
            categories = [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'slug': cat.slug,
                    'color': cat.color
                }
                for cat in post.categories.all()
            ]
            
            # Get tags
            tags = [tag.name for tag in post.tags.all()]
            
            # Render body content (simplified for JSON)
            body_content = []
            for block in post.body:
                if block.block_type == 'paragraph':
                    body_content.append({
                        'type': 'paragraph',
                        'value': str(block.value)[:200] + '...' if len(str(block.value)) > 200 else str(block.value)
                    })
                elif block.block_type == 'heading':
                    body_content.append({
                        'type': 'heading',
                        'value': str(block.value)
                    })
                # Add more block types as needed
            
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'intro': post.intro,
                'url': post.url,
                'author': {
                    'username': post.author.username if post.author else 'Anonymous',
                    'display_name': post.author.get_full_name() if post.author and post.author.get_full_name() else (post.author.username if post.author else 'Anonymous')
                } if post.author else None,
                'date': post.date.isoformat() if post.date else None,
                'reading_time': post.reading_time,
                'ai_generated': post.ai_generated,
                'ai_summary': post.ai_summary,
                'categories': categories,
                'tags': tags,
                'featured_image': get_featured_image_url(post),
                'body_preview': body_content[:2]  # First 2 blocks for preview
            })
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        return Response({
            'posts': posts_data,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'page_size': page_size,
                'has_next': has_next,
                'has_previous': has_previous
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch blog posts: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def blog_post_detail(request, post_slug):
    """Get individual blog post for React frontend."""
    try:
        from apps.blog.models import BlogPage
        
        # Get the blog post
        post = get_object_or_404(BlogPage.objects.live().public(), slug=post_slug)
        
        # Get categories
        categories = [
            {
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'color': cat.color
            }
            for cat in post.categories.all()
        ]
        
        # Get tags
        tags = [tag.name for tag in post.tags.all()]
        
        # Render full body content
        body_content = []
        for block in post.body:
            if block.block_type == 'paragraph':
                body_content.append({
                    'type': 'paragraph',
                    'value': str(block.value)
                })
            elif block.block_type == 'heading':
                body_content.append({
                    'type': 'heading',
                    'value': str(block.value)
                })
            elif block.block_type == 'code':
                body_content.append({
                    'type': 'code',
                    'value': {
                        'language': block.value.get('language', 'text'),
                        'code': block.value.get('code', ''),
                        'caption': block.value.get('caption', '')
                    }
                })
            elif block.block_type == 'callout':
                body_content.append({
                    'type': 'callout',
                    'value': {
                        'type': block.value.get('type', 'info'),
                        'title': block.value.get('title', ''),
                        'text': str(block.value.get('text', ''))
                    }
                })
            elif block.block_type == 'quote':
                body_content.append({
                    'type': 'quote',
                    'value': {
                        'text': str(block.value.get('text', '')),
                        'attribution': block.value.get('attribute_name', '')
                    }
                })
            # Add more block types as needed
        
        # Get related posts
        related_posts = BlogPage.objects.live().public().exclude(
            id=post.id
        ).filter(
            categories__in=post.categories.all()
        ).distinct().order_by('-first_published_at')[:3]
        
        related_posts_data = [
            {
                'id': related.id,
                'title': related.title,
                'slug': related.slug,
                'intro': related.intro[:100] + '...' if len(related.intro) > 100 else related.intro,
                'url': related.url,
                'date': related.date.isoformat() if related.date else None,
                'reading_time': related.reading_time
            }
            for related in related_posts
        ]
        
        return Response({
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'intro': post.intro,
            'url': post.url,
            'author': {
                'username': post.author.username if post.author else 'Anonymous',
                'display_name': post.author.get_full_name() if post.author and post.author.get_full_name() else (post.author.username if post.author else 'Anonymous')
            } if post.author else None,
            'date': post.date.isoformat() if post.date else None,
            'reading_time': post.reading_time,
            'ai_generated': post.ai_generated,
            'ai_summary': post.ai_summary,
            'categories': categories,
            'tags': tags,
            'featured_image': get_featured_image_url(post),
            'body': body_content,
            'related_posts': related_posts_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch blog post: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def blog_categories(request):
    """Get blog categories for React frontend."""
    try:
        from apps.blog.models import BlogCategory
        
        categories = BlogCategory.objects.all().order_by('name')
        
        categories_data = [
            {
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'description': cat.description,
                'color': cat.color,
                'post_count': cat.blogpage_set.live().public().count()
            }
            for cat in categories
        ]
        
        return Response({'categories': categories_data})
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch blog categories: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def wagtail_homepage(request):
    """Get Wagtail homepage data for React frontend."""
    try:
        from apps.blog.models import HomePage, BlogPage
        
        # Get the homepage
        homepage = HomePage.objects.live().first()
        if not homepage:
            return Response({
                'error': 'Homepage not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get features
        features = []
        for block in homepage.features:
            if block.block_type == 'feature':
                features.append({
                    'title': block.value.get('title', ''),
                    'description': block.value.get('description', ''),
                    'icon': block.value.get('icon', '')
                })
        
        # Get stats
        stats = []
        for block in homepage.stats:
            if block.block_type == 'stat':
                stats.append({
                    'number': block.value.get('number', ''),
                    'label': block.value.get('label', ''),
                    'description': block.value.get('description', '')
                })
        
        # Get recent blog posts
        recent_posts = BlogPage.objects.live().public().order_by('-first_published_at')[:3]
        recent_posts_data = [
            {
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'intro': post.intro,
                'url': post.url,
                'date': post.date.isoformat() if post.date else None,
                'reading_time': post.reading_time,
                'ai_generated': post.ai_generated
            }
            for post in recent_posts
        ]
        
        return Response({
            'title': homepage.title,
            'hero_title': homepage.hero_title,
            'hero_subtitle': homepage.hero_subtitle,
            'hero_description': str(homepage.hero_description) if homepage.hero_description else '',
            'features_title': homepage.features_title,
            'features': features,
            'stats': stats,
            'recent_posts': recent_posts_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch homepage: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# WAGTAIL LEARNING CONTENT API ENDPOINTS
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def learning_index(request):
    """Get learning index page with featured courses."""
    try:
        from apps.blog.models import LearningIndexPage, CoursePage, SkillLevel
        
        # Get the learning index page
        learning_page = LearningIndexPage.objects.live().first()
        if not learning_page:
            return Response({
                'error': 'Learning index page not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get featured courses
        featured_courses = CoursePage.objects.live().public().filter(
            featured=True
        ).order_by('-first_published_at')[:6]
        
        featured_courses_data = []
        for course in featured_courses:
            featured_courses_data.append({
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'url': course.url,
                'course_code': course.course_code,
                'short_description': course.short_description,
                'difficulty_level': course.difficulty_level,
                'estimated_duration': course.estimated_duration,
                'is_free': course.is_free,
                'price': str(course.price) if course.price else None,
                'skill_level': {
                    'name': course.skill_level.name,
                    'slug': course.skill_level.slug,
                    'color': course.skill_level.color
                } if course.skill_level else None,
                'instructor': {
                    'name': course.instructor.get_full_name(),
                    'email': course.instructor.email
                } if course.instructor else None,
                'course_image': course.course_image.url if course.course_image else None,
                'categories': [
                    {
                        'name': cat.name,
                        'slug': cat.slug,
                        'color': cat.color
                    }
                    for cat in course.categories.all()
                ]
            })
        
        # Get skill levels
        skill_levels = SkillLevel.objects.all()
        skill_levels_data = [
            {
                'id': level.id,
                'name': level.name,
                'slug': level.slug,
                'description': level.description,
                'color': level.color,
                'order': level.order
            }
            for level in skill_levels
        ]
        
        return Response({
            'title': learning_page.title,
            'intro': str(learning_page.intro) if learning_page.intro else '',
            'featured_courses_title': learning_page.featured_courses_title,
            'featured_courses': featured_courses_data,
            'skill_levels': skill_levels_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch learning index: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def courses_list(request):
    """Get list of Wagtail courses with filtering and pagination."""
    try:
        from apps.blog.models import CoursePage, SkillLevel, BlogCategory
        
        # Get query parameters
        skill_level_slug = request.GET.get('skill_level')
        category_slug = request.GET.get('category')
        difficulty = request.GET.get('difficulty')
        is_free = request.GET.get('is_free')
        search = request.GET.get('search')
        page_num = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 12))
        
        # Start with base queryset
        courses = CoursePage.objects.live().public().order_by('-first_published_at')
        
        # Apply filters
        if skill_level_slug:
            courses = courses.filter(skill_level__slug=skill_level_slug)
        
        if category_slug:
            courses = courses.filter(categories__slug=category_slug)
        
        if difficulty:
            courses = courses.filter(difficulty_level=difficulty)
        
        if is_free is not None:
            is_free_bool = is_free.lower() in ('true', '1')
            courses = courses.filter(is_free=is_free_bool)
        
        if search:
            courses = courses.search(search)
        
        # Pagination
        total_count = courses.count()
        start = (page_num - 1) * page_size
        end = start + page_size
        paginated_courses = courses[start:end]
        
        # Serialize courses
        courses_data = []
        for course in paginated_courses:
            # Get lesson count
            lesson_count = course.get_children().live().public().count()
            
            courses_data.append({
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'url': course.url,
                'course_code': course.course_code,
                'short_description': course.short_description,
                'difficulty_level': course.difficulty_level,
                'estimated_duration': course.estimated_duration,
                'is_free': course.is_free,
                'price': str(course.price) if course.price else None,
                'lesson_count': lesson_count,
                'featured': course.featured,
                'skill_level': {
                    'name': course.skill_level.name,
                    'slug': course.skill_level.slug,
                    'color': course.skill_level.color
                } if course.skill_level else None,
                'instructor': {
                    'name': course.instructor.get_full_name(),
                    'email': course.instructor.email
                } if course.instructor else None,
                'course_image': course.course_image.url if course.course_image else None,
                'categories': [
                    {
                        'name': cat.name,
                        'slug': cat.slug,
                        'color': cat.color
                    }
                    for cat in course.categories.all()
                ],
                'tags': serialize_tags(course)
            })
        
        # Pagination info
        pagination = {
            'current_page': page_num,
            'total_pages': (total_count + page_size - 1) // page_size,
            'total_count': total_count,
            'page_size': page_size,
            'has_next': end < total_count,
            'has_previous': page_num > 1
        }
        
        return Response({
            'courses': courses_data,
            'pagination': pagination
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch courses: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def course_detail(request, course_slug):
    """Get detailed information about a specific Wagtail course."""
    try:
        from apps.blog.models import CoursePage
        
        # Get the course
        course = CoursePage.objects.live().public().filter(slug=course_slug).first()
        if not course:
            return Response({
                'error': 'Course not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get course lessons
        lessons = course.get_children().live().public().order_by('lessonpage__lesson_number')
        lessons_data = []
        for lesson in lessons:
            lesson_specific = lesson.specific
            lessons_data.append({
                'id': lesson.id,
                'title': lesson.title,
                'slug': lesson.slug,
                'url': lesson.url,
                'lesson_number': lesson_specific.lesson_number,
                'estimated_duration': lesson_specific.estimated_duration,
                'intro': str(lesson_specific.intro) if lesson_specific.intro else ''
            })
        
        # Get related courses
        related_courses = CoursePage.objects.live().public().exclude(
            id=course.id
        ).filter(
            skill_level=course.skill_level
        ).order_by('-first_published_at')[:3]
        
        related_courses_data = []
        for related in related_courses:
            related_courses_data.append({
                'id': related.id,
                'title': related.title,
                'slug': related.slug,
                'url': related.url,
                'short_description': related.short_description,
                'difficulty_level': related.difficulty_level,
                'course_image': related.course_image.url if related.course_image else None
            })
        
        # Serialize syllabus safely
        syllabus_data = []
        try:
            for block in course.syllabus:
                if block.block_type == 'module':
                    syllabus_data.append({
                        'title': str(block.value.get('title', '')),
                        'description': str(block.value.get('description', '')),
                        'lessons': [
                            {
                                'lesson_title': str(lesson.get('lesson_title', '')),
                                'lesson_description': str(lesson.get('lesson_description', '')),
                                'estimated_time': str(lesson.get('estimated_time', ''))
                            }
                            for lesson in block.value.get('lessons', [])
                        ]
                    })
        except Exception as e:
            logger.error(f"Error serializing syllabus: {e}")
            syllabus_data = []
        
        # Serialize features safely
        features_data = []
        try:
            for block in course.features:
                if block.block_type == 'feature':
                    features_data.append({
                        'icon': str(block.value.get('icon', '')),
                        'title': str(block.value.get('title', '')),
                        'description': str(block.value.get('description', ''))
                    })
        except Exception as e:
            logger.error(f"Error serializing features: {e}")
            features_data = []
        
        return Response({
            'id': course.id,
            'title': course.title,
            'slug': course.slug,
            'course_code': course.course_code,
            'short_description': course.short_description,
            'detailed_description': str(course.detailed_description),
            'prerequisites': str(course.prerequisites) if course.prerequisites else '',
            'estimated_duration': course.estimated_duration,
            'difficulty_level': course.difficulty_level,
            'is_free': course.is_free,
            'price': str(course.price) if course.price else None,
            'enrollment_limit': course.enrollment_limit,
            'featured': course.featured,
            'syllabus': syllabus_data,
            'features': features_data,
            'skill_level': {
                'name': course.skill_level.name,
                'slug': course.skill_level.slug,
                'color': course.skill_level.color,
                'description': course.skill_level.description
            } if course.skill_level else None,
            'instructor': {
                'name': course.instructor.get_full_name(),
                'email': course.instructor.email
            } if course.instructor else None,
            'course_image': course.course_image.url if course.course_image else None,
            'categories': [
                {
                    'name': cat.name,
                    'slug': cat.slug,
                    'color': cat.color
                }
                for cat in course.categories.all()
            ],
            'learning_objectives': [
                {
                    'title': obj.title,
                    'description': obj.description,
                    'category': obj.category
                }
                for obj in course.learning_objectives.all()
            ],
            'tags': serialize_tags(course),
            'lessons': lessons_data,
            'related_courses': related_courses_data,
            'meta': {
                'search_description': course.search_description,
                'first_published_at': course.first_published_at.isoformat() if course.first_published_at else None,
                'last_published_at': course.last_published_at.isoformat() if course.last_published_at else None
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch course: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def lesson_detail(request, course_slug, lesson_slug):
    """Get detailed information about a specific Wagtail lesson."""
    try:
        from apps.blog.models import LessonPage, CoursePage
        
        # Get the course first
        course = CoursePage.objects.live().public().filter(slug=course_slug).first()
        if not course:
            return Response({
                'error': 'Course not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the lesson
        lesson = course.get_children().live().public().filter(slug=lesson_slug).first()
        if not lesson:
            return Response({
                'error': 'Lesson not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        lesson = lesson.specific
        
        # Safely get lesson content
        content_data = []
        try:
            for block in lesson.content:
                block_data = {
                    'type': block.block_type,
                    'value': block.value
                }
                
                # Process specific block types and ensure JSON serializable
                if block.block_type == 'text':
                    # Handle RichText objects by converting to string
                    block_data['value'] = str(block.value)
                elif block.block_type == 'heading':
                    # Handle heading blocks
                    block_data['value'] = str(block.value)
                elif block.block_type == 'code_example':
                    block_data['value'] = {
                        'title': block.value.get('title', ''),
                        'language': block.value.get('language', 'text'),
                        'code': block.value.get('code', ''),
                        'explanation': str(block.value.get('explanation', ''))
                    }
                elif block.block_type == 'interactive_exercise':
                    block_data['value'] = {
                        'title': block.value.get('title', ''),
                        'instructions': str(block.value.get('instructions', '')),
                        'starter_code': block.value.get('starter_code', ''),
                        'solution': block.value.get('solution', ''),
                        'hints': block.value.get('hints', [])
                    }
                elif block.block_type == 'video':
                    block_data['value'] = {
                        'title': block.value.get('title', ''),
                        'video_url': block.value.get('video_url', ''),
                        'description': str(block.value.get('description', ''))
                    }
                elif block.block_type == 'callout':
                    block_data['value'] = {
                        'type': block.value.get('type', 'info'),
                        'title': block.value.get('title', ''),
                        'text': str(block.value.get('text', ''))
                    }
                elif block.block_type == 'quiz':
                    block_data['value'] = {
                        'question': block.value.get('question', ''),
                        'options': block.value.get('options', []),
                        'correct_answer': block.value.get('correct_answer', 0),
                        'explanation': str(block.value.get('explanation', ''))
                    }
                elif block.block_type == 'runnable_code_example':
                    block_data['value'] = {
                        'title': block.value.get('title', ''),
                        'language': block.value.get('language', 'python'),
                        'code': block.value.get('code', ''),
                        'mock_output': block.value.get('mock_output', ''),
                        'ai_explanation': block.value.get('ai_explanation', '')
                    }
                elif block.block_type == 'fill_blank_code':
                    # Parse JSON strings for complex fields
                    import json
                    solutions = {}
                    alternative_solutions = {}
                    ai_hints = {}
                    
                    try:
                        solutions = json.loads(block.value.get('solutions', '{}'))
                    except (json.JSONDecodeError, TypeError):
                        solutions = {}
                    
                    try:
                        alternative_solutions = json.loads(block.value.get('alternative_solutions', '{}'))
                    except (json.JSONDecodeError, TypeError):
                        alternative_solutions = {}
                    
                    try:
                        ai_hints = json.loads(block.value.get('ai_hints', '{}'))
                    except (json.JSONDecodeError, TypeError):
                        ai_hints = {}
                    
                    block_data['value'] = {
                        'title': block.value.get('title', ''),
                        'language': block.value.get('language', 'python'),
                        'template': block.value.get('template', ''),
                        'solutions': solutions,
                        'alternative_solutions': alternative_solutions,
                        'ai_hints': ai_hints
                    }
                elif block.block_type == 'multiple_choice_code':
                    # Parse JSON strings for complex fields
                    import json
                    choices = {}
                    solutions = {}
                    ai_explanations = {}
                    
                    try:
                        choices = json.loads(block.value.get('choices', '{}'))
                    except (json.JSONDecodeError, TypeError):
                        choices = {}
                    
                    try:
                        solutions = json.loads(block.value.get('solutions', '{}'))
                    except (json.JSONDecodeError, TypeError):
                        solutions = {}
                    
                    try:
                        ai_explanations = json.loads(block.value.get('ai_explanations', '{}'))
                    except (json.JSONDecodeError, TypeError):
                        ai_explanations = {}
                    
                    block_data['value'] = {
                        'title': block.value.get('title', ''),
                        'language': block.value.get('language', 'python'),
                        'template': block.value.get('template', ''),
                        'choices': choices,
                        'solutions': solutions,
                        'ai_explanations': ai_explanations
                    }
                else:
                    # For any other block types, try to convert value to string
                    try:
                        block_data['value'] = str(block.value)
                    except:
                        block_data['value'] = ''
                
                content_data.append(block_data)
        except AttributeError:
            # If content field doesn't exist or has issues, provide empty content
            content_data = []
        
        # Safely get lesson objectives
        objectives_data = []
        try:
            for block in lesson.lesson_objectives:
                if block.block_type == 'objective':
                    objectives_data.append(block.value)
        except AttributeError:
            objectives_data = []
        
        # Safely get resources
        resources_data = []
        try:
            for block in lesson.resources:
                if block.block_type == 'resource':
                    resources_data.append({
                        'title': block.value.get('title', ''),
                        'url': block.value.get('url', ''),
                        'description': block.value.get('description', ''),
                        'type': block.value.get('type', 'article')
                    })
        except AttributeError:
            resources_data = []
        
        # Get navigation (previous/next lessons)
        navigation = {}
        try:
            lessons = course.get_children().live().public().order_by('lessonpage__lesson_number')
            lesson_list = list(lessons)
            current_index = next((i for i, l in enumerate(lesson_list) if l.id == lesson.id), None)
            
            if current_index is not None:
                if current_index > 0:
                    prev_lesson = lesson_list[current_index - 1]
                    navigation['previous'] = {
                        'title': prev_lesson.title,
                        'slug': prev_lesson.slug,
                        'url': prev_lesson.url
                    }
                if current_index < len(lesson_list) - 1:
                    next_lesson = lesson_list[current_index + 1]
                    navigation['next'] = {
                        'title': next_lesson.title,
                        'slug': next_lesson.slug,
                        'url': next_lesson.url
                    }
        except Exception:
            navigation = {}
        
        # Get lesson exercises
        exercises_data = []
        try:
            exercises = lesson.get_children().live().public()
            for exercise in exercises:
                exercise_specific = exercise.specific
                exercises_data.append({
                    'id': exercise.id,
                    'title': exercise.title,
                    'slug': exercise.slug,
                    'url': exercise.url,
                    'exercise_type': getattr(exercise_specific, 'exercise_type', 'coding'),
                    'difficulty': getattr(exercise_specific, 'difficulty', 'beginner'),
                    'points': getattr(exercise_specific, 'points', 10)
                })
        except Exception:
            exercises_data = []
        
        return Response({
            'id': lesson.id,
            'title': lesson.title,
            'slug': lesson.slug,
            'lesson_number': getattr(lesson, 'lesson_number', 1),
            'estimated_duration': getattr(lesson, 'estimated_duration', '30 minutes'),
            'intro': str(lesson.intro) if hasattr(lesson, 'intro') else '',
            'content': content_data,
            'objectives': objectives_data,
            'prerequisites': str(getattr(lesson, 'lesson_prerequisites', '')),
            'resources': resources_data,
            'course': {
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'url': course.url
            },
            'navigation': navigation,
            'exercises': exercises_data,
            'meta': {
                'search_description': getattr(lesson, 'search_description', ''),
                'first_published_at': lesson.first_published_at.isoformat() if lesson.first_published_at else None,
                'last_published_at': lesson.last_published_at.isoformat() if lesson.last_published_at else None
            }
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Lesson detail error: {str(e)}")
        logger.error(traceback.format_exc())
        return Response({
            'error': f'Failed to fetch lesson: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def exercise_detail(request, course_slug, lesson_slug, exercise_slug):
    """Get detailed information about a specific Wagtail exercise."""
    try:
        from apps.blog.models import ExercisePage, LessonPage, CoursePage
        
        # Get the course and lesson first
        course = CoursePage.objects.live().public().filter(slug=course_slug).first()
        if not course:
            return Response({
                'error': 'Course not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        lesson = course.get_children().live().public().filter(slug=lesson_slug).first()
        if not lesson:
            return Response({
                'error': 'Lesson not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the exercise
        exercise = lesson.get_children().live().public().filter(slug=exercise_slug).first()
        if not exercise:
            return Response({
                'error': 'Exercise not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        exercise = exercise.specific
        
        # Get test cases (only show non-hidden ones to students)
        test_cases_data = []
        for block in exercise.test_cases:
            if block.block_type == 'test_case':
                test_case = {
                    'input': block.value.get('input', ''),
                    'expected_output': block.value.get('expected_output', ''),
                    'description': block.value.get('description', ''),
                    'is_hidden': block.value.get('is_hidden', False)
                }
                # Only include non-hidden test cases in API response
                if not test_case['is_hidden']:
                    test_cases_data.append(test_case)
        
        # Get hints
        hints_data = []
        for block in exercise.hints:
            if block.block_type == 'hint':
                hints_data.append({
                    'hint_text': str(block.value.get('hint_text', '')),
                    'reveal_after_attempts': block.value.get('reveal_after_attempts', 3)
                })
        
        return Response({
            'id': exercise.id,
            'title': exercise.title,
            'slug': exercise.slug,
            'exercise_type': exercise.exercise_type,
            'difficulty': exercise.difficulty,
            'points': exercise.points,
            'description': str(exercise.description),
            'starter_code': exercise.starter_code,
            'programming_language': exercise.programming_language,
            'test_cases': test_cases_data,
            'hints': hints_data,
            'question_data': exercise.question_data,
            'time_limit': exercise.time_limit,
            'max_attempts': exercise.max_attempts,
            'course': {
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'url': course.url
            },
            'lesson': {
                'id': lesson.id,
                'title': lesson.title,
                'slug': lesson.slug,
                'url': lesson.url
            },
            'meta': {
                'search_description': exercise.search_description,
                'first_published_at': exercise.first_published_at.isoformat() if exercise.first_published_at else None,
                'last_published_at': exercise.last_published_at.isoformat() if exercise.last_published_at else None
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch exercise: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def wagtail_playground(request):
    """Get Wagtail CodePlaygroundPage data for React frontend."""
    try:
        from apps.blog.models import CodePlaygroundPage
        
        # Get the playground page
        playground = CodePlaygroundPage.objects.live().first()
        if not playground:
            return Response({
                'error': 'Playground page not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get features
        features = []
        for block in playground.features:
            if block.block_type == 'feature':
                features.append({
                    'title': block.value.get('title', ''),
                    'description': block.value.get('description', ''),
                    'icon': block.value.get('icon', '')
                })
        
        # Get code examples
        code_examples = []
        for block in playground.code_examples:
            if block.block_type == 'example':
                code_examples.append({
                    'title': block.value.get('title', ''),
                    'description': block.value.get('description', ''),
                    'language': block.value.get('language', 'python'),
                    'code': block.value.get('code', ''),
                    'category': block.value.get('category', 'basic')
                })
        
        # Get shortcuts
        shortcuts = []
        for block in playground.shortcuts:
            if block.block_type == 'shortcut':
                shortcuts.append({
                    'keys': block.value.get('keys', ''),
                    'description': block.value.get('description', '')
                })
        
        # Get initial code - use default if not set
        initial_code = playground.default_code
        if not initial_code:
            initial_code = '''# Welcome to Python Learning Studio Playground!
# Write your Python code here and click Run to execute it.

def greet(name):
    """A simple greeting function"""
    return f"Hello, {name}! Welcome to Python programming!"

# Try it out
message = greet("Programmer")
print(message)

# You can also do calculations
result = 42 * 2
print(f"The answer to everything times 2 is: {result}")
'''
        
        return Response({
            'id': playground.id,
            'title': playground.title,
            'slug': playground.slug,
            'description': str(playground.description),
            'default_code': initial_code,
            'programming_language': playground.programming_language,
            'features': features,
            'code_examples': code_examples,
            'shortcuts': shortcuts,
            'settings': {
                'enable_file_operations': playground.enable_file_operations,
                'enable_auto_save': playground.enable_auto_save,
                'enable_multiple_languages': playground.enable_multiple_languages
            },
            'meta': {
                'search_description': playground.search_description,
                'first_published_at': playground.first_published_at.isoformat() if playground.first_published_at else None,
                'last_published_at': playground.last_published_at.isoformat() if playground.last_published_at else None,
                'url': playground.url
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch playground: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# WAGTAIL COURSE ENROLLMENT API ENDPOINTS
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def wagtail_course_enroll(request, course_slug):
    """Enroll user in a Wagtail course."""
    try:
        from apps.blog.models import CoursePage, WagtailCourseEnrollment
        
        # Get the course
        course = CoursePage.objects.live().public().filter(slug=course_slug).first()
        if not course:
            return Response({
                'error': 'Course not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is already enrolled
        enrollment, created = WagtailCourseEnrollment.objects.get_or_create(
            user=request.user,
            course=course
        )
        
        if created:
            return Response({
                'success': True,
                'message': 'Successfully enrolled in course',
                'enrollment': {
                    'id': enrollment.id,
                    'course': course.title,
                    'enrolled_at': enrollment.enrolled_at.isoformat(),
                    'progress_percentage': enrollment.progress_percentage
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': True,
                'message': 'Already enrolled in this course',
                'enrollment': {
                    'id': enrollment.id,
                    'course': course.title,
                    'enrolled_at': enrollment.enrolled_at.isoformat(),
                    'progress_percentage': enrollment.progress_percentage
                }
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({
            'error': f'Failed to enroll in course: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def wagtail_course_unenroll(request, course_slug):
    """Unenroll user from a Wagtail course."""
    try:
        from apps.blog.models import CoursePage, WagtailCourseEnrollment
        
        # Get the course
        course = CoursePage.objects.live().public().filter(slug=course_slug).first()
        if not course:
            return Response({
                'error': 'Course not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is enrolled
        try:
            enrollment = WagtailCourseEnrollment.objects.get(
                user=request.user,
                course=course
            )
            enrollment.delete()
            
            return Response({
                'success': True,
                'message': 'Successfully unenrolled from course'
            }, status=status.HTTP_200_OK)
            
        except WagtailCourseEnrollment.DoesNotExist:
            return Response({
                'error': 'Not enrolled in this course'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({
            'error': f'Failed to unenroll from course: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wagtail_course_enrollment_status(request, course_slug):
    """Check user's enrollment status for a Wagtail course."""
    try:
        from apps.blog.models import CoursePage, WagtailCourseEnrollment
        
        # Get the course
        course = CoursePage.objects.live().public().filter(slug=course_slug).first()
        if not course:
            return Response({
                'error': 'Course not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check enrollment status
        try:
            enrollment = WagtailCourseEnrollment.objects.get(
                user=request.user,
                course=course
            )
            
            return Response({
                'enrolled': True,
                'enrollment': {
                    'id': enrollment.id,
                    'enrolled_at': enrollment.enrolled_at.isoformat(),
                    'progress_percentage': enrollment.progress_percentage,
                    'completed': enrollment.completed,
                    'completed_at': enrollment.completed_at.isoformat() if enrollment.completed_at else None,
                    'last_activity': enrollment.last_activity.isoformat(),
                    'total_time_spent': enrollment.total_time_spent
                }
            })
            
        except WagtailCourseEnrollment.DoesNotExist:
            return Response({
                'enrolled': False,
                'enrollment': None
            })
            
    except Exception as e:
        return Response({
            'error': f'Failed to check enrollment status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wagtail_user_enrollments(request):
    """Get all Wagtail course enrollments for the authenticated user."""
    try:
        from apps.blog.models import WagtailCourseEnrollment
        
        # Get user's enrollments
        enrollments = WagtailCourseEnrollment.objects.filter(
            user=request.user
        ).select_related('course').order_by('-enrolled_at')
        
        enrollments_data = []
        for enrollment in enrollments:
            course = enrollment.course
            enrollments_data.append({
                'id': enrollment.id,
                'course': {
                    'id': course.id,
                    'title': course.title,
                    'slug': course.slug,
                    'course_code': course.course_code,
                    'short_description': course.short_description,
                    'difficulty_level': course.difficulty_level,
                    'is_free': course.is_free,
                    'price': course.price,
                    'url': course.url
                },
                'enrolled_at': enrollment.enrolled_at.isoformat(),
                'progress_percentage': enrollment.progress_percentage,
                'completed': enrollment.completed,
                'completed_at': enrollment.completed_at.isoformat() if enrollment.completed_at else None,
                'last_activity': enrollment.last_activity.isoformat(),
                'total_time_spent': enrollment.total_time_spent
            })
        
        return Response({
            'enrollments': enrollments_data,
            'total_count': len(enrollments_data)
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch enrollments: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


