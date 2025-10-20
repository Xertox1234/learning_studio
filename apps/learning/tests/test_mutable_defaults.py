"""
Data integrity tests to verify JSONField defaults don't share state.

This test suite ensures that mutable default anti-patterns are not present
in the codebase, preventing data corruption bugs.
"""

from django.test import TestCase
from django.apps import apps

from apps.learning.models import Lesson
from apps.users.models import User


class MutableDefaultTests(TestCase):
    """Tests to prevent mutable default anti-patterns."""

    def test_no_literal_mutable_defaults_in_models(self):
        """
        Scan all models for literal mutable defaults ([], {}) anti-pattern.

        This test ensures we use callable defaults (list, dict) instead of
        literal defaults ([], {}) which would be shared across instances.

        Related: Todo #019
        """
        dangerous_patterns = []

        for model in apps.get_models():
            # Skip models from third-party apps
            if not model.__module__.startswith('apps.'):
                continue

            for field in model._meta.get_fields():
                if hasattr(field, 'default') and field.default is not None:
                    # Check if default is a literal mutable object (not callable)
                    # This is the DANGEROUS pattern: default=[] or default={}

                    # Safe patterns: default=list, default=dict (callables)
                    # Unsafe patterns: default=[], default={} (literals)

                    if isinstance(field.default, (list, dict, set)):
                        dangerous_patterns.append({
                            'model': model.__name__,
                            'field': field.name,
                            'default_type': type(field.default).__name__,
                            'default_value': field.default
                        })

        # Assert no literal mutable defaults found
        if dangerous_patterns:
            error_msg = "\n\nFound literal mutable defaults (anti-pattern):\n"
            for pattern in dangerous_patterns:
                error_msg += (
                    f"\n  {pattern['model']}.{pattern['field']}: "
                    f"default={pattern['default_value']} (type: {pattern['default_type']})"
                )
            error_msg += "\n\nFix by using callable defaults:\n"
            error_msg += "  - Replace default=[] with default=list\n"
            error_msg += "  - Replace default={} with default=dict\n"
            error_msg += "  - Replace default=set() with default=set\n"
            self.fail(error_msg)

    def test_jsonfield_defaults_are_callables(self):
        """
        Verify all JSONField defaults are callables, not literals.

        Callables (safe):   default=list, default=dict
        Literals (unsafe):  default=[], default={}

        Related: Todo #019
        """
        from django.db import models as django_models

        issues = []

        for model in apps.get_models():
            # Skip third-party models
            if not model.__module__.startswith('apps.'):
                continue

            for field in model._meta.get_fields():
                # Check JSONField instances
                if isinstance(field, django_models.JSONField):
                    if hasattr(field, 'default') and field.default is not None:
                        # Verify default is callable (list, dict, or function)
                        # NOT a literal instance ([], {})
                        if callable(field.default):
                            # Good! default=list or default=dict or default=custom_function
                            pass
                        else:
                            # Bad! default=[] or default={}
                            issues.append({
                                'model': model.__name__,
                                'field': field.name,
                                'default': field.default
                            })

        if issues:
            error_msg = "\n\nFound JSONField with non-callable defaults:\n"
            for issue in issues:
                error_msg += (
                    f"\n  {issue['model']}.{issue['field']}: "
                    f"default={issue['default']}"
                )
            error_msg += "\n\nAll JSONField defaults must be callables!\n"
            self.fail(error_msg)


class DataIntegrityDocumentationTests(TestCase):
    """Tests to document correct usage patterns."""

    def test_correct_jsonfield_pattern_documented(self):
        """
        Document the CORRECT pattern for JSONField defaults.

        This test serves as documentation for future developers.
        """
        # ✅ CORRECT PATTERN: Use callable (function/type reference)
        # This creates a NEW list for each model instance

        # Example from Lesson model:
        # structured_content = models.JSONField(default=list, blank=True)
        #                                               ^^^^
        #                                          callable (type reference)

        # ❌ WRONG PATTERN: Use literal
        # This would share the SAME list across ALL instances!
        # structured_content = models.JSONField(default=[], blank=True)
        #                                               ^^
        #                                          literal (shared object)

        # Verify our models use the correct pattern
        from apps.learning.models import Lesson

        field = Lesson._meta.get_field('structured_content')

        # Verify it has a default
        self.assertIsNotNone(field.default)

        # Verify the default is callable
        self.assertTrue(
            callable(field.default),
            f"Lesson.structured_content.default should be callable, "
            f"got: {type(field.default)}"
        )

        # Verify it's the `list` type (callable that returns new list)
        self.assertEqual(field.default, list)
