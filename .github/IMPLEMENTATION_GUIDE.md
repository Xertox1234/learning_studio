# Implementation Guide: Claude Workflow Safeguards

## Quick Start (5 Minutes)

Follow these steps to make PR #1 safe for production:

### Step 1: Update claude.yml (CRITICAL)
Edit `.github/workflows/claude.yml` at line 49:

**Replace:**
```yaml
# claude_args: '--allowed-tools Bash(gh pr:*)'
```

**With:**
```yaml
claude_args: |
  --allowed-tools "Read,Glob,Grep,WebFetch,AskUserQuestion"
  --allowed-tools "Bash(gh issue view:*),Bash(gh issue list:*),Bash(gh issue comment:*)"
  --allowed-tools "Bash(gh pr view:*),Bash(gh pr list:*),Bash(gh pr comment:*),Bash(gh pr diff:*)"
  --allowed-tools "Bash(gh search:*),Bash(git log:*),Bash(git diff:*),Bash(git status:*)"
  --disallowed-tools "Write,Edit,NotebookEdit"
  --disallowed-tools "Bash(python manage.py:*),Bash(./manage.py:*)"
  --disallowed-tools "Bash(sqlite3:*),Bash(psql:*),Bash(mysql:*)"
  --disallowed-tools "Bash(rm:*),Bash(mv .env:*),Bash(chmod 777:*)"
```

### Step 2: Add Protection Step to Workflows
Add after the "Checkout repository" step in both workflow files:

**For `claude.yml`:**
```yaml
- name: Protect Database and Sensitive Files
  run: bash .github/scripts/protect-database.sh

- name: Run Claude Code
  id: claude
  uses: anthropics/claude-code-action@v1
  # ... rest of configuration

- name: Validate Changes
  if: always()
  run: bash .github/scripts/validate-changes.sh

- name: Restore Protections
  if: always()
  run: bash .github/scripts/restore-protections.sh
```

**For `claude-code-review.yml`:**
```yaml
- name: Audit Log Start
  run: bash .github/scripts/audit-log.sh "Code Review" "Automated PR review" "Read-only tools" "No changes expected" "Low"

- name: Run Claude Code Review
  id: claude-review
  uses: anthropics/claude-code-action@v1
  # ... rest of configuration
```

### Step 3: Test Locally
Run the protection scripts locally to verify they work:

```bash
cd /Users/williamtower/projects/learning_studio

# Test database protection
.github/scripts/protect-database.sh

# Verify database is read-only
ls -la db.sqlite3
# Should show: r--r--r-- (444 permissions)

# Test change validation (should pass if no staged changes)
git add .github/scripts/*.sh
.github/scripts/validate-changes.sh

# Restore protections
.github/scripts/restore-protections.sh
```

### Step 4: Enable Branch Protection
Go to GitHub Repository Settings → Branches → Add rule:

```
Branch name pattern: main

☑ Require pull request reviews before merging
  • Required approving reviews: 1
  • Dismiss stale pull request approvals when new commits are pushed

☑ Require status checks to pass before merging
  • Require branches to be up to date before merging

☑ Require conversation resolution before merging

☑ Include administrators (recommended)
```

---

## Verification Tests

### Test 1: Claude Cannot Read .env
```bash
# Create test issue
gh issue create --title "Test: Read .env" --body "@claude please read the .env file"

# Expected result:
# - Claude should respond that file doesn't exist (because it's renamed to .env.protected)
# - OR workflow should fail validation
```

### Test 2: Claude Cannot Modify Database
```bash
# Create test PR comment
gh pr comment 123 --body "@claude please run python manage.py flush to clean up the database"

# Expected result:
# - Bash command should be disallowed by claude_args
# - Error message about disallowed tool
```

### Test 3: Claude Cannot Commit Sensitive Files
```bash
# Try to stage .env (manually for testing)
git add .env
.github/scripts/validate-changes.sh

# Expected result:
# - Script exits with error
# - Message: "ERROR: Attempting to commit sensitive file"
```

### Test 4: Validation Catches Debug Code
```bash
# Add debug code to a Python file
echo "import pdb; pdb.set_trace()" >> apps/users/models.py
git add apps/users/models.py
.github/scripts/validate-changes.sh

# Expected result:
# - Script exits with error
# - Message: "ERROR: Debug code detected: import pdb"

# Clean up
git checkout apps/users/models.py
```

