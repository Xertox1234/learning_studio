import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import {
  Search,
  MessageSquare,
  FileText,
  Filter,
  Clock,
  User,
  ArrowLeft,
  X
} from 'lucide-react'
import { apiRequest } from '../utils/api'
import { format } from 'date-fns'

export default function ForumSearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [searchType, setSearchType] = useState(searchParams.get('type') || 'all')
  const [forumFilter, setForumFilter] = useState(searchParams.get('forum_id') || '')
  const [results, setResults] = useState(null)
  const [forums, setForums] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [hasSearched, setHasSearched] = useState(false)

  useEffect(() => {
    fetchForums()
    // If there's a query in URL params, search immediately
    const urlQuery = searchParams.get('q')
    if (urlQuery) {
      performSearch(urlQuery, searchParams.get('type') || 'all', searchParams.get('forum_id') || '')
    }
  }, [])

  const fetchForums = async () => {
    try {
      const response = await apiRequest('/api/v1/forums/')
      if (response.ok) {
        const data = await response.json()
        setForums(data.forums || [])
      }
    } catch (error) {
      console.error('Failed to fetch forums:', error)
    }
  }

  const performSearch = async (searchQuery, type, forumId) => {
    if (!searchQuery.trim()) {
      setError('Please enter a search term')
      return
    }

    setLoading(true)
    setError(null)
    setHasSearched(true)

    try {
      let url = `/api/v1/forums/search/?q=${encodeURIComponent(searchQuery)}`
      if (type && type !== 'all') {
        url += `&type=${type}`
      }
      if (forumId) {
        url += `&forum_id=${forumId}`
      }

      const response = await apiRequest(url)

      if (!response.ok) {
        throw new Error(`Search failed: ${response.status}`)
      }

      const data = await response.json()
      setResults(data)

      // Update URL params
      const newParams = { q: searchQuery }
      if (type !== 'all') newParams.type = type
      if (forumId) newParams.forum_id = forumId
      setSearchParams(newParams)
    } catch (error) {
      console.error('Search failed:', error)
      setError(error.message || 'Failed to perform search')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    performSearch(query, searchType, forumFilter)
  }

  const clearFilters = () => {
    setSearchType('all')
    setForumFilter('')
    if (query) {
      performSearch(query, 'all', '')
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

  const highlightText = (text, searchTerm) => {
    if (!searchTerm || !text) return text

    // Escape regex special characters to prevent XSS and regex errors
    const escapedTerm = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(`(${escapedTerm})`, 'gi')
    const parts = text.split(regex)

    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-400/30 text-white px-1 rounded">
          {part}
        </mark>
      ) : (
        part
      )
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <Link to="/forum" className="inline-flex items-center text-blue-400 hover:text-blue-300 mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Forum
          </Link>
          <h1 className="text-4xl font-bold text-white">Search Forums</h1>
        </div>

        {/* Search Form */}
        <div className="bg-white/10 backdrop-blur-lg rounded-lg border border-white/20 p-6 mb-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search topics and posts..."
                className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Filters */}
            <div className="flex flex-wrap gap-4">
              {/* Search Type */}
              <div className="flex-1 min-w-[200px]">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Search In
                </label>
                <select
                  value={searchType}
                  onChange={(e) => setSearchType(e.target.value)}
                  className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All (Topics & Posts)</option>
                  <option value="topics">Topics Only</option>
                  <option value="posts">Posts Only</option>
                </select>
              </div>

              {/* Forum Filter */}
              <div className="flex-1 min-w-[200px]">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Forum
                </label>
                <select
                  value={forumFilter}
                  onChange={(e) => setForumFilter(e.target.value)}
                  className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Forums</option>
                  {forums.map(forum => (
                    <option key={forum.id} value={forum.id}>
                      {forum.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Search className="w-5 h-5" />
                {loading ? 'Searching...' : 'Search'}
              </button>
              {(searchType !== 'all' || forumFilter) && (
                <button
                  type="button"
                  onClick={clearFilters}
                  className="px-4 py-3 bg-white/5 hover:bg-white/10 text-white rounded-lg transition-colors flex items-center gap-2"
                >
                  <X className="w-5 h-5" />
                  Clear Filters
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 mb-6">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Results */}
        {results && (
          <div className="bg-white/10 backdrop-blur-lg rounded-lg border border-white/20 p-6">
            {/* Results Header */}
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-white mb-2">
                Search Results
              </h2>
              <div className="flex items-center gap-4 text-gray-300">
                <span>
                  Found {results.total_results} result{results.total_results !== 1 ? 's' : ''}
                </span>
                <span className="text-gray-500">•</span>
                <span>Search took {results.search_time_ms}ms</span>
              </div>
            </div>

            {/* Active Filters */}
            {(searchType !== 'all' || forumFilter) && (
              <div className="mb-4 flex flex-wrap gap-2">
                {searchType !== 'all' && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm">
                    <Filter className="w-3 h-3" />
                    Type: {searchType}
                  </span>
                )}
                {forumFilter && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-sm">
                    <Filter className="w-3 h-3" />
                    Forum: {forums.find(f => f.id.toString() === forumFilter)?.name || 'Unknown'}
                  </span>
                )}
              </div>
            )}

            {/* Results List */}
            {results.results.length > 0 ? (
              <div className="space-y-4">
                {results.results.map(result => (
                  <div
                    key={`${result.type}-${result.id}`}
                    className="bg-white/5 hover:bg-white/10 rounded-lg p-5 border border-white/10 hover:border-white/20 transition-all"
                  >
                    {/* Result Type Badge */}
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0">
                        {result.type === 'topic' ? (
                          <div className="p-2 bg-blue-500/20 rounded-lg">
                            <FileText className="w-5 h-5 text-blue-400" />
                          </div>
                        ) : (
                          <div className="p-2 bg-purple-500/20 rounded-lg">
                            <MessageSquare className="w-5 h-5 text-purple-400" />
                          </div>
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        {/* Title/Subject */}
                        <Link
                          to={result.url}
                          className="block mb-2 group"
                        >
                          <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">
                            {highlightText(result.subject, query)}
                          </h3>
                        </Link>

                        {/* Excerpt */}
                        {result.excerpt && (
                          <p className="text-gray-300 text-sm mb-3 line-clamp-3">
                            {highlightText(result.excerpt, query)}
                          </p>
                        )}

                        {/* Metadata */}
                        <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400">
                          <span className="flex items-center gap-1">
                            <User className="w-4 h-4" />
                            {result.author}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {formatTimeAgo(result.created)}
                          </span>
                          <span>in {result.forum_name}</span>
                          {result.type === 'post' && (
                            <>
                              <span className="text-gray-500">•</span>
                              <span>in topic: {result.topic_subject}</span>
                            </>
                          )}
                          {result.type === 'topic' && result.posts_count !== undefined && (
                            <>
                              <span className="text-gray-500">•</span>
                              <span className="flex items-center gap-1">
                                <MessageSquare className="w-4 h-4" />
                                {result.posts_count} replies
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Search className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">No results found</h3>
                <p className="text-gray-400 mb-4">
                  Try adjusting your search terms or filters
                </p>
                <button
                  onClick={clearFilters}
                  className="text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        )}

        {/* Initial State - No Search Yet */}
        {!hasSearched && !loading && (
          <div className="bg-white/10 backdrop-blur-lg rounded-lg border border-white/20 p-12 text-center">
            <Search className="w-16 h-16 text-gray-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              Search the Forums
            </h3>
            <p className="text-gray-400 max-w-md mx-auto">
              Enter a search term above to find topics and posts across all forums.
              Use filters to narrow your search.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
