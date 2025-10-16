import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { sanitizeHTML } from '../utils/sanitize'
import {
  MessageSquare,
  Clock,
  Eye,
  ArrowLeft,
  User,
  Calendar,
  Hash,
  ChevronRight,
  Edit,
  Trash2,
  MoreVertical,
  Lock,
  Unlock,
  Pin,
  PinOff,
  Move,
  Shield
} from 'lucide-react'
import { format } from 'date-fns'
import { useTopicDetail, useTopicPosts, useDeletePost, useLockTopic, usePinTopic } from '../hooks/useForumQuery'
import { useAuth } from '../contexts/AuthContext'
import { useQueryClient } from '@tanstack/react-query'
import PostCreateForm from '../components/forum/PostCreateForm'
import PostEditForm from '../components/forum/PostEditForm'
import toast from 'react-hot-toast'

export default function ForumTopicPage() {
  const { forumSlug, forumId, topicSlug, topicId} = useParams()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [editingPostId, setEditingPostId] = useState(null)
  const [showReplyForm, setShowReplyForm] = useState(false)
  const [showModerationMenu, setShowModerationMenu] = useState(false)
  const menuRef = useRef(null)
  const menuButtonRef = useRef(null)

  // Fetch topic and posts with React Query
  const { data: topic, isLoading: loadingTopic, error: topicError } = useTopicDetail(topicId)
  const { data: postsData, isLoading: loadingPosts } = useTopicPosts(topicId, { page: 1, page_size: 100 })
  const deletePostMutation = useDeletePost()
  const lockTopicMutation = useLockTopic()
  const pinTopicMutation = usePinTopic()

  const posts = postsData?.results || []
  const loading = loadingTopic || loadingPosts
  const error = topicError?.message || null
  const moderationLoading = lockTopicMutation.isPending || pinTopicMutation.isPending

  // Keyboard navigation - close moderation menu on Escape
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && showModerationMenu) {
        setShowModerationMenu(false)
        // Return focus to trigger button
        menuButtonRef.current?.focus()
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [showModerationMenu])

  // Focus management for moderation menu
  useEffect(() => {
    if (showModerationMenu && menuRef.current) {
      // Focus first menu item when opened
      const firstMenuItem = menuRef.current.querySelector('[role="menuitem"]')
      firstMenuItem?.focus()
    }
  }, [showModerationMenu])

  const formatTimeAgo = (date) => {
    if (!date) return 'unknown'
    const now = new Date()
    const targetDate = new Date(date)
    const diff = now - targetDate
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    if (minutes > 0) return `${minutes}m ago`
    return 'just now'
  }

  const getDisplayName = (poster) => {
    if (poster.first_name || poster.last_name) {
      return `${poster.first_name || ''} ${poster.last_name || ''}`.trim()
    }
    return poster.username
  }

  const handleReplyCreated = (newPost) => {
    // React Query will automatically refetch the posts and topic
    queryClient.invalidateQueries({ queryKey: ['topics', topicId, 'posts'] })
    queryClient.invalidateQueries({ queryKey: ['topics', topicId] })
    setShowReplyForm(false)
    toast.success('Reply posted successfully!')
  }

  const handlePostEdited = (updatedPost) => {
    // React Query will automatically refetch the posts
    queryClient.invalidateQueries({ queryKey: ['topics', topicId, 'posts'] })
    setEditingPostId(null)
    toast.success('Post updated successfully!')
  }

  const handleDeletePost = async (postId) => {
    if (!confirm('Are you sure you want to delete this post?')) {
      return
    }

    try {
      await deletePostMutation.mutateAsync(postId)
      toast.success('Post deleted successfully!')
    } catch (error) {
      console.error('Failed to delete post:', error)
      toast.error('Failed to delete post. Please try again.')
    }
  }

  const canEditPost = (post) => {
    return user && (user.id === post.poster.id || user.is_staff)
  }

  const canDeletePost = (post) => {
    return user && (user.id === post.poster.id || user.is_staff)
  }

  const canModerate = () => {
    return user && (
      user.is_staff ||
      user.is_superuser ||
      (user.trust_level && user.trust_level.level >= 3)
    )
  }

  const handleLockTopic = async () => {
    if (moderationLoading) return

    try {
      const isCurrentlyLocked = topic.status === 'locked' || topic.status === 1
      const lock = !isCurrentlyLocked  // Pass boolean instead of action string

      await lockTopicMutation.mutateAsync({
        topicId,
        lock
      })

      toast.success(`Topic ${lock ? 'locked' : 'unlocked'} successfully!`)
      setShowModerationMenu(false)
    } catch (error) {
      console.error('Failed to lock/unlock topic:', error)
      toast.error(`Failed to ${isCurrentlyLocked ? 'unlock' : 'lock'} topic: ${error.message}`)
    }
  }

  const handlePinTopic = async (pinType = 'sticky') => {
    if (moderationLoading) return

    try {
      const isCurrentlyPinned = topic.type === 'sticky' || topic.type === 'announce' || topic.type === 1 || topic.type === 2
      const pin = !isCurrentlyPinned  // Pass boolean instead of action string

      await pinTopicMutation.mutateAsync({
        topicId,
        pin
      })

      toast.success(`Topic ${pin ? 'pinned' : 'unpinned'} successfully!`)
      setShowModerationMenu(false)
    } catch (error) {
      console.error('Failed to pin/unpin topic:', error)
      toast.error(`Failed to ${isCurrentlyPinned ? 'unpin' : 'pin'} topic: ${error.message}`)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-300 dark:bg-gray-700 rounded w-48 mb-4"></div>
            <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-32"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !topic) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Topic Not Found</h1>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error || 'The topic you are looking for does not exist.'}</p>
          <Link
            to="/forum"
            className="btn-primary inline-flex items-center space-x-2"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Forums</span>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="container-custom py-6">
          {/* Breadcrumb */}
          <nav className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
            <Link to="/forum" className="hover:text-primary transition-colors">
              Forums
            </Link>
            <ChevronRight className="h-4 w-4" />
            <Link to={`/forum/forum/${topic.forum.slug}-${topic.forum.id}/`} className="hover:text-primary transition-colors">
              {topic.forum.name}
            </Link>
            <ChevronRight className="h-4 w-4" />
            <span className="text-gray-900 dark:text-gray-100">{topic.subject}</span>
          </nav>

          {/* Topic Header */}
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-bold">{topic.subject}</h1>
                {(topic.status === 'locked' || topic.status === 1) && (
                  <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-medium rounded-full flex items-center gap-1">
                    <Lock className="w-3 h-3" />
                    Locked
                  </span>
                )}
                {(topic.type === 'sticky' || topic.type === 1) && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full flex items-center gap-1">
                    <Pin className="w-3 h-3" />
                    Pinned
                  </span>
                )}
                {(topic.type === 'announce' || topic.type === 2) && (
                  <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-medium rounded-full flex items-center gap-1">
                    <Pin className="w-3 h-3" />
                    Announcement
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-6 text-sm text-gray-600 dark:text-gray-400">
                <span className="flex items-center space-x-1">
                  <User className="h-4 w-4" />
                  <span>Started by <strong>{getDisplayName(topic.poster)}</strong></span>
                </span>
                <span className="flex items-center space-x-1">
                  <Calendar className="h-4 w-4" />
                  <span>{formatTimeAgo(topic.created)}</span>
                </span>
                <span className="flex items-center space-x-1">
                  <MessageSquare className="h-4 w-4" />
                  <span>{topic.posts_count} {topic.posts_count === 1 ? 'reply' : 'replies'}</span>
                </span>
                <span className="flex items-center space-x-1">
                  <Eye className="h-4 w-4" />
                  <span>{topic.views_count} views</span>
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* Moderation Menu for TL3+ Users */}
              {canModerate() && (
                <div className="relative">
                  <button
                    ref={menuButtonRef}
                    onClick={() => setShowModerationMenu(!showModerationMenu)}
                    className="btn-secondary flex items-center space-x-2"
                    disabled={moderationLoading}
                    aria-label="Open moderation menu"
                    aria-expanded={showModerationMenu}
                    aria-haspopup="true"
                  >
                    <Shield className="h-4 w-4" />
                    <span>Moderate</span>
                  </button>
                  {showModerationMenu && (
                    <div
                      ref={menuRef}
                      className="absolute right-0 top-full mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-1 min-w-[180px] z-10"
                      role="menu"
                      aria-label="Moderation actions"
                    >
                      <button
                        onClick={handleLockTopic}
                        disabled={moderationLoading}
                        className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-2 disabled:opacity-50"
                        role="menuitem"
                        tabIndex={0}
                      >
                        {(topic.status === 'locked' || topic.status === 1) ? (
                          <>
                            <Unlock className="w-4 h-4" />
                            <span>Unlock Topic</span>
                          </>
                        ) : (
                          <>
                            <Lock className="w-4 h-4" />
                            <span>Lock Topic</span>
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => handlePinTopic('sticky')}
                        disabled={moderationLoading}
                        className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-2 disabled:opacity-50"
                        role="menuitem"
                        tabIndex={0}
                      >
                        {(topic.type === 'sticky' || topic.type === 'announce' || topic.type === 1 || topic.type === 2) ? (
                          <>
                            <PinOff className="w-4 h-4" />
                            <span>Unpin Topic</span>
                          </>
                        ) : (
                          <>
                            <Pin className="w-4 h-4" />
                            <span>Pin Topic</span>
                          </>
                        )}
                      </button>
                      <Link
                        to="/forum/moderation/queue"
                        className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-2 border-t border-gray-200 dark:border-gray-700 mt-1 pt-2"
                        role="menuitem"
                        tabIndex={0}
                      >
                        <Shield className="w-4 h-4" />
                        <span>Moderation Queue</span>
                      </Link>
                    </div>
                  )}
                </div>
              )}
              <Link
                to="/forum"
                className="btn-secondary flex items-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Back to Forums</span>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Posts */}
      <div className="container-custom py-8">
        <div className="space-y-6">
          {posts.map((post, index) => (
            <div key={post.id} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              {/* Post Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                    <span className="text-sm font-medium">
                      {getDisplayName(post.poster)[0].toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium">{getDisplayName(post.poster)}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {formatTimeAgo(post.created)}
                      {post.updated && post.updated !== post.created && (
                        <span> • Edited {formatTimeAgo(post.updated)}</span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">
                    <Hash className="h-3 w-3" />
                    <span>{post.position}</span>
                  </span>
                  
                  {/* Post Actions */}
                  {(canEditPost(post) || canDeletePost(post)) && (
                    <div className="relative group">
                      <button className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                        <MoreVertical className="w-4 h-4" />
                      </button>
                      <div className="absolute right-0 top-8 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-1 min-w-[120px] opacity-0 group-hover:opacity-100 transition-opacity z-10">
                        {canEditPost(post) && (
                          <button
                            onClick={() => setEditingPostId(post.id)}
                            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-2"
                          >
                            <Edit className="w-3 h-3" />
                            <span>Edit</span>
                          </button>
                        )}
                        {canDeletePost(post) && (
                          <button
                            onClick={() => handleDeletePost(post.id)}
                            className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 text-red-600 dark:text-red-400 flex items-center space-x-2"
                          >
                            <Trash2 className="w-3 h-3" />
                            <span>Delete</span>
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Post Content or Edit Form */}
              {editingPostId === post.id ? (
                <div className="p-6">
                  <PostEditForm
                    post={post}
                    onEditComplete={handlePostEdited}
                    onCancel={() => setEditingPostId(null)}
                  />
                </div>
              ) : (
                <div className="p-6">
                  <div
                    className="prose prose-gray dark:prose-invert max-w-none"
                    dangerouslySetInnerHTML={{ __html: sanitizeHTML(post.content, { mode: 'default' }) }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Reply Section */}
        <div className="mt-8">
          {showReplyForm ? (
            <PostCreateForm
              topicId={topicId}
              onReplyCreated={handleReplyCreated}
              placeholder="Write your reply to this topic..."
              buttonText="Post Reply"
              showCancel={true}
              onCancel={() => setShowReplyForm(false)}
            />
          ) : (
            <div className="text-center">
              <button
                onClick={() => setShowReplyForm(true)}
                className="btn-primary inline-flex items-center space-x-2"
              >
                <MessageSquare className="h-4 w-4" />
                <span>Reply to Topic</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}