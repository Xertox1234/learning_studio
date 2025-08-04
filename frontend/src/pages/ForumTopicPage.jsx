import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
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
  MoreVertical
} from 'lucide-react'
import axios from 'axios'
import { format } from 'date-fns'
import { apiRequest } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import PostCreateForm from '../components/forum/PostCreateForm'
import PostEditForm from '../components/forum/PostEditForm'

export default function ForumTopicPage() {
  const { forumSlug, forumId, topicSlug, topicId } = useParams()
  const { user } = useAuth()
  const [topic, setTopic] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingPostId, setEditingPostId] = useState(null)
  const [showReplyForm, setShowReplyForm] = useState(false)

  useEffect(() => {
    fetchTopic()
  }, [forumSlug, forumId, topicSlug, topicId])

  const fetchTopic = async () => {
    try {
      console.log('Fetching topic with params:', { forumSlug, forumId, topicSlug, topicId });
      
      const response = await apiRequest(
        `/api/v1/forums/${forumSlug}/${forumId}/topics/${topicSlug}/${topicId}/`
      );
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Topic fetch error:', response.status, errorText);
        throw new Error(`Failed to fetch topic: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Topic data received:', data);
      setTopic(data);
    } catch (error) {
      console.error('Failed to fetch topic:', error);
      setError(error.message || 'Failed to load topic');
    } finally {
      setLoading(false);
    }
  }

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
    // Add the new post to the topic's posts array
    setTopic(prevTopic => ({
      ...prevTopic,
      posts: [...prevTopic.posts, newPost],
      posts_count: prevTopic.posts_count + 1
    }))
    setShowReplyForm(false)
  }

  const handlePostEdited = (updatedPost) => {
    // Update the specific post in the topic's posts array
    setTopic(prevTopic => ({
      ...prevTopic,
      posts: prevTopic.posts.map(post => 
        post.id === updatedPost.id ? updatedPost : post
      )
    }))
    setEditingPostId(null)
  }

  const handleDeletePost = async (postId) => {
    if (!confirm('Are you sure you want to delete this post?')) {
      return
    }

    try {
      const response = await apiRequest(`/api/v1/posts/${postId}/delete/`, {
        method: 'DELETE'
      })

      if (response.ok) {
        // Remove the post from the topic's posts array
        setTopic(prevTopic => ({
          ...prevTopic,
          posts: prevTopic.posts.filter(post => post.id !== postId),
          posts_count: prevTopic.posts_count - 1
        }))
      }
    } catch (error) {
      console.error('Failed to delete post:', error)
      alert('Failed to delete post. Please try again.')
    }
  }

  const canEditPost = (post) => {
    return user && (user.id === post.poster.id || user.is_staff)
  }

  const canDeletePost = (post) => {
    return user && (user.id === post.poster.id || user.is_staff)
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
              <h1 className="text-3xl font-bold mb-2">{topic.subject}</h1>
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

      {/* Posts */}
      <div className="container-custom py-8">
        <div className="space-y-6">
          {topic.posts.map((post, index) => (
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
                    dangerouslySetInnerHTML={{ __html: post.content }}
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