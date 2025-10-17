# Optimize Forum Post List with Cursor Pagination

**Priority**: 🟡 P1 - HIGH
**Category**: Performance
**Effort**: 6-8 hours
**Deadline**: Within 2 weeks

## Problem

Forum topic page fetches ALL posts (up to 100) on every reply, causing performance degradation and wasted bandwidth. This also triggers full refetches on every new reply instead of optimistically updating.

## Location

`frontend/src/pages/ForumTopicPage.jsx:43,97-110`

## Current Code

```jsx
// Fetches 100 posts every time
const { data: postsData } = useTopicPosts(topicId, {
    page: 1,
    page_size: 100
})

const handleReplyCreated = (newPost) => {
    // Invalidates and refetches ALL 100 posts!
    queryClient.invalidateQueries({ queryKey: ['topics', topicId, 'posts'] })
}
```

## Performance Impact

- **100 posts × 2KB** = 200KB per fetch
- After every reply: **200KB re-downloaded**
- 10 replies in thread = **2MB wasted bandwidth**
- Mobile users: **significant data usage**
- **5-10 second delays** on slow connections

## Solution

Implement cursor-based infinite scroll pagination with optimistic updates.

## Implementation Steps

### Step 1: Update Backend to Support Cursor Pagination

```python
# apps/forum_integration/views.py
from rest_framework.pagination import CursorPagination
from rest_framework.decorators import api_view
from rest_framework.response import Response


class PostCursorPagination(CursorPagination):
    """
    Cursor-based pagination for forum posts.
    More efficient than offset pagination for large datasets.
    """
    page_size = 20
    ordering = 'created_at'  # Important: must be indexed!
    cursor_query_param = 'cursor'


@api_view(['GET'])
def topic_posts(request, topic_id):
    """
    Get paginated posts for a topic using cursor pagination.
    """
    try:
        topic = Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return Response(
            {'error': 'Topic not found'},
            status=404
        )

    # Optimize query with prefetch
    posts = Post.objects.filter(
        topic=topic
    ).select_related(
        'author',
        'author__profile'
    ).prefetch_related(
        'reactions'
    ).order_by('created_at')

    # Apply cursor pagination
    paginator = PostCursorPagination()
    paginated_posts = paginator.paginate_queryset(posts, request)

    # Serialize
    posts_data = []
    for post in paginated_posts:
        posts_data.append({
            'id': post.id,
            'content': post.content,
            'author': {
                'id': post.author.id,
                'username': post.author.username,
                'avatar': post.author.profile.avatar.url if post.author.profile.avatar else None,
                'trust_level': post.author.profile.trust_level,
            },
            'created_at': post.created_at,
            'updated_at': post.updated_at,
            'is_edited': post.updated_at > post.created_at,
            'reaction_count': post.reactions.count(),
        })

    # Return paginated response
    return paginator.get_paginated_response(posts_data)
```

### Step 2: Create React Hook for Infinite Posts

```jsx
// frontend/src/hooks/useInfiniteTopicPosts.js
import { useInfiniteQuery } from '@tanstack/react-query'

export function useInfiniteTopicPosts(topicId) {
    return useInfiniteQuery({
        queryKey: ['topics', topicId, 'posts'],
        queryFn: async ({ pageParam = null }) => {
            const url = new URL(`/api/v1/forum/topics/${topicId}/posts/`, window.location.origin)

            if (pageParam) {
                url.searchParams.set('cursor', pageParam)
            }

            const response = await fetch(url, {
                credentials: 'include',
            })

            if (!response.ok) {
                throw new Error('Failed to fetch posts')
            }

            return response.json()
        },
        getNextPageParam: (lastPage) => {
            // Extract cursor from 'next' URL
            if (lastPage.next) {
                const url = new URL(lastPage.next)
                return url.searchParams.get('cursor')
            }
            return undefined
        },
        staleTime: 30000, // 30 seconds
        cacheTime: 5 * 60 * 1000, // 5 minutes
    })
}
```

### Step 3: Update ForumTopicPage Component

