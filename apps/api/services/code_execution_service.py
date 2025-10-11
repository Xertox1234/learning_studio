"""
Unified code execution service for handling all code execution logic.
"""

import logging
from typing import Dict, List, Any, Optional

from apps.learning.code_execution import code_executor
from apps.learning.docker_executor import get_code_executor

logger = logging.getLogger(__name__)


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
        
        # Try Docker executor first
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
            logger.warning(f"Docker executor failed, using fallback: {e}")
            
            # Fallback to basic executor
            try:
                execution_result = code_executor.execute_python_code(
                    code=code,
                    timeout=time_limit,
                    memory_limit=memory_limit
                )
                
                return {
                    'success': execution_result.success,
                    'stdout': execution_result.output,
                    'stderr': execution_result.error,
                    'execution_time': execution_result.execution_time,
                    'memory_used': execution_result.memory_used * 1024 * 1024,  # Convert to bytes
                    'timeout': execution_result.timeout,
                    'from_cache': False,
                    'test_results': []
                }
                
            except Exception as fallback_error:
                logger.error(f"Both executors failed: {fallback_error}")
                return {
                    'success': False,
                    'error': 'Code execution failed',
                    'stdout': '',
                    'stderr': str(fallback_error),
                    'execution_time': 0,
                    'memory_used': 0,
                    'from_cache': False
                }
    
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