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
from apps.learning.code_execution import exercise_evaluator, code_executor
from apps.learning.services import learning_ai
from ..serializers import (
    CodeExecutionRequestSerializer, CodeExecutionResponseSerializer,
    AIAssistanceRequestSerializer, AIAssistanceResponseSerializer
)
from ..services import CodeExecutionService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_code(request):
    """Execute Python code in a secure Docker environment."""
    try:
        data = request.data
        code = data.get('code', '')
        test_cases = data.get('test_cases', [])
        time_limit = data.get('time_limit', 30)
        memory_limit = data.get('memory_limit', 256)
        
        # Use the unified code execution service
        result = CodeExecutionService.execute_code(
            code=code,
            test_cases=test_cases,
            time_limit=time_limit,
            memory_limit=memory_limit,
            use_cache=True
        )
        
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
        
        # Execute code with test cases using the service
        result = CodeExecutionService.execute_with_test_cases(
            code=code,
            test_cases=test_cases,
            time_limit=30,
            memory_limit=256
        )
        
        # TODO: Create submission record when ExerciseSubmission model is available
        # For now, just return the result without storing submission
        result['submission_id'] = None  # Placeholder
        
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