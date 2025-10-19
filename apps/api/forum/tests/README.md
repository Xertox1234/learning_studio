# Forum API Tests

## Overview

This directory contains comprehensive backend tests for the forum API endpoints, specifically focusing on cursor-based pagination for topic posts.

## Test Files

### `test_topic_pagination.py`

Comprehensive test suite for cursor-based pagination in the topic posts endpoint (`/api/v2/forum/topics/{id}/posts/`).

**Total Tests:** 18
**Status:** All passing ✅

## Test Coverage

### Core Pagination Tests

1. **test_cursor_pagination_returns_correct_page_size**
   - Verifies default page size is 20 posts
   - Creates 50 posts and validates exactly 20 are returned

2. **test_cursor_pagination_next_link_exists**
   - Ensures `next` URL is present when more pages exist
   - Validates `previous` is None for first page
   - Checks cursor parameter is included in next URL

3. **test_cursor_pagination_prevents_duplicates**
   - Critical test for cursor pagination stability
   - Creates 30 posts, fetches first page
   - Adds 5 new posts after cursor creation
   - Validates no duplicate posts between pages
   - **Note:** Cursor pagination WILL show new posts added after cursor creation (by design)

### Page Size Tests

4. **test_custom_page_size_parameter**
   - Tests `?page_size=10` parameter
   - Validates exactly 10 posts returned

5. **test_max_page_size_enforced**
   - Creates 150 posts
   - Requests `?page_size=200` (exceeds max of 100)
   - Validates only 100 posts returned

6. **test_cursor_pagination_with_page_size_edge_cases**
   - Tests `page_size=1` (minimum)
   - Tests `page_size=0` (fallback to default)
   - Tests `page_size` as string (`"5"`)
   - Tests negative `page_size` (graceful handling)

### Empty and Single Page Tests

7. **test_empty_results**
   - Tests pagination with 0 posts
   - Validates empty results array
   - Ensures no `next` or `previous` links

8. **test_single_page_results**
   - Creates 15 posts (less than page_size of 20)
   - Validates all posts returned on one page
   - Ensures no `next` link exists

### Navigation and Ordering Tests

9. **test_cursor_navigation_through_all_pages**
   - Creates 55 posts (3 pages: 20, 20, 15)
   - Navigates through all pages using cursors
   - Validates total post count
   - Ensures no duplicates across pages
   - Confirms correct number of pages

10. **test_posts_ordered_by_created_ascending**
    - Validates posts are ordered by `created` date
    - Checks ascending order (oldest to newest)

### Authentication and Access Tests

11. **test_unauthenticated_access_allowed**
    - Validates read-only access for unauthenticated users
    - Ensures forum posts are publicly viewable

### Response Structure Tests

12. **test_response_structure_matches_drf_cursor_pagination**
    - Validates DRF cursor pagination format
    - Checks for `next`, `previous`, and `results` keys
    - Validates post field structure

13. **test_poster_information_included**
    - Ensures poster data is properly serialized
    - Validates nested user information

### Data Integrity Tests

14. **test_only_approved_posts_returned**
    - Creates 10 approved and 5 unapproved posts
    - Validates only approved posts returned (10, not 15)
    - Ensures unapproved content is filtered

15. **test_posts_from_correct_topic_only**
    - Creates posts in two different topics
    - Validates only posts from requested topic are returned
    - Prevents cross-topic data leakage

### Edge Case Tests

16. **test_invalid_cursor_returns_error**
    - Tests malformed cursor parameter
    - Validates 404 error for invalid cursors

17. **test_nonexistent_topic_returns_404**
    - Requests posts for topic ID 99999
    - Validates 404 response

### Side Effect Tests

18. **test_view_count_incremented_on_fetch**
    - Validates topic view count is incremented
    - Checks side effects of GET request

## Key Implementation Details

### Test Setup

Each test creates a complete forum hierarchy:

```python
# User with TrustLevel
user = User.objects.create_user(...)
TrustLevel.objects.get_or_create(user=user, defaults={'level': 1})

# Forum hierarchy: Root Category → Forum → Topic
root_forum = Forum.objects.create(type=Forum.FORUM_CAT)
forum = Forum.objects.create(type=Forum.FORUM_POST, parent=root_forum)
topic = Topic.objects.create(
    forum=forum,
    type=Topic.TOPIC_POST,
    status=Topic.TOPIC_UNLOCKED,
    approved=True
)
```

### Helper Methods

**`_create_posts(count)`**
- Creates multiple posts with distinct timestamps
- Adds millisecond delays to ensure proper ordering
- Returns list of created posts

### Cursor Pagination Behavior

**Important:** Cursor pagination prevents showing the SAME posts twice, but WILL show new posts added after the cursor was created. This is by design:

- **Prevents:** Duplicate posts from previous pages
- **Allows:** New posts created after cursor generation
- **Benefit:** Users don't miss new content when browsing

## Running Tests

### Run All Forum Tests

```bash
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py test apps.api.forum.tests
```

### Run Pagination Tests Only

```bash
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py test apps.api.forum.tests.test_topic_pagination
```

### Run Specific Test

```bash
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py test apps.api.forum.tests.test_topic_pagination.TopicCursorPaginationTests.test_cursor_pagination_prevents_duplicates
```

### Run with Verbose Output

```bash
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py test apps.api.forum.tests.test_topic_pagination --verbosity=2
```

## Test Database

- Tests use SQLite in-memory database (`file:memorydb_default?mode=memory&cache=shared`)
- Database is created and destroyed for each test run
- All migrations are applied automatically

## API Endpoint

**URL Pattern:** `/api/v2/forum/topics/{topic_id}/posts/`

**Query Parameters:**
- `cursor` - Pagination cursor (auto-managed by DRF)
- `page_size` - Items per page (default: 20, max: 100)

**Response Format:**
```json
{
  "next": "http://example.com/api/v2/forum/topics/1/posts/?cursor=cD0yMD...",
  "previous": null,
  "results": [
    {
      "id": 1,
      "poster": {
        "username": "testuser",
        "email": "test@example.com"
      },
      "content": "Post content",
      "created": "2025-10-17T12:00:00Z",
      "updated": "2025-10-17T12:00:00Z",
      "approved": true,
      "position": 1,
      "is_topic_head": true,
      "permissions": {}
    }
  ]
}
```

## Dependencies

- Django REST Framework
- django-machina (forum models)
- apps.forum_integration (TrustLevel model)

## Future Enhancements

Potential additions to test coverage:

1. **Performance Tests**
   - Measure pagination performance with 1000+ posts
   - Benchmark cursor encoding/decoding

2. **Concurrent Access Tests**
   - Test cursor stability with simultaneous requests
   - Validate thread safety

3. **Permission Tests**
   - Test moderator-only post visibility
   - Validate TrustLevel-based filtering

4. **Error Recovery Tests**
   - Test database connection failures
   - Validate graceful degradation

## Related TODO

This test suite resolves **TODO #009** - Backend tests for cursor pagination.

## Maintenance Notes

- Update tests when pagination parameters change
- Add new tests for any custom filtering logic
- Maintain test data creation patterns for consistency
