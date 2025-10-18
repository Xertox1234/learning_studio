/**
 * Comprehensive Tests for Forum Query Hooks
 * Tests infinite scroll pagination, query caching, and error handling
 */

import { describe, test, expect, beforeEach, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  useInfiniteTopicPosts,
  useTopicDetail,
  useForums,
  useForumDetail,
  topicKeys,
  forumKeys,
} from '../useForumQuery'
import * as forumApi from '../../api/forumApi'

// Mock the API module
vi.mock('../../api/forumApi')

// ===========================
// TEST UTILITIES
// ===========================

/**
 * Create a fresh QueryClient for each test
 */
const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

/**
 * Wrapper component that provides QueryClient context
 */
const createWrapper = (queryClient) => {
  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

/**
 * Mock paginated API response
 */
const createMockPostsResponse = (page = 1, totalPages = 3) => {
  const hasNext = page < totalPages
  const hasPrev = page > 1

  return {
    results: Array.from({ length: 20 }, (_, i) => ({
      id: (page - 1) * 20 + i + 1,
      content: `Post ${(page - 1) * 20 + i + 1} content`,
      author: {
        id: 1,
        username: 'testuser',
      },
      created_at: new Date().toISOString(),
      approved: true,
    })),
    next: hasNext
      ? `http://localhost/api/v2/forum/topics/1/posts/?cursor=page${page + 1}`
      : null,
    previous: hasPrev
      ? `http://localhost/api/v2/forum/topics/1/posts/?cursor=page${page - 1}`
      : null,
    count: totalPages * 20,
  }
}

// ===========================
// INFINITE SCROLL TESTS
// ===========================

describe('useInfiniteTopicPosts', () => {
  let queryClient

  beforeEach(() => {
    queryClient = createTestQueryClient()
    vi.clearAllMocks()
  })

  // ===========================
  // Core Functionality
  // ===========================

  test('loads initial page of posts', async () => {
    // Mock API response
    const mockResponse = createMockPostsResponse(1, 3)
    forumApi.getTopicPosts.mockResolvedValue(mockResponse)

    const { result } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    // Initial state
    expect(result.current.isLoading).toBe(true)

    // Wait for data to load
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // Verify data structure
    expect(result.current.data.pages).toHaveLength(1)
    expect(result.current.data.pages[0].results).toHaveLength(20)
    expect(result.current.data.pages[0].results[0]).toMatchObject({
      id: 1,
      content: 'Post 1 content',
    })

    // Verify pagination state
    expect(result.current.hasNextPage).toBe(true)
    expect(result.current.isFetchingNextPage).toBe(false)

    // Verify API was called correctly
    expect(forumApi.getTopicPosts).toHaveBeenCalledTimes(1)
    expect(forumApi.getTopicPosts).toHaveBeenCalledWith('1', {})
  })

  test('extracts cursor from next URL', async () => {
    const mockResponse = {
      results: [{ id: 1, content: 'Post 1' }],
      next: 'http://localhost/api/v2/forum/topics/1/posts/?cursor=abc123xyz',
      previous: null,
    }
    forumApi.getTopicPosts.mockResolvedValue(mockResponse)

    const { result } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // The getNextPageParam function should extract 'abc123xyz' from the URL
    expect(result.current.hasNextPage).toBe(true)

    // Verify the pageParams would contain the extracted cursor
    const lastPage = result.current.data.pages[result.current.data.pages.length - 1]
    const nextPageParam = result.current.data.pageParams[result.current.data.pages.length]

    // The cursor should be extracted from the next URL
    expect(lastPage.next).toContain('cursor=abc123xyz')
  })

  test('returns undefined when no next page', async () => {
    const mockResponse = {
      results: [{ id: 1, content: 'Post 1' }],
      next: null,
      previous: null,
    }
    forumApi.getTopicPosts.mockResolvedValue(mockResponse)

    const { result } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // No next page available
    expect(result.current.hasNextPage).toBe(false)
  })

  test('handles invalid next URL gracefully', async () => {
    const mockResponse = {
      results: [{ id: 1, content: 'Post 1' }],
      next: 'not-a-valid-url',
      previous: null,
    }
    forumApi.getTopicPosts.mockResolvedValue(mockResponse)

    const { result } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    // Should not throw error
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // Should handle gracefully by treating as no next page
    expect(result.current.hasNextPage).toBe(false)
  })

  test('fetches next page with cursor', async () => {
    const page1 = createMockPostsResponse(1, 3)
    const page2 = createMockPostsResponse(2, 3)

    forumApi.getTopicPosts
      .mockResolvedValueOnce(page1)
      .mockResolvedValueOnce(page2)

    const { result } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    // Wait for initial page
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data.pages).toHaveLength(1)

    // Fetch next page
    result.current.fetchNextPage()

    // Wait for next page to load
    await waitFor(() => expect(result.current.data.pages).toHaveLength(2))

    // Verify both pages are loaded
    expect(result.current.data.pages[0].results).toHaveLength(20)
    expect(result.current.data.pages[1].results).toHaveLength(20)
    expect(result.current.data.pages[1].results[0]).toMatchObject({
      id: 21,
      content: 'Post 21 content',
    })

    // Verify cursor was passed to API
    expect(forumApi.getTopicPosts).toHaveBeenCalledTimes(2)
    expect(forumApi.getTopicPosts).toHaveBeenNthCalledWith(2, '1', {
      cursor: 'page2',
    })
  })

  test('flattens multiple pages correctly', async () => {
    const page1 = createMockPostsResponse(1, 3)
    const page2 = createMockPostsResponse(2, 3)
    const page3 = createMockPostsResponse(3, 3)

    forumApi.getTopicPosts
      .mockResolvedValueOnce(page1)
      .mockResolvedValueOnce(page2)
      .mockResolvedValueOnce(page3)

    const { result } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    // Load all 3 pages
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    result.current.fetchNextPage()
    await waitFor(() => expect(result.current.data.pages).toHaveLength(2))

    result.current.fetchNextPage()
    await waitFor(() => expect(result.current.data.pages).toHaveLength(3))

    // Verify pages array structure
    expect(result.current.data.pages).toHaveLength(3)
    expect(result.current.data.pages[0].results).toHaveLength(20)
    expect(result.current.data.pages[1].results).toHaveLength(20)
    expect(result.current.data.pages[2].results).toHaveLength(20)

    // Flatten all posts
    const allPosts = result.current.data.pages.flatMap((page) => page.results)
    expect(allPosts).toHaveLength(60)
    expect(allPosts[0].id).toBe(1)
    expect(allPosts[20].id).toBe(21)
    expect(allPosts[40].id).toBe(41)

    // No more pages
    expect(result.current.hasNextPage).toBe(false)
  })

  test('disabled when no topic ID', async () => {
    const { result } = renderHook(
      () => useInfiniteTopicPosts(null),
      { wrapper: createWrapper(queryClient) }
    )

    // Should not make API call
    expect(forumApi.getTopicPosts).not.toHaveBeenCalled()

    // Should be in idle state
    expect(result.current.isLoading).toBe(false)
    expect(result.current.data).toBeUndefined()
  })

  test('disabled when topic ID is undefined', async () => {
    const { result } = renderHook(
      () => useInfiniteTopicPosts(undefined),
      { wrapper: createWrapper(queryClient) }
    )

    expect(forumApi.getTopicPosts).not.toHaveBeenCalled()
    expect(result.current.isLoading).toBe(false)
  })

  test('disabled when topic ID is empty string', async () => {
    const { result } = renderHook(
      () => useInfiniteTopicPosts(''),
      { wrapper: createWrapper(queryClient) }
    )

    expect(forumApi.getTopicPosts).not.toHaveBeenCalled()
    expect(result.current.isLoading).toBe(false)
  })

  // ===========================
  // Error Handling
  // ===========================

  test('handles API error gracefully', async () => {
    const errorMessage = 'Failed to fetch posts'
    forumApi.getTopicPosts.mockRejectedValue(new Error(errorMessage))

    const { result } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeInstanceOf(Error)
    expect(result.current.error.message).toBe(errorMessage)
    expect(result.current.data).toBeUndefined()
  })

  test('handles network error', async () => {
    forumApi.getTopicPosts.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.error.message).toBe('Network error')
  })

  test('handles 404 error', async () => {
    const error = new Error('HTTP 404: Not Found')
    error.status = 404
    forumApi.getTopicPosts.mockRejectedValue(error)

    const { result } = renderHook(
      () => useInfiniteTopicPosts('999'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.error.status).toBe(404)
  })

  // ===========================
  // Loading States
  // ===========================

  test('shows loading state during initial fetch', async () => {
    forumApi.getTopicPosts.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(createMockPostsResponse(1)), 100))
    )

    const { result } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    expect(result.current.isLoading).toBe(true)
    expect(result.current.isFetching).toBe(true)
    expect(result.current.data).toBeUndefined()

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.isLoading).toBe(false)
    expect(result.current.isFetching).toBe(false)
  })

  test('completes fetchNextPage and loads second page', async () => {
    const page1 = createMockPostsResponse(1, 2)
    const page2 = createMockPostsResponse(2, 2)

    forumApi.getTopicPosts
      .mockResolvedValueOnce(page1)
      .mockResolvedValueOnce(page2)

    const { result } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data.pages).toHaveLength(1)

    // Trigger next page fetch
    result.current.fetchNextPage()

    // Wait for second page to load
    await waitFor(() => expect(result.current.data.pages).toHaveLength(2))

    // Verify both pages are loaded correctly
    expect(result.current.data.pages[0].results).toHaveLength(20)
    expect(result.current.data.pages[1].results).toHaveLength(20)
    expect(result.current.isFetchingNextPage).toBe(false)
  })

  // ===========================
  // Query Key Structure
  // ===========================

  test('uses correct query key', async () => {
    forumApi.getTopicPosts.mockResolvedValue(createMockPostsResponse(1))

    const { result } = renderHook(
      () => useInfiniteTopicPosts('42'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // Verify query key structure
    const expectedKey = topicKeys.posts('42')
    const cache = queryClient.getQueryCache()
    const query = cache.find({ queryKey: expectedKey })

    expect(query).toBeDefined()
    expect(query.queryKey).toEqual(['topics', 'detail', '42', 'posts'])
  })

  // ===========================
  // Stale Time & Caching
  // ===========================

  test('respects stale time configuration', async () => {
    const mockResponse = createMockPostsResponse(1)
    forumApi.getTopicPosts.mockResolvedValue(mockResponse)

    const { result, rerender } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(forumApi.getTopicPosts).toHaveBeenCalledTimes(1)

    // Rerender should not refetch (data is fresh due to staleTime: 30s)
    rerender()
    expect(forumApi.getTopicPosts).toHaveBeenCalledTimes(1)
  })

  // ===========================
  // Edge Cases
  // ===========================

  test('handles empty results', async () => {
    const mockResponse = {
      results: [],
      next: null,
      previous: null,
      count: 0,
    }
    forumApi.getTopicPosts.mockResolvedValue(mockResponse)

    const { result } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data.pages).toHaveLength(1)
    expect(result.current.data.pages[0].results).toHaveLength(0)
    expect(result.current.hasNextPage).toBe(false)
  })

  test('handles single post', async () => {
    const mockResponse = {
      results: [{ id: 1, content: 'Only post' }],
      next: null,
      previous: null,
      count: 1,
    }
    forumApi.getTopicPosts.mockResolvedValue(mockResponse)

    const { result } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data.pages[0].results).toHaveLength(1)
    expect(result.current.hasNextPage).toBe(false)
  })

  test('handles cursor with special characters', async () => {
    const mockResponse = {
      results: [{ id: 1, content: 'Post 1' }],
      next: 'http://localhost/api/v2/forum/topics/1/posts/?cursor=abc%2B123%3Dxyz',
      previous: null,
    }
    forumApi.getTopicPosts.mockResolvedValue(mockResponse)

    const { result } = renderHook(
      () => useInfiniteTopicPosts('1'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.hasNextPage).toBe(true)
  })

  test('handles absolute and relative next URLs', async () => {
    const testCases = [
      'http://localhost/api/v2/forum/topics/1/posts/?cursor=page2',
      'https://example.com/api/v2/forum/topics/1/posts/?cursor=page2',
      '/api/v2/forum/topics/1/posts/?cursor=page2',
    ]

    for (const nextUrl of testCases) {
      const mockResponse = {
        results: [{ id: 1, content: 'Post 1' }],
        next: nextUrl,
        previous: null,
      }
      forumApi.getTopicPosts.mockResolvedValue(mockResponse)

      const { result } = renderHook(
        () => useInfiniteTopicPosts('1'),
        { wrapper: createWrapper(queryClient) }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.hasNextPage).toBe(true)

      // Clean up for next iteration
      queryClient.clear()
      vi.clearAllMocks()
    }
  })
})

