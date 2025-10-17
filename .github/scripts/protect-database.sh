#!/bin/bash
# Database Protection Script
# Purpose: Prevent AI workflows from modifying database and sensitive files
# Usage: Run before Claude Code execution in GitHub Actions

set -euo pipefail

echo "=================================="
echo "Database Protection Script"
echo "=================================="

# Make database read-only if it exists
if [ -f "db.sqlite3" ]; then
    chmod 444 db.sqlite3
    echo "✓ Database set to read-only mode (chmod 444)"
    echo "  Current permissions: $(ls -la db.sqlite3 | awk '{print $1}')"
else
    echo "ℹ Database file not found (expected in CI environment)"
fi

# Protect .env file by renaming it temporarily
if [ -f ".env" ]; then
    mv .env .env.protected
    echo "✓ Environment file protected (.env → .env.protected)"
fi

# Create .gitattributes to prevent binary file commits
cat > .gitattributes << 'EOF'
# Binary files - prevent accidental commits
*.sqlite3 binary diff=none merge=binary
*.db binary diff=none merge=binary
*.sqlite binary diff=none merge=binary

# Sensitive files - enforce LF line endings and prevent diffs
.env* text eol=lf diff=none
*.key binary diff=none
*.pem binary diff=none
*credentials* diff=none

# Database migrations - prevent AI modification
**/migrations/*.py text diff=python
EOF

echo "✓ Git attributes configured for sensitive files"

# Create .claude-restricted marker file
cat > .claude-restricted << 'EOF'
# Files and directories that Claude Code cannot modify
# This file serves as documentation and configuration reference

RESTRICTED_FILES:
  - db.sqlite3 (database file)
  - .env* (environment configuration)
  - *.key (cryptographic keys)
  - *credentials* (credential files)

RESTRICTED_COMMANDS:
  - python manage.py migrate
  - python manage.py flush
  - python manage.py shell
  - sqlite3 db.sqlite3
  - psql
  - mysql
  - rm -rf
  - chmod 777

ALLOWED_OPERATIONS:
  - Read files via Read tool
  - Search code via Grep/Glob
  - View git history
  - Comment on PRs via gh CLI
  - Read documentation

Last Updated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

echo "✓ Claude restrictions documented in .claude-restricted"

# Verify protections
echo ""
echo "Protection Status:"
echo "----------------------------------"
[ -f "db.sqlite3" ] && echo "  Database: $(ls -lh db.sqlite3 | awk '{print $1, $5}')" || echo "  Database: Not present"
[ -f ".env.protected" ] && echo "  .env: Protected (renamed)" || echo "  .env: Not present"
[ -f ".gitattributes" ] && echo "  .gitattributes: Created" || echo "  .gitattributes: Failed"
echo "----------------------------------"

echo ""
echo "✅ Database protection enabled successfully"
echo ""
echo "To restore after workflow:"
echo "  chmod 644 db.sqlite3"
echo "  mv .env.protected .env"
