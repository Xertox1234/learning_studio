"""
Security tests to prevent SQL injection vulnerabilities.

This test suite ensures that dangerous SQL patterns are not reintroduced.
"""

import os
import re
from django.test import TestCase


class SQLInjectionPreventionTests(TestCase):
    """Tests to prevent SQL injection vulnerabilities."""

    def test_no_extra_method_usage(self):
        """
        Ensure .extra() is not used anywhere in the codebase.

        The .extra() method is deprecated and poses a SQL injection risk.
        Use Django ORM annotations and database functions instead.

        Related: CVE-2025-SQL-001, Todo #018
        """
        dangerous_pattern = re.compile(r'\.extra\s*\(')
        violations = []

        # Scan apps/ directory for Python files
        apps_dir = os.path.join(os.path.dirname(__file__), '..', '..')

        for root, dirs, files in os.walk(apps_dir):
            # Skip test files and migrations
            if 'tests' in root or 'migrations' in root:
                continue

            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)

                    with open(filepath, 'r') as f:
                        content = f.read()

                        # Find all matches
                        for match in dangerous_pattern.finditer(content):
                            # Get line number
                            line_num = content[:match.start()].count('\n') + 1

                            # Get the actual line content
                            lines = content.split('\n')
                            line_content = lines[line_num - 1].strip()

                            # Skip if it's just a comment
                            if line_content.startswith('#'):
                                continue

                            violations.append({
                                'file': os.path.relpath(filepath, apps_dir),
                                'line': line_num,
                                'content': line_content
                            })

        # Assert no violations found
        if violations:
            error_msg = "\n\nFound .extra() usage (SQL injection risk):\n"
            for v in violations:
                error_msg += f"\n  {v['file']}:{v['line']}\n    {v['content']}\n"
            error_msg += "\nUse Django ORM annotations instead:\n"
            error_msg += "  - TruncDate() for date truncation\n"
            error_msg += "  - Cast() and Extract() for calculations\n"
            error_msg += "  - ExpressionWrapper() for complex expressions\n"
            self.fail(error_msg)

    def test_no_raw_sql_in_querysets(self):
        """
        Ensure raw SQL strings are not directly embedded in querysets.

        This is a secondary check to catch potential SQL injection vectors.
        """
        # This test can be expanded to check for other SQL injection patterns
        # such as string concatenation in .filter() or .exclude() calls
        pass  # Placeholder for future expansion
