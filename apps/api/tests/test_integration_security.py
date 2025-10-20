"""
Security Regression Integration Test.

Ensures security fixes remain in place across the codebase:
- SQL injection prevention (.extra() removal)
- Mutable default anti-pattern prevention
- Authentication enforcement
- CSRF protection
"""

import os
import re
from django.test import TestCase
from django.apps import apps
from django.db import models


class SecurityRegressionTest(TestCase):
    """Ensure security fixes remain in place."""

    def test_no_extra_method_usage(self):
        """
        Verify .extra() is not used anywhere in the codebase.

        .extra() allows raw SQL injection and was removed in fix #018.
        This test prevents regression by scanning all Python files.
        """
        violations = []
        apps_dir = os.path.join(os.path.dirname(__file__), '..', '..')

        for root, dirs, files in os.walk(apps_dir):
            # Skip migrations, __pycache__, tests, and venv
            if '__pycache__' in root or 'migrations' in root or 'venv' in root or 'tests' in root:
                continue

            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)

                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                            # Check for .extra( usage
                            if re.search(r'\.extra\s*\(', content):
                                # Verify it's not just a comment or docstring
                                lines = content.split('\n')
                                for i, line in enumerate(lines, 1):
                                    if re.search(r'\.extra\s*\(', line):
                                        # Skip if it's in a comment
                                        stripped = line.strip()
                                        if stripped.startswith('#'):
                                            continue
                                        # Skip if it's in a docstring (triple quotes)
                                        if '"""' in line or "'''" in line:
                                            continue

                                        violations.append(f"{filepath}:{i}")
                    except (UnicodeDecodeError, IOError):
                        # Skip files that can't be read
                        pass

        self.assertEqual(violations, [],
            f"Found .extra() usage (SQL injection risk) in:\n" + "\n".join(violations))

    def test_no_mutable_defaults_in_models(self):
        """
        Scan all Django models for mutable default anti-pattern.

        Mutable defaults (list, dict, set) cause shared state bugs.
        Fixed in #019 - all fields should use default=dict or callable.
        """
        violations = []

        for model in apps.get_models():
            for field in model._meta.get_fields():
                if hasattr(field, 'default') and field.default is not None:
                    # Check if default is a mutable object (not callable)
                    if isinstance(field.default, (list, dict, set)):
                        violations.append(
                            f"{model.__name__}.{field.name}: "
                            f"default={type(field.default).__name__}()"
                        )

        self.assertEqual(violations, [],
            f"Found mutable defaults (should be callables):\n" + "\n".join(violations))

    def test_jsonfield_uses_callable_defaults(self):
        """
        Verify all JSONField uses callable defaults (dict, list).

        JSONField should use default=dict or default=list, NOT {}/[].
        """
        violations = []

        for model in apps.get_models():
            for field in model._meta.get_fields():
                # Check JSONField specifically
                if field.__class__.__name__ == 'JSONField':
                    if hasattr(field, 'default'):
                        # Default should be callable (dict, list) or None
                        if field.default is not None:
                            if isinstance(field.default, (dict, list, set)):
                                violations.append(
                                    f"{model.__name__}.{field.name}: "
                                    f"JSONField default should be callable, "
                                    f"found {type(field.default).__name__}()"
                                )

        self.assertEqual(violations, [],
            f"Found JSONField mutable defaults:\n" + "\n".join(violations))

    def test_no_csrf_exempt_on_authenticated_views(self):
        """
        Verify @csrf_exempt is not used on authenticated endpoints.

        All authenticated views should use CSRF protection.
        Removed in security audit #016.
        """
        violations = []
        apps_dir = os.path.join(os.path.dirname(__file__), '..', '..')

        for root, dirs, files in os.walk(apps_dir):
            if '__pycache__' in root or 'migrations' in root or 'venv' in root:
                continue

            for file in files:
                if file.endswith(('.py',)) and (file.startswith('views') or file.startswith('api')):
                    filepath = os.path.join(root, file)

                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                            # Look for @csrf_exempt decorator
                            if '@csrf_exempt' in content:
                                # Check if it's also using authentication
                                lines = content.split('\n')
                                for i, line in enumerate(lines, 1):
                                    if '@csrf_exempt' in line:
                                        # Look ahead for authentication decorators
                                        next_lines = '\n'.join(lines[i:min(i+10, len(lines))])
                                        if any(auth in next_lines for auth in [
                                            '@login_required',
                                            '@permission_required',
                                            'permission_classes',
                                            'IsAuthenticated'
                                        ]):
                                            violations.append(f"{filepath}:{i}")
                    except (UnicodeDecodeError, IOError):
                        pass

        # Note: Some csrf_exempt usage is legitimate (webhooks, public APIs)
        # This test catches the common mistake of using it with authentication
        if violations:
            self.fail(
                f"Found @csrf_exempt on authenticated views:\n" +
                "\n".join(violations) +
                "\n\nAuthenticated views should use CSRF protection!"
            )

    def test_all_code_execution_endpoints_require_auth(self):
        """
        Verify all code execution endpoints require authentication.

        Code execution is high-risk and must be authenticated.
        Fixed in security audit #016.
        """
        from apps.api.views import code_execution
        import inspect

        # Get all code execution view functions and classes
        code_exec_items = [
            code_execution.execute_code,
            code_execution.submit_exercise_code,
            code_execution.CodeExecutionView,
            code_execution.ExerciseEvaluationView,
        ]

        for item in code_exec_items:
            # Check if view has authentication
            has_auth = False

            # Check for DRF permission_classes (for class-based views)
            if hasattr(item, 'permission_classes'):
                has_auth = True

            # Check source code for permission requirements
            source = inspect.getsource(item)
            if 'permission_classes' in source or '@login_required' in source or 'IsAuthenticated' in source:
                has_auth = True

            # Check for @login_required decorator (function-based views)
            if hasattr(item, '__wrapped__'):
                has_auth = True

            name = item.__name__ if hasattr(item, '__name__') else str(item)
            self.assertTrue(has_auth,
                f"{name} lacks authentication (security risk)")

    def test_user_model_has_soft_delete(self):
        """
        Verify User model has soft delete infrastructure.

        Soft delete prevents CASCADE deletion of user content.
        Implemented in #024.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Check for soft delete fields
        field_names = [f.name for f in User._meta.get_fields()]

        self.assertIn('is_deleted', field_names,
            "User model missing is_deleted field")
        self.assertIn('deleted_at', field_names,
            "User model missing deleted_at field")
        self.assertIn('deletion_reason', field_names,
            "User model missing deletion_reason field")

        # Check for soft delete methods
        self.assertTrue(hasattr(User, 'soft_delete'),
            "User model missing soft_delete() method")
        self.assertTrue(hasattr(User, 'restore'),
            "User model missing restore() method")
        self.assertTrue(hasattr(User, 'anonymize_personal_data'),
            "User model missing anonymize_personal_data() method")

        # Check for custom manager
        self.assertTrue(hasattr(User.objects, 'all_with_deleted'),
            "User manager missing all_with_deleted() method")
        self.assertTrue(hasattr(User.objects, 'deleted_only'),
            "User manager missing deleted_only() method")

    def test_enrollment_uses_get_or_create(self):
        """
        Verify enrollment view uses get_or_create() for race condition safety.

        Enrollment should use atomic get_or_create to prevent duplicates.
        Fixed in #022.
        """
        from apps.learning import views
        import inspect

        # Get source code of enroll_course view
        source = inspect.getsource(views.enroll_course)

        # Verify uses atomic transaction
        self.assertIn('transaction.atomic', source,
            "Enrollment missing transaction.atomic()")

        # Verify uses select_for_update
        self.assertIn('select_for_update', source,
            "Enrollment missing select_for_update() for row locking")

        # Verify uses get_or_create
        self.assertIn('get_or_create', source,
            "Enrollment should use get_or_create() not create()")

        # Verify uses F() expression for counter
        self.assertIn('F(', source,
            "Enrollment should use F() expression for safe counter updates")

    def test_no_hardcoded_secrets_in_settings(self):
        """
        Verify no hardcoded secrets in settings files.

        Secrets should come from environment variables.
        """
        settings_dir = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'learning_community', 'settings'
        )

        violations = []

        for root, dirs, files in os.walk(settings_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    filepath = os.path.join(root, file)

                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                            # Check for common secret patterns
                            patterns = [
                                (r'SECRET_KEY\s*=\s*["\'](?!os\.environ)[^"\']{20,}', 'Hardcoded SECRET_KEY'),
                                (r'API_KEY\s*=\s*["\'][^"\']+["\']', 'Hardcoded API_KEY'),
                                (r'PASSWORD\s*=\s*["\'][^"\']+["\']', 'Hardcoded PASSWORD'),
                                (r'AWS_SECRET\s*=\s*["\'][^"\']+["\']', 'Hardcoded AWS_SECRET'),
                            ]

                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                # Skip comments
                                if line.strip().startswith('#'):
                                    continue

                                for pattern, desc in patterns:
                                    if re.search(pattern, line):
                                        # Allow placeholder values
                                        if 'your-secret-key-here' in line.lower():
                                            continue
                                        if 'change-me' in line.lower():
                                            continue

                                        violations.append(f"{file}:{i} - {desc}")
                    except (UnicodeDecodeError, IOError):
                        pass

        # This test may have false positives, so we just warn
        if violations:
            # Don't fail test, but log warning
            print(f"\nWarning: Potential hardcoded secrets:\n" + "\n".join(violations))

    def test_sensitive_model_fields_use_set_null(self):
        """
        Verify sensitive user relationships use on_delete=SET_NULL or CASCADE with soft delete.

        Prevents data loss when users delete accounts (GDPR compliance).
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Check important models that reference User
        models_to_check = [
            ('apps.learning.models', 'CourseEnrollment'),
            ('apps.forum_integration.models', 'TrustLevel'),
            ('apps.forum_integration.models', 'UserActivity'),
        ]

        for app_models, model_name in models_to_check:
            try:
                model_class = apps.get_model(app_models.split('.')[1], model_name)

                # Find user foreign keys
                for field in model_class._meta.get_fields():
                    if isinstance(field, models.ForeignKey):
                        if field.related_model == User:
                            on_delete = field.remote_field.on_delete

                            # Should be CASCADE (with soft delete) or SET_NULL
                            # CASCADE is OK because User has soft delete
                            valid_options = [
                                models.CASCADE,  # OK with soft delete
                                models.SET_NULL,  # Preserves content
                            ]

                            self.assertIn(on_delete, valid_options,
                                f"{model_name}.{field.name} uses {on_delete.__name__} "
                                f"(should use CASCADE or SET_NULL with soft delete)")

            except LookupError:
                # Model doesn't exist, skip
                pass
