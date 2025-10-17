# Claude Workflow Safety Scripts

These scripts protect your repository from accidental data corruption by AI operations.

## Scripts

### 1. protect-database.sh
**Purpose:** Make database and sensitive files read-only before AI execution

**Usage:**
```bash
bash .github/scripts/protect-database.sh
```

**What it does:**
- Sets db.sqlite3 to read-only (chmod 444)
- Renames .env to .env.protected
- Creates .gitattributes for sensitive file protection
- Documents restrictions in .claude-restricted

**When to run:** Before any Claude Code workflow execution

---

### 2. validate-changes.sh
**Purpose:** Validate that AI hasn't staged dangerous changes for commit

**Usage:**
```bash
bash .github/scripts/validate-changes.sh
```

**What it checks:**
- No sensitive files (.env, db.sqlite3, *.key)
- No destructive migrations (RemoveField, DeleteModel)
- No dangerous SQL (DROP, TRUNCATE)
- No debug code (pdb, breakpoint)
- No exposed secrets (hardcoded passwords, API keys)
- No insecure settings changes

**When to run:** Before git commit in workflows

**Exit codes:**
- 0: All checks passed (safe to commit)
- 1: Validation failed (do not commit)

---

### 3. audit-log.sh
**Purpose:** Create audit trail of AI operations for compliance and forensics

**Usage:**
```bash
# Start of operation
bash .github/scripts/audit-log.sh "Operation Name" "Prompt" "Allowed Tools" "Expected Changes" "Risk Level"

# Example
bash .github/scripts/audit-log.sh \
  "Code Review" \
  "Review PR #123" \
  "Read-only tools" \
  "No changes expected" \
  "Low"
```

**What it logs:**
- Timestamp, workflow, actor
- Git state (status, diff, commits)
- Database size and checksum
- File checksums for critical files
- Creates snapshots in .github/audit/snapshots/

**When to run:**
- Start of workflow (captures before state)
- End of workflow (captures after state)

---

### 4. restore-protections.sh
**Purpose:** Restore normal file permissions after AI workflow completes

**Usage:**
```bash
bash .github/scripts/restore-protections.sh
```

**What it does:**
- Restores db.sqlite3 permissions (chmod 644)
- Renames .env.protected back to .env
- Cleans up temporary marker files

**When to run:** After Claude Code workflow execution (in `always()` condition)

---

## Integration with GitHub Actions

### Example Workflow Integration

```yaml
jobs:
  claude:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      # PROTECTION: Before AI execution
      - name: Protect Sensitive Files
        run: bash .github/scripts/protect-database.sh

      - name: Audit Log Start
        run: bash .github/scripts/audit-log.sh "AI Task" "User prompt" "Restricted tools" "Code changes" "Medium"

      # AI EXECUTION
      - name: Run Claude Code
        uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          claude_args: '--allowed-tools "Read,Grep,Glob" --disallowed-tools "Write,Edit"'

      # VALIDATION: After AI execution
      - name: Validate Changes
        if: always()
        run: bash .github/scripts/validate-changes.sh

      # CLEANUP: Always run
      - name: Restore Protections
        if: always()
        run: bash .github/scripts/restore-protections.sh
```

---

## Quick Testing

Test locally before deploying:

```bash
cd /Users/williamtower/projects/learning_studio

# 1. Test protection
.github/scripts/protect-database.sh
ls -la db.sqlite3  # Should be r--r--r--

# 2. Test validation with clean state
.github/scripts/validate-changes.sh  # Should pass

# 3. Test validation catches sensitive files
git add .env
.github/scripts/validate-changes.sh  # Should fail
git reset HEAD .env

# 4. Test restoration
.github/scripts/restore-protections.sh
ls -la db.sqlite3  # Should be rw-r--r--
```

---

## Maintenance

### Audit Log Cleanup
Audit logs and snapshots accumulate over time. Clean up old entries:

```bash
# Archive logs older than 30 days
find .github/audit/snapshots -mtime +30 -type d -exec rm -rf {} \;

# Or create monthly archives
tar -czf audit-$(date +%Y-%m).tar.gz .github/audit/
```

### Updating Restrictions
Edit `validate-changes.sh` to add new patterns:

```bash
# Add new sensitive file patterns
SENSITIVE_FILES=(
    "\.env$"
    "\.env\..*"
    "db\.sqlite3$"
    "your-new-pattern"  # Add here
)

# Add new dangerous code patterns
DEBUG_PATTERNS=(
    "import pdb"
    "your-new-pattern"  # Add here
)
```

---

## Troubleshooting

### "Permission denied" errors
```bash
chmod +x .github/scripts/*.sh
```

### Database protection fails in CI
The scripts handle missing files gracefully. If db.sqlite3 doesn't exist in CI (expected), scripts will skip protection with info message.

### Too many false positives in validation
Review and adjust patterns in `validate-changes.sh`. Comment out overly strict checks, but document why.

### Audit logs growing too large
Set up automated cleanup (see Maintenance section) or increase storage limits.

---

## Security Notice

These scripts are part of a defense-in-depth strategy:

1. **Layer 1:** Tool restrictions in workflow files
2. **Layer 2:** File permissions (these scripts)
3. **Layer 3:** Change validation (these scripts)
4. **Layer 4:** Audit logging (these scripts)
5. **Layer 5:** Branch protection (GitHub settings)

**No single layer is sufficient. All layers must be active for maximum protection.**

---

## Support

For detailed implementation guide, see:
- `/Users/williamtower/projects/learning_studio/.github/IMPLEMENTATION_GUIDE.md`

For comprehensive analysis, see:
- `/Users/williamtower/projects/learning_studio/CLAUDE_WORKFLOW_DATA_INTEGRITY_ANALYSIS.md`

For critical findings summary, see:
- `/Users/williamtower/projects/learning_studio/CRITICAL_FINDINGS_SUMMARY.md`

Create issues with label `claude-workflows` for support.