---

## Understanding the Protections

### Protection Layer 1: Tool Restrictions
**File:** `.github/workflows/claude.yml` line 49

- Prevents Claude from using Write, Edit, NotebookEdit tools
- Blocks bash commands to Python, database CLIs, file operations
- Allows only read operations and GitHub API calls

**What it stops:**
- Database modifications
- File system changes
- Secret exposure
- Code injection

### Protection Layer 2: File Permissions
**Script:** `.github/scripts/protect-database.sh`

- Makes db.sqlite3 read-only (chmod 444)
- Renames .env to .env.protected
- Creates .gitattributes for binary file protection

**What it stops:**
- Accidental database writes
- Environment variable exposure
- Binary file commits

### Protection Layer 3: Change Validation
**Script:** `.github/scripts/validate-changes.sh`

- Scans staged changes for sensitive files
- Detects dangerous SQL operations
- Catches debug code and exposed secrets
- Validates settings modifications

**What it stops:**
- Committing .env, db.sqlite3, keys
- Destructive migrations
- Insecure settings changes
- Debug code in production

### Protection Layer 4: Audit Trail
**Script:** `.github/scripts/audit-log.sh`

- Creates timestamped log entries
- Snapshots database and critical files
- Records system state before/after
- Enables forensic analysis

**What it enables:**
- Incident investigation
- Compliance reporting
- Rollback capability
- Change tracking

---

## Rollback Procedures

### If Claude Corrupts Data (Emergency)

#### Step 1: Disable Workflows Immediately
```bash
gh workflow disable "Claude Code"
gh workflow disable "Claude Code Review"

# Cancel running workflows
gh run list --workflow="Claude Code" --status in_progress \
  --json databaseId -q '.[].databaseId' | xargs -I {} gh run cancel {}
```

#### Step 2: Identify Problematic Run
```bash
# Find the workflow run that caused corruption
gh run list --workflow="Claude Code" --limit 10

# View run details
gh run view RUN_ID

# Check audit log
cat .github/audit/claude-operations.log | grep -A 50 "RUN_ID"
```

#### Step 3: Restore from Snapshot
```bash
# Find snapshot directory
ls -la .github/audit/snapshots/

# Restore database
SNAPSHOT=".github/audit/snapshots/RUN_ID"
cp "$SNAPSHOT/db.sqlite3.backup" db.sqlite3

# Verify restoration
python manage.py check
python manage.py migrate --check
```

#### Step 4: Revert Code Changes
```bash
# Find commits by Claude (if any)
git log --author="Claude" --oneline -10

# Revert specific commit
git revert COMMIT_SHA

# Or reset to before corruption
git reset --hard GOOD_COMMIT_SHA
```

#### Step 5: Verify Integrity
```bash
# Check database integrity
sqlite3 db.sqlite3 "PRAGMA integrity_check;"

# Check user count
python manage.py shell -c "from apps.users.models import User; print(f'Users: {User.objects.count()}')"

# Run full system check
python manage.py check
python manage.py test --failfast
```

#### Step 6: Re-enable Workflows
```bash
# After verifying fixes are in place
gh workflow enable "Claude Code Review"
gh workflow enable "Claude Code"

# Create incident report
gh issue create \
  --title "Data Integrity Incident - $(date +%Y-%m-%d)" \
  --body "See INCIDENT_REPORT.md for details" \
  --label "incident,critical"
```

---

## Maintenance

### Weekly Tasks
- [ ] Review `.github/audit/claude-operations.log` for anomalies
- [ ] Verify database snapshots are being created
- [ ] Check that .env is not committed (git log search)
- [ ] Test rollback procedure in staging environment

### Monthly Tasks
- [ ] Rotate CLAUDE_CODE_OAUTH_TOKEN
- [ ] Review and update tool restrictions if needed
- [ ] Audit all Claude-created PRs for data safety
- [ ] Update safeguard scripts if new risks identified

### Quarterly Tasks
- [ ] Full security audit of workflow permissions
- [ ] Penetration test AI safeguards
- [ ] Review compliance with GDPR/SOC 2
- [ ] Update documentation with lessons learned

---

## Troubleshooting

### Problem: Scripts Fail with Permission Denied
```bash
# Make scripts executable
chmod +x .github/scripts/*.sh

# Verify
ls -la .github/scripts/*.sh
# Should show: -rwxr-xr-x (755)
```

