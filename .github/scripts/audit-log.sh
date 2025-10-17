#!/bin/bash
# Audit Logging Script
# Purpose: Create audit trail of AI operations for compliance and forensics
# Usage: Run before and after Claude Code execution

set -euo pipefail

AUDIT_DIR=".github/audit"
AUDIT_LOG="$AUDIT_DIR/claude-operations.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
RUN_ID="${GITHUB_RUN_ID:-local-$(date +%s)}"

# Create audit directory
mkdir -p "$AUDIT_DIR"

echo "=================================="
echo "Audit Logging - Start"
echo "=================================="

# Capture system state before operation
cat >> "$AUDIT_LOG" << EOF
================================================================================
AUDIT LOG ENTRY - START
================================================================================
Timestamp: $TIMESTAMP
Run ID: $RUN_ID
Workflow: ${GITHUB_WORKFLOW:-Manual}
Event: ${GITHUB_EVENT_NAME:-Manual}
Triggered By: ${GITHUB_ACTOR:-System}
Repository: ${GITHUB_REPOSITORY:-Unknown}
Branch: ${GITHUB_REF_NAME:-Unknown}
Commit SHA: ${GITHUB_SHA:-Unknown}

--------------------------------------------------------------------------------
SYSTEM STATE - BEFORE OPERATION
--------------------------------------------------------------------------------

Git Status:
$(git status --porcelain 2>&1 || echo "Git status unavailable")

Recent Commits (last 5):
$(git log --oneline -5 2>&1 || echo "Git log unavailable")

Modified Files (uncommitted):
$(git diff --name-only 2>&1 || echo "No uncommitted changes")

Staged Files:
$(git diff --cached --name-only 2>&1 || echo "No staged files")

Database Status:
$(if [ -f "db.sqlite3" ]; then
    echo "  File: db.sqlite3"
    echo "  Size: $(stat -f%z db.sqlite3 2>/dev/null || stat -c%s db.sqlite3 2>/dev/null || echo 'Unknown')"
    echo "  Checksum: $(md5sum db.sqlite3 2>/dev/null || md5 -q db.sqlite3 2>/dev/null || echo 'Unknown')"
    echo "  Permissions: $(ls -la db.sqlite3 | awk '{print $1}')"
else
    echo "  Database file not present"
fi)

Environment Files:
$(ls -la .env* 2>/dev/null || echo "  No .env files found")

Critical File Checksums:
$(find apps -name "models.py" -type f -exec sh -c 'echo "  $1: $(md5sum "$1" 2>/dev/null | cut -d" " -f1 || md5 -q "$1" 2>/dev/null)"' _ {} \; 2>/dev/null | head -10)

Python Packages:
$(pip list --format=freeze 2>/dev/null | grep -E "^(Django|djangorestframework|wagtail)=" || echo "  Package list unavailable")

Disk Usage:
$(du -sh . 2>/dev/null || echo "  Disk usage unavailable")

EOF

echo "✓ Pre-operation state captured"

# Create snapshot directory for this run
SNAPSHOT_DIR="$AUDIT_DIR/snapshots/$RUN_ID"
mkdir -p "$SNAPSHOT_DIR"

# Backup critical files
if [ -f "db.sqlite3" ]; then
    cp db.sqlite3 "$SNAPSHOT_DIR/db.sqlite3.backup" 2>/dev/null || true
    echo "✓ Database snapshot created"
fi

# Backup settings
cp -r learning_community/settings "$SNAPSHOT_DIR/settings_backup" 2>/dev/null || true
echo "✓ Settings snapshot created"

# Backup models
find apps -name "models.py" -type f -exec sh -c '
    DIR="$1/$(dirname "$2")"
    mkdir -p "$DIR"
    cp "$2" "$DIR/"
' _ "$SNAPSHOT_DIR/models_backup" {} \; 2>/dev/null || true
echo "✓ Models snapshot created"

# Save git state
git diff > "$SNAPSHOT_DIR/git_diff.patch" 2>/dev/null || true
git diff --cached > "$SNAPSHOT_DIR/git_diff_staged.patch" 2>/dev/null || true
git log --oneline -20 > "$SNAPSHOT_DIR/git_log.txt" 2>/dev/null || true
echo "✓ Git state snapshot created"

# Append operation details
cat >> "$AUDIT_LOG" << EOF

--------------------------------------------------------------------------------
OPERATION DETAILS
--------------------------------------------------------------------------------

Claude Operation: ${1:-Unknown}
Prompt: ${2:-Not specified}

Allowed Tools: ${3:-All tools (UNSAFE)}

Expected Changes:
${4:-Not documented}

Risk Level: ${5:-Unknown}

--------------------------------------------------------------------------------
SNAPSHOTS
--------------------------------------------------------------------------------

Snapshot Directory: $SNAPSHOT_DIR
Database Backup: $([ -f "$SNAPSHOT_DIR/db.sqlite3.backup" ] && echo "Created" || echo "N/A")
Settings Backup: $([ -d "$SNAPSHOT_DIR/settings_backup" ] && echo "Created" || echo "N/A")
Models Backup: $([ -d "$SNAPSHOT_DIR/models_backup" ] && echo "Created" || echo "N/A")
Git State: $([ -f "$SNAPSHOT_DIR/git_diff.patch" ] && echo "Created" || echo "N/A")

EOF

echo ""
echo "✅ Audit log entry created"
echo "   Log file: $AUDIT_LOG"
echo "   Snapshots: $SNAPSHOT_DIR"
echo ""
echo "To complete audit trail, run this script again with 'complete' argument after operation"
echo "Usage: ./audit-log.sh complete"