```jsx
// frontend/src/pages/ForumTopicPage.jsx
import { useInfiniteTopicPosts } from '../hooks/useInfiniteTopicPosts'
import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useRef, useEffect } from 'react'

const ForumTopicPage = () => {
    const { topicId } = useParams()
    const queryClient = useQueryClient()

    // Infinite posts query
    const {
        data,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
        isLoading,
        isError,
    } = useInfiniteTopicPosts(topicId)

    // Intersection observer for infinite scroll
    const observerTarget = useRef(null)

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
                    fetchNextPage()
                }
            },
            { threshold: 1.0 }
        )

        if (observerTarget.current) {
            observer.observe(observerTarget.current)
        }

        return () => observer.disconnect()
    }, [hasNextPage, isFetchingNextPage, fetchNextPage])

    // Optimistic update on new reply
    const handleReplyCreated = useCallback((newPost) => {
        queryClient.setQueryData(
            ['topics', topicId, 'posts'],
            (oldData) => {
                if (!oldData) return oldData

                // Add new post to the last page
                const newPages = [...oldData.pages]
                const lastPage = newPages[newPages.length - 1]

                return {
                    ...oldData,
                    pages: [
                        ...newPages.slice(0, -1),
                        {
                            ...lastPage,
                            results: [...lastPage.results, newPost],
                        },
                    ],
                }
            }
        )

        // Scroll to new post
        setTimeout(() => {
            const newPostElement = document.getElementById(`post-${newPost.id}`)
            newPostElement?.scrollIntoView({ behavior: 'smooth' })
        }, 100)
    }, [queryClient, topicId])

    // Flatten all pages into single array
    const allPosts = data?.pages.flatMap((page) => page.results) ?? []

    if (isLoading) {
        return <LoadingSpinner />
    }

    if (isError) {
        return <ErrorMessage />
    }

    return (
        <div className="forum-topic-page">
            <TopicHeader topic={data.pages[0].topic} />

            <div className="posts-list">
                {allPosts.map((post) => (
                    <PostCard key={post.id} post={post} />
                ))}

                {/* Infinite scroll trigger */}
                {hasNextPage && (
                    <div
                        ref={observerTarget}
                        className="load-more-trigger"
                    >
                        {isFetchingNextPage ? (
                            <LoadingSpinner />
                        ) : (
                            <button onClick={() => fetchNextPage()}>
                                Load More
                            </button>
                        )}
                    </div>
                )}
            </div>

            <ReplyForm
                topicId={topicId}
                onReplyCreated={handleReplyCreated}
            />
        </div>
    )
}

export default ForumTopicPage
```

### Step 4: Update ReplyForm Component

```jsx
// frontend/src/components/forum/ReplyForm.jsx
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

const ReplyForm = ({ topicId, onReplyCreated }) => {
    const [content, setContent] = useState('')

    const createReplyMutation = useMutation({
        mutationFn: async (replyData) => {
            const response = await fetch(`/api/v1/forum/topics/${topicId}/posts/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(replyData),
            })

            if (!response.ok) {
                throw new Error('Failed to create reply')
            }

            return response.json()
        },
        onSuccess: (newPost) => {
            // Optimistic update via callback
            onReplyCreated(newPost)

            // Clear form
            setContent('')
        },
    })

    const handleSubmit = (e) => {
        e.preventDefault()

        if (!content.trim()) return

        createReplyMutation.mutate({
            content: content.trim(),
        })
    }

    return (
        <form onSubmit={handleSubmit} className="reply-form">
            <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Write your reply..."
                rows={4}
                disabled={createReplyMutation.isPending}
            />

            <button
                type="submit"
                disabled={!content.trim() || createReplyMutation.isPending}
            >
                {createReplyMutation.isPending ? 'Posting...' : 'Post Reply'}
            </button>

            {createReplyMutation.isError && (
                <div className="error-message">
                    Failed to post reply. Please try again.
                </div>
            )}
        </form>
    )
}

export default ReplyForm
```

### Step 5: Add Database Index for Cursor Pagination

```python
# apps/forum_integration/models.py

class Post(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            # Critical for cursor pagination performance
            models.Index(
                fields=['topic', 'created_at'],
                name='post_topic_created_idx'
            ),
        ]
        ordering = ['created_at']
