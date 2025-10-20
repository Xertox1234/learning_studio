---
status: ready
priority: p2
issue_id: "017"
tags: [code-quality, technical-debt, data-accuracy]
dependencies: []
source: Code Triage (TODO/FIXME comments)
discovered: 2025-10-19
---

# Fix Hardcoded Statistics in Home View

## Problem Statement

The home page view displays hardcoded statistics instead of calculating actual values from the database. This misleads visitors about platform usage and becomes increasingly inaccurate over time.

**Location**: `apps/learning/views.py:16-24`

**Current Code**:
```python
def home_view(request):
    """Home page view with platform overview."""
    context = {
        'total_courses': Course.objects.filter(is_published=True).count(),
        'total_exercises': Exercise.objects.filter(is_published=True).count(),
        'total_users': 10000,  # ❌ This would be calculated from real user data
        'success_rate': 94,    # ❌ Hardcoded - should be calculated
    }
    return render(request, 'base/home.html', context)
```

**Impact**:
- **Credibility**: Visitors see fake statistics, undermining trust
- **Accuracy**: Numbers never reflect actual platform usage
- **Misleading**: Could show "10,000 users" when there are only 10 real users
- **Inconsistency**: Courses/exercises are real, but users/success_rate are fake
- **Marketing**: Can't showcase actual platform growth and success

## Findings

**Discovered by**: Code Triage (TODO comment scan)

**Hardcoded Values Found**:
1. **total_users: 10000** (line 21)
   - Comment: "This would be calculated from real user data"
   - Should use Django User model count

2. **success_rate: 94** (line 22)
   - No comment explaining it's hardcoded
   - Should calculate from exercise completion data

**Why This Matters**:
- Home page is first impression for new visitors
- Statistics provide social proof and platform credibility
- Investors/stakeholders may rely on these metrics
- Real data drives better product decisions

## Proposed Solutions

### Option 1: Calculate Both Statistics (RECOMMENDED)

**Pros**:
- Shows real, accurate platform metrics
- Builds trust with transparent data
- Enables tracking actual growth
- Consistent with courses/exercises counts

**Cons**:
- Adds 2 database queries to home page load
- Need to decide on success_rate calculation logic

**Effort**: Medium (30 minutes)
**Risk**: Low (simple queries with caching option)

**Implementation**:
```python
from django.contrib.auth import get_user_model
from django.db.models import Avg, Q

User = get_user_model()

def home_view(request):
    """Home page view with platform overview."""

    # Calculate success rate from exercise submissions
    # Success = submissions marked as correct/passed
    from apps.learning.models import ExerciseSubmission

    total_submissions = ExerciseSubmission.objects.count()
    if total_submissions > 0:
        successful_submissions = ExerciseSubmission.objects.filter(
            is_correct=True
        ).count()
        success_rate = int((successful_submissions / total_submissions) * 100)
    else:
        success_rate = 0  # No submissions yet

    context = {
        'total_courses': Course.objects.filter(is_published=True).count(),
        'total_exercises': Exercise.objects.filter(is_published=True).count(),
        'total_users': User.objects.filter(is_active=True).count(),  # ✅ Real data
        'success_rate': success_rate,  # ✅ Calculated from submissions
    }
    return render(request, 'base/home.html', context)
```

### Option 2: Calculate Users Only, Cache Success Rate

**Pros**:
- Fixes the more obvious issue (user count)
- Success rate calculation more complex, can defer
- Simple, quick fix

**Cons**:
- Still leaves one hardcoded stat
- Inconsistent approach (some real, some fake)

**Effort**: Small (10 minutes)
**Risk**: Low

**Implementation**:
```python
from django.contrib.auth import get_user_model

User = get_user_model()

def home_view(request):
    """Home page view with platform overview."""
    context = {
        'total_courses': Course.objects.filter(is_published=True).count(),
        'total_exercises': Exercise.objects.filter(is_published=True).count(),
        'total_users': User.objects.filter(is_active=True).count(),  # ✅ Real data
        'success_rate': 94,  # TODO: Calculate from exercise completion data
    }
    return render(request, 'base/home.html', context)
```

### Option 3: Add Caching for Performance

