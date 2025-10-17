# Forum React Query Migration - Manual Testing Guide

**Created:** 2025-10-15
**Purpose:** Verify all 6 migrated forum pages work correctly with React Query
**Estimated Time:** 45-60 minutes

---

## Prerequisites

### 1. Start Both Servers

**Terminal 1 - Django Backend:**
```bash
cd /Users/williamtower/projects/learning_studio
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py runserver
```
Expected: Server running on http://localhost:8000

**Terminal 2 - React Frontend:**
```bash
cd /Users/williamtower/projects/learning_studio/frontend
npm run dev
```
Expected: Server running on http://localhost:3000 or http://localhost:3001

### 2. Test User Credentials

**Admin User (TL4 - Full Moderation):**
- Email: `test@pythonlearning.studio`
- Password: `testpass123`

**Create Additional Test Users:**
```bash
# TL0 user (new user, needs moderation)
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.create_user('newuser', 'newuser@test.com', 'testpass123')
>>> user.trust_level = None
>>> user.save()
```

### 3. Sample Data

**Create Sample Forums (if needed):**
```bash
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py create_sample_forums
```

---

## Testing Checklist

### ✅ Page 1: ForumPage.jsx - Forum List

**Location:** http://localhost:3000/forum

#### Test 1.1: Initial Load
- [ ] Page loads without errors
- [ ] Forum categories display correctly
- [ ] Forum statistics show (topics, posts, users, online users)
- [ ] Each forum shows topic count and post count
- [ ] "Last Post" information appears for forums with activity

**Expected Behavior:**
- React Query caches the data (check React Query Devtools)
- Skeleton loaders appear during initial load
- No duplicate network requests (check Network tab)

#### Test 1.2: React Query Caching
- [ ] Navigate to a forum, then click "Back to Forums"
- [ ] Forum list appears **instantly** (from cache)
- [ ] Data refetches in background (check Network tab)

**Expected Behavior:**
- Instant display from cache
- Background refetch after 5 minutes (stale time)

#### Test 1.3: Error Handling
- [ ] Stop Django server
- [ ] Refresh the forum page
- [ ] Error message displays with "Try Again" and "Refresh" buttons

**Expected Behavior:**
- User-friendly error message
- Retry options available

---

### ✅ Page 2: ForumDetailPage.jsx - Topic List

**Location:** http://localhost:3000/forum/{forum-slug}/{forum-id}

#### Test 2.1: Topic List Display
- [ ] Topics display in correct order (Latest Activity by default)
- [ ] Each topic shows: title, author, creation date, reply count, view count
- [ ] Last post information appears
- [ ] Pinned topics appear first (with pin badge)
- [ ] Locked topics show lock badge

#### Test 2.2: Search & Filter
- [ ] Enter text in search box
- [ ] Topics filter in real-time
- [ ] Change sort order (Latest Activity, Date Created, Most Replies, Most Views)
- [ ] Sorting updates the list correctly

**Expected Behavior:**
- Client-side filtering (no API calls for search)
- Smooth, instant updates

#### Test 2.3: Create New Topic (Authenticated)
- [ ] Log in as test user
- [ ] Click "New Topic" button
- [ ] Verify redirect to topic creation page with `?forum={id}` parameter

#### Test 2.4: Pagination
- [ ] If forum has >20 topics, verify pagination appears
- [ ] Click next page
- [ ] Topics load correctly

**Expected Behavior:**
- React Query caches each page separately
- Navigation between cached pages is instant

---

### ✅ Page 3: TopicCreatePage.jsx - Create Topic

**Location:** http://localhost:3000/forum/topics/create?forum={forum-id}

#### Test 3.1: Form Validation
- [ ] Try to submit empty form
- [ ] Error message: "Please enter a subject"
- [ ] Enter subject only, try to submit
- [ ] Error message: "Please enter some content"

