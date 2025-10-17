#!/bin/bash
# Change Validation Script
# Purpose: Prevent AI from committing sensitive files or dangerous code
# Usage: Run before git commit in GitHub Actions

set -euo pipefail

echo "=================================="
echo "Change Validation Script"
echo "=================================="

ERRORS=0

# Check for sensitive files in staged changes
echo ""
echo "Checking for sensitive files..."

SENSITIVE_FILES=(
    "\.env$"
    "\.env\..*"
    "db\.sqlite3$"
    ".*\.key$"
    ".*\.pem$"
    ".*credentials.*"
    ".*secret.*"
    ".*password.*\.txt$"
)

for pattern in "${SENSITIVE_FILES[@]}"; do
    if git diff --cached --name-only | grep -qE "$pattern"; then
        FILES=$(git diff --cached --name-only | grep -E "$pattern")
        echo "❌ ERROR: Attempting to commit sensitive file(s):"
        echo "$FILES" | sed 's/^/    /'
        ERRORS=$((ERRORS + 1))
    fi
done

[ $ERRORS -eq 0 ] && echo "✓ No sensitive files detected"

# Check for destructive migrations
echo ""
echo "Checking for database migrations..."

if git diff --cached --name-only | grep -qE "migrations/.*\.py$"; then
    MIGRATION_FILES=$(git diff --cached --name-only | grep -E "migrations/.*\.py$")
    echo "⚠️  WARNING: AI should not create database migrations"
    echo "Migration files detected:"
    echo "$MIGRATION_FILES" | sed 's/^/    /'

    # Check for destructive operations in migrations
    if git diff --cached | grep -qE "(RemoveField|DeleteModel|RunSQL.*DROP|RunSQL.*TRUNCATE)"; then
        echo "❌ ERROR: Destructive migration operations detected"
        echo "The following dangerous operations were found:"
        git diff --cached | grep -E "(RemoveField|DeleteModel|RunSQL.*DROP|RunSQL.*TRUNCATE)" | sed 's/^/    /'
        ERRORS=$((ERRORS + 1))
    else
        echo "ℹ️  Migration detected but no destructive operations found"
        echo "   Manual review still recommended"
    fi
fi

# Check for direct database access in code
echo ""
echo "Checking for direct database manipulation..."

DANGEROUS_SQL=(
    "DROP TABLE"
    "TRUNCATE TABLE"
    "DELETE FROM.*WHERE 1=1"
    "UPDATE.*SET.*WHERE 1=1"
    "cursor\.execute.*DROP"
    "cursor\.execute.*TRUNCATE"
    "\.raw\(.*DROP"
    "\.raw\(.*DELETE"
)

for pattern in "${DANGEROUS_SQL[@]}"; do
    if git diff --cached | grep -qE "$pattern"; then
        echo "❌ ERROR: Direct SQL manipulation detected: $pattern"
        git diff --cached | grep -E "$pattern" | sed 's/^/    /'
        ERRORS=$((ERRORS + 1))
    fi
done

[ $ERRORS -eq 0 ] && echo "✓ No dangerous SQL operations detected"

# Check for debug code and secrets in code
echo ""
echo "Checking for debug code and exposed secrets..."

DEBUG_PATTERNS=(
    "import pdb"
    "pdb\.set_trace"
    "breakpoint\(\)"
    "print\(.*password"
    "print\(.*secret"
    "print\(.*api_key"
    "console\.log\(.*password"
    "console\.log\(.*secret"
    "SECRET_KEY\s*=\s*['\"]"
    "API_KEY\s*=\s*['\"]"
    "PASSWORD\s*=\s*['\"]"
)

for pattern in "${DEBUG_PATTERNS[@]}"; do
    if git diff --cached | grep -qiE "$pattern"; then
        echo "❌ ERROR: Debug code or exposed secret detected: $pattern"
        git diff --cached | grep -iE "$pattern" | sed 's/^/    /'
        ERRORS=$((ERRORS + 1))
    fi
done

[ $ERRORS -eq 0 ] && echo "✓ No debug code or exposed secrets detected"

# Check for settings file modifications
echo ""
echo "Checking for settings modifications..."

if git diff --cached --name-only | grep -qE "settings/.*\.py$"; then
    SETTINGS_FILES=$(git diff --cached --name-only | grep -E "settings/.*\.py$")
    echo "⚠️  WARNING: Settings files modified:"
    echo "$SETTINGS_FILES" | sed 's/^/    /'

    # Check for dangerous settings changes
    DANGEROUS_SETTINGS=(
        "DEBUG\s*=\s*True"
        "ALLOWED_HOSTS\s*=\s*\['?\*'?\]"
        "SECRET_KEY\s*=\s*['\"]"
        "CSRF_COOKIE_SECURE\s*=\s*False"
        "SESSION_COOKIE_SECURE\s*=\s*False"
    )

    for pattern in "${DANGEROUS_SETTINGS[@]}"; do
        if git diff --cached | grep -qE "$pattern"; then
            echo "❌ ERROR: Dangerous settings change detected: $pattern"
            git diff --cached | grep -E "$pattern" | sed 's/^/    /'
            ERRORS=$((ERRORS + 1))
        fi
    done
fi

# Check file permissions changes
echo ""
echo "Checking for permission changes..."

if git diff --cached | grep -qE "chmod\s+(777|666)"; then
    echo "❌ ERROR: Insecure file permissions detected (chmod 777/666)"
    git diff --cached | grep -E "chmod\s+(777|666)" | sed 's/^/    /'
    ERRORS=$((ERRORS + 1))
fi

[ $ERRORS -eq 0 ] && echo "✓ No insecure permission changes detected"

# Summary
echo ""
echo "=================================="
echo "Validation Summary"
echo "=================================="

if [ $ERRORS -eq 0 ]; then
    echo "✅ All validation checks passed"
    echo ""
    echo "Changes are safe to commit."
    exit 0
else
    echo "❌ Validation failed with $ERRORS error(s)"
    echo ""
    echo "Please review and fix the errors above before committing."
    echo ""
    echo "If you believe these changes are safe, they must be:"
    echo "  1. Reviewed manually by a human maintainer"
    echo "  2. Approved by security team"
    echo "  3. Committed with proper justification"
    echo ""
    exit 1
fi