**Pros**:
- Real statistics without performance penalty
- Home page stays fast under high traffic
- Can use Django's cache framework

**Cons**:
- More complex implementation
- Cache invalidation needed on user/submission changes
- May be premature optimization

**Effort**: Large (1-2 hours)
**Risk**: Medium (cache invalidation complexity)

**Implementation**:
```python
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()

def home_view(request):
    """Home page view with platform overview."""

    # Try cache first (5-minute TTL)
    stats = cache.get('home_page_stats')

    if stats is None:
        # Calculate and cache
        stats = {
            'total_courses': Course.objects.filter(is_published=True).count(),
            'total_exercises': Exercise.objects.filter(is_published=True).count(),
            'total_users': User.objects.filter(is_active=True).count(),
            'success_rate': _calculate_success_rate(),
        }
        cache.set('home_page_stats', stats, 300)  # 5 minutes

    return render(request, 'base/home.html', stats)
```

## Recommended Action

**Start with Option 2** (users only), then enhance to Option 1 when success rate calculation is defined.

**Reasoning**:
1. User count is straightforward and unambiguous
2. Success rate calculation needs product decision (what counts as "success"?)
3. Option 3 (caching) can be added later if performance becomes an issue
4. Quick win to fix the most obvious fake statistic

## Technical Details

**Affected Files**:
- `apps/learning/views.py:16-24` (home_view function)
- `templates/base/home.html` (displays statistics)

**Related Components**:
- Django User model (via `get_user_model()`)
- ExerciseSubmission model (for success_rate calculation)
- Potential: CourseEnrollment model (alternative success metric)

**Database Changes**: None required

**Performance Considerations**:
- User count query: `SELECT COUNT(*) FROM auth_user WHERE is_active = TRUE`
- Success rate query: 2 COUNT queries on ExerciseSubmission table
- Total added queries: 1-3 depending on option chosen
- Consider caching if home page traffic > 100 req/min

**Success Rate Calculation Options**:
1. **Exercise submissions**: % of correct submissions
2. **Course completions**: % of users who complete enrolled courses
3. **User activity**: % of users active in last 30 days
4. **Hybrid**: Weighted average of multiple metrics

**Recommendation**: Start with exercise submissions (simplest, most direct)

## Acceptance Criteria

- [ ] `total_users` shows actual count from User model
- [ ] Only active users counted (`is_active=True`)
- [ ] `success_rate` either calculated or has clear TODO comment
- [ ] Home page loads without errors
- [ ] Statistics update when users/submissions change
- [ ] Manual verification shows realistic numbers
- [ ] No performance regression (home page < 200ms load time)
- [ ] Consider caching if needed for scale

## Work Log

### 2025-10-19 - Initial Discovery

**By:** Claude Triage System
**Actions:**
- Issue discovered during TODO/FIXME comment scan
- Found 2 hardcoded statistics in home view
- Categorized as P2 (Important) - data accuracy issue
- Estimated effort: Medium (30 minutes for full fix)
- Marked as ready to pick up

**Learnings:**
- Hardcoded statistics undermine platform credibility
- Home page is critical first impression - needs real data
- Success rate calculation requires product decision
- Start simple (user count), enhance later (success rate)

## Notes

- This affects first impression for all new visitors
- Consider adding unit tests for statistics calculations
- Future enhancement: Add trends (growth over time)
- Consider A/B testing: do statistics increase sign-ups?

## Follow-up Tasks

After implementing this fix, consider:
1. Add statistics dashboard for admins
2. Track metrics over time (daily/weekly/monthly)
3. Add more meaningful metrics (completion rate, avg time to complete, etc.)
4. Cache statistics with 5-minute TTL for performance
5. Add Prometheus/Grafana monitoring for real-time stats

## References

- **File**: `apps/learning/views.py`
- **Function**: `home_view` (line 16)
- **Template**: `templates/base/home.html`
- **Django Docs**: [get_user_model()](https://docs.djangoproject.com/en/stable/topics/auth/customizing/#django.contrib.auth.get_user_model)
- **Caching**: [Django Cache Framework](https://docs.djangoproject.com/en/stable/topics/cache/)