#### Test 3.2: Create Normal Topic
- [ ] Fill in subject: "Test Topic - React Query Migration"
- [ ] Fill in content: "This is a test topic to verify React Query works correctly."
- [ ] Select Topic Type: "Normal Topic"
- [ ] Click "Create Topic"

**Expected Behavior:**
- Loading state: Button shows "Creating..."
- Success toast: "Topic created successfully!"
- Redirect to new topic page
- React Query invalidates forum list and topic list caches

#### Test 3.3: Verify Cache Invalidation
- [ ] Navigate back to forum list
- [ ] New topic appears in the list
- [ ] Topic count incremented
- [ ] Post count incremented

#### Test 3.4: Cancel Creation
- [ ] Start creating a topic
- [ ] Click "Cancel"
- [ ] Verify redirect back to forum list
- [ ] No topic created

---

### ✅ Page 4: ForumTopicPage.jsx - Topic Detail

**Location:** http://localhost:3000/forum/topics/{forum-slug}/{forum-id}/{topic-slug}/{topic-id}

#### Test 4.1: Topic Display
- [ ] Topic title displays correctly
- [ ] Topic metadata shows (author, creation date, reply count, views)
- [ ] All posts display in order
- [ ] First post is the topic content
- [ ] Breadcrumb navigation works

#### Test 4.2: Post Actions (Authenticated)
- [ ] Hover over your own post
- [ ] Three-dot menu appears
- [ ] "Edit" option available
- [ ] "Delete" option available

#### Test 4.3: Delete Post
- [ ] Click "Delete" on a post
- [ ] Confirmation dialog appears
- [ ] Confirm deletion

**Expected Behavior:**
- Optimistic update: Post disappears immediately
- Success toast: "Post deleted successfully!"
- React Query invalidates post list
- If error occurs, post reappears with error toast

#### Test 4.4: Moderation Menu (TL3+ Users)
- [ ] Log in as admin user (test@pythonlearning.studio)
- [ ] "Moderate" button appears in header
- [ ] Click "Moderate" button
- [ ] Menu opens with options:
  - Lock/Unlock Topic
  - Pin/Unpin Topic
  - Moderation Queue link

#### Test 4.5: Lock Topic
- [ ] Click "Lock Topic" from moderation menu
- [ ] Success toast appears
- [ ] Topic shows "Locked" badge
- [ ] Reply button disabled or shows locked message

**Expected Behavior:**
- Mutation executes via `useLockTopic` hook
- Topic refetches automatically
- UI updates to show locked state

#### Test 4.6: Pin Topic
- [ ] Click "Pin Topic" from moderation menu
- [ ] Success toast appears
- [ ] Topic shows "Pinned" badge
- [ ] Navigate back to forum - topic appears at top

**Expected Behavior:**
- Mutation executes via `usePinTopic` hook
- Forum list cache invalidates
- Pinned topic appears first in list

#### Test 4.7: Keyboard Navigation
- [ ] Press **Escape** while moderation menu is open
- [ ] Menu closes
- [ ] Focus returns to "Moderate" button

**Expected Behavior:**
- Proper focus management
- Accessible keyboard navigation

---

### ✅ Page 5: TopicReplyPage.jsx - Create Reply

**Location:** http://localhost:3000/forum/topics/{forum-slug}/{forum-id}/{topic-slug}/{topic-id}/reply

#### Test 5.1: Reply Form Display
- [ ] Topic title shows in header
- [ ] Breadcrumb shows: Forums > Forum Name > Topic Title > Reply
- [ ] Large textarea for reply content
- [ ] Markdown help text visible

#### Test 5.2: Create Reply
- [ ] Enter content: "This is a test reply using React Query!"
- [ ] Click "Post Reply"

**Expected Behavior:**
- Button shows "Posting..." during mutation
- Success toast: "Reply posted successfully!"
- Redirect back to topic page
- New reply appears at bottom of topic
- React Query invalidates topic posts cache

