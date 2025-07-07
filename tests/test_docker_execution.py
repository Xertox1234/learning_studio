"""
Test suite for Docker-based code execution system.
"""

import json
import time
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from apps.learning.docker_executor import DockerCodeExecutor, CachedCodeExecutor, get_code_executor
from apps.learning.models import Exercise, TestCase as ExerciseTestCase, ProgrammingLanguage
from apps.learning.code_execution import CodeExecutor

User = get_user_model()


class DockerCodeExecutorTests(TestCase):
    """Test the DockerCodeExecutor class."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock Docker to avoid requiring actual Docker in tests
        self.mock_docker_patcher = patch('apps.learning.docker_executor.docker')
        self.mock_docker = self.mock_docker_patcher.start()
        
        # Create mock Docker client
        self.mock_client = MagicMock()
        self.mock_docker.from_env.return_value = self.mock_client
        
        self.executor = DockerCodeExecutor()
    
    def tearDown(self):
        """Clean up test environment."""
        self.mock_docker_patcher.stop()
    
    def test_executor_initialization(self):
        """Test executor initializes correctly."""
        self.assertIsInstance(self.executor, DockerCodeExecutor)
        self.assertEqual(self.executor.image_name, "python-learning-studio-executor")
        self.assertEqual(self.executor.max_execution_time, 30)
        self.assertEqual(self.executor.max_memory, "256m")
    
    def test_build_executor_image_success(self):
        """Test successful Docker image building."""
        # Mock image doesn't exist
        self.mock_client.images.get.side_effect = Exception("Image not found")
        
        # Mock successful build
        mock_image = MagicMock()
        self.mock_client.images.build.return_value = (mock_image, [])
        
        result = self.executor.build_executor_image()
        
        self.assertTrue(result)
        self.mock_client.images.build.assert_called_once()
    
    def test_build_executor_image_already_exists(self):
        """Test when Docker image already exists."""
        # Mock image exists
        mock_image = MagicMock()
        self.mock_client.images.get.return_value = mock_image
        
        result = self.executor.build_executor_image()
        
        self.assertTrue(result)
        self.mock_client.images.build.assert_not_called()
    
    def test_execute_code_simple(self):
        """Test simple code execution."""
        code = "print('Hello, World!')"
        
        # Mock successful container execution
        mock_container = MagicMock()
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = json.dumps({
            'success': True,
            'stdout': 'Hello, World!\n',
            'stderr': '',
            'execution_time': 0.1
        }).encode('utf-8')
        
        self.mock_client.containers.run.return_value = mock_container
        self.mock_client.images.get.return_value = MagicMock()  # Image exists
        
        result = self.executor.execute_code(code)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['stdout'], 'Hello, World!\n')
        self.assertEqual(result['stderr'], '')
    
    def test_execute_code_with_test_cases(self):
        """Test code execution with test cases."""
        code = """
def add(a, b):
    return a + b

