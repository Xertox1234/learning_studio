---
status: pending
priority: p2
issue_id: "029"
tags: [deployment, devops, phase4, documentation]
dependencies: [028]
---

# Deployment Preparation & Documentation (Phase 4)

## Problem Statement

After completing all P1 fixes and integration testing, we need comprehensive deployment preparation to ensure safe, successful production rollout. This includes migration planning, documentation updates, rollback procedures, and monitoring setup.

**Category**: DevOps / Deployment
**Severity**: High (P2) - Required for production
**Dependencies**: Integration testing (Todo #028) must pass

## Findings

**Context**: End of Phase 4 (Day 8)

**Changes to Deploy**:
- 9 critical P1 fixes implemented
- 3 new database migrations (soft delete, CASCADE→SET_NULL, indexes)
- 2 frontend changes (skip nav, CodeMirror keyboard nav)
- 1 major refactoring (wagtail.py modularization)
- Type hints added (90%+ coverage)

**Deployment Risks**:
- Database migrations on large tables (users, posts, topics)
- Soft delete changes default User queryset
- CASCADE→SET_NULL requires data migration
- wagtail.py refactoring needs gradual rollout

## Proposed Solutions

### Option 1: Comprehensive Deployment Plan (RECOMMENDED)

**Phases**:
1. Pre-deployment checklist
2. Migration dry-run on staging
3. Feature flag configuration
4. Monitoring setup
5. Deployment execution
6. Post-deployment verification
7. Rollback procedures

**Pros**:
- Minimizes production risk
- Clear rollback path
- Comprehensive verification
- Documented for future deploys

**Cons**: Time-intensive preparation (4 hours)

**Effort**: 4 hours
**Risk**: Low (planning only)

**Implementation**:

**Phase 1: Pre-Deployment Checklist**

```markdown
# File: docs/DEPLOYMENT_CHECKLIST.md (NEW)

# Deployment Checklist - P1 Fixes Rollout

## Pre-Deployment (T-24 hours)

### Code Preparation
- [ ] All 9 P1 todos marked as complete
- [ ] Integration test suite passes (100%)
- [ ] Security regression tests pass
- [ ] Performance benchmarks meet targets
- [ ] Type checking passes (mypy)
- [ ] All linting passes (flake8, eslint)

### Database Preparation
- [ ] Migration files reviewed by team
- [ ] Migration dry-run on staging complete
- [ ] Data backup verified (last 7 days)
- [ ] Migration rollback scripts prepared
- [ ] Estimated migration time documented

### Feature Flags
- [ ] USE_MODULAR_WAGTAIL_VIEWS=False (gradual rollout)
- [ ] ENABLE_SOFT_DELETE=True
- [ ] ENABLE_KEYBOARD_NAV=True

### Documentation
- [ ] CHANGELOG.md updated with all changes
- [ ] CLAUDE.md updated with new patterns
- [ ] API documentation updated (if applicable)
- [ ] Migration notes documented

### Monitoring
- [ ] Sentry error tracking configured
- [ ] Database query monitoring enabled
- [ ] Performance metrics baseline established
- [ ] Alert thresholds configured

## Deployment (T-0)

### Step 1: Enable Maintenance Mode
```bash
# Set maintenance page
touch /var/www/maintenance.html
```

### Step 2: Backup Database
```bash
pg_dump learning_studio_prod > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Step 3: Deploy Code
```bash
git pull origin main
pip install -r requirements.txt
npm install && npm run build
```

### Step 4: Run Migrations (Monitor Closely)
```bash
# Migration 1: Add soft delete fields (~30 seconds)
python manage.py migrate users 0XXX_add_soft_delete

# Migration 2: Change CASCADE to SET_NULL (~5-10 minutes on large tables)
python manage.py migrate forum_integration 0XXX_change_cascade_to_set_null

# Migration 3: Add indexes (~2-3 minutes)
python manage.py migrate learning 0XXX_add_performance_indexes
```

### Step 5: Restart Services
```bash
sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart nginx
```

### Step 6: Smoke Tests
```bash
# Health check
curl https://pythonlearning.studio/api/v1/health/

# Authentication test
curl -X POST https://pythonlearning.studio/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}'

# Forum test
curl https://pythonlearning.studio/api/v1/forums/

# Accessibility test (manual)
# - Load homepage
# - Press Tab → skip link should appear
# - Navigate to exercise
# - Tab through fill-in-blanks
```

### Step 7: Disable Maintenance Mode
```bash
rm /var/www/maintenance.html
```

## Post-Deployment (T+1 hour)

### Monitoring Checks
- [ ] Sentry: No new errors (check last 1 hour)
- [ ] Database: Query performance normal
- [ ] Response times: P95 < 500ms
- [ ] Error rate: < 0.1%
- [ ] User complaints: None

### Functional Verification
- [ ] User login/signup works
- [ ] Course enrollment works (no duplicates)
- [ ] Forum posting works (content preserved)
- [ ] Exercise submission works (keyboard nav)
- [ ] Blog loads correctly (wagtail.py refactor)

### Data Integrity Checks
```sql
-- Verify soft delete fields exist
SELECT COUNT(*) FROM auth_user WHERE is_deleted = false;

-- Verify CASCADE→SET_NULL migration
SELECT COUNT(*) FROM forum_topic WHERE poster_id IS NULL;
SELECT COUNT(*) FROM forum_post WHERE poster_id IS NULL;

-- Verify no .extra() usage (grep codebase)
grep -r "\.extra(" apps/ --include="*.py"
```

## Rollback Procedures

### If Critical Issue Detected

#### Step 1: Enable Maintenance Mode Immediately
```bash
touch /var/www/maintenance.html
```

#### Step 2: Restore Previous Code
```bash
git checkout <previous-commit-hash>
pip install -r requirements.txt
npm install && npm run build
sudo systemctl restart gunicorn
```

#### Step 3: Rollback Migrations (If Needed)
```bash
# Rollback in reverse order
python manage.py migrate learning 0XXX_previous_migration
python manage.py migrate forum_integration 0XXX_previous_migration
python manage.py migrate users 0XXX_previous_migration
```

#### Step 4: Restore Database (Last Resort)
```bash
psql learning_studio_prod < backup_YYYYMMDD_HHMMSS.sql
```

#### Step 5: Verify Rollback
- [ ] Health check passes
- [ ] Authentication works
- [ ] Critical features functional
- [ ] Sentry errors cleared

## Success Criteria

Deployment considered successful when:
- ✅ All smoke tests pass
- ✅ No new Sentry errors (1 hour window)
- ✅ Response times within SLA (P95 < 500ms)
- ✅ Error rate < 0.1%
- ✅ Zero user-reported issues (4 hour window)
- ✅ All integration tests pass in production
```

**Phase 2: Migration Dry-Run Script**

```python
# File: scripts/migration_dry_run.py (NEW)
"""
Dry-run migration script for staging environment.

Tests all migrations on staging database with production-like data.
"""

import subprocess
import time
from django.core.management import call_command
from django.db import connection

def run_migration_dry_run():
    """Run all new migrations and measure performance."""

    migrations = [
        ('users', '0XXX_add_soft_delete'),
        ('forum_integration', '0XXX_change_cascade_to_set_null'),
        ('learning', '0XXX_add_performance_indexes'),
    ]

    results = []

    for app, migration in migrations:
        print(f"\n{'='*60}")
        print(f"Testing: {app}.{migration}")
        print('='*60)

        # Measure migration time
        start_time = time.time()

        try:
            # Run migration
            call_command('migrate', app, migration, verbosity=2)

            elapsed_time = time.time() - start_time

            # Check affected rows
            with connection.cursor() as cursor:
                if app == 'users':
                    cursor.execute("SELECT COUNT(*) FROM auth_user WHERE is_deleted IS NOT NULL")
                elif app == 'forum_integration':
                    cursor.execute("SELECT COUNT(*) FROM forum_post WHERE poster_username != ''")

                affected_rows = cursor.fetchone()[0]

            results.append({
                'migration': f"{app}.{migration}",
                'time': elapsed_time,
                'affected_rows': affected_rows,
                'status': 'SUCCESS'
            })

            print(f"✅ SUCCESS: {elapsed_time:.2f}s, {affected_rows} rows affected")

        except Exception as e:
            results.append({
                'migration': f"{app}.{migration}",
                'time': None,
                'affected_rows': None,
                'status': 'FAILED',
                'error': str(e)
            })

            print(f"❌ FAILED: {e}")

    # Print summary
    print("\n" + "="*60)
    print("MIGRATION DRY-RUN SUMMARY")
    print("="*60)

    for result in results:
        status_emoji = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"{status_emoji} {result['migration']}: {result['time']:.2f}s")

    total_time = sum(r['time'] for r in results if r['time'])
    print(f"\nTotal migration time: {total_time:.2f}s")

