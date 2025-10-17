#!/bin/bash
# Restore Protections Script
# Purpose: Restore normal file permissions after AI workflow completes
# Usage: Run after Claude Code execution in GitHub Actions

set -euo pipefail

echo "=================================="
echo "Restore Protections Script"
echo "=================================="

# Restore database permissions
if [ -f "db.sqlite3" ]; then
    chmod 644 db.sqlite3
    echo "✓ Database permissions restored (chmod 644)"
fi

# Restore .env file
if [ -f ".env.protected" ]; then
    mv .env.protected .env
    echo "✓ Environment file restored (.env.protected → .env)"
fi

# Clean up temporary marker files (but keep .gitattributes)
if [ -f ".claude-restricted" ]; then
    rm .claude-restricted
    echo "✓ Cleaned up temporary markers"
fi

echo ""
echo "✅ File protections restored to normal state"
