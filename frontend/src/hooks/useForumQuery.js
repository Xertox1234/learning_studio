/**
 * React Query hooks for forum operations
 * Provides caching, background refetching, and optimistic updates
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as forumApi from '../api/forumApi'

// ===========================
// QUERY KEYS
// ===========================

export const forumKeys = {
  all: ['forums'],
  lists: () => [...forumKeys.all, 'list'],
  list: () => [...forumKeys.lists()],
  details: () => [...forumKeys.all, 'detail'],
  detail: (slug) => [...forumKeys.details(), slug],
  topics: (slug) => [...forumKeys.detail(slug), 'topics'],
  stats: (slug) => [...forumKeys.detail(slug), 'stats'],
}

export const topicKeys = {
  all: ['topics'],
  lists: () => [...topicKeys.all, 'list'],
  list: (filters) => [...topicKeys.lists(), filters],
  details: () => [...topicKeys.all, 'detail'],
  detail: (id) => [...topicKeys.details(), id],
  posts: (id) => [...topicKeys.detail(id), 'posts'],
}

export const postKeys = {
  all: ['posts'],
  lists: () => [...postKeys.all, 'list'],
  list: (filters) => [...postKeys.lists(), filters],
  details: () => [...postKeys.all, 'detail'],
  detail: (id) => [...postKeys.details(), id],
}

export const moderationKeys = {
  all: ['moderation'],
  queue: (filters) => [...moderationKeys.all, 'queue', filters],
  stats: () => [...moderationKeys.all, 'stats'],
  analytics: () => [...moderationKeys.all, 'analytics'],
}

// ===========================
// FORUM HOOKS
// ===========================

/**
 * Get all forums organized by category
 */
export const useForums = (options = {}) => {
  return useQuery({
    queryKey: forumKeys.list(),
    queryFn: forumApi.getForums,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  })
}

/**
 * Get forum details by slug
 */
export const useForumDetail = (slug, options = {}) => {
  return useQuery({
    queryKey: forumKeys.detail(slug),
    queryFn: () => forumApi.getForumDetail(slug),
    enabled: !!slug,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  })
}

/**
 * Get topics for a specific forum
 */
export const useForumTopics = (slug, params = {}, options = {}) => {
  return useQuery({
    queryKey: [...forumKeys.topics(slug), params],
    queryFn: () => forumApi.getForumTopics(slug, params),
    enabled: !!slug,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  })
}

/**
 * Get forum statistics
 */
export const useForumStats = (slug, options = {}) => {
  return useQuery({
    queryKey: forumKeys.stats(slug),
    queryFn: () => forumApi.getForumStats(slug),
    enabled: !!slug,
    staleTime: 1 * 60 * 1000, // 1 minute
    ...options,
  })
}

// ===========================
// TOPIC HOOKS
// ===========================

/**
 * Get all topics with filtering
 */
export const useTopics = (filters = {}, options = {}) => {
  return useQuery({
    queryKey: topicKeys.list(filters),
    queryFn: () => forumApi.getTopics(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  })
}

/**
 * Get topic details
 */
export const useTopicDetail = (topicId, options = {}) => {
  return useQuery({
    queryKey: topicKeys.detail(topicId),
    queryFn: () => forumApi.getTopicDetail(topicId),
    enabled: !!topicId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  })
}

/**
 * Get posts for a specific topic
 */
export const useTopicPosts = (topicId, params = {}, options = {}) => {
  return useQuery({
    queryKey: [...topicKeys.posts(topicId), params],
    queryFn: () => forumApi.getTopicPosts(topicId, params),
    enabled: !!topicId,
    staleTime: 1 * 60 * 1000, // 1 minute
    ...options,
  })
}

/**
 * Create a new topic with optimistic update
 */
export const useCreateTopic = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: forumApi.createTopic,
    onSuccess: (newTopic) => {
      // Invalidate and refetch forums list
      queryClient.invalidateQueries({ queryKey: forumKeys.lists() })
      // Invalidate topics list
      queryClient.invalidateQueries({ queryKey: topicKeys.lists() })
      // If we know the forum, invalidate forum topics
      if (newTopic.forum) {
        queryClient.invalidateQueries({
          queryKey: forumKeys.topics(newTopic.forum.slug)
        })
      }
    },
  })
}