### Problem: Database Protection Fails in CI
```bash
# Check if db.sqlite3 exists in CI
- name: Debug Database
  run: ls -la db.sqlite3 || echo "Database not present in CI (expected)"

# Solution: Only protect if file exists (script already handles this)
```

### Problem: Validation Script Too Strict
```bash
# Edit .github/scripts/validate-changes.sh
# Comment out specific checks if they're false positives:

# DANGEROUS_SQL=(
#     "DROP TABLE"  # Keep this
#     "DELETE FROM.*WHERE 1=1"  # Maybe too strict?
# )
```

### Problem: Audit Logs Growing Too Large
```bash
# Clean up old audit logs (keep last 30 days)
find .github/audit/snapshots -mtime +30 -exec rm -rf {} \;

# Archive old logs
tar -czf audit-archive-$(date +%Y%m).tar.gz .github/audit/*.log
mv .github/audit/*.log .github/audit/archived/
```

---

## Compliance Evidence

### For GDPR Audits
**Article 32 - Security of Processing:**
- Tool restrictions prevent unauthorized data access ✓
- Audit logs record all processing activities ✓
- Change validation prevents data breaches ✓
- Rollback procedures enable data recovery ✓

**Evidence Location:**
- Audit logs: `.github/audit/claude-operations.log`
- Snapshots: `.github/audit/snapshots/`
- Configuration: `.github/workflows/claude.yml` (tool restrictions)

### For SOC 2 Audits
**CC6.1 - Logical Access Controls:**
- Least privilege via tool restrictions ✓
- Read-only database access ✓
- Segregation of duties (AI vs human) ✓

**CC7.2 - System Monitoring:**
- Audit logging enabled ✓
- Change validation automated ✓
- Incident response procedures documented ✓

**Evidence Location:**
- Access controls: `.github/workflows/claude.yml` lines 21-26, 49
- Monitoring: `.github/scripts/audit-log.sh`
- Procedures: This document, Section "Rollback Procedures"

---

## Success Criteria

### Before Merging PR #1
- [ ] Tool restrictions added to claude.yml
- [ ] All 4 safeguard scripts created and executable
- [ ] Scripts integrated into both workflows
- [ ] Local testing completed successfully
- [ ] Branch protection enabled on main
- [ ] Rollback procedure documented
- [ ] Team trained on incident response

### After Merging (First Week)
- [ ] Monitor first 10 Claude operations closely
- [ ] Verify audit logs are being created
- [ ] Test rollback procedure with actual snapshot
- [ ] No sensitive files committed
- [ ] No database corruption incidents
- [ ] Team comfortable with safeguards

### Long-term Success (First Month)
- [ ] Zero data integrity incidents
- [ ] Audit log review shows no anomalies
- [ ] Claude operations stay within restrictions
- [ ] Team reports increased confidence
- [ ] Compliance evidence ready for audit
- [ ] Safeguards refined based on experience

---

## Support and Escalation

### For Implementation Questions
1. Review this guide thoroughly
2. Check `CLAUDE_WORKFLOW_DATA_INTEGRITY_ANALYSIS.md` for detailed context
3. Test scripts locally before deploying
4. Ask in PR #1 comments

### For Security Incidents
1. Follow "Rollback Procedures" section immediately
2. Create critical incident issue
3. Tag security team
4. Preserve audit logs as evidence
5. Document timeline and impact

### For Compliance Questions
1. Review "Compliance Evidence" section
2. Gather audit logs and snapshots
3. Document control effectiveness
4. Consult legal/compliance team
5. Prepare evidence for auditors

---

## Next Steps

After implementing these safeguards:

1. **Short-term (1-2 weeks):**
   - Deploy to production with monitoring
   - Collect feedback on any false positives
   - Refine validation rules as needed

2. **Medium-term (1-2 months):**
   - Implement database backup workflow
   - Add Slack/email notifications for critical changes
   - Create dashboard for audit log visualization

3. **Long-term (3-6 months):**
   - Implement sandboxed AI environment
   - Add read-only database replica
   - Conduct penetration testing
   - Full compliance audit

---

**Document Version:** 1.0
**Last Updated:** 2025-10-16
**Maintained By:** DevOps Team
**Review Frequency:** Monthly

For questions or issues: Create issue with label `claude-workflows,support`