print(add(2, 3))
"""
        test_cases = [
            {
                'name': 'Test 1',
                'test_code': 'print(add(2, 3))',
                'expected_output': '5'
            },
            {
                'name': 'Test 2', 
                'test_code': 'print(add(10, 20))',
                'expected_output': '30'
            }
        ]
        
        # Mock successful execution with test results
        mock_container = MagicMock()
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = json.dumps({
            'success': True,
            'stdout': '5\n',
            'stderr': '',
            'execution_time': 0.2,
            'test_results': [
                {'test_number': 1, 'passed': True, 'expected_output': '5', 'actual_output': '5'},
                {'test_number': 2, 'passed': True, 'expected_output': '30', 'actual_output': '30'}
            ]
        }).encode('utf-8')
        
        self.mock_client.containers.run.return_value = mock_container
        self.mock_client.images.get.return_value = MagicMock()
        
        result = self.executor.execute_code(code, test_cases)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['test_results']), 2)
        self.assertTrue(all(test['passed'] for test in result['test_results']))
    
    def test_execute_code_timeout(self):
        """Test code execution timeout handling."""
        code = "while True: pass"  # Infinite loop
        
        # Mock container timeout
        mock_container = MagicMock()
        mock_container.wait.side_effect = Exception("timeout")
        
        self.mock_client.containers.run.return_value = mock_container
        self.mock_client.images.get.return_value = MagicMock()
        
        result = self.executor.execute_code(code, time_limit=1)
        
        self.assertFalse(result['success'])
        self.assertIn('timeout', result.get('error_type', '').lower())
    
    def test_execute_code_security_error(self):
        """Test security error handling."""
        code = "import os; os.system('rm -rf /')"
        
        # Mock security error response
        mock_container = MagicMock()
        mock_container.wait.return_value = {'StatusCode': 1}
        mock_container.logs.return_value = json.dumps({
            'success': False,
            'error': 'Security Error: Restricted pattern detected: import os',
            'error_type': 'security'
        }).encode('utf-8')
        
        self.mock_client.containers.run.return_value = mock_container
        self.mock_client.images.get.return_value = MagicMock()
        
        result = self.executor.execute_code(code)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'security')
    
    def test_parse_memory_limit(self):
        """Test memory limit parsing."""
        self.assertEqual(self.executor._parse_memory_limit("128m"), 128 * 1024 * 1024)
        self.assertEqual(self.executor._parse_memory_limit("1g"), 1 * 1024 * 1024 * 1024)
        self.assertEqual(self.executor._parse_memory_limit("1073741824"), 1073741824)


class CachedCodeExecutorTests(TestCase):
    """Test the CachedCodeExecutor class."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock Docker
        self.mock_docker_patcher = patch('apps.learning.docker_executor.docker')
        self.mock_docker = self.mock_docker_patcher.start()
        self.mock_client = MagicMock()
        self.mock_docker.from_env.return_value = self.mock_client
        
        # Mock cache
        self.mock_cache_patcher = patch('apps.learning.docker_executor.cache')
        self.mock_cache = self.mock_cache_patcher.start()
        
        self.executor = CachedCodeExecutor()
    
    def tearDown(self):
        """Clean up test environment."""
        self.mock_docker_patcher.stop()
        self.mock_cache_patcher.stop()
    
    def test_cache_hit(self):
        """Test cache hit scenario."""
        code = "print('Hello, World!')"
        cached_result = {
            'success': True,
            'stdout': 'Hello, World!\n',
            'stderr': '',
            'execution_time': 0.1
        }
        
        # Mock cache hit
        self.mock_cache.get.return_value = cached_result
        
        result = self.executor.execute_code(code, use_cache=True)
        
        self.assertTrue(result['from_cache'])
        self.assertEqual(result['stdout'], 'Hello, World!\n')
        self.mock_cache.get.assert_called_once()
    
    def test_cache_miss(self):
        """Test cache miss scenario."""
        code = "print('Hello, World!')"
        
        # Mock cache miss
        self.mock_cache.get.return_value = None
        
        # Mock successful execution
        mock_container = MagicMock()
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = json.dumps({
            'success': True,
            'stdout': 'Hello, World!\n',
            'stderr': '',
            'execution_time': 0.1
        }).encode('utf-8')
        
        self.mock_client.containers.run.return_value = mock_container
        self.mock_client.images.get.return_value = MagicMock()
        
        result = self.executor.execute_code(code, use_cache=True)
        
        self.assertFalse(result['from_cache'])
        self.mock_cache.set.assert_called_once()
    
    def test_generate_cache_key(self):
        """Test cache key generation."""
        code = "print('test')"
        test_cases = [{'name': 'test', 'expected': 'test'}]
        
        key1 = self.executor._generate_cache_key(code, test_cases)
        key2 = self.executor._generate_cache_key(code, test_cases)
        key3 = self.executor._generate_cache_key(code + " ", test_cases)
        
        self.assertEqual(key1, key2)  # Same code should generate same key
        self.assertNotEqual(key1, key3)  # Different code should generate different key
        self.assertTrue(key1.startswith('code_execution:'))


