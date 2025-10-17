"""
Code execution views for running and evaluating code submissions.
"""

import logging
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.learning.models import Exercise
from apps.learning.exercise_models import Submission
from apps.learning.code_execution import exercise_evaluator, code_executor
from apps.learning.services import learning_ai
from ..serializers import (
    CodeExecutionRequestSerializer, CodeExecutionResponseSerializer,
    AIAssistanceRequestSerializer, AIAssistanceResponseSerializer
)
from ..services import CodeExecutionService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # 🔒 SECURITY FIX: Require authentication
@ratelimit(key='user', rate='10/m', method='POST', block=True)  # 🔒 SECURITY: Rate limit per user
@ratelimit(key='ip', rate='30/m', method='POST', block=True)  # 🔒 SECURITY: Rate limit per IP
def execute_code(request):
    """
    Execute Python code in a secure Docker environment.

    SECURITY NOTE: This endpoint requires authentication and Docker.
    The dangerous exec() fallback has been removed (CVE-2024-EXEC-001).

    Docker is REQUIRED for secure code execution. If Docker is unavailable,
    the service will return 503 Service Unavailable.
    """
    try:
        data = request.data
        code = data.get('code', '')

        # Validate input
        if not code or not isinstance(code, str):
            return Response({
                'success': False,
                'error': 'Valid code string is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Length limit for safety
        if len(code) > 10000:
            return Response({
                'success': False,
                'error': 'Code exceeds maximum length of 10,000 characters'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 🔒 SECURITY AUDIT LOG: Track all code execution attempts
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        code_length = len(code)

        logger.info(
            f"CODE_EXECUTION_AUDIT: "
            f"user_id={request.user.id} "
            f"username={request.user.username} "
            f"ip={client_ip} "
            f"code_length={code_length} "
            f"user_agent={user_agent[:100]}"
        )

        # 🔒 SECURITY: Docker is REQUIRED - no fallback to exec()
        # The exec() fallback was removed due to security vulnerability CVE-2024-EXEC-001
        import time as time_module
        start_time = time_module.time()

        try:
            result = CodeExecutionService.execute_code(
                code=code,
                test_cases=[],
                time_limit=5,
                use_cache=False
            )

            execution_success = result.get('success', False)
            execution_time = time_module.time() - start_time

            # 🔒 SECURITY AUDIT LOG: Log execution result
            logger.info(
                f"CODE_EXECUTION_RESULT: "
                f"user_id={request.user.id} "
                f"success={execution_success} "
                f"execution_time={execution_time:.3f}s "
                f"executor={'docker' if 'from_cache' not in result or not result.get('from_cache') else 'docker_cached'}"
            )

            return Response(result)

        except Exception as docker_error:
            # 🔒 SECURITY: Docker unavailable - return error instead of using exec()
            logger.error(
                f"CODE_EXECUTION_UNAVAILABLE: "
                f"user_id={request.user.id} "
                f"docker_error={str(docker_error)[:200]} "
                f"Service unavailable - exec() fallback has been removed for security"
            )

            return Response({
                'success': False,
                'error': 'Code execution service temporarily unavailable',
                'message': 'Our secure code execution environment is currently offline. Please try again in a few moments.',
                'details': 'Docker container service is required for secure code execution.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    except Exception as e:
        logger.error(f"Code execution error: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error during code execution'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='20/m', method='POST', block=True)  # 🔒 SECURITY: Higher limit for exercise submissions
def submit_exercise_code(request, exercise_id):
    """Submit code for an exercise using Docker executor."""
    try:
        exercise = get_object_or_404(Exercise, id=exercise_id, is_published=True)
        data = request.data
        code = data.get('code', '')

        # 🔒 SECURITY AUDIT LOG: Track exercise submission attempts
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        logger.info(
            f"EXERCISE_SUBMISSION_AUDIT: "
            f"user_id={request.user.id} "
            f"exercise_id={exercise_id} "
            f"exercise_title={exercise.title} "
            f"ip={client_ip} "
            f"code_length={len(code)}"
        )

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
        
        # Execute code with test cases using the service
        result = CodeExecutionService.execute_with_test_cases(
            code=code,
            test_cases=test_cases,
            time_limit=30,
            memory_limit=256
        )
        
        # Create submission record
        # Determine submission status
        if result.get('success'):
            tests_passed = result.get('tests_passed', 0)
            tests_total = result.get('tests_total', 0)
            if tests_total > 0 and tests_passed == tests_total:
                submission_status = 'passed'
            elif tests_passed > 0:
                submission_status = 'failed'
            else:
                submission_status = 'failed'
        else:
            if 'timeout' in result.get('error', '').lower():
                submission_status = 'timeout'
            elif 'memory' in result.get('error', '').lower():
                submission_status = 'memory_exceeded'
            else:
                submission_status = 'error'
        
        # Get latest attempt number for this user and exercise
        latest_submission = Submission.objects.filter(
            user=request.user,
            exercise=exercise
        ).order_by('-attempt_number').first()
        
        attempt_number = (latest_submission.attempt_number + 1) if latest_submission else 1
        
        # Create submission
        submission = Submission.objects.create(
            exercise=exercise,
            user=request.user,
            code=code,
            status=submission_status,
            score=result.get('score', 0),
            passed_tests=result.get('tests_passed', 0),
            total_tests=result.get('tests_total', 0),
            execution_time=result.get('execution_time'),
            output=result.get('output', ''),
            error_message=result.get('error', ''),
            attempt_number=attempt_number
        )
        
        # Add submission ID to result
        result['submission_id'] = str(submission.submission_id)
        result['attempt_number'] = attempt_number
        
        return Response(result)
        
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
        status_info = CodeExecutionService.get_docker_status()
        return Response(status_info)
    except Exception as e:
        logger.error(f"Docker status error: {e}")
        return Response({
            'docker_available': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CodeExecutionView(APIView):
    """API view for code execution - legacy endpoint for compatibility."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CodeExecutionRequestSerializer(data=request.data)
        if serializer.is_valid():
            # Use the unified service
            result = CodeExecutionService.execute_code(
                code=serializer.validated_data['code'],
                test_cases=serializer.validated_data.get('test_inputs', []),
                time_limit=serializer.validated_data.get('timeout', 10),
                use_cache=True
            )
            
            # Format response for legacy API
            response_serializer = CodeExecutionResponseSerializer({
                'success': result.get('success', False),
                'output': result.get('stdout', ''),
                'error': result.get('stderr', '') or result.get('error', ''),
                'execution_time': result.get('execution_time', 0),
                'memory_used': result.get('memory_used', 0)
            })
            
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(
    ratelimit(
        key='user',
        rate=settings.RATE_LIMIT_SETTINGS['AI_REQUESTS'],
        method='POST',
        block=True
    ),
    name='post'
)
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
                response = self._get_ai_response(
                    assistance_type, content, context, difficulty
                )
                
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
                return Response(
                    response_serializer.data,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_ai_response(self, assistance_type, content, context, difficulty):
        """Get AI response based on assistance type."""
        import json
        
        if assistance_type == 'code_explanation':
            return learning_ai.generate_exercise_explanation(content)
        elif assistance_type == 'error_help':
            return learning_ai.explain_error_message(content, context)
        elif assistance_type == 'hint_generation':
            return learning_ai.generate_hints_for_exercise(content, context)
        elif assistance_type == 'code_review':
            return learning_ai.review_student_code(content, context)
        elif assistance_type == 'exercise_generation':
            return learning_ai.create_exercise_from_concept(content, difficulty)
        elif assistance_type == 'contextual_chat':
            # Parse context for contextual chat
            try:
                context_data = json.loads(context) if context else {}
                exercise_context = context_data.get('exercise', {})
                student_code = context_data.get('student_code', '')
                conversation_history = context_data.get('conversation_history', [])
                return learning_ai.contextual_chat_response(
                    content, exercise_context, student_code, conversation_history
                )
            except json.JSONDecodeError:
                return learning_ai.contextual_chat_response(content)
        elif assistance_type == 'real_world_examples':
            industry_focus = context or 'general'
            return learning_ai.generate_real_world_examples(content, industry_focus)
        elif assistance_type == 'debugging_guidance':
            return learning_ai.generate_debugging_guidance(content, context, difficulty)
        elif assistance_type == 'struggle_analysis':
            # Parse context for struggle analysis
            try:
                context_data = json.loads(context) if context else {}
                time_spent = context_data.get('time_spent', 0)
                wrong_attempts = context_data.get('wrong_attempts', 0)
                code_attempts = context_data.get('code_attempts', [])
                exercise_data = context_data.get('exercise_data', {})
                return learning_ai.analyze_student_struggle(
                    exercise_data, time_spent, wrong_attempts, code_attempts
                )
            except json.JSONDecodeError:
                return "I'd be happy to help, but I need more information about what you're working on."
        else:
            raise ValueError(f"Invalid assistance type: {assistance_type}")


class ExerciseEvaluationView(APIView):
    """API view for exercise evaluation."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Evaluate exercise code submission."""
        code = request.data.get('code', '')
        exercise_data = request.data.get('exercise_data', {})
        
        if not code or not exercise_data:
            return Response({
                'error': 'Code and exercise data are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = exercise_evaluator.evaluate_submission(code, exercise_data)
            return Response(result)
        except Exception as e:
            logger.error(f"Exercise evaluation error: {e}")
            return Response({
                'error': 'Evaluation failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)