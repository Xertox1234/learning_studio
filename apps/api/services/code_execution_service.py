"""
Unified code execution service for handling all code execution logic.
"""

import logging
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.core.checks import register, Warning, Error

from apps.learning.code_execution import code_executor
from apps.learning.docker_executor import get_code_executor

logger = logging.getLogger(__name__)


@register()
def check_docker_availability(app_configs, **kwargs):
    """
    Django system check to verify Docker is available for code execution.

    This is a security-critical check added to prevent deployment without
    the required Docker infrastructure (CVE-2024-EXEC-001).
    """
    errors = []

    # Check if Docker requirement is enabled
    require_docker = getattr(settings, 'CODE_EXECUTION_REQUIRE_DOCKER', True)

    if not require_docker:
        errors.append(
            Warning(
                'CODE_EXECUTION_REQUIRE_DOCKER is disabled',
                hint='Docker should be required for production environments',
                obj='code_execution',
                id='security.W001',
            )
        )
        return errors

    # Try to connect to Docker
    try:
        import docker
        client = docker.from_env()
        client.ping()
        logger.info("Docker availability check passed")
    except ImportError:
        errors.append(
            Error(
                'Docker Python library is not installed',
                hint='Install docker library: pip install docker',
                obj='code_execution',
                id='security.E001',
            )
        )
    except Exception as e:
        errors.append(
            Error(
                f'Docker is not available: {str(e)}',
                hint='Ensure Docker daemon is running and accessible. '
                     'Code execution requires Docker for security.',
                obj='code_execution',
                id='security.E002',
            )
        )

    return errors


class CodeExecutionService:
    """Service for executing code in a secure environment."""
    
    @staticmethod
    def execute_code(
        code: str,
        test_cases: Optional[List[Dict]] = None,
        time_limit: int = 30,
        memory_limit: int = 256,
        use_cache: bool = True,
        language: str = 'python'
    ) -> Dict[str, Any]:
        """
        Execute code with Docker isolation, falling back to basic executor if needed.
        
        Args:
            code: The code to execute
            test_cases: Optional list of test cases to run
            time_limit: Maximum execution time in seconds (max 60)
            memory_limit: Maximum memory in MB (max 512)
            use_cache: Whether to use cached results
            language: Programming language (currently only 'python' supported)
            
        Returns:
            Dict containing execution results
        """
        # Validate and sanitize inputs
        time_limit = min(int(time_limit), 60)  # Max 60 seconds
        memory_limit = min(int(memory_limit), 512)  # Max 512MB
        
        if not code.strip():
            return {
                'success': False,
                'error': 'No code provided',
                'stdout': '',
                'stderr': '',
                'execution_time': 0,
                'memory_used': 0
            }
        
        # 🔒 SECURITY: Docker is REQUIRED - no fallback executors
        # All fallback execution methods have been removed for security (CVE-2024-EXEC-001)
        try:
            docker_executor = get_code_executor()
            result = docker_executor.execute_code(
                code=code,
                test_cases=test_cases or [],
                time_limit=time_limit,
                memory_limit=f"{memory_limit}m",
                use_cache=use_cache
            )
            return result

        except Exception as e:
            # 🔒 SECURITY: No fallback - Docker failure means service unavailable
            logger.error(
                f"CODE_EXECUTION_DOCKER_FAILURE: "
                f"Docker executor failed, service unavailable. "
                f"Error: {str(e)[:200]}"
            )

            # Re-raise the exception to be handled by the view layer
            # This will result in a ServiceUnavailable response to the user
            raise Exception(
                "Code execution service unavailable: Docker container system is required "
                "for secure code execution. Please contact support if this persists."
            ) from e
    
    @staticmethod
    def execute_with_test_cases(
        code: str,
        test_cases: List[Dict[str, str]],
        time_limit: int = 30,
        memory_limit: int = 256
    ) -> Dict[str, Any]:
        """
        Execute code against a set of test cases for exercise evaluation.
        
        Args:
            code: Student's code submission
            test_cases: List of test cases with expected outputs
            time_limit: Maximum execution time
            memory_limit: Maximum memory usage
            
        Returns:
            Dict with test results and score
        """
        # Execute code with test cases
        result = CodeExecutionService.execute_code(
            code=code,
            test_cases=test_cases,
            time_limit=time_limit,
            memory_limit=memory_limit,
            use_cache=False  # Don't cache student submissions
        )
        
        # Calculate score based on test results
        test_results = result.get('test_results', [])
        passed_tests = sum(1 for test in test_results if test.get('passed', False))
        total_tests = len(test_results)
        score = int((passed_tests / total_tests) * 100) if total_tests > 0 else 0
        
        # Add score to result
        result['score'] = score
        result['passed_tests'] = passed_tests
        result['total_tests'] = total_tests
        result['is_correct'] = score >= 80  # 80% passing threshold
        
        return result
    
    @staticmethod
    def get_docker_status() -> Dict[str, Any]:
        """
        Get Docker system status and information.
        
        Returns:
            Dict with Docker status information
        """
        try:
            docker_executor = get_code_executor()
            system_info = docker_executor.executor.get_system_info()
            
            return {
                'docker_available': True,
                'system_info': system_info,
                'executor_type': 'docker',
                'languages_supported': ['python', 'javascript', 'java', 'cpp', 'html']
            }
            
        except Exception as e:
            logger.warning(f"Could not get Docker status: {e}")
            return {
                'docker_available': False,
                'error': str(e),
                'executor_type': 'fallback',
                'languages_supported': ['python']
            }