if __name__ == '__main__':
    run_migration_dry_run()
```

**Phase 3: Update Documentation**

```markdown
# File: CHANGELOG.md (UPDATE)

## [Unreleased] - 2025-10-20

### Security
- **CRITICAL**: Fixed SQL injection vulnerability via Django .extra() (CVE-2025-SQL-001)
- Added comprehensive security regression test suite (79 tests)

### Fixed
- **CRITICAL**: Fixed mutable default in JSONField causing data corruption
- **CRITICAL**: Fixed enrollment race condition (duplicate enrollments)
- **CRITICAL**: Fixed CASCADE deletes destroying community content
- **CRITICAL**: Fixed forum pagination OOM risk (100x memory reduction)

### Added
- Soft delete infrastructure for user accounts (GDPR compliant)
- Skip navigation link for keyboard users (WCAG 2.1 Level A)
- Keyboard navigation for fill-in-blank exercises (WCAG 2.1 Level A)
- Type hints across entire Python codebase (90%+ coverage)
- Comprehensive integration test suite (5 suites, 50+ tests)

### Changed
- Refactored wagtail.py monolith (Phase 1: blog module extracted)
- Changed 90 CASCADE deletes to SET_NULL (preserves community content)
- Enrollment flow now uses atomic transactions (prevents duplicates)