#### Test 5.3: Reply Validation
- [ ] Try to submit empty reply
- [ ] Error message appears: "Please enter your reply content"

#### Test 5.4: Cancel Reply
- [ ] Start typing a reply
- [ ] Click "Cancel"
- [ ] Redirect back to topic
- [ ] No reply created

---

### ✅ Page 6: ModerationQueuePage.jsx - Moderation Queue

**Location:** http://localhost:3000/forum/moderation/queue

**Note:** Requires TL3+ user (admin or moderator)

#### Test 6.1: Queue Display
- [ ] Log in as admin (test@pythonlearing.studio)
- [ ] Navigate to moderation queue
- [ ] Items display in priority order
- [ ] Each item shows: type, content preview, author, trust level, priority

#### Test 6.2: Filter Controls
- [ ] Click "Posts" filter
- [ ] Only posts appear
- [ ] Click "Topics" filter
- [ ] Only topics appear
- [ ] Click "All" filter
- [ ] All items appear

**Expected Behavior:**
- React Query fetches with filter parameters
- Each filter combination cached separately
- Instant switching between cached filters

#### Test 6.3: Keyboard Shortcuts
- [ ] Focus on queue (click anywhere in the list)
- [ ] Press **?** key
- [ ] Keyboard shortcuts modal appears
- [ ] Modal shows all available shortcuts:
  - **a** = Approve item
  - **r** = Reject item
  - **j** = Navigate down
  - **k** = Navigate up
  - **x** = Toggle selection
  - **Shift+A** = Approve selected
  - **Shift+R** = Reject selected
  - **?** = Show help

#### Test 6.4: Approve Single Item
- [ ] Click "Approve" on an item
- [ ] Item disappears from queue
- [ ] Success toast: "Item approved successfully!"
- [ ] Undo notification appears (30 seconds)

**Expected Behavior:**
- Optimistic update: Item removed from UI immediately
- Mutation executes via `useReviewModeration` hook
- Queue and stats caches invalidate
- If error, item reappears with error toast

#### Test 6.5: Undo Approval
- [ ] Approve an item
- [ ] Click "Undo" within 30 seconds
- [ ] Item reappears in queue
- [ ] Status reverted

**Expected Behavior:**
- Opposite mutation executes
- UI updates immediately
- Toast notification confirms undo

#### Test 6.6: Keyboard Approval
- [ ] Press **j** to navigate down
- [ ] Focused item highlights
- [ ] Press **a** to approve
- [ ] Item disappears with success toast

#### Test 6.7: Batch Operations
- [ ] Press **x** to select first item
- [ ] Press **j** then **x** to select second item
- [ ] Press **Shift+A** to approve selected
- [ ] Both items disappear
- [ ] Success toast: "Successfully approved 2 items"

**Expected Behavior:**
- Parallel API requests for all selected items
- Progress indicator during batch processing
- Individual error handling per item
- Partial success supported (e.g., "1 of 2 failed")

#### Test 6.8: Add Review Notes
- [ ] Click "Add note" on an item
- [ ] Enter text: "Approved - quality content"
- [ ] Approve the item
- [ ] Note saves with approval

**Expected Behavior:**
- Notes included in mutation payload
- Backend stores notes with moderation action

---

### ✅ Page 7: ModerationAnalyticsPage.jsx - Analytics Dashboard

**Location:** http://localhost:3000/forum/moderation/analytics

**Note:** Requires TL3+ user

#### Test 7.1: Analytics Display
- [ ] Overall statistics show (pending, approved, rejected)
- [ ] Charts display correctly
- [ ] Time range selector visible (7, 30, 90 days)

#### Test 7.2: Time Range Filter
- [ ] Select "30 days"
- [ ] Data updates to show 30-day stats
- [ ] Select "7 days"
- [ ] Data updates to show 7-day stats

