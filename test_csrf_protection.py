#!/usr/bin/env python
"""
CSRF Protection Testing Script

Tests the CSRF protection changes made in Phase 2.2:
1. JWT authentication works without CSRF token
2. Session authentication requires CSRF token
3. Deprecated code execution endpoint returns 410 Gone
4. All endpoints properly enforce authentication

Usage:
    python test_csrf_protection.py
"""

import requests
import json
import sys
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

# Test Results Tracker
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
            # API returns 'token' not 'access'
            return data.get('token') or data.get('access')
        else:
            print(f"{Colors.RED}Failed to obtain JWT token: {response.status_code}{Colors.END}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}ERROR: Cannot connect to {BASE_URL}{Colors.END}")
        print(f"{Colors.YELLOW}Make sure the Django development server is running:{Colors.END}")
        print(f"  DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py runserver")
        return None
    except Exception as e:
        print(f"{Colors.RED}Error obtaining JWT token: {e}{Colors.END}")
        return None

def get_session_and_csrf():
    """Get session cookie and CSRF token."""
    try:
        session = requests.Session()

        # Login to get session cookie
        response = session.post(
            f'{BASE_URL}/api/v1/auth/login/',
            json=TEST_USER,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            print(f"{Colors.RED}Failed to login for session: {response.status_code}{Colors.END}")
            return None, None

        # Get CSRF token from cookie
        csrf_token = session.cookies.get('csrftoken')

        return session, csrf_token
    except Exception as e:
        print(f"{Colors.RED}Error obtaining session/CSRF: {e}{Colors.END}")
        return None, None

def test_deprecated_code_execution():
    """Test deprecated execute_code_view endpoint."""
    print_section("TEST 1: Deprecated Code Execution Endpoint")

    try:
        response = requests.post(
            f'{BASE_URL}/execute-code/',
            json={'code': 'print("test")'},
            headers={'Content-Type': 'application/json'}
        )

        # Should return 410 Gone
        passed = response.status_code == 410
        details = f"Status: {response.status_code}, Expected: 410 Gone"
        record_test("Deprecated endpoint returns 410 Gone", passed, details)

        if passed:
            data = response.json()
            has_error = 'error' in data
            has_migration = 'migration_guide' in data
            record_test("Response includes error message", has_error)
            record_test("Response includes migration guide", has_migration)

            if has_migration:
                print(f"\n{Colors.YELLOW}Migration Guide:{Colors.END}")
                print(f"  Old: {data['migration_guide'].get('old_endpoint')}")
                print(f"  New: {data['migration_guide'].get('new_endpoint')}")
                print(f"  Auth Required: {data['migration_guide'].get('authentication_required')}")

    except Exception as e:
        record_test("Deprecated endpoint test", False, f"Error: {e}")

def test_jwt_authentication(token):
    """Test JWT authentication (should work without CSRF)."""
    print_section("TEST 2: JWT Authentication (No CSRF Required)")

    if not token:
        print(f"{Colors.RED}Skipping JWT tests - no token available{Colors.END}")
        return

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Test 1: Execute code with JWT (no CSRF needed)
    try:
        response = requests.post(
            f'{BASE_URL}/api/v1/code-execution/',
            json={'code': 'print("JWT test")'},
            headers=headers
        )

        passed = response.status_code in [200, 201]
        details = f"Status: {response.status_code}"
        record_test("JWT auth on /api/v1/code-execution/ (no CSRF)", passed, details)

    except Exception as e:
        record_test("JWT code execution test", False, f"Error: {e}")

    # Test 2: Create forum topic with JWT (no CSRF needed)
    try:
        # First, get a valid forum ID
        response = requests.get(
            f'{BASE_URL}/api/v1/forum/forums/',
            headers={'Authorization': f'Bearer {token}'}
        )

        if response.status_code == 200:
            forums = response.json().get('results', [])
            if forums:
                forum_id = forums[0]['id']

                # Try to create a topic
                response = requests.post(
                    f'{BASE_URL}/api/v1/forum/topics/',
                    json={
                        'forum_id': forum_id,
                        'subject': f'Test Topic {datetime.now().timestamp()}',
                        'content': 'Test content for CSRF testing'
                    },
                    headers=headers
                )

                passed = response.status_code in [200, 201]
                details = f"Status: {response.status_code}"
                record_test("JWT auth on forum topic creation (no CSRF)", passed, details)
            else:
                record_test("JWT forum topic creation", False, "No forums available for testing")
        else:
            record_test("JWT forum list", False, f"Status: {response.status_code}")

    except Exception as e:
        record_test("JWT forum topic test", False, f"Error: {e}")

def test_session_authentication_without_csrf(session):
    """Test session authentication without CSRF token (should fail)."""
    print_section("TEST 3: Session Auth WITHOUT CSRF Token (Should Fail)")

    if not session:
        print(f"{Colors.RED}Skipping session tests - no session available{Colors.END}")
        return

    # Test 1: Try code execution without CSRF (should fail with 403)
    try:
        response = session.post(
            f'{BASE_URL}/api/v1/code-execution/',
            json={'code': 'print("session test")'},
            headers={'Content-Type': 'application/json'}
            # Note: No X-CSRFToken header
        )

        # Should fail with 403 Forbidden due to missing CSRF token
        passed = response.status_code == 403
        details = f"Status: {response.status_code}, Expected: 403 Forbidden"
        record_test("Session auth without CSRF fails correctly", passed, details)

    except Exception as e:
        record_test("Session without CSRF test", False, f"Error: {e}")

def test_session_authentication_with_csrf(session, csrf_token):
    """Test session authentication with CSRF token (should succeed)."""
    print_section("TEST 4: Session Auth WITH CSRF Token (Should Succeed)")

    if not session or not csrf_token:
        print(f"{Colors.RED}Skipping session+CSRF tests - session or CSRF token not available{Colors.END}")
        return

    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token
    }

    # Test 1: Execute code with session + CSRF
    try:
        response = session.post(
            f'{BASE_URL}/api/v1/code-execution/',
            json={'code': 'print("session + CSRF test")'},
            headers=headers
        )

        passed = response.status_code in [200, 201]
        details = f"Status: {response.status_code}"
        record_test("Session auth with CSRF succeeds", passed, details)

    except Exception as e:
        record_test("Session with CSRF test", False, f"Error: {e}")