### Performance
- **6-30x faster** blog/course/exercise listings (N+1 query fixes)
- **100x reduction** in forum pagination memory usage
- Database indexes added for 50-100x query performance

### Deployment Notes
- **Database migrations required** (estimated 10-15 minutes downtime)
- Feature flag USE_MODULAR_WAGTAIL_VIEWS for gradual rollout
- Soft delete changes default User queryset (test compatibility)
- See DEPLOYMENT_CHECKLIST.md for full procedure
```

```markdown
# File: CLAUDE.md (UPDATE - add new section)

## Recent Updates (2025-10-20)

### Critical P1 Fixes Deployed

**Security**:
- SQL injection via .extra() eliminated (CVE-2025-SQL-001)
- Security regression suite (79 tests, 100% passing)

**Data Integrity**:
- Soft delete infrastructure (GDPR compliant)
- CASCADE→SET_NULL for community content preservation
- Enrollment race condition fixed (atomic transactions)

**Accessibility**:
- Skip navigation link (WCAG 2.1 Level A)
- CodeMirror keyboard navigation (WCAG 2.1 Level A)

**Performance**:
- Forum pagination: 500MB → 5MB memory (100x reduction)
- N+1 queries fixed: 30-1,500 queries → 3-12 queries (6-30x faster)

**Code Quality**:
- Type hints: 0% → 90% coverage
- wagtail.py refactored: 51,489 lines → modular structure
- Integration test suite: 5 suites, 50+ tests

### New Patterns to Follow

**Soft Delete Pattern**:
```python
# Use soft_delete() instead of delete()
user.soft_delete(reason='GDPR request')
user.anonymize_personal_data()

# Query soft-deleted users
User.all_objects.filter(is_deleted=True)
```

**Type Hints Standard**:
```python
from typing import Optional, List, Dict, Any
from django.http import HttpRequest, HttpResponse

def view_function(request: HttpRequest) -> HttpResponse:
    """View with full type hints."""
    pass
```

**Atomic Transactions for Critical Operations**:
```python
from django.db import transaction

@transaction.atomic
def critical_operation(request):
    # Lock rows, prevent race conditions
    obj = Model.objects.select_for_update().get(id=pk)
    # ... safe operations
```
```

## Recommended Action

✅ **Option 1** - Comprehensive deployment plan with rollback procedures

## Technical Details

**Files to Create**:
- `docs/DEPLOYMENT_CHECKLIST.md` (NEW)
- `scripts/migration_dry_run.py` (NEW)

**Files to Update**:
- `CHANGELOG.md` (document all changes)
- `CLAUDE.md` (new patterns and updates)

## Acceptance Criteria

- [ ] Deployment checklist created
- [ ] Migration dry-run script created
- [ ] Dry-run executed on staging (successful)
- [ ] CHANGELOG.md updated
- [ ] CLAUDE.md updated
- [ ] Feature flags configured
- [ ] Rollback procedures documented
- [ ] Monitoring dashboards configured
- [ ] Team review of deployment plan complete

## Resources

- Django migrations: https://docs.djangoproject.com/en/5.0/topics/migrations/
- Zero-downtime deploys: https://docs.djangoproject.com/en/5.0/howto/deployment/
- Feature flags: https://www.martinfowler.com/articles/feature-toggles.html

## Work Log

### 2025-10-20 - Phase 4 Planning
**By:** Claude Code Review System
**Actions:**
- Designed comprehensive deployment plan
- Created migration dry-run script
- Documented rollback procedures
- Categorized as P2 (deployment gate)

**Learnings:**
- Deployment preparation prevents production issues
- Migration dry-runs catch problems early
- Clear rollback path reduces risk

## Notes

- This is a **deployment preparation** task
- **Required for production rollout**
- Moderate complexity (4 hours)
- Low risk (planning/documentation)
- Should be completed in Phase 4 (Day 8)
- Execute dry-run on staging before production