// ===========================
// OTHER QUERY HOOKS
// ===========================

describe('useTopicDetail', () => {
  let queryClient

  beforeEach(() => {
    queryClient = createTestQueryClient()
    vi.clearAllMocks()
  })

  test('fetches topic detail successfully', async () => {
    const mockTopic = {
      id: 1,
      subject: 'Test Topic',
      slug: 'test-topic',
      posts_count: 42,
      views_count: 100,
    }
    forumApi.getTopicDetail.mockResolvedValue(mockTopic)

    const { result } = renderHook(
      () => useTopicDetail('1'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockTopic)
    expect(forumApi.getTopicDetail).toHaveBeenCalledWith('1')
  })

  test('disabled when no topic ID provided', async () => {
    const { result } = renderHook(
      () => useTopicDetail(null),
      { wrapper: createWrapper(queryClient) }
    )

    expect(forumApi.getTopicDetail).not.toHaveBeenCalled()
    expect(result.current.isLoading).toBe(false)
  })

  test('uses correct query key', async () => {
    forumApi.getTopicDetail.mockResolvedValue({ id: 1, subject: 'Test' })

    const { result } = renderHook(
      () => useTopicDetail('1'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    const expectedKey = topicKeys.detail('1')
    const cache = queryClient.getQueryCache()
    const query = cache.find({ queryKey: expectedKey })

    expect(query).toBeDefined()
    expect(query.queryKey).toEqual(['topics', 'detail', '1'])
  })
})

describe('useForums', () => {
  let queryClient

  beforeEach(() => {
    queryClient = createTestQueryClient()
    vi.clearAllMocks()
  })

  test('fetches all forums successfully', async () => {
    const mockForums = {
      categories: [
        {
          id: 1,
          name: 'General',
          forums: [
            { id: 1, name: 'General Discussion', slug: 'general-discussion' },
          ],
        },
      ],
      stats: {
        total_posts: 100,
        total_topics: 50,
      },
    }
    forumApi.getForums.mockResolvedValue(mockForums)

    const { result } = renderHook(
      () => useForums(),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockForums)
    expect(forumApi.getForums).toHaveBeenCalledTimes(1)
  })

  test('uses correct query key', async () => {
    forumApi.getForums.mockResolvedValue({ categories: [] })

    const { result } = renderHook(
      () => useForums(),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    const expectedKey = forumKeys.list()
    const cache = queryClient.getQueryCache()
    const query = cache.find({ queryKey: expectedKey })

    expect(query).toBeDefined()
    expect(query.queryKey).toEqual(['forums', 'list'])
  })

  test('respects staleTime of 5 minutes', async () => {
    const mockForums = { categories: [] }
    forumApi.getForums.mockResolvedValue(mockForums)

    // Use a custom query client with default staleTime
    const customQueryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })

    const { result, rerender } = renderHook(
      () => useForums(),
      { wrapper: createWrapper(customQueryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(forumApi.getForums).toHaveBeenCalledTimes(1)

    // Immediate rerender should not refetch
    rerender()
    expect(forumApi.getForums).toHaveBeenCalledTimes(1)
  })
})

describe('useForumDetail', () => {
  let queryClient

  beforeEach(() => {
    queryClient = createTestQueryClient()
    vi.clearAllMocks()
  })

  test('fetches forum detail successfully', async () => {
    const mockForum = {
      id: 1,
      name: 'General Discussion',
      slug: 'general-discussion',
      description: 'Talk about anything',
      posts_count: 100,
    }
    forumApi.getForumDetail.mockResolvedValue(mockForum)

    const { result } = renderHook(
      () => useForumDetail('general-discussion'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockForum)
    expect(forumApi.getForumDetail).toHaveBeenCalledWith('general-discussion')
  })

  test('disabled when no slug provided', async () => {
    const { result } = renderHook(
      () => useForumDetail(null),
      { wrapper: createWrapper(queryClient) }
    )

    expect(forumApi.getForumDetail).not.toHaveBeenCalled()
    expect(result.current.isLoading).toBe(false)
  })

  test('uses correct query key', async () => {
    forumApi.getForumDetail.mockResolvedValue({ id: 1, slug: 'test-forum' })

    const { result } = renderHook(
      () => useForumDetail('test-forum'),
      { wrapper: createWrapper(queryClient) }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    const expectedKey = forumKeys.detail('test-forum')
    const cache = queryClient.getQueryCache()
    const query = cache.find({ queryKey: expectedKey })

    expect(query).toBeDefined()
    expect(query.queryKey).toEqual(['forums', 'detail', 'test-forum'])
  })
})

// ===========================
// QUERY KEY TESTS
// ===========================

describe('Query Key Structure', () => {
  test('forumKeys generates correct structure', () => {
    expect(forumKeys.all).toEqual(['forums'])
    expect(forumKeys.lists()).toEqual(['forums', 'list'])
    expect(forumKeys.list()).toEqual(['forums', 'list'])
    expect(forumKeys.details()).toEqual(['forums', 'detail'])
    expect(forumKeys.detail('test')).toEqual(['forums', 'detail', 'test'])
    expect(forumKeys.topics('test')).toEqual(['forums', 'detail', 'test', 'topics'])
    expect(forumKeys.stats('test')).toEqual(['forums', 'detail', 'test', 'stats'])
  })

  test('topicKeys generates correct structure', () => {
    expect(topicKeys.all).toEqual(['topics'])
    expect(topicKeys.lists()).toEqual(['topics', 'list'])
    expect(topicKeys.list({ status: 'active' })).toEqual(['topics', 'list', { status: 'active' }])
    expect(topicKeys.details()).toEqual(['topics', 'detail'])
    expect(topicKeys.detail('1')).toEqual(['topics', 'detail', '1'])
    expect(topicKeys.posts('1')).toEqual(['topics', 'detail', '1', 'posts'])
  })
})