/**
 * Update a topic
 */
export const useUpdateTopic = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ topicId, updateData }) => forumApi.updateTopic(topicId, updateData),
    onMutate: async ({ topicId, updateData }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: topicKeys.detail(topicId) })

      // Snapshot previous value
      const previousTopic = queryClient.getQueryData(topicKeys.detail(topicId))

      // Optimistically update
      queryClient.setQueryData(topicKeys.detail(topicId), (old) => ({
        ...old,
        ...updateData,
      }))

      return { previousTopic }
    },
    onError: (err, { topicId }, context) => {
      // Rollback on error
      if (context?.previousTopic) {
        queryClient.setQueryData(topicKeys.detail(topicId), context.previousTopic)
      }
    },
    onSettled: (data, error, { topicId }) => {
      // Refetch after mutation
      queryClient.invalidateQueries({ queryKey: topicKeys.detail(topicId) })
      queryClient.invalidateQueries({ queryKey: topicKeys.lists() })
    },
  })
}

/**
 * Delete a topic
 */
export const useDeleteTopic = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: forumApi.deleteTopic,
    onSuccess: (_, topicId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: topicKeys.detail(topicId) })
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: topicKeys.lists() })
      queryClient.invalidateQueries({ queryKey: forumKeys.lists() })
    },
  })
}

/**
 * Subscribe to a topic
 */
export const useSubscribeTopic = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: forumApi.subscribeTopic,
    onSuccess: (_, topicId) => {
      queryClient.invalidateQueries({ queryKey: topicKeys.detail(topicId) })
    },
  })
}

/**
 * Unsubscribe from a topic
 */
export const useUnsubscribeTopic = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: forumApi.unsubscribeTopic,
    onSuccess: (_, topicId) => {
      queryClient.invalidateQueries({ queryKey: topicKeys.detail(topicId) })
    },
  })
}

/**
 * Lock/unlock a topic
 */
export const useLockTopic = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ topicId, lock }) =>
      lock ? forumApi.lockTopic(topicId) : forumApi.unlockTopic(topicId),
    onSuccess: (_, { topicId }) => {
      queryClient.invalidateQueries({ queryKey: topicKeys.detail(topicId) })
      queryClient.invalidateQueries({ queryKey: topicKeys.lists() })
    },
  })
}

/**
 * Pin/unpin a topic
 */
export const usePinTopic = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ topicId, pin }) =>
      pin ? forumApi.pinTopic(topicId) : forumApi.unpinTopic(topicId),
    onSuccess: (_, { topicId }) => {
      queryClient.invalidateQueries({ queryKey: topicKeys.detail(topicId) })
      queryClient.invalidateQueries({ queryKey: topicKeys.lists() })
    },
  })
}

/**
 * Move topic to another forum
 */
export const useMoveTopic = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ topicId, forumId }) => forumApi.moveTopic(topicId, forumId),
    onSuccess: (_, { topicId }) => {
      queryClient.invalidateQueries({ queryKey: topicKeys.detail(topicId) })
      queryClient.invalidateQueries({ queryKey: topicKeys.lists() })
      queryClient.invalidateQueries({ queryKey: forumKeys.lists() })
    },
  })
}

// ===========================
// POST HOOKS
// ===========================

/**
 * Get all posts with filtering
 */
export const usePosts = (filters = {}, options = {}) => {
  return useQuery({
    queryKey: postKeys.list(filters),
    queryFn: () => forumApi.getPosts(filters),
    staleTime: 1 * 60 * 1000, // 1 minute
    ...options,
  })
}

/**
 * Get post details
 */
export const usePostDetail = (postId, options = {}) => {
  return useQuery({
    queryKey: postKeys.detail(postId),
    queryFn: () => forumApi.getPostDetail(postId),
    enabled: !!postId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  })
}

/**
 * Create a new post with optimistic update
 */