```

```bash
# Create and apply migration
python manage.py makemigrations forum_integration --name add_cursor_pagination_index
python manage.py migrate forum_integration
```

### Step 6: Add Loading States

```jsx
// frontend/src/components/forum/LoadingSpinner.jsx
const LoadingSpinner = () => (
    <div className="loading-spinner">
        <div className="spinner-circle"></div>
        <span>Loading posts...</span>
    </div>
)

export default LoadingSpinner
```

### Step 7: Add Error Boundary

```jsx
// frontend/src/components/forum/PostsErrorBoundary.jsx
import { Component } from 'react'

class PostsErrorBoundary extends Component {
    constructor(props) {
        super(props)
        this.state = { hasError: false }
    }

    static getDerivedStateFromError(error) {
        return { hasError: true }
    }

    componentDidCatch(error, errorInfo) {
        console.error('Forum posts error:', error, errorInfo)
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="error-boundary">
                    <h2>Something went wrong loading posts</h2>
                    <button onClick={() => window.location.reload()}>
                        Reload Page
                    </button>
                </div>
            )
        }

        return this.props.children
    }
}

export default PostsErrorBoundary
```

## Testing

```javascript
// tests/forum/pagination.test.jsx
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ForumTopicPage from '../ForumTopicPage'
import { vi } from 'vitest'

describe('Forum Pagination', () => {
    it('should load initial posts on mount', async () => {
        const queryClient = new QueryClient()

        render(
            <QueryClientProvider client={queryClient}>
                <ForumTopicPage />
            </QueryClientProvider>
        )

        await waitFor(() => {
            expect(screen.getByText(/post 1/i)).toBeInTheDocument()
        })
    })

    it('should load more posts on scroll', async () => {
        const queryClient = new QueryClient()

        render(
            <QueryClientProvider client={queryClient}>
                <ForumTopicPage />
            </QueryClientProvider>
        )

        // Scroll to bottom
        const loadMoreButton = await screen.findByText(/load more/i)
        loadMoreButton.click()

        await waitFor(() => {
            expect(screen.getByText(/post 21/i)).toBeInTheDocument()
        })
    })

    it('should optimistically add new reply', async () => {
        const queryClient = new QueryClient()

        render(
            <QueryClientProvider client={queryClient}>
                <ForumTopicPage />
            </QueryClientProvider>
        )

        // Submit new reply
        const textarea = screen.getByPlaceholderText(/write your reply/i)
        const submitButton = screen.getByText(/post reply/i)

        fireEvent.change(textarea, { target: { value: 'New test reply' } })
        fireEvent.click(submitButton)

        // Should appear immediately (optimistic)
        await waitFor(() => {
            expect(screen.getByText(/new test reply/i)).toBeInTheDocument()
        })
    })
})
```

## Verification

### Before Fix
```
Network tab shows:
- Initial load: 200KB (100 posts)
- After reply 1: 200KB (refetch all 100)
- After reply 2: 200KB (refetch all 100)
- Total for 3 replies: 600KB
```

### After Fix
```
Network tab shows:
- Initial load: 40KB (20 posts)
- Scroll page 2: 40KB (20 more posts)
- After reply: 2KB (optimistic update, then revalidate)
- Total for 3 replies: ~86KB (7x reduction!)
```

## Checklist

- [ ] Backend cursor pagination implemented
- [ ] Database index added for created_at
- [ ] useInfiniteQuery hook created
- [ ] ForumTopicPage refactored to use infinite scroll
- [ ] Intersection observer for auto-loading
- [ ] Optimistic updates on new reply
- [ ] Loading states implemented
- [ ] Error boundary added
- [ ] Tests added and passing
- [ ] Manual testing confirms bandwidth reduction

## Expected Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Initial load | 200KB | 40KB | 80% reduction |
| Per reply bandwidth | 200KB | 2KB | 99% reduction |
| Load time (slow 3G) | 8-10s | 1-2s | 5x faster |
| Mobile data usage | High | Low | 80% reduction |

## References

- React Query: Infinite Queries
- DRF: Cursor Pagination
- Intersection Observer API
- Comprehensive Security Audit 2025, Finding #9