**Expected Behavior:**
- React Query fetches with `days` parameter
- Each time range cached separately
- Loading state during fetch
- Charts re-render with new data

#### Test 7.3: Conditional Query
- [ ] Log out
- [ ] Try to access analytics page
- [ ] Redirected to login or shows permission error

**Expected Behavior:**
- Query disabled if `!canModerate`
- No API call made for unauthorized users
- Proper error handling

---

## React Query Specific Tests

### RQ-1: Cache Persistence
- [ ] Load forum list
- [ ] Navigate to topic
- [ ] Navigate back to forum list
- [ ] **Verify:** Forum list appears instantly from cache
- [ ] **Check Network tab:** Background refetch occurs

### RQ-2: Optimistic Updates
- [ ] Create a reply
- [ ] **Verify:** Reply appears immediately with temp ID
- [ ] **Verify:** Reply has `_isOptimistic: true` flag (check React Query Devtools)
- [ ] **Wait:** For API response
- [ ] **Verify:** Temp ID replaced with real ID from backend

### RQ-3: Error Rollback
- [ ] Stop Django backend
- [ ] Try to approve an item in moderation queue
- [ ] **Verify:** Item initially disappears (optimistic)
- [ ] **Verify:** Error toast appears
- [ ] **Verify:** Item reappears in queue (rollback)

### RQ-4: Query Key Invalidation
- [ ] Open React Query Devtools (bottom right in dev mode)
- [ ] Create a new topic
- [ ] **Verify:** Devtools shows multiple queries invalidating:
  - `['forums', 'list']`
  - `['topics', 'list']`
  - `['forums', {slug}, 'topics']`

### RQ-5: Stale Time Behavior
- [ ] Load a forum (stale time: 5 minutes)
- [ ] Wait 6 minutes
- [ ] Click on the forum again
- [ ] **Verify:** Cached data shows immediately
- [ ] **Verify:** Background refetch occurs (data marked stale)

### RQ-6: Garbage Collection
- [ ] Load several forums
- [ ] Check React Query Devtools
- [ ] Navigate away and wait 10+ minutes
- [ ] **Verify:** Unused queries garbage collected (removed from cache)

### RQ-7: Concurrent Requests Deduplication
- [ ] Open forum in two browser tabs
- [ ] Open Network tab in both
- [ ] Refresh both tabs simultaneously
- [ ] **Verify:** Only ONE network request made (shared across tabs)

---

## Performance Tests

### P-1: Initial Load Performance
- [ ] Clear browser cache
- [ ] Open DevTools > Network tab
- [ ] Load forum list
- [ ] **Verify:** Total requests < 10
- [ ] **Verify:** Load time < 2 seconds (on local server)

### P-2: Navigation Performance
- [ ] Navigate between cached pages
- [ ] **Verify:** Navigation feels instant (<100ms)
- [ ] No loading spinners for cached data

### P-3: Batch Operation Performance
- [ ] Select 10 items in moderation queue
- [ ] Batch approve
- [ ] **Verify:** All requests fire in parallel
- [ ] **Verify:** Total time ~= single request time (not 10x)

---

## Accessibility Tests

### A-1: Keyboard Navigation (ModerationQueuePage)
- [ ] **Tab** through all interactive elements
- [ ] Focus indicators visible
- [ ] **j/k** keys navigate queue items
- [ ] **Escape** closes modals
- [ ] Focus management correct (returns to trigger after modal close)

### A-2: Screen Reader Support
- [ ] Use screen reader (macOS VoiceOver or NVDA)
- [ ] Navigate forum list
- [ ] **Verify:** Headings announced correctly
- [ ] **Verify:** Buttons have accessible labels
- [ ] **Verify:** Form labels associated with inputs

### A-3: Focus Management
- [ ] Open moderation menu
- [ ] Press **Escape**
- [ ] **Verify:** Menu closes
- [ ] **Verify:** Focus returns to "Moderate" button

