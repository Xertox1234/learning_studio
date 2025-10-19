# Forum Query Hooks Test Suite

## Overview

This directory contains comprehensive tests for the forum query hooks powered by React Query. The test suite ensures infinite scroll pagination, caching, error handling, and query key management work correctly.

## Test Files

### `useForumQuery.test.jsx`

Comprehensive test suite for forum query hooks with **31 passing tests** covering:

- `useInfiniteTopicPosts` (20 tests)
- `useTopicDetail` (3 tests)
- `useForums` (3 tests)
- `useForumDetail` (3 tests)
- Query Key Structure (2 tests)

## Test Coverage

### `useInfiniteTopicPosts` - Infinite Scroll Hook

#### Core Functionality (7 tests)
- ✅ **loads initial page of posts** - Verifies first page loads with 20 posts
- ✅ **extracts cursor from next URL** - Tests cursor extraction from pagination URLs
- ✅ **returns undefined when no next page** - Handles end of pagination
- ✅ **handles invalid next URL gracefully** - No errors on malformed URLs
- ✅ **fetches next page with cursor** - Verifies cursor is passed to API
- ✅ **flattens multiple pages correctly** - Tests loading 3 pages (60 posts total)
- ✅ **disabled when no topic ID** - Query disabled with null/undefined/empty ID

#### Error Handling (3 tests)
- ✅ **handles API error gracefully** - Error state with error message
- ✅ **handles network error** - Network failure handling
- ✅ **handles 404 error** - HTTP error status codes

#### Loading States (2 tests)
- ✅ **shows loading state during initial fetch** - `isLoading` and `isFetching` flags
- ✅ **completes fetchNextPage and loads second page** - Multi-page loading

#### Query Key Structure (1 test)
- ✅ **uses correct query key** - Validates React Query cache key format

#### Caching (1 test)
- ✅ **respects stale time configuration** - No unnecessary refetches (30s stale time)

#### Edge Cases (6 tests)
- ✅ **handles empty results** - Empty array response
- ✅ **handles single post** - Single item response
- ✅ **handles cursor with special characters** - URL encoding in cursors
- ✅ **handles absolute and relative next URLs** - Multiple URL formats
- ✅ **disabled when topic ID is undefined** - Undefined ID handling
- ✅ **disabled when topic ID is empty string** - Empty string handling

### `useTopicDetail` (3 tests)
- ✅ **fetches topic detail successfully** - Loads topic metadata
- ✅ **disabled when no topic ID provided** - Conditional query execution
- ✅ **uses correct query key** - Cache key validation

### `useForums` (3 tests)
- ✅ **fetches all forums successfully** - Loads forum categories and stats
- ✅ **uses correct query key** - Cache key validation
- ✅ **respects staleTime of 5 minutes** - Cache duration verification

### `useForumDetail` (3 tests)
- ✅ **fetches forum detail successfully** - Loads forum by slug
- ✅ **disabled when no slug provided** - Conditional execution
- ✅ **uses correct query key** - Cache key validation

### Query Key Structure (2 tests)
- ✅ **forumKeys generates correct structure** - Validates hierarchical key structure
- ✅ **topicKeys generates correct structure** - Validates topic key patterns

## Test Utilities

### `createTestQueryClient()`
Creates a fresh QueryClient with optimized test settings:
- No retries (faster test execution)
- Zero cache time and stale time (isolated tests)

### `createWrapper(queryClient)`
React component wrapper providing QueryClient context for hooks.

### `createMockPostsResponse(page, totalPages)`
Generates realistic paginated API responses:
- 20 posts per page
- Cursor-based pagination URLs
- Complete post metadata (author, timestamps, approval status)

## Running Tests

```bash
# Run all forum query tests
npm test -- src/hooks/__tests__/useForumQuery.test.jsx

# Run tests in watch mode
npm test -- src/hooks/__tests__/useForumQuery.test.jsx --watch

# Run with verbose output
npm run test:run -- src/hooks/__tests__/useForumQuery.test.jsx --reporter=verbose

# Run with UI (if installed)
npm run test:ui
```