def test_unauthenticated_access():
    """Test that unauthenticated access is properly blocked."""
    print_section("TEST 5: Unauthenticated Access (Should Fail)")

    # Test 1: Try to execute code without any authentication
    try:
        response = requests.post(
            f'{BASE_URL}/api/v1/code-execution/',
            json={'code': 'print("no auth")'},
            headers={'Content-Type': 'application/json'}
        )

        passed = response.status_code == 401
        details = f"Status: {response.status_code}, Expected: 401 Unauthorized"
        record_test("Unauthenticated code execution blocked", passed, details)

    except Exception as e:
        record_test("Unauthenticated access test", False, f"Error: {e}")

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
    """Run all CSRF protection tests."""
    print_header("CSRF Protection Test Suite - Phase 2.2")
    print(f"Testing against: {BASE_URL}")
    print(f"Test user: {TEST_USER['email']}")

    # Test 1: Deprecated endpoint
    test_deprecated_code_execution()

    # Test 2: JWT authentication
    print("\nObtaining JWT token...")
    jwt_token = get_jwt_token()
    if jwt_token:
        print(f"{Colors.GREEN}✓ JWT token obtained{Colors.END}")
        test_jwt_authentication(jwt_token)
    else:
        print(f"{Colors.RED}✗ Failed to obtain JWT token - skipping JWT tests{Colors.END}")
        return 1

    # Test 3 & 4: Session authentication
    print("\nObtaining session and CSRF token...")
    session, csrf_token = get_session_and_csrf()
    if session and csrf_token:
        print(f"{Colors.GREEN}✓ Session and CSRF token obtained{Colors.END}")
        test_session_authentication_without_csrf(session)
        test_session_authentication_with_csrf(session, csrf_token)
    else:
        print(f"{Colors.YELLOW}⚠ Session tests skipped{Colors.END}")

    # Test 5: Unauthenticated access
    test_unauthenticated_access()

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
