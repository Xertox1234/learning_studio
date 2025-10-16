import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import ForumErrorBoundary from '../components/forum/ForumErrorBoundary'
import { useForums } from '../hooks/useForumQuery'
import {
  MessageSquare,
  Users,
  TrendingUp,
  Clock,
  Search,
  Filter,
  Plus,
  Award,
  Eye,
  MessageCircle,
  Heart,
  Bookmark,
  ChevronRight
} from 'lucide-react'
import { format } from 'date-fns'
import clsx from 'clsx'

export default function ForumPage() {
  // Use React Query hook for data fetching
  const { data, isLoading, error } = useForums()

  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [sortBy, setSortBy] = useState('activity')
  const [showForumDropdown, setShowForumDropdown] = useState(false)

  // Transform API data to flat array for easier filtering
  const forums = data?.categories?.flatMap(category =>
    category.forums.map(forum => ({
      ...forum,
      color: forum.color || 'bg-blue-500' // Fallback color
    }))
  ) || []

  const stats = data?.stats || {
    total_topics: 0,
    total_posts: 0,
    total_users: 0,
    online_users: 0
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showForumDropdown && !event.target.closest('.forum-dropdown-container')) {
        setShowForumDropdown(false)
      }
    }

    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [showForumDropdown])

  // Show error state if API fails
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-8 border border-gray-200 dark:border-gray-700 max-w-md">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Failed to Load Forums</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {error.message || 'An error occurred while fetching forum data.'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary w-full"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // Dynamic categories based on real forum data
  const categories = [
    { id: 'all', name: 'All Categories', count: forums.length },
    { id: 'beginner', name: 'Beginner Questions', count: forums.filter(f => f.name.toLowerCase().includes('beginner')).length },
    { id: 'advanced', name: 'Advanced Topics', count: forums.filter(f => f.name.toLowerCase().includes('advanced')).length },
    { id: 'trending', name: 'Trending', count: forums.filter(f => f.stats?.trending).length },
  ]

  const filteredForums = forums.filter(forum => {
    const matchesSearch = forum.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         forum.description.toLowerCase().includes(searchQuery.toLowerCase())
    
    let matchesCategory = true
    if (selectedCategory === 'beginner') {
      matchesCategory = forum.name.toLowerCase().includes('beginner')
    } else if (selectedCategory === 'advanced') {
      matchesCategory = forum.name.toLowerCase().includes('advanced')
    } else if (selectedCategory === 'trending') {
      matchesCategory = forum.stats?.trending === true
    } else if (selectedCategory !== 'all') {
      matchesCategory = true // Keep all for other categories
    }
    
    return matchesSearch && matchesCategory
  })

  const sortedForums = [...filteredForums].sort((a, b) => {
    if (sortBy === 'activity') {
      // Handle different date formats from API vs mock data
      const aDate = a.last_post?.created_at ? 
        (typeof a.last_post.created_at === 'string' ? new Date(a.last_post.created_at) : a.last_post.created_at) : 
        new Date(0)
      const bDate = b.last_post?.created_at ? 
        (typeof b.last_post.created_at === 'string' ? new Date(b.last_post.created_at) : b.last_post.created_at) : 
        new Date(0)
      return bDate - aDate
    } else if (sortBy === 'topics') {
      return b.topics_count - a.topics_count
    } else if (sortBy === 'posts') {
      return b.posts_count - a.posts_count
    }
    return 0
  })

  const formatTimeAgo = (date) => {
    if (!date) return 'unknown'
    
    const now = new Date()
    const targetDate = typeof date === 'string' ? new Date(date) : date
    const diff = now - targetDate
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    if (minutes > 0) return `${minutes}m ago`
    return 'just now'
  }

  const getTrustLevelBadge = (level) => {
    const badges = {
      0: { name: 'New', color: 'bg-gray-500' },
      1: { name: 'Basic', color: 'bg-green-500' },
      2: { name: 'Member', color: 'bg-blue-500' },
      3: { name: 'Regular', color: 'bg-purple-500' },
      4: { name: 'Leader', color: 'bg-orange-500' },
    }
    return badges[level] || badges[0]
  }

  return (
    <ForumErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-blue-50 to-gray-50 dark:from-blue-900/20 dark:to-gray-900 border-b border-gray-200 dark:border-gray-700">
        <div className="container-custom py-12">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div>
              <h1 className="text-4xl font-bold mb-2">Community Forum</h1>
              <p className="text-lg text-gray-600 dark:text-gray-400">
                Connect, learn, and share with Python developers worldwide
              </p>
            </div>
            <div className="relative group forum-dropdown-container">
              <button
                className="btn-primary flex items-center space-x-2"
                onClick={() => setShowForumDropdown(!showForumDropdown)}
              >
                <Plus className="h-4 w-4" />
                <span>New Topic</span>
              </button>
              
              {/* Forum Selection Dropdown */}
              {showForumDropdown && (
                <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                  <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                    <p className="text-sm font-medium">Select a forum:</p>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    {forums.map((forum) => (
                      <Link
                        key={forum.id}
                        to={`/forum/topics/create?forum=${forum.id}`}
                        className="block px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      >
                        <div className="flex items-center space-x-2">
                          <span className="text-lg">{forum.icon}</span>
                          <span>{forum.name}</span>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-3">
                <MessageSquare className="h-8 w-8 text-blue-600" />
                <div>
                  <p className="text-2xl font-bold">{stats.total_topics.toLocaleString()}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Topics</p>
                </div>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-3">
                <Users className="h-8 w-8 text-green-500" />
                <div>
                  <p className="text-2xl font-bold">{stats.total_users.toLocaleString()}</p>
                  <p className="text-sm text-muted-foreground">Members</p>
                </div>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-3">
                <TrendingUp className="h-8 w-8 text-orange-500" />
                <div>
                  <p className="text-2xl font-bold">{stats.online_users}</p>
                  <p className="text-sm text-muted-foreground">Online Now</p>
                </div>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-3">
                <Award className="h-8 w-8 text-purple-500" />
                <div>
                  <p className="text-2xl font-bold">{stats.total_posts.toLocaleString()}</p>
                  <p className="text-sm text-muted-foreground">Total Posts</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container-custom py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <aside className="lg:w-64 space-y-6">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search forums..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg border bg-card focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            {/* Categories */}
            <div className="bg-card rounded-lg border p-4">
              <h3 className="font-semibold mb-3 flex items-center">
                <Filter className="h-4 w-4 mr-2" />
                Categories
              </h3>
              <div className="space-y-2">
                {categories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    className={clsx(
                      'w-full text-left px-3 py-2 rounded-md text-sm transition-colors',
                      selectedCategory === category.id
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-muted'
                    )}
                  >
                    <div className="flex justify-between items-center">
                      <span>{category.name}</span>
                      <span className="text-xs opacity-70">{category.count}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Sort Options */}
            <div className="bg-card rounded-lg border p-4">
              <h3 className="font-semibold mb-3">Sort By</h3>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-3 py-2 rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="activity">Recent Activity</option>
                <option value="topics">Most Topics</option>
                <option value="posts">Most Posts</option>
              </select>
            </div>

            {/* Quick Links */}
            <div className="bg-card rounded-lg border p-4">
              <h3 className="font-semibold mb-3">Quick Links</h3>
              <div className="space-y-2">
                <Link to="/forum/guidelines" className="block text-sm hover:text-primary transition-colors">
                  Community Guidelines
                </Link>
                <Link to="/forum/badges" className="block text-sm hover:text-primary transition-colors">
                  Trust Levels & Badges
                </Link>
                <Link to="/forum/faq" className="block text-sm hover:text-primary transition-colors">
                  Forum FAQ
                </Link>
              </div>
            </div>
          </aside>

          {/* Forum List */}
          <div className="flex-1">
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="forum-card animate-pulse">
                    <div className="h-6 bg-muted rounded w-1/3 mb-4"></div>
                    <div className="h-4 bg-muted rounded w-2/3 mb-2"></div>
                    <div className="h-4 bg-muted rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {sortedForums.map((forum) => (
                  <Link
                    key={forum.id}
                    to={`/forum/${forum.slug}/${forum.id}`}
                    className="forum-card block group"
                  >
                    <div className="flex items-start space-x-4">
                      {/* Forum Icon */}
                      <div className={clsx(
                        'w-16 h-16 rounded-lg flex items-center justify-center text-2xl',
                        forum.color,
                        'bg-opacity-10'
                      )}>
                        {forum.icon}
                      </div>

                      {/* Forum Content */}
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="text-xl font-semibold mb-1 group-hover:text-primary transition-colors">
                              {forum.name}
                              {forum.stats.trending && (
                                <span className="ml-2 text-xs bg-orange-500 text-white px-2 py-1 rounded-full">
                                  Trending
                                </span>
                              )}
                            </h3>
                            <p className="text-muted-foreground mb-3">{forum.description}</p>
                          </div>
                          <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                        </div>

                        {/* Stats Row */}
                        <div className="flex items-center space-x-6 text-sm text-muted-foreground mb-3">
                          <span className="flex items-center space-x-1">
                            <MessageCircle className="h-4 w-4" />
                            <span>{forum.topics_count.toLocaleString()} topics</span>
                          </span>
                          <span className="flex items-center space-x-1">
                            <Eye className="h-4 w-4" />
                            <span>{forum.posts_count.toLocaleString()} posts</span>
                          </span>
                          <span className="flex items-center space-x-1">
                            <Users className="h-4 w-4" />
                            <span>{forum.stats?.online_users || 0} online</span>
                          </span>
                          <span className="flex items-center space-x-1">
                            <TrendingUp className="h-4 w-4" />
                            <span>{forum.stats?.weekly_posts || 0} this week</span>
                          </span>
                        </div>

                        {/* Last Post */}
                        {forum.last_post ? (
                          <div className="bg-muted/30 rounded-md p-3">
                            <div className="flex items-center space-x-3">
                              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-medium">
                                {forum.last_post.author?.username?.[0]?.toUpperCase() || '?'}
                              </div>
                              <div className="flex-1">
                                <p className="text-sm font-medium mb-1">
                                  {forum.last_post.title}
                                </p>
                                <div className="flex items-center space-x-3 text-xs text-muted-foreground">
                                  <span className="flex items-center space-x-1">
                                    <span>by {forum.last_post.author?.username || 'Unknown'}</span>
                                    {forum.last_post.author?.trust_level !== undefined && (
                                      <span className={clsx(
                                        'px-1.5 py-0.5 rounded text-xs',
                                        getTrustLevelBadge(forum.last_post.author.trust_level).color,
                                        'bg-opacity-20'
                                      )}>
                                        {getTrustLevelBadge(forum.last_post.author.trust_level).name}
                                      </span>
                                    )}
                                  </span>
                                  <span className="flex items-center space-x-1">
                                    <Clock className="h-3 w-3" />
                                    <span>{formatTimeAgo(forum.last_post.created_at)}</span>
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="bg-muted/30 rounded-md p-3 text-center text-sm text-muted-foreground">
                            No posts yet
                          </div>
                        )}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      </div>
    </ForumErrorBoundary>
  )
}