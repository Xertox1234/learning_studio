#!/usr/bin/env python3
"""
Secure Python Code Execution Script
Runs student code in an isolated environment with safety restrictions.
"""

import sys
import os
import json
import traceback
import signal
import resource
import subprocess
import tempfile
import time
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr


class CodeExecutionError(Exception):
    """Custom exception for code execution errors."""
    pass


class SecurityError(Exception):
    """Custom exception for security violations."""
    pass


class CodeExecutor:
    """Secure code executor with safety restrictions."""
    
    def __init__(self, time_limit=30, memory_limit=128*1024*1024):  # 128MB
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.restricted_imports = {
            'os', 'sys', 'subprocess', 'socket', 'urllib', 'requests',
            'importlib', '__import__', 'exec', 'eval', 'compile',
            'open', 'file', 'input', 'raw_input', 'execfile',
            'reload', 'vars', 'locals', 'globals', 'dir',
            'multiprocessing', 'threading', 'thread',
            'ctypes', 'platform', 'tempfile', 'shutil',
            'pickle', 'marshal', 'shelve', 'dbm'
        }
        
    def setup_security(self):
        """Set up security restrictions."""
        # Set memory limit
        resource.setrlimit(resource.RLIMIT_AS, (self.memory_limit, self.memory_limit))
        
        # Set CPU time limit
        resource.setrlimit(resource.RLIMIT_CPU, (self.time_limit, self.time_limit))
        
        # Limit number of processes
        resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))
        
        # Limit file size
        resource.setrlimit(resource.RLIMIT_FSIZE, (1024*1024, 1024*1024))  # 1MB
        
    def validate_code(self, code):
        """Validate code for security issues."""
        dangerous_patterns = [
            'import os', 'import sys', 'import subprocess', 'import socket',
            'from os', 'from sys', 'from subprocess', 'from socket',
            '__import__', 'exec(', 'eval(', 'compile(',
            'open(', 'file(', 'input(', 'raw_input(',
            'globals(', 'locals(', 'vars(', 'dir(',
            'getattr(', 'setattr(', 'delattr(', 'hasattr(',
            'reload(', 'execfile(', '\\x', 'chr(', 'ord(',
            'while True:', 'for i in range(99999'
        ]
        
        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if pattern in code_lower:
                raise SecurityError(f"Restricted pattern detected: {pattern}")
                
        # Check for infinite loops (basic detection)
        lines = code.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('while') and 'True' in line and ':' in line:
                if 'break' not in code:
                    raise SecurityError("Potential infinite loop detected")
                    
    def create_safe_environment(self):
        """Create a safe execution environment."""
        safe_builtins = {
            'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool,
            'bytearray': bytearray, 'bytes': bytes, 'chr': chr, 'complex': complex,
            'dict': dict, 'divmod': divmod, 'enumerate': enumerate, 'filter': filter,
            'float': float, 'format': format, 'frozenset': frozenset, 'hex': hex,
            'int': int, 'isinstance': isinstance, 'issubclass': issubclass,
            'len': len, 'list': list, 'map': map, 'max': max, 'min': min,
            'oct': oct, 'ord': ord, 'pow': pow, 'print': print, 'range': range,
            'repr': repr, 'reversed': reversed, 'round': round, 'set': set,
            'slice': slice, 'sorted': sorted, 'str': str, 'sum': sum,
            'tuple': tuple, 'type': type, 'zip': zip,
            # Math functions
            '__import__': self.safe_import,
        }
        
        # Allow specific safe modules
        safe_modules = {
            'math': __import__('math'),
            'random': __import__('random'),
            'datetime': __import__('datetime'),
            'collections': __import__('collections'),
            'itertools': __import__('itertools'),
            'functools': __import__('functools'),
            'operator': __import__('operator'),
            'string': __import__('string'),
            're': __import__('re'),
            'json': __import__('json'),
        }
        
        return {
            '__builtins__': safe_builtins,
            '__name__': '__main__',
            '__doc__': None,
            **safe_modules
        }
        
    def safe_import(self, name, *args, **kwargs):
        """Safe import function that only allows specific modules."""
        allowed_modules = {
            'math', 'random', 'datetime', 'collections', 'itertools',
            'functools', 'operator', 'string', 're', 'json'
        }
        
        if name not in allowed_modules:
            raise SecurityError(f"Import of module '{name}' is not allowed")
            
        return __import__(name, *args, **kwargs)
        
    def timeout_handler(self, signum, frame):
        """Handle timeout signal."""
        raise CodeExecutionError("Code execution timed out")
        
    def execute_code(self, code, test_cases=None):
        """Execute code safely and return results."""
        try:
            # Set up security
            self.setup_security()
            
            # Validate code
            self.validate_code(code)
            
            # Set up timeout
            signal.signal(signal.SIGALRM, self.timeout_handler)
            signal.alarm(self.time_limit)
            
            # Capture output
            stdout_capture = StringIO()
            stderr_capture = StringIO()
            
            # Create safe environment
            safe_env = self.create_safe_environment()
            
            # Execute code
            start_time = time.time()
            
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    exec(code, safe_env)
                except Exception as e:
                    stderr_capture.write(f"Error: {str(e)}\n")
                    stderr_capture.write(traceback.format_exc())
            
            execution_time = time.time() - start_time
            
            # Cancel timeout
            signal.alarm(0)
            
            # Get output
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            # Run test cases if provided
            test_results = []
            if test_cases:
                test_results = self.run_test_cases(code, test_cases, safe_env)
            
            return {
                'success': True,
                'stdout': stdout_output,
                'stderr': stderr_output,
                'execution_time': execution_time,
                'test_results': test_results,
                'memory_used': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            }
            
        except SecurityError as e:
            return {
                'success': False,
                'error': f"Security Error: {str(e)}",
                'error_type': 'security'
            }
        except CodeExecutionError as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Execution Error: {str(e)}",
                'error_type': 'execution',
                'traceback': traceback.format_exc()
            }
        finally:
            # Ensure timeout is cancelled
            signal.alarm(0)
            
    def run_test_cases(self, code, test_cases, safe_env):
        """Run test cases against the executed code."""
        test_results = []
        
        for i, test_case in enumerate(test_cases):
            try:
                # Prepare test environment
                test_env = safe_env.copy()
                
                # Execute the user code first
                exec(code, test_env)
                
                # Run the test case
                test_code = test_case.get('test_code', '')
                expected_output = test_case.get('expected_output', '')
                
                # Capture test output
                test_stdout = StringIO()
                with redirect_stdout(test_stdout):
                    exec(test_code, test_env)
                
                actual_output = test_stdout.getvalue().strip()
                expected_output = expected_output.strip()
                
                passed = actual_output == expected_output
                
                test_results.append({
                    'test_number': i + 1,
                    'passed': passed,
                    'expected_output': expected_output,
                    'actual_output': actual_output,
                    'test_name': test_case.get('name', f'Test {i + 1}')
                })
                
            except Exception as e:
                test_results.append({
                    'test_number': i + 1,
                    'passed': False,
                    'error': str(e),
                    'test_name': test_case.get('name', f'Test {i + 1}')
                })
                
        return test_results


def main():
    """Main execution function."""
    try:
        # Read input from environment variables or stdin
        code = os.environ.get('CODE', '')
        test_cases_json = os.environ.get('TEST_CASES', '[]')
        time_limit = int(os.environ.get('TIME_LIMIT', '30'))
        memory_limit = int(os.environ.get('MEMORY_LIMIT', str(128*1024*1024)))
        
        # If no code from environment, read from stdin
        if not code:
            code = sys.stdin.read()
            
        # Parse test cases
        test_cases = json.loads(test_cases_json) if test_cases_json else []
        
        # Create executor and run code
        executor = CodeExecutor(time_limit=time_limit, memory_limit=memory_limit)
        result = executor.execute_code(code, test_cases)
        
        # Output result as JSON
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        error_result = {
            'success': False,
            'error': f"System Error: {str(e)}",
            'error_type': 'system',
            'traceback': traceback.format_exc()
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()