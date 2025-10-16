/**
 * Forum API Client - Uses v2 DRF ViewSet endpoints
 * Provides centralized access to all forum operations
 */

const API_BASE = '/api/v2/forum'

/**
 * Helper function to get auth token from localStorage or cookie
 */
const getAuthToken = () => {
  // Try localStorage first (if using JWT)
  const token = localStorage.getItem('access_token')
  if (token) {
    // Validate JWT format (header.payload.signature)
    if (!/^[\w-]+\.[\w-]+\.[\w-]+$/.test(token)) {
      console.warn('Invalid token format detected, removing')
      localStorage.removeItem('access_token')
      return null
    }
    return token
  }

  // Fallback to reading from cookie (if using session auth)
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? match[1] : null
}

/**
 * Generic API request helper
 */
const apiRequest = async (endpoint, options = {}) => {
  const token = getAuthToken()
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    // Check if it's a JWT (contains dots) or CSRF token
    if (token.includes('.')) {
      headers['Authorization'] = `Bearer ${token}`
    } else {
      headers['X-CSRFToken'] = token
    }
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include', // Include cookies for Django session auth
  })

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`
    try {
      const error = await response.json()
      errorMessage = error.error || error.detail || errorMessage
    } catch (parseError) {
      // JSON parse failed, use default message with response text
      const text = await response.text().catch(() => '')
      if (text) errorMessage += ` - ${text.substring(0, 200)}`
    }

    const apiError = new Error(errorMessage)
    apiError.status = response.status
    apiError.response = response
    throw apiError
  }

  return response.json()
}

// ===========================
// FORUM ENDPOINTS
// ===========================

/**
 * Get all forums organized by category
 * @returns {Promise<{categories: Array, stats: Object}>}
 */
export const getForums = async () => {
  return apiRequest('/forums/')
}

/**
 * Get forum details by slug
 * @param {string} slug - Forum slug
 * @returns {Promise<Object>}
 */
export const getForumDetail = async (slug) => {
  return apiRequest(`/forums/${slug}/`)
}

/**
 * Get topics for a specific forum
 * @param {string} slug - Forum slug
 * @param {Object} params - Query parameters (page, page_size)
 * @returns {Promise<{results: Array, pagination: Object}>}
 */
export const getForumTopics = async (slug, params = {}) => {
  const queryString = new URLSearchParams(params).toString()
  return apiRequest(`/forums/${slug}/topics/${queryString ? `?${queryString}` : ''}`)
}

/**
 * Get forum statistics
 * @param {string} slug - Forum slug
 * @returns {Promise<Object>}
 */
export const getForumStats = async (slug) => {
  return apiRequest(`/forums/${slug}/stats/`)
}

// ===========================
// TOPIC ENDPOINTS
// ===========================

/**
 * Get all topics with optional filtering
 * @param {Object} filters - Filter parameters (subject, forum, poster, locked, type, etc.)
 * @returns {Promise<{results: Array, pagination: Object}>}
 */
export const getTopics = async (filters = {}) => {
  const queryString = new URLSearchParams(filters).toString()
  return apiRequest(`/topics/${queryString ? `?${queryString}` : ''}`)
}

/**
 * Create a new topic
 * @param {Object} topicData - Topic data
 * @param {string} topicData.subject - Topic subject/title
 * @param {number} topicData.forum_id - Forum ID
 * @param {string} topicData.first_post_content - Content of the first post
 * @param {number} topicData.type - Topic type (0=regular, 1=sticky, 2=announce)
 * @returns {Promise<Object>}
 */
export const createTopic = async (topicData) => {
  return apiRequest('/topics/', {
    method: 'POST',
    body: JSON.stringify(topicData),
  })
}

/**
 * Get topic details
 * @param {number} topicId - Topic ID
 * @returns {Promise<Object>}
 */
export const getTopicDetail = async (topicId) => {
  return apiRequest(`/topics/${topicId}/`)
}

/**
 * Update a topic
 * @param {number} topicId - Topic ID
 * @param {Object} updateData - Fields to update (subject, type, etc.)
 * @returns {Promise<Object>}
 */
export const updateTopic = async (topicId, updateData) => {
  return apiRequest(`/topics/${topicId}/`, {
    method: 'PUT',
    body: JSON.stringify(updateData),
  })
}

/**
 * Delete a topic
 * @param {number} topicId - Topic ID
 * @returns {Promise<void>}
 */
export const deleteTopic = async (topicId) => {
  return apiRequest(`/topics/${topicId}/`, {
    method: 'DELETE',
  })
}

/**
 * Get posts for a specific topic
 * @param {number} topicId - Topic ID
 * @param {Object} params - Query parameters (page, page_size)
 * @returns {Promise<{results: Array, pagination: Object}>}
 */
export const getTopicPosts = async (topicId, params = {}) => {
  const queryString = new URLSearchParams(params).toString()
  return apiRequest(`/topics/${topicId}/posts/${queryString ? `?${queryString}` : ''}`)
}

/**
 * Subscribe to a topic
 * @param {number} topicId - Topic ID
 * @returns {Promise<Object>}
 */
export const subscribeTopic = async (topicId) => {
  return apiRequest(`/topics/${topicId}/subscribe/`, {
    method: 'POST',
  })
}

/**
 * Unsubscribe from a topic
 * @param {number} topicId - Topic ID
 * @returns {Promise<Object>}
 */
export const unsubscribeTopic = async (topicId) => {
  return apiRequest(`/topics/${topicId}/unsubscribe/`, {
    method: 'POST',
  })
}

/**
 * Lock a topic (moderators only)
 * @param {number} topicId - Topic ID
 * @returns {Promise<Object>}
 */
export const lockTopic = async (topicId) => {
  return apiRequest(`/topics/${topicId}/lock/`, {
    method: 'POST',
  })
}

/**
 * Unlock a topic (moderators only)
 * @param {number} topicId - Topic ID
 * @returns {Promise<Object>}
 */
export const unlockTopic = async (topicId) => {
  return apiRequest(`/topics/${topicId}/unlock/`, {
    method: 'POST',
  })
}

/**
 * Pin a topic (moderators only)
 * @param {number} topicId - Topic ID
 * @returns {Promise<Object>}
 */
export const pinTopic = async (topicId) => {
  return apiRequest(`/topics/${topicId}/pin/`, {
    method: 'POST',
  })
}

/**
 * Unpin a topic (moderators only)
 * @param {number} topicId - Topic ID
 * @returns {Promise<Object>}
 */
export const unpinTopic = async (topicId) => {
  return apiRequest(`/topics/${topicId}/unpin/`, {
    method: 'POST',
  })
}

/**
 * Move topic to another forum (moderators only)
 * @param {number} topicId - Topic ID
 * @param {number} forumId - Destination forum ID
 * @returns {Promise<Object>}
 */
export const moveTopic = async (topicId, forumId) => {
  return apiRequest(`/topics/${topicId}/move/`, {
    method: 'POST',
    body: JSON.stringify({ forum_id: forumId }),
  })
}

// ===========================
// POST ENDPOINTS
// ===========================

/**
 * Get all posts with optional filtering
 * @param {Object} filters - Filter parameters (topic, poster, approved, etc.)
 * @returns {Promise<{results: Array, pagination: Object}>}
 */
export const getPosts = async (filters = {}) => {
  const queryString = new URLSearchParams(filters).toString()
  return apiRequest(`/posts/${queryString ? `?${queryString}` : ''}`)
}

/**
 * Create a new post
 * @param {Object} postData - Post data
 * @param {number} postData.topic - Topic ID
 * @param {string} postData.content - Post content
 * @returns {Promise<Object>}
 */
export const createPost = async (postData) => {
  return apiRequest('/posts/', {
    method: 'POST',
    body: JSON.stringify(postData),
  })
}

/**
 * Get post details
 * @param {number} postId - Post ID
 * @returns {Promise<Object>}
 */
export const getPostDetail = async (postId) => {
  return apiRequest(`/posts/${postId}/`)
}

/**
 * Update a post
 * @param {number} postId - Post ID
 * @param {Object} updateData - Fields to update (content, etc.)
 * @returns {Promise<Object>}
 */
export const updatePost = async (postId, updateData) => {
  return apiRequest(`/posts/${postId}/`, {
    method: 'PUT',
    body: JSON.stringify(updateData),
  })
}

/**
 * Delete a post
 * @param {number} postId - Post ID
 * @returns {Promise<void>}
 */
export const deletePost = async (postId) => {
  return apiRequest(`/posts/${postId}/`, {
    method: 'DELETE',
  })
}

/**
 * Get formatted quote for a post
 * @param {number} postId - Post ID
 * @returns {Promise<{quoted_content: string}>}
 */
export const quotePost = async (postId) => {
  return apiRequest(`/posts/${postId}/quote/`, {
    method: 'POST',
  })
}

// ===========================
// MODERATION ENDPOINTS
// ===========================

/**
 * Get moderation queue
 * @param {Object} filters - Filter parameters (status, content_type, author, etc.)
 * @returns {Promise<{results: Array, pagination: Object}>}
 */
export const getModerationQueue = async (filters = {}) => {
  const queryString = new URLSearchParams(filters).toString()
  return apiRequest(`/moderation/${queryString ? `?${queryString}` : ''}`)
}

/**
 * Review a moderation queue item
 * @param {number} itemId - Queue item ID
 * @param {string} action - 'approve' or 'reject'
 * @param {string} reason - Optional reason for rejection
 * @returns {Promise<Object>}
 */
export const reviewModerationItem = async (itemId, action, reason = '') => {
  return apiRequest(`/moderation/${itemId}/review/`, {
    method: 'POST',
    body: JSON.stringify({ action, reason }),
  })
}

/**
 * Get moderation statistics
 * @returns {Promise<Object>}
 */
export const getModerationStats = async () => {
  return apiRequest('/moderation/stats/')
}

/**
 * Get moderation analytics
 * @param {Object} filters - Filter parameters (days, etc.)
 * @returns {Promise<Object>}
 */
export const getModerationAnalytics = async (filters = {}) => {
  const queryString = new URLSearchParams(filters).toString()
  return apiRequest(`/moderation/analytics/${queryString ? `?${queryString}` : ''}`)
}

// Default export with all methods
export default {
  // Forums
  getForums,
  getForumDetail,
  getForumTopics,
  getForumStats,

  // Topics
  getTopics,
  createTopic,
  getTopicDetail,
  updateTopic,
  deleteTopic,
  getTopicPosts,
  subscribeTopic,
  unsubscribeTopic,
  lockTopic,
  unlockTopic,
  pinTopic,
  unpinTopic,
  moveTopic,

  // Posts
  getPosts,
  createPost,
  getPostDetail,
  updatePost,
  deletePost,
  quotePost,

  // Moderation
  getModerationQueue,
  reviewModerationItem,
  getModerationStats,
  getModerationAnalytics,
}