export const useCreatePost = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: forumApi.createPost,
    onMutate: async (newPost) => {
      // Cancel outgoing refetches for this topic's posts
      await queryClient.cancelQueries({
        queryKey: topicKeys.posts(newPost.topic)
      })

      // Snapshot previous value
      const previousPosts = queryClient.getQueryData(
        topicKeys.posts(newPost.topic)
      )

      // Optimistically add new post
      queryClient.setQueryData(topicKeys.posts(newPost.topic), (old) => {
        if (!old) return old
        return {
          ...old,
          results: [
            ...old.results,
            {
              ...newPost,
              id: -Date.now(), // Negative IDs are clearly temporary
              created_at: new Date().toISOString(),
              approved: false, // May need approval
              _isOptimistic: true, // Flag for UI to show pending state
            },
          ],
        }
      })

      return { previousPosts }
    },
    onError: (err, newPost, context) => {
      // Rollback on error
      if (context?.previousPosts) {
        queryClient.setQueryData(
          topicKeys.posts(newPost.topic),
          context.previousPosts
        )
      }
    },
    onSuccess: (newPost) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({
        queryKey: topicKeys.posts(newPost.topic)
      })
      queryClient.invalidateQueries({
        queryKey: topicKeys.detail(newPost.topic)
      })
      queryClient.invalidateQueries({ queryKey: forumKeys.lists() })
    },
  })
}

/**
 * Update a post
 */
export const useUpdatePost = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ postId, updateData }) => forumApi.updatePost(postId, updateData),
    onMutate: async ({ postId, updateData }) => {
      await queryClient.cancelQueries({ queryKey: postKeys.detail(postId) })

      const previousPost = queryClient.getQueryData(postKeys.detail(postId))

      queryClient.setQueryData(postKeys.detail(postId), (old) => ({
        ...old,
        ...updateData,
      }))

      return { previousPost }
    },
    onError: (err, { postId }, context) => {
      if (context?.previousPost) {
        queryClient.setQueryData(postKeys.detail(postId), context.previousPost)
      }
    },
    onSettled: (data, error, { postId }) => {
      queryClient.invalidateQueries({ queryKey: postKeys.detail(postId) })
      queryClient.invalidateQueries({ queryKey: postKeys.lists() })
    },
  })
}

/**
 * Delete a post
 */
export const useDeletePost = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: forumApi.deletePost,
    onSuccess: (_, postId) => {
      queryClient.removeQueries({ queryKey: postKeys.detail(postId) })
      queryClient.invalidateQueries({ queryKey: postKeys.lists() })
      queryClient.invalidateQueries({ queryKey: topicKeys.all })
    },
  })
}

/**
 * Get formatted quote for a post
 */
export const useQuotePost = () => {
  return useMutation({
    mutationFn: forumApi.quotePost,
  })
}

// ===========================
// MODERATION HOOKS
// ===========================

/**
 * Get moderation queue
 */
export const useModerationQueue = (filters = {}, options = {}) => {
  return useQuery({
    queryKey: moderationKeys.queue(filters),
    queryFn: () => forumApi.getModerationQueue(filters),
    staleTime: 30 * 1000, // 30 seconds - moderation queue should be fresh
    ...options,
  })
}

/**
 * Review a moderation queue item
 */
export const useReviewModeration = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ itemId, action, reason }) =>
      forumApi.reviewModerationItem(itemId, action, reason),
    onSuccess: () => {
      // Invalidate all moderation queries
      queryClient.invalidateQueries({ queryKey: moderationKeys.all })
      // Also invalidate posts/topics as they may have been approved
      queryClient.invalidateQueries({ queryKey: postKeys.all })
      queryClient.invalidateQueries({ queryKey: topicKeys.all })
    },
  })
}

/**
 * Get moderation statistics
 */
export const useModerationStats = (options = {}) => {
  return useQuery({
    queryKey: moderationKeys.stats(),
    queryFn: forumApi.getModerationStats,
    staleTime: 1 * 60 * 1000, // 1 minute
    ...options,
  })
}

/**
 * Get moderation analytics
 */
export const useModerationAnalytics = (filters = {}, options = {}) => {
  return useQuery({
    queryKey: [...moderationKeys.analytics(), filters],
    queryFn: () => forumApi.getModerationAnalytics(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  })
}
