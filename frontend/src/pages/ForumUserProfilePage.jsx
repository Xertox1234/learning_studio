import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  User,
  MessageSquare,
  FileText,
  Award,
  Clock,
  TrendingUp,
  ArrowLeft,
  Calendar,
  Activity,
  Star,
  Target
} from 'lucide-react'
import { apiRequest } from '../utils/api'
import { format } from 'date-fns'

export default function ForumUserProfilePage() {
  const { userId } = useParams()
  const [profile, setProfile] = useState(null)
  const [activeTab, setActiveTab] = useState('overview') // overview, topics, posts
  const [userTopics, setUserTopics] = useState([])
  const [userPosts, setUserPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [topicsPage, setTopicsPage] = useState(1)
  const [postsPage, setPostsPage] = useState(1)
  const [topicsPagination, setTopicsPagination] = useState(null)
  const [postsPagination, setPostsPagination] = useState(null)

  useEffect(() => {
    fetchUserProfile()
  }, [userId])

  useEffect(() => {
    if (activeTab === 'topics' && userTopics.length === 0) {
      fetchUserTopics()
    } else if (activeTab === 'posts' && userPosts.length === 0) {
      fetchUserPosts()
    }
  }, [activeTab])

  const fetchUserProfile = async () => {
    try {
      setLoading(true)
      const response = await apiRequest(`/api/v1/forums/users/${userId}/profile/`)

      if (!response.ok) {
        throw new Error(`Failed to fetch user profile: ${response.status}`)
      }

      const data = await response.json()
      setProfile(data)
    } catch (error) {
      console.error('Failed to fetch user profile:', error)
      setError(error.message || 'Failed to load user profile')
    } finally {
      setLoading(false)
    }
  }

  const fetchUserTopics = async (page = 1) => {
    try {
      const response = await apiRequest(`/api/v1/forums/users/${userId}/topics/?page=${page}`)

      if (!response.ok) {
        throw new Error(`Failed to fetch user topics: ${response.status}`)
      }

      const data = await response.json()
      setUserTopics(data.results || [])
      setTopicsPagination(data.pagination || null)
      setTopicsPage(page)
    } catch (error) {
      console.error('Failed to fetch user topics:', error)
    }
  }

  const fetchUserPosts = async (page = 1) => {
    try {
      const response = await apiRequest(`/api/v1/forums/users/${userId}/posts/?page=${page}`)

      if (!response.ok) {
        throw new Error(`Failed to fetch user posts: ${response.status}`)
      }

      const data = await response.json()
      setUserPosts(data.results || [])
      setPostsPagination(data.pagination || null)
      setPostsPage(page)
    } catch (error) {
      console.error('Failed to fetch user posts:', error)
    }
  }

  const getTrustLevelBadge = (trustLevel) => {
    const badges = {
      0: { name: 'New Member', color: 'bg-gray-500', icon: '🌱' },
      1: { name: 'Basic', color: 'bg-blue-500', icon: '🌿' },
      2: { name: 'Member', color: 'bg-green-500', icon: '🌳' },
      3: { name: 'Regular', color: 'bg-purple-500', icon: '⭐' },
      4: { name: 'Leader', color: 'bg-yellow-500', icon: '👑' }
    }
    return badges[trustLevel] || badges[0]
  }

  const getTrustLevelProgress = (stats) => {
    const trustLevel = stats?.trust_level?.current_level || 0

    // Requirements for next level (simplified - actual requirements are more complex)
    const requirements = {
      0: { topics_read: 5, posts_read: 30, time_period_days: 0, topics_entered: 5 },
      1: { topics_read: 15, posts_read: 100, time_period_days: 10, topics_entered: 15 },
      2: { topics_read: 100, posts_read: 500, time_period_days: 50, topics_entered: 50 },
      3: { topics_read: 250, posts_read: 1000, time_period_days: 100, topics_entered: 100 }
    }

    if (trustLevel >= 4) {
      return { percentage: 100, nextLevel: null }
    }

    const nextReqs = requirements[trustLevel]
    if (!nextReqs) {
      return { percentage: 100, nextLevel: null }
    }

    // Calculate progress based on topics/posts
    const topicsProgress = Math.min((stats.topics_created_count || 0) / nextReqs.topics_entered * 100, 100)
    const postsProgress = Math.min((stats.posts_count || 0) / nextReqs.posts_read * 100, 100)
    const percentage = Math.floor((topicsProgress + postsProgress) / 2)

    return { percentage, nextLevel: trustLevel + 1 }
  }

  const formatDate = (date) => {
    if (!date) return 'Unknown'
    try {
      return format(new Date(date), 'MMM d, yyyy')
    } catch {
      return 'Unknown'
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading user profile...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="bg-red-500/10 border border-red-500 rounded-lg p-6 max-w-md">
          <h2 className="text-red-400 text-xl font-bold mb-2">Error</h2>
          <p className="text-white">{error}</p>
          <Link to="/forum" className="mt-4 inline-block text-blue-400 hover:text-blue-300">
            ← Back to Forum
          </Link>
        </div>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">User profile not found</div>
      </div>
    )
  }

  const trustBadge = getTrustLevelBadge(profile.statistics?.trust_level?.current_level || 0)
  const progress = getTrustLevelProgress(profile.statistics)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <Link to="/forum" className="inline-flex items-center text-blue-400 hover:text-blue-300 mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Forum
          </Link>
          <h1 className="text-4xl font-bold text-white">User Profile</h1>
        </div>

        {/* Profile Header Card */}
        <div className="bg-white/10 backdrop-blur-lg rounded-lg border border-white/20 p-6 mb-6">
          <div className="flex items-start gap-6">
            {/* Avatar */}
            <div className="flex-shrink-0">
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <User className="w-12 h-12 text-white" />
              </div>
            </div>

            {/* User Info */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h2 className="text-3xl font-bold text-white">{profile.user.username}</h2>
                <span className={`${trustBadge.color} text-white px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1`}>
                  <span>{trustBadge.icon}</span>
                  <span>{trustBadge.name}</span>
                </span>
              </div>

              {profile.user.email && (
                <p className="text-gray-300 mb-2">{profile.user.email}</p>
              )}

              <div className="flex flex-wrap gap-4 text-sm text-gray-300">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  <span>Joined {formatDate(profile.user.date_joined)}</span>
                </div>
                {profile.user.last_login && (
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    <span>Last seen {formatTimeAgo(profile.user.last_login)}</span>
                  </div>
                )}
              </div>

              {/* Trust Level Progress */}
              {progress.nextLevel !== null && (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-sm text-gray-300 mb-1">
                    <span>Progress to Level {progress.nextLevel}</span>
                    <span>{progress.percentage}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${progress.percentage}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Statistics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white/10 backdrop-blur-lg rounded-lg border border-white/20 p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <FileText className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{profile.statistics?.topics_created_count || 0}</div>
                <div className="text-sm text-gray-300">Topics Created</div>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-lg border border-white/20 p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <MessageSquare className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{profile.statistics?.posts_count || 0}</div>
                <div className="text-sm text-gray-300">Posts</div>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-lg border border-white/20 p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/20 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{profile.statistics?.likes_received || 0}</div>
                <div className="text-sm text-gray-300">Likes Received</div>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-lg border border-white/20 p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-500/20 rounded-lg">
                <Award className="w-6 h-6 text-yellow-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{profile.statistics?.best_answers || 0}</div>
                <div className="text-sm text-gray-300">Best Answers</div>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white/10 backdrop-blur-lg rounded-lg border border-white/20 overflow-hidden">
          <div className="flex border-b border-white/20">
            <button
              onClick={() => setActiveTab('overview')}
              className={`flex-1 px-6 py-4 font-medium transition-colors ${
                activeTab === 'overview'
                  ? 'bg-white/10 text-white border-b-2 border-blue-500'
                  : 'text-gray-300 hover:text-white hover:bg-white/5'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <Activity className="w-5 h-5" />
                <span>Overview</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('topics')}
              className={`flex-1 px-6 py-4 font-medium transition-colors ${
                activeTab === 'topics'
                  ? 'bg-white/10 text-white border-b-2 border-blue-500'
                  : 'text-gray-300 hover:text-white hover:bg-white/5'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <FileText className="w-5 h-5" />
                <span>Topics ({profile.statistics?.topics_created_count || 0})</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('posts')}
              className={`flex-1 px-6 py-4 font-medium transition-colors ${
                activeTab === 'posts'
                  ? 'bg-white/10 text-white border-b-2 border-blue-500'
                  : 'text-gray-300 hover:text-white hover:bg-white/5'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <MessageSquare className="w-5 h-5" />
                <span>Posts ({profile.statistics?.posts_count || 0})</span>
              </div>
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Recent Activity */}
                <div>
                  <h3 className="text-xl font-bold text-white mb-4">Recent Activity</h3>

                  {/* Recent Topics */}
                  {profile.recent_topics && profile.recent_topics.length > 0 && (
                    <div className="mb-6">
                      <h4 className="text-lg font-semibold text-gray-300 mb-3">Recent Topics</h4>
                      <div className="space-y-3">
                        {profile.recent_topics.map(topic => (
                          <Link
                            key={topic.id}
                            to={`/forum/${topic.forum.slug}/${topic.forum.id}/${topic.slug}/${topic.id}`}
                            className="block bg-white/5 hover:bg-white/10 rounded-lg p-4 border border-white/10 hover:border-white/20 transition-all"
                          >
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1">
                                <h5 className="text-white font-medium mb-1">{topic.subject}</h5>
                                <div className="flex items-center gap-3 text-sm text-gray-400">
                                  <span className="flex items-center gap-1">
                                    <MessageSquare className="w-4 h-4" />
                                    {topic.posts_count || 0}
                                  </span>
                                  <span>{formatTimeAgo(topic.created)}</span>
                                  <span>in {topic.forum.name}</span>
                                </div>
                              </div>
                            </div>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recent Posts */}
                  {profile.recent_posts && profile.recent_posts.length > 0 && (
                    <div>
                      <h4 className="text-lg font-semibold text-gray-300 mb-3">Recent Posts</h4>
                      <div className="space-y-3">
                        {profile.recent_posts.map(post => (
                          <Link
                            key={post.id}
                            to={`/forum/${post.topic.forum.slug}/${post.topic.forum.id}/${post.topic.slug}/${post.topic.id}`}
                            className="block bg-white/5 hover:bg-white/10 rounded-lg p-4 border border-white/10 hover:border-white/20 transition-all"
                          >
                            <div className="flex items-start gap-4">
                              <div className="flex-1">
                                <h5 className="text-white font-medium mb-2">
                                  Re: {post.topic.subject}
                                </h5>
                                <p className="text-gray-300 text-sm line-clamp-2 mb-2">
                                  {post.content.substring(0, 200)}...
                                </p>
                                <div className="flex items-center gap-3 text-sm text-gray-400">
                                  <span>{formatTimeAgo(post.created)}</span>
                                  <span>in {post.topic.forum.name}</span>
                                </div>
                              </div>
                            </div>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}

                  {(!profile.recent_topics || profile.recent_topics.length === 0) &&
                   (!profile.recent_posts || profile.recent_posts.length === 0) && (
                    <div className="text-center py-8 text-gray-400">
                      <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>No recent activity</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'topics' && (
              <div>
                {userTopics.length > 0 ? (
                  <div className="space-y-3">
                    {userTopics.map(topic => (
                      <Link
                        key={topic.id}
                        to={`/forum/${topic.forum.slug}/${topic.forum.id}/${topic.slug}/${topic.id}`}
                        className="block bg-white/5 hover:bg-white/10 rounded-lg p-4 border border-white/10 hover:border-white/20 transition-all"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <h5 className="text-white font-medium mb-2">{topic.subject}</h5>
                            <div className="flex items-center gap-4 text-sm text-gray-400">
                              <span className="flex items-center gap-1">
                                <MessageSquare className="w-4 h-4" />
                                {topic.posts_count || 0} posts
                              </span>
                              <span>{formatTimeAgo(topic.created)}</span>
                              <span>in {topic.forum.name}</span>
                            </div>
                          </div>
                        </div>
                      </Link>
                    ))}

                    {/* Pagination */}
                    {topicsPagination && topicsPagination.total_pages > 1 && (
                      <div className="flex justify-center gap-2 mt-6">
                        <button
                          onClick={() => fetchUserTopics(topicsPage - 1)}
                          disabled={!topicsPagination.has_previous}
                          className="px-4 py-2 bg-white/5 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                        >
                          Previous
                        </button>
                        <span className="px-4 py-2 text-white">
                          Page {topicsPagination.current_page} of {topicsPagination.total_pages}
                        </span>
                        <button
                          onClick={() => fetchUserTopics(topicsPage + 1)}
                          disabled={!topicsPagination.has_next}
                          className="px-4 py-2 bg-white/5 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                        >
                          Next
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-400">
                    <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No topics created yet</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'posts' && (
              <div>
                {userPosts.length > 0 ? (
                  <div className="space-y-3">
                    {userPosts.map(post => (
                      <Link
                        key={post.id}
                        to={`/forum/${post.topic.forum.slug}/${post.topic.forum.id}/${post.topic.slug}/${post.topic.id}`}
                        className="block bg-white/5 hover:bg-white/10 rounded-lg p-4 border border-white/10 hover:border-white/20 transition-all"
                      >
                        <div className="flex items-start gap-4">
                          <div className="flex-1">
                            <h5 className="text-white font-medium mb-2">
                              Re: {post.topic.subject}
                            </h5>
                            <p className="text-gray-300 text-sm mb-3 line-clamp-3">
                              {post.content.substring(0, 300)}...
                            </p>
                            <div className="flex items-center gap-4 text-sm text-gray-400">
                              <span>{formatTimeAgo(post.created)}</span>
                              <span>in {post.topic.forum.name}</span>
                            </div>
                          </div>
                        </div>
                      </Link>
                    ))}

                    {/* Pagination */}
                    {postsPagination && postsPagination.total_pages > 1 && (
                      <div className="flex justify-center gap-2 mt-6">
                        <button
                          onClick={() => fetchUserPosts(postsPage - 1)}
                          disabled={!postsPagination.has_previous}
                          className="px-4 py-2 bg-white/5 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                        >
                          Previous
                        </button>
                        <span className="px-4 py-2 text-white">
                          Page {postsPagination.current_page} of {postsPagination.total_pages}
                        </span>
                        <button
                          onClick={() => fetchUserPosts(postsPage + 1)}
                          disabled={!postsPagination.has_next}
                          className="px-4 py-2 bg-white/5 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                        >
                          Next
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-400">
                    <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No posts yet</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
