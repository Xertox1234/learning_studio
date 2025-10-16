"""
Secure code execution service for Python Learning Studio.
Handles safe execution of student code submissions in isolated Docker containers.
"""

import os
import json
import time
import uuid
import tempfile
import subprocess
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# Import the new Docker executor
try:
    from .docker_executor import get_code_executor
    # Test if Docker is actually available
    try:
        get_code_executor()
        DOCKER_EXECUTOR_AVAILABLE = True
    except (ImportError, Exception) as e:
        # Handle Docker not being available (not installed or not running)
        logger.info(f"Docker executor not available: {e}")
        DOCKER_EXECUTOR_AVAILABLE = False
except ImportError:
    DOCKER_EXECUTOR_AVAILABLE = False


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    output: str
    error: str
    execution_time: float
    memory_used: float
    exit_code: int
    timeout: bool = False
    memory_exceeded: bool = False


@dataclass
class TestResult:
    """Result of test case execution."""
    test_name: str
    passed: bool
    expected: str
    actual: str
    execution_time: float
    error: str = ""


class CodeExecutor:
    """Secure code execution engine using Docker containers."""
    
    def __init__(self):
        self.docker_available = self._check_docker_availability()
        self.docker_executor = get_code_executor() if DOCKER_EXECUTOR_AVAILABLE else None
        self.base_images = {
            'python': 'python:3.11-slim',
            'javascript': 'node:18-alpine',
            'java': 'openjdk:11-jre-slim',
            'cpp': 'gcc:latest',
        }
        
    def _check_docker_availability(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ['docker', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("Docker not available. Code execution will be limited.")
            return False
    
    def execute_python_code(
        self, 
        code: str, 
        test_inputs: List[str] = None,
        timeout: int = 10,
        memory_limit: int = 128
    ) -> ExecutionResult:
        """Execute Python code safely."""
        # Try new Docker executor first
        if self.docker_executor:
            try:
                # Convert test_inputs to test_cases format
                test_cases = []
                if test_inputs:
                    for i, test_input in enumerate(test_inputs):
                        test_cases.append({
                            'name': f'Test {i + 1}',
                            'test_code': f'print({test_input})',
                            'expected_output': str(test_input)
                        })
                
                result = self.docker_executor.execute_code(
                    code=code,
                    test_cases=test_cases,
                    time_limit=timeout,
                    memory_limit=f"{memory_limit}m"
                )
                
                # Convert to ExecutionResult format
                return ExecutionResult(
                    success=result.get('success', False),
                    output=result.get('stdout', ''),
                    error=result.get('stderr', '') or result.get('error', ''),
                    execution_time=result.get('execution_time', 0.0),
                    memory_used=result.get('memory_used', 0) / (1024 * 1024),  # Convert to MB
                    exit_code=0 if result.get('success') else 1,
                    timeout=result.get('error_type') == 'timeout'
                )
            except Exception as e:
                logger.warning(f"Docker executor failed, falling back to local execution: {e}")
        
        # Fallback to existing implementation
        if not self.docker_available:
            return self._execute_python_locally(code, test_inputs, timeout)
        
        return self._execute_in_docker(
            code=code,
            language='python',
            test_inputs=test_inputs,
            timeout=timeout,
            memory_limit=memory_limit
        )
    
    def _execute_python_locally(
        self, 
        code: str, 
        test_inputs: List[str] = None,
        timeout: int = 10
    ) -> ExecutionResult:
        """Execute Python code locally (fallback when Docker unavailable)."""
        start_time = time.time()
        
        try:
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Prepare input if provided
            input_str = '\n'.join(test_inputs) if test_inputs else ""
            
            # Execute code
            result = subprocess.run(
                ['python', temp_file],
                input=input_str,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                execution_time=execution_time,
                memory_used=0.0,  # Cannot measure without Docker
                exit_code=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error="Code execution timed out",
                execution_time=timeout,
                memory_used=0.0,
                exit_code=-1,
                timeout=True
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution error: {str(e)}",
                execution_time=time.time() - start_time,
                memory_used=0.0,
                exit_code=-1
            )
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def _execute_in_docker(
        self,
        code: str,
        language: str,
        test_inputs: List[str] = None,
        timeout: int = 10,
        memory_limit: int = 128
    ) -> ExecutionResult:
        """Execute code in Docker container."""
        container_id = None
        start_time = time.time()
        
        try:
            # Create temporary directory for code
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write code to file
                if language == 'python':
                    code_file = os.path.join(temp_dir, 'solution.py')
                    run_command = ['python', '/app/solution.py']
                elif language == 'javascript':
                    code_file = os.path.join(temp_dir, 'solution.js')
                    run_command = ['node', '/app/solution.js']
                else:
                    raise ValueError(f"Unsupported language: {language}")
                
                with open(code_file, 'w') as f:
                    f.write(code)
                
                # Prepare input file if needed
                if test_inputs:
                    input_file = os.path.join(temp_dir, 'input.txt')
                    with open(input_file, 'w') as f:
                        f.write('\n'.join(test_inputs))
                
                # Docker run command
                docker_cmd = [
                    'docker', 'run', '--rm',
                    f'--memory={memory_limit}m',
                    f'--memory-swap={memory_limit}m',
                    '--cpus=0.5',
                    '--network=none',  # No network access
                    '--user=1000:1000',  # Non-root user
                    '-v', f'{temp_dir}:/app:ro',  # Read-only mount
                    '--workdir', '/app',
                    self.base_images[language]
                ] + run_command
                
                # Execute with timeout
                if test_inputs:
                    with open(input_file, 'r') as input_f:
                        result = subprocess.run(
                            docker_cmd,
                            stdin=input_f,
                            capture_output=True,
                            text=True,
                            timeout=timeout + 5  # Add buffer for Docker overhead
                        )
                else:
                    result = subprocess.run(
                        docker_cmd,
                        capture_output=True,
                        text=True,
                        timeout=timeout + 5
                    )
                
                execution_time = time.time() - start_time
                
                # Parse memory usage from stderr if available
                memory_used = 0.0
                if "memory" in result.stderr.lower():
                    # Try to extract memory usage information
                    pass
                
                return ExecutionResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    error=result.stderr,
                    execution_time=execution_time,
                    memory_used=memory_used,
                    exit_code=result.returncode
                )
                
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error="Code execution timed out",
                execution_time=timeout,
                memory_used=0.0,
                exit_code=-1,
                timeout=True
            )
        except Exception as e:
            logger.error(f"Docker execution error: {str(e)}")
            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution error: {str(e)}",
                execution_time=time.time() - start_time,
                memory_used=0.0,
                exit_code=-1
            )
    
    def run_test_cases(
        self, 
        code: str, 
        test_cases: List[Dict], 
        language: str = 'python'
    ) -> List[TestResult]:
        """Run multiple test cases against code."""
        results = []
        
        for test_case in test_cases:
            test_name = test_case.get('name', f'Test {len(results) + 1}')
            test_input = test_case.get('input', [])
            expected_output = test_case.get('expected', '').strip()
            
            # Execute code with test input
            execution_result = self.execute_python_code(
                code=code,
                test_inputs=test_input if isinstance(test_input, list) else [test_input],
                timeout=test_case.get('timeout', 10)
            )
            
            # Compare output
            actual_output = execution_result.output.strip()
            passed = (
                execution_result.success and 
                actual_output == expected_output
            )
            
            results.append(TestResult(
                test_name=test_name,
                passed=passed,
                expected=expected_output,
                actual=actual_output,
                execution_time=execution_result.execution_time,
                error=execution_result.error
            ))
        
        return results
    
    def validate_code_safety(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """Basic code safety validation."""
        unsafe_patterns = {
            'python': [
                'import os', 'import sys', 'import subprocess',
                'import shutil', '__import__', 'eval(', 'exec(',
                'open(', 'file(', 'input(', 'raw_input(',
                'compile(', 'globals()', 'locals()', 'vars(',
                'import socket', 'import urllib', 'import requests'
            ],
            'javascript': [
                'require(', 'import ', 'fetch(', 'XMLHttpRequest',
                'process.', 'global.', 'window.', 'document.',
                'eval(', 'Function(', 'setTimeout', 'setInterval'
            ]
        }
        
        issues = []
        patterns = unsafe_patterns.get(language, [])
        
        for pattern in patterns:
            if pattern in code:
                issues.append(f"Potentially unsafe pattern detected: {pattern}")
        
        return {
            'safe': len(issues) == 0,
            'issues': issues,
            'warnings': [] if len(issues) == 0 else ["Code contains potentially unsafe operations"]
        }


class ExerciseEvaluator:
    """Evaluates student submissions against exercise requirements."""
    
    def __init__(self):
        self.executor = CodeExecutor()
    
    def evaluate_submission(
        self, 
        submission_code: str, 
        exercise_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a student submission."""
        from .exercise_models import TestCase
        
        # Basic validation
        safety_check = self.executor.validate_code_safety(
            submission_code, 
            exercise_data.get('language', 'python')
        )
        
        if not safety_check['safe']:
            return {
                'status': 'error',
                'message': 'Code contains unsafe operations',
                'issues': safety_check['issues'],
                'score': 0,
                'test_results': []
            }
        
        # Get test cases
        test_cases = exercise_data.get('test_cases', [])
        if not test_cases:
            # Fallback to basic execution
            result = self.executor.execute_python_code(submission_code)
            return {
                'status': 'passed' if result.success else 'failed',
                'message': result.error if result.error else 'Code executed successfully',
                'score': 100 if result.success else 0,
                'execution_time': result.execution_time,
                'output': result.output,
                'test_results': []
            }
        
        # Run test cases
        test_results = self.executor.run_test_cases(
            code=submission_code,
            test_cases=test_cases,
            language=exercise_data.get('language', 'python')
        )
        
        # Calculate score
        passed_tests = sum(1 for result in test_results if result.passed)
        total_tests = len(test_results)
        score = int((passed_tests / total_tests) * 100) if total_tests > 0 else 0
        
        # Determine status
        if score == 100:
            status = 'passed'
            message = 'All tests passed!'
        elif score >= 80:
            status = 'passed'
            message = f'Most tests passed ({passed_tests}/{total_tests})'
        elif score > 0:
            status = 'failed'
            message = f'Some tests failed ({passed_tests}/{total_tests})'
        else:
            status = 'failed'
            message = 'All tests failed'
        
        return {
            'status': status,
            'message': message,
            'score': score,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'test_results': [
                {
                    'name': tr.test_name,
                    'passed': tr.passed,
                    'expected': tr.expected,
                    'actual': tr.actual,
                    'execution_time': tr.execution_time,
                    'error': tr.error
                }
                for tr in test_results
            ],
            'total_execution_time': sum(tr.execution_time for tr in test_results)
        }
    
    def generate_feedback(self, evaluation_result: Dict[str, Any]) -> str:
        """Generate helpful feedback based on evaluation results."""
        if evaluation_result['status'] == 'passed':
            if evaluation_result['score'] == 100:
                return "Excellent work! Your solution passed all test cases."
            else:
                return f"Good job! Your solution works for most cases ({evaluation_result['passed_tests']}/{evaluation_result['total_tests']} tests passed)."
        
        feedback = []
        feedback.append(f"Your solution passed {evaluation_result['passed_tests']} out of {evaluation_result['total_tests']} test cases.")
        
        # Analyze failed tests
        failed_tests = [
            test for test in evaluation_result.get('test_results', [])
            if not test['passed']
        ]
        
        if failed_tests:
            feedback.append("\nFailed test cases:")
            for test in failed_tests[:3]:  # Show first 3 failed tests
                if test['error']:
                    feedback.append(f"- {test['name']}: {test['error']}")
                else:
                    feedback.append(f"- {test['name']}: Expected '{test['expected']}', got '{test['actual']}'")
        
        feedback.append("\nTips for improvement:")
        feedback.append("- Check your logic for edge cases")
        feedback.append("- Ensure your output format matches exactly")
        feedback.append("- Test your solution with the provided examples")
        
        return "\n".join(feedback)


# Global instances
code_executor = CodeExecutor()
exercise_evaluator = ExerciseEvaluator()