---

## Error Handling Tests

### E-1: Network Failure
- [ ] Stop Django backend
- [ ] Try to create a topic
- [ ] **Verify:** Error toast with clear message
- [ ] **Verify:** Form remains filled (no data loss)
- [ ] **Verify:** Retry option available

### E-2: Validation Errors
- [ ] Submit empty form
- [ ] **Verify:** Client-side validation errors
- [ ] Fill form incorrectly
- [ ] **Verify:** Backend validation errors display

### E-3: Permission Errors
- [ ] Log in as TL0 user
- [ ] Try to access moderation queue
- [ ] **Verify:** Permission denied message
- [ ] **Verify:** Redirect to safe page

---

## Browser Compatibility Tests

Test in multiple browsers:
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)

For each browser:
- [ ] Forum list loads
- [ ] Create topic works
- [ ] Create reply works
- [ ] Moderation actions work
- [ ] React Query Devtools opens

---

## Mobile Responsiveness Tests

Test on mobile viewport (or use Chrome DevTools device mode):
- [ ] Forum list displays correctly
- [ ] Topic list readable
- [ ] Forms usable on small screens
- [ ] Moderation menu accessible
- [ ] Touch targets large enough (44x44px minimum)

---

## Final Verification Checklist

### Code Quality
- [ ] No console errors in browser console
- [ ] No console warnings (except expected chunk size warning)
- [ ] React Query Devtools shows all queries
- [ ] Network tab shows no duplicate requests

### Functionality
- [ ] All 6 pages load without errors
- [ ] All forms submit successfully
- [ ] All mutations execute correctly
- [ ] All cache invalidations work
- [ ] All error handling works

### User Experience
- [ ] Loading states display correctly
- [ ] Error messages are user-friendly
- [ ] Success toasts appear
- [ ] Navigation feels smooth
- [ ] No UI flickering or jarring updates

### Performance
- [ ] Cached pages load instantly
- [ ] Background refetches don't block UI
- [ ] Optimistic updates feel instant
- [ ] Batch operations complete quickly

---

## Common Issues & Solutions

### Issue: "Invalid token format" warning
**Cause:** Old/corrupted JWT token in localStorage
**Solution:**
```javascript
localStorage.removeItem('access_token')
// Refresh page
```

### Issue: React Query Devtools not appearing
**Cause:** Not in development mode
**Solution:**
```bash
# Verify NODE_ENV
echo $NODE_ENV  # Should be empty or 'development'

# Or check in browser console
console.log(process.env.NODE_ENV)
```

### Issue: Queries not invalidating after mutation
**Cause:** Query key mismatch
**Solution:** Check React Query Devtools for exact query keys, ensure mutation uses same keys

### Issue: Optimistic update doesn't rollback on error
**Cause:** Missing error handler or context
**Solution:** Check browser console for error details, verify `onError` handler in mutation

---

## Reporting Issues

If you find any bugs during testing:

1. **Note the page and action** that caused the issue
2. **Check browser console** for errors
3. **Check React Query Devtools** for query state
4. **Check Network tab** for failed requests
5. **Document steps to reproduce**

**Example Bug Report:**
```
Page: ForumTopicPage
Action: Deleted a post
Expected: Post disappears
Actual: Error toast "Failed to delete post: 404"
Console Error: [error details]
Network: DELETE /api/v1/posts/123/delete/ → 404
```

---

## Success Criteria

✅ All 6 pages load without errors
✅ All CRUD operations work (Create, Read, Update, Delete)
✅ React Query caching verified
✅ Optimistic updates work correctly
✅ Error handling graceful
✅ Accessibility features functional
✅ Keyboard shortcuts work
✅ Mobile responsive
✅ No performance issues

**When all criteria met:** Migration is production-ready! 🎉

---

**Tester Name:** _______________
**Date Completed:** _______________
**Pass/Fail:** _______________
**Notes:**