class APIEndpointTests(APITestCase):
    """Test the API endpoints for code execution."""
    
    def setUp(self):
        """Set up test environment."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Mock Docker
        self.mock_docker_patcher = patch('apps.learning.docker_executor.docker')
        self.mock_docker = self.mock_docker_patcher.start()
        self.mock_client = MagicMock()
        self.mock_docker.from_env.return_value = self.mock_client
    
    def tearDown(self):
        """Clean up test environment."""
        self.mock_docker_patcher.stop()
    
    def test_execute_code_endpoint(self):
        """Test the code execution API endpoint."""
        url = reverse('api:execute-code')
        data = {
            'code': 'print("Hello, API!")',
            'time_limit': 10,
            'memory_limit': 128
        }
        
        # Mock successful execution
        mock_container = MagicMock()
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = json.dumps({
            'success': True,
            'stdout': 'Hello, API!\n',
            'stderr': '',
            'execution_time': 0.1
        }).encode('utf-8')
        
        self.mock_client.containers.run.return_value = mock_container
        self.mock_client.images.get.return_value = MagicMock()
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['stdout'], 'Hello, API!\n')
    
    def test_execute_code_no_code(self):
        """Test API endpoint with no code provided."""
        url = reverse('api:execute-code')
        data = {'code': ''}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('No code provided', response.data['error'])
    
    def test_execute_code_unauthenticated(self):
        """Test API endpoint without authentication."""
        self.client.force_authenticate(user=None)
        
        url = reverse('api:execute-code')
        data = {'code': 'print("test")'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_docker_status_endpoint(self):
        """Test the Docker status API endpoint."""
        url = reverse('api:docker-status')
        
        # Mock system info
        self.mock_client.info.return_value = {
            'ServerVersion': '20.10.0',
            'ContainersRunning': 2,
            'MemTotal': 8589934592,
            'NCPU': 4
        }
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['docker_available'])
        self.assertEqual(response.data['executor_type'], 'docker')


class ExerciseSubmissionTests(APITestCase):
    """Test exercise submission with Docker execution."""
    
    def setUp(self):
        """Set up test environment."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com', 
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.python_lang = ProgrammingLanguage.objects.create(
            name='Python',
            slug='python',
            version='3.11'
        )
        
        self.exercise = Exercise.objects.create(
            title='Simple Addition',
            description='Write a function that adds two numbers',
            difficulty_level='beginner',
            programming_language=self.python_lang,
            is_published=True
        )
        
        self.test_case = ExerciseTestCase.objects.create(
            exercise=self.exercise,
            name='Test Case 1',
            input_data='2, 3',
            expected_output='5',
            is_sample=True
        )
        
        # Mock Docker
        self.mock_docker_patcher = patch('apps.learning.docker_executor.docker')
        self.mock_docker = self.mock_docker_patcher.start()
        self.mock_client = MagicMock()
        self.mock_docker.from_env.return_value = self.mock_client
    
    def tearDown(self):
        """Clean up test environment."""
        self.mock_docker_patcher.stop()
    
    def test_submit_exercise_success(self):
        """Test successful exercise submission."""
        url = reverse('api:submit-exercise-code', kwargs={'exercise_id': self.exercise.id})
        data = {
            'code': '''
def add(a, b):
    return a + b

print(add(2, 3))
'''
        }
        
        # Mock successful execution
        mock_container = MagicMock()
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = json.dumps({
            'success': True,
            'stdout': '5\n',
            'stderr': '',
            'execution_time': 0.1,
            'test_results': [
                {
                    'test_number': 1,
                    'passed': True,
                    'expected_output': '5',
                    'actual_output': '5',
                    'test_name': 'Test Case 1'
                }
            ]
        }).encode('utf-8')
        
        self.mock_client.containers.run.return_value = mock_container
        self.mock_client.images.get.return_value = MagicMock()
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['score'], 100)
        self.assertEqual(response.data['passed_tests'], 1)
        self.assertEqual(response.data['total_tests'], 1)
    
    def test_submit_exercise_failure(self):
        """Test exercise submission with failing test."""
        url = reverse('api:submit-exercise-code', kwargs={'exercise_id': self.exercise.id})
        data = {
            'code': '''
def add(a, b):
    return a - b  # Wrong implementation

print(add(2, 3))
'''
        }
        
        # Mock execution with failing test
        mock_container = MagicMock()
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = json.dumps({
            'success': True,
            'stdout': '-1\n',
            'stderr': '',
            'execution_time': 0.1,
            'test_results': [
                {
                    'test_number': 1,
                    'passed': False,
                    'expected_output': '5',
                    'actual_output': '-1',
                    'test_name': 'Test Case 1'
                }
            ]
        }).encode('utf-8')
        
        self.mock_client.containers.run.return_value = mock_container
        self.mock_client.images.get.return_value = MagicMock()
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])  # API call succeeded
        self.assertEqual(response.data['score'], 0)  # But exercise failed
        self.assertEqual(response.data['passed_tests'], 0)


