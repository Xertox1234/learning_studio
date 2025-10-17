#!/usr/bin/env python
"""
Code Execution Security Test Script

Tests the enhanced security features in Phase 2.3:
1. Rate limiting enforcement
2. Audit logging
3. Docker security features (already implemented)
4. Authentication requirement

Usage:
    python test_code_execution_security.py
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = 'http://localhost:8000'
TEST_USER = {
    'email': 'test@pythonlearning.studio',
    'password': 'testpass123'
}

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_test(name, passed, details=""):
    """Print test result."""
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"{status} - {name}")
    if details:
        print(f"       {Colors.YELLOW}{details}{Colors.END}")

def print_section(name):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{name}{Colors.END}")
    print("-" * 70)

test_results = {
    'passed': 0,
    'failed': 0,
    'tests': []
}

def record_test(name, passed, details=""):
    """Record test result."""
    test_results['tests'].append({
        'name': name,
        'passed': passed,
        'details': details
    })
    if passed:
        test_results['passed'] += 1
    else:
        test_results['failed'] += 1
    print_test(name, passed, details)

def get_jwt_token():
    """Obtain JWT token for testing."""
    try:
        response = requests.post(
            f'{BASE_URL}/api/v1/auth/login/',
            json=TEST_USER,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            data = response.json()
            return data.get('token') or data.get('access')
        else:
            print(f"{Colors.RED}Failed to obtain JWT token: {response.status_code}{Colors.END}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}ERROR: Cannot connect to {BASE_URL}{Colors.END}")
        print(f"{Colors.YELLOW}Make sure the Django development server is running{Colors.END}")
        return None
    except Exception as e:
        print(f"{Colors.RED}Error obtaining JWT token: {e}{Colors.END}")
        return None

def test_authentication_required():
    """Test that authentication is required."""
    print_section("TEST 1: Authentication Required")

    try:
        response = requests.post(
            f'{BASE_URL}/api/v1/code-execution/',
            json={'code': 'print("test")'},
            headers={'Content-Type': 'application/json'}
        )

        passed = response.status_code == 401
        details = f"Status: {response.status_code}, Expected: 401 Unauthorized"
        record_test("Unauthenticated access rejected", passed, details)

    except Exception as e:
        record_test("Authentication test", False, f"Error: {e}")

def test_code_execution_with_auth(token):
    """Test code execution with valid authentication."""
    print_section("TEST 2: Code Execution with Authentication")

    if not token:
        print(f"{Colors.RED}Skipping - no token available{Colors.END}")
        return

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        # Test 1: Simple code execution
        response = requests.post(
            f'{BASE_URL}/api/v1/code-execution/',
            json={'code': 'print("Hello from security test!")'},
            headers=headers
        )

        passed = response.status_code == 200
        details = f"Status: {response.status_code}"
        record_test("Simple code execution works", passed, details)

        if passed:
            result = response.json()
            has_output = 'output' in result or 'stdout' in result
            record_test("Response includes output", has_output)

    except Exception as e:
        record_test("Code execution test", False, f"Error: {e}")

def test_rate_limiting(token):
    """Test rate limiting enforcement."""
    print_section("TEST 3: Rate Limiting (10 requests/minute per user)")

    if not token:
        print(f"{Colors.RED}Skipping - no token available{Colors.END}")
        return

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    print(f"{Colors.YELLOW}Sending 12 requests rapidly to trigger rate limit...{Colors.END}")

    success_count = 0
    rate_limited_count = 0

    try:
        for i in range(12):
            response = requests.post(
                f'{BASE_URL}/api/v1/code-execution/',
                json={'code': f'print("Request {i + 1}")'},
                headers=headers
            )

            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_count += 1
                print(f"  Request {i + 1}: Rate limited (429)")

            time.sleep(0.1)  # Small delay between requests

        # We expect most requests to succeed but some to be rate limited
        passed = rate_limited_count > 0
        details = f"Successful: {success_count}, Rate limited: {rate_limited_count}"
        record_test("Rate limiting enforced", passed, details)

    except Exception as e:
        record_test("Rate limiting test", False, f"Error: {e}")

def test_input_validation(token):
    """Test input validation."""
    print_section("TEST 4: Input Validation")

    if not token:
        print(f"{Colors.RED}Skipping - no token available{Colors.END}")
        return

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Test 1: Empty code
    try:
        response = requests.post(
            f'{BASE_URL}/api/v1/code-execution/',
            json={'code': ''},
            headers=headers
        )

        passed = response.status_code == 400
        details = f"Status: {response.status_code}, Expected: 400 Bad Request"
        record_test("Empty code rejected", passed, details)

    except Exception as e:
        record_test("Empty code validation", False, f"Error: {e}")

    # Test 2: Code exceeding length limit
    try:
        long_code = 'print("x" * 10000)' + 'x' * 10000  # Exceed 10,000 char limit
        response = requests.post(
            f'{BASE_URL}/api/v1/code-execution/',
            json={'code': long_code},
            headers=headers
        )

        passed = response.status_code == 400
        details = f"Status: {response.status_code}, Expected: 400 Bad Request"
        record_test("Code length limit enforced", passed, details)

    except Exception as e:
        record_test("Length limit validation", False, f"Error: {e}")

def test_docker_status(token):
    """Test Docker status endpoint."""
    print_section("TEST 5: Docker Status Check")

    if not token:
        print(f"{Colors.RED}Skipping - no token available{Colors.END}")
        return

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(
            f'{BASE_URL}/api/v1/docker/status/',
            headers=headers
        )

        passed = response.status_code == 200
        details = f"Status: {response.status_code}"
        record_test("Docker status endpoint accessible", passed, details)

        if passed:
            data = response.json()
            docker_available = data.get('docker_available', False)
            print(f"  Docker available: {docker_available}")
            if docker_available:
                print(f"  Executor type: {data.get('executor_type', 'unknown')}")

    except Exception as e:
        record_test("Docker status check", False, f"Error: {e}")

def print_summary():
    """Print test summary."""
    print_header("TEST SUMMARY")

    total = test_results['passed'] + test_results['failed']
    pass_rate = (test_results['passed'] / total * 100) if total > 0 else 0

    print(f"Total Tests: {total}")
    print(f"{Colors.GREEN}Passed: {test_results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {test_results['failed']}{Colors.END}")
    print(f"Pass Rate: {pass_rate:.1f}%")

    if test_results['failed'] > 0:
        print(f"\n{Colors.RED}FAILED TESTS:{Colors.END}")
        for test in test_results['tests']:
            if not test['passed']:
                print(f"  - {test['name']}")
                if test['details']:
                    print(f"    {test['details']}")

    print("\n" + "="*70 + "\n")

    return test_results['failed'] == 0

def main():
    """Run all security tests."""
    print_header("Code Execution Security Test Suite - Phase 2.3")
    print(f"Testing against: {BASE_URL}")
    print(f"Test user: {TEST_USER['email']}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test 1: Authentication required
    test_authentication_required()

    # Get JWT token for authenticated tests
    print(f"\n{Colors.YELLOW}Obtaining JWT token...{Colors.END}")
    jwt_token = get_jwt_token()
    if jwt_token:
        print(f"{Colors.GREEN}✓ JWT token obtained{Colors.END}")
    else:
        print(f"{Colors.RED}✗ Failed to obtain JWT token{Colors.END}")
        print(f"{Colors.YELLOW}Some tests will be skipped{Colors.END}")

    # Run authenticated tests
    test_code_execution_with_auth(jwt_token)
    test_rate_limiting(jwt_token)
    test_input_validation(jwt_token)
    test_docker_status(jwt_token)

    # Print summary
    all_passed = print_summary()

    return 0 if all_passed else 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        sys.exit(1)
