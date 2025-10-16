# Headless Wagtail Migration - Progress Notes

**Date Started**: October 13, 2025
**Status**: In Progress - Phase 3

## Completed Phases

### ✅ Phase 1: Removed Duplicate Django Template Routes
**File Modified**: `learning_community/urls.py`

**Changes**:
- Commented out imports for old Django view functions
- Disabled URL routes for:
  - `/courses/` (Django template)
  - `/exercises/` (Django template)
  - `/dashboard/` (Django template)
  - `/my-courses/` (Django template)
  - `/community/` (Django template)
  - `/code-playground/` (Django template)

**Impact**: These routes now fall through to Wagtail catch-all or will 404. React frontend handles them instead.

---

### ✅ Phase 2: Decoupled Forum from Django-Machina Templates
**File Modified**: `learning_community/urls.py`

**Changes**:
- Disabled `path('forum/', include('apps.forum_integration.forum_urls'))`
- Forum is now 100% API-driven through React SPA
- Django-machina models and admin still functional for data management
- Forum templates no longer served

**Impact**: Forum accessible ONLY through React at `/forum` route. API endpoints at `/api/v1/forums/` still active.

---

## Current Phase

### 🔄 Phase 3: Remove Webpack & Consolidate to Vite
**Status**: In Progress

**Plan**:
1. Remove webpack.config.js
2. Update root package.json (remove webpack dependencies)
3. Remove bundled files from static/js/dist/
4. Upgrade frontend to React 19 for consistency
5. Update Django to serve React build from static/react/

---

## Active Routes After Migration

### React SPA Routes (Frontend)
- `/` - HomePage
- `/forum` - ForumPage (headless)
- `/forum/:slug/:id` - ForumDetailPage
- `/forum/topics/:slug/:id` - ForumTopicPage
- `/courses` - WagtailCoursesPage
- `/courses/:slug` - WagtailCourseDetailPage
- `/exercises` - WagtailExerciseListPage
- `/exercises/:slug` - WagtailExercisePage
- `/blog` - BlogPage
- `/blog/:slug` - BlogPostPage
- `/dashboard` - DashboardPage

### Django Backend Routes (API Only)
- `/api/v1/` - All API endpoints
- `/admin/` - Wagtail CMS admin
- `/django-admin/` - Django admin
- `/accounts/` - Authentication (allauth)
- `/login/`, `/register/` - React auth pages

### Legacy Routes (Kept for Testing)
- `/playground/` - Code playground (Django template)
- `/test-exercise/`, `/test-editor/`, `/simple-test/` - Test pages

---

## Testing Checklist

After each phase, verify:
- [ ] Django server starts without errors
- [ ] React dev server starts without errors
- [ ] API endpoints respond correctly
- [ ] Wagtail admin accessible
- [ ] Forum pages load in React
- [ ] Course pages load in React
- [ ] Exercise pages load in React
- [ ] Authentication works

---

## Rollback Instructions

If issues arise:

```bash
# Phase 1 & 2 Rollback
git checkout learning_community/urls.py

# Phase 3 Rollback
git checkout webpack.config.js package.json
```

---

## Next Steps

1. Complete Phase 3 (Webpack removal)
2. Phase 4: Configure Django catch-all for React SPA
3. Phase 5: Archive old templates, update documentation