class SecurityTests(TestCase):
    """Test security features of the code execution system."""
    
    def setUp(self):
        """Set up test environment."""
        # Use the actual code executor for security tests
        self.executor = CodeExecutor()
    
    def test_validate_code_safety_dangerous_imports(self):
        """Test detection of dangerous imports."""
        dangerous_codes = [
            "import os\nos.system('rm -rf /')",
            "import subprocess\nsubprocess.call(['rm', '-rf', '/'])",
            "import socket\nsocket.create_connection(('evil.com', 80))",
            "from os import system\nsystem('echo hacked')"
        ]
        
        for code in dangerous_codes:
            with self.subTest(code=code):
                result = self.executor.validate_code_safety(code)
                self.assertFalse(result['safe'])
                self.assertGreater(len(result['issues']), 0)
    
    def test_validate_code_safety_safe_code(self):
        """Test validation of safe code."""
        safe_codes = [
            "print('Hello, World!')",
            "def add(a, b):\n    return a + b\nprint(add(2, 3))",
            "import math\nprint(math.sqrt(16))",
            "for i in range(10):\n    print(i)"
        ]
        
        for code in safe_codes:
            with self.subTest(code=code):
                result = self.executor.validate_code_safety(code)
                self.assertTrue(result['safe'])
                self.assertEqual(len(result['issues']), 0)


class PerformanceTests(TestCase):
    """Test performance aspects of the code execution system."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock Docker for performance tests
        self.mock_docker_patcher = patch('apps.learning.docker_executor.docker')
        self.mock_docker = self.mock_docker_patcher.start()
        self.mock_client = MagicMock()
        self.mock_docker.from_env.return_value = self.mock_client
        
        self.executor = get_code_executor()
    
    def tearDown(self):
        """Clean up test environment."""
        self.mock_docker_patcher.stop()
    
    def test_execution_time_limits(self):
        """Test that execution time limits are enforced."""
        code = "import time\ntime.sleep(10)"  # Sleep for 10 seconds
        
        # Mock timeout response
        mock_container = MagicMock()
        mock_container.wait.side_effect = Exception("timeout")
        
        self.mock_client.containers.run.return_value = mock_container
        self.mock_client.images.get.return_value = MagicMock()
        
        start_time = time.time()
        result = self.executor.execute_code(code, time_limit=2)
        execution_time = time.time() - start_time
        
        # Should timeout quickly, not wait for the full sleep
        self.assertLess(execution_time, 5)
        self.assertFalse(result['success'])
    
    def test_memory_limits(self):
        """Test that memory limits are enforced."""
        code = """
# Try to allocate a lot of memory
data = []
for i in range(1000000):
    data.append([0] * 1000)
"""
        
        # Mock memory limit exceeded response
        mock_container = MagicMock()
        mock_container.wait.return_value = {'StatusCode': 137}  # SIGKILL (out of memory)
        mock_container.logs.return_value = json.dumps({
            'success': False,
            'error': 'Memory limit exceeded',
            'error_type': 'memory'
        }).encode('utf-8')
        
        self.mock_client.containers.run.return_value = mock_container
        self.mock_client.images.get.return_value = MagicMock()
        
        result = self.executor.execute_code(code, memory_limit="64m")
        
        self.assertFalse(result['success'])


if __name__ == '__main__':
    unittest.main()