## Test Patterns Used

### 1. API Mocking with Vitest
```javascript
import { vi } from 'vitest'
import * as forumApi from '../../api/forumApi'

vi.mock('../../api/forumApi')

// In test
forumApi.getTopicPosts.mockResolvedValue(mockData)
```

### 2. Hook Testing with React Testing Library
```javascript
import { renderHook, waitFor } from '@testing-library/react'

const { result } = renderHook(
  () => useInfiniteTopicPosts('1'),
  { wrapper: createWrapper(queryClient) }
)

await waitFor(() => expect(result.current.isSuccess).toBe(true))
```

### 3. Multi-Page Pagination Testing
```javascript
// Mock multiple pages
forumApi.getTopicPosts
  .mockResolvedValueOnce(page1)
  .mockResolvedValueOnce(page2)
  .mockResolvedValueOnce(page3)

// Load pages sequentially
result.current.fetchNextPage()
await waitFor(() => expect(result.current.data.pages).toHaveLength(2))
```

### 4. Error State Testing
```javascript
forumApi.getTopicPosts.mockRejectedValue(new Error('Network error'))

await waitFor(() => expect(result.current.isError).toBe(true))
expect(result.current.error.message).toBe('Network error')
```

## Key Testing Insights

### Cursor Extraction
The `getNextPageParam` function extracts cursors from URLs like:
```
http://localhost/api/v2/forum/topics/1/posts/?cursor=abc123
```
Returns: `"abc123"`

### Query Key Hierarchy
```javascript
topicKeys.posts('42') // ['topics', 'detail', '42', 'posts']
forumKeys.detail('general') // ['forums', 'detail', 'general']
```

### Stale Time Strategy
- Forums: 5 minutes (rarely change)
- Topics: 2 minutes (moderate updates)
- Posts: 30 seconds (frequent updates, especially with infinite scroll)

## Best Practices Demonstrated

1. ✅ **Isolated Tests** - Fresh QueryClient per test
2. ✅ **Realistic Mocks** - Complete API response structures
3. ✅ **Error Coverage** - Network, API, and HTTP errors
4. ✅ **Edge Cases** - Empty results, single items, invalid inputs
5. ✅ **Async Handling** - Proper use of `waitFor` for async state
6. ✅ **Query Key Validation** - Ensures correct cache key structure
7. ✅ **Loading States** - Tests all loading/fetching flags
8. ✅ **Pagination Logic** - Cursor extraction and multi-page loading

## Test Statistics

- **Total Tests**: 31
- **Passing**: 31 (100%)
- **Test Execution Time**: ~2 seconds
- **Test Coverage**: Core infinite scroll functionality, error handling, edge cases

## Related Files

- **Implementation**: `/Users/williamtower/projects/learning_studio/frontend/src/hooks/useForumQuery.js`
- **API Client**: `/Users/williamtower/projects/learning_studio/frontend/src/api/forumApi.js`
- **Vitest Config**: `/Users/williamtower/projects/learning_studio/frontend/vitest.config.js`

## Future Test Enhancements

Consider adding tests for:
- [ ] Mutation hooks (`useCreatePost`, `useUpdatePost`, etc.)
- [ ] Optimistic updates verification
- [ ] Cache invalidation patterns
- [ ] Background refetching behavior
- [ ] Query cancellation on unmount
- [ ] Integration tests with real backend API

## Troubleshooting

### Test Timeout Issues
If tests timeout, increase the timeout in `waitFor`:
```javascript
await waitFor(() => expect(condition).toBe(true), { timeout: 5000 })
```

### Mock Reset Between Tests
Always clear mocks in `beforeEach`:
```javascript
beforeEach(() => {
  vi.clearAllMocks()
})
```

### JSX Syntax Errors
Test files with JSX must use `.jsx` extension:
```
useForumQuery.test.jsx  ✅
useForumQuery.test.js   ❌
```
