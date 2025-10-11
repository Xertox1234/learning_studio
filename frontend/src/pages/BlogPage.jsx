import React, { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Calendar, Clock, User, FileText, Search, Tag, ChevronLeft, ChevronRight } from 'lucide-react'
import { api } from '../utils/api'
import clsx from 'clsx'

export default function BlogPage() {
  const [posts, setPosts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pagination, setPagination] = useState({})
  const [searchParams, setSearchParams] = useSearchParams()
  const [searchQuery, setSearchQuery] = useState('')

  const currentCategory = searchParams.get('category')
  const currentPage = parseInt(searchParams.get('page')) || 1
  const currentSearch = searchParams.get('search') || ''

  useEffect(() => {
    fetchBlogData()
  }, [searchParams])

  const fetchBlogData = async () => {
    try {
      setLoading(true)
      
      // Fetch posts and categories in parallel
      const [postsResponse, categoriesResponse] = await Promise.all([
        api.get('/blog/', {
          params: {
            category: currentCategory,
            search: currentSearch,
            page: currentPage,
            page_size: 9
          }
        }),
        api.get('/blog/categories/')
      ])

      setPosts(postsResponse.data.posts)
      setPagination(postsResponse.data.pagination)
      setCategories(categoriesResponse.data.categories)
      setError(null)
    } catch (err) {
      console.error('Error fetching blog data:', err)
      setError('Failed to load blog posts. Please try again later.')
    } finally {
      setLoading(false)
    }
  }

  const handleCategoryFilter = (categorySlug) => {
    const newParams = new URLSearchParams(searchParams)
    if (categorySlug) {
      newParams.set('category', categorySlug)
    } else {
      newParams.delete('category')
    }
    newParams.delete('page') // Reset to first page
    setSearchParams(newParams)
  }

  const handlePageChange = (newPage) => {
    const newParams = new URLSearchParams(searchParams)
    newParams.set('page', newPage.toString())
    setSearchParams(newParams)
  }

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      const newParams = new URLSearchParams(searchParams)
      newParams.set('search', searchQuery.trim())
      newParams.delete('page') // Reset to first page
      setSearchParams(newParams)
    }
  }

  const clearSearch = () => {
    setSearchQuery('')
    const newParams = new URLSearchParams(searchParams)
    newParams.delete('search')
    newParams.delete('page') // Reset to first page
    setSearchParams(newParams)
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="container-custom py-8">
        <div className="animate-pulse">
          {/* Header skeleton */}
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-64 mb-2"></div>
          <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-96 mb-8"></div>
          
          {/* Category filter skeleton */}
          <div className="flex gap-2 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-8 bg-gray-200 dark:bg-gray-700 rounded-full w-20"></div>
            ))}
          </div>
          
          {/* Featured post skeleton */}
          <div className="mb-12">
            <div className="h-7 bg-gray-200 dark:bg-gray-700 rounded w-40 mb-6"></div>
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-8">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="h-64 lg:h-80 bg-gray-200 dark:bg-gray-700 rounded-xl"></div>
                <div className="flex flex-col justify-center">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20 mb-4"></div>
                  <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                  <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
                  <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                  <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-2/3 mb-6"></div>
                  <div className="flex gap-4 mb-6">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                  </div>
                  <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded-full w-40"></div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Blog posts grid skeleton */}
          <div className="h-7 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="h-48 bg-gray-200 dark:bg-gray-700"></div>
                <div className="p-6">
                  <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                  <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3 mb-4"></div>
                  <div className="flex justify-between items-center">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container-custom py-8">
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-6 text-center">
          <FileText className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-destructive mb-2">Error Loading Blog</h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <button
            onClick={fetchBlogData}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container-custom py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4 text-gray-900 dark:text-white">Python Learning Blog</h1>
        <p className="text-lg text-gray-600 dark:text-gray-300 mb-6">
          Discover tutorials, insights, and AI-powered learning strategies for Python development
        </p>
        
        {/* Search Bar */}
        <div className="max-w-2xl">
          <form onSubmit={handleSearch} className="relative">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search articles..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-12 py-3 border border-gray-300 dark:border-gray-600 rounded-full bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm"
              />
              {currentSearch && (
                <button
                  type="button"
                  onClick={clearSearch}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </form>
          {currentSearch && (
            <div className="mt-3 flex items-center text-sm text-gray-600 dark:text-gray-400">
              <span>Showing results for:</span>
              <span className="ml-2 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-full font-medium">
                "{currentSearch}"
              </span>
              <button
                onClick={clearSearch}
                className="ml-2 text-blue-600 dark:text-blue-400 hover:underline"
              >
                Clear search
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Category Filter */}
      {categories.length > 0 && (
        <div className="mb-8">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleCategoryFilter(null)}
              className={clsx(
                'px-4 py-2 rounded-full text-sm font-medium transition-colors',
                !currentCategory
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted hover:bg-muted/80'
              )}
            >
              All Posts
            </button>
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => handleCategoryFilter(category.slug)}
                className={clsx(
                  'px-4 py-2 rounded-full text-sm font-medium transition-colors',
                  currentCategory === category.slug
                    ? 'text-white'
                    : 'bg-muted hover:bg-muted/80'
                )}
                style={{
                  backgroundColor: currentCategory === category.slug ? category.color : undefined
                }}
              >
                {category.name}
                {category.post_count > 0 && (
                  <span className="ml-2 text-xs opacity-75">({category.post_count})</span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Featured Post - Only show on main blog page without filters */}
      {posts.length > 0 && posts[0] && !currentCategory && !currentSearch && (
        <div className="mb-12">
          <h2 className="text-2xl font-bold mb-6">Featured Post</h2>
          <article className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-blue-900/20 dark:to-purple-900/20 border border-blue-200/50 dark:border-gray-700 hover:border-blue-300/50 dark:hover:border-gray-600 transition-all duration-300 hover:shadow-2xl">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Featured Image */}
              <div className="relative overflow-hidden">
                {posts[0].featured_image ? (
                  <img
                    src={posts[0].featured_image}
                    alt={posts[0].title}
                    className="w-full h-64 lg:h-80 object-cover rounded-xl lg:rounded-l-none lg:rounded-r-xl transition-transform duration-300 group-hover:scale-105"
                  />
                ) : (
                  <div className="w-full h-64 lg:h-80 bg-gradient-to-br from-blue-400 to-purple-500 rounded-xl lg:rounded-l-none lg:rounded-r-xl flex items-center justify-center">
                    <FileText className="h-16 w-16 text-white/80" />
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent" />
              </div>

              {/* Content */}
              <div className="p-8 flex flex-col justify-center">
                {/* Categories */}
                {posts[0].categories.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {posts[0].categories.map((category) => (
                      <span
                        key={category.id}
                        className="px-3 py-1 text-sm font-semibold text-white rounded-full shadow-lg"
                        style={{ backgroundColor: category.color }}
                      >
                        {category.name}
                      </span>
                    ))}
                  </div>
                )}

                {/* Title */}
                <h3 className="text-3xl font-bold mb-4 text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  <Link to={`/blog/${posts[0].slug}`}>
                    {posts[0].title}
                  </Link>
                </h3>

                {/* Intro */}
                <p className="text-lg text-gray-600 dark:text-gray-300 mb-6 leading-relaxed">
                  {posts[0].intro}
                </p>

                {/* Meta Info */}
                <div className="flex flex-wrap items-center gap-6 text-sm text-gray-500 dark:text-gray-400 mb-6">
                  {posts[0].author && (
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                        {posts[0].author.display_name.charAt(0).toUpperCase()}
                      </div>
                      <span className="font-medium">{posts[0].author.display_name}</span>
                    </div>
                  )}
                  {posts[0].date && (
                    <div className="flex items-center space-x-2">
                      <Calendar className="h-4 w-4" />
                      <span>{formatDate(posts[0].date)}</span>
                    </div>
                  )}
                  {posts[0].reading_time && (
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4" />
                      <span>{posts[0].reading_time} min read</span>
                    </div>
                  )}
                </div>

                {/* CTA */}
                <Link
                  to={`/blog/${posts[0].slug}`}
                  className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-full hover:from-blue-700 hover:to-purple-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1 w-fit"
                >
                  Read Full Article
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Link>
              </div>
            </div>
          </article>
        </div>
      )}

      {/* Blog Posts Grid */}
      {((!currentCategory && !currentSearch && posts.length > 1) || ((currentCategory || currentSearch) && posts.length > 0)) && (
        <>
          <h2 className="text-2xl font-bold mb-6">
            {!currentCategory && !currentSearch ? 'Latest Posts' : 'Posts'}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-8">
            {(!currentCategory && !currentSearch ? posts.slice(1) : posts).map((post, index) => (
              <article key={post.id} className="group relative overflow-hidden bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 transition-all duration-300 hover:shadow-2xl hover:-translate-y-1">
                {/* Featured Image */}
                <div className="relative overflow-hidden">
                  {post.featured_image ? (
                    <img
                      src={post.featured_image}
                      alt={post.title}
                      className="w-full h-48 object-cover transition-transform duration-300 group-hover:scale-110"
                      loading="lazy"
                    />
                  ) : (
                    <div className="w-full h-48 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center">
                      <FileText className="h-12 w-12 text-gray-400 dark:text-gray-500" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  
                  {/* Categories Overlay */}
                  {post.categories.length > 0 && (
                    <div className="absolute top-4 left-4 flex flex-wrap gap-2">
                      {post.categories.slice(0, 2).map((category) => (
                        <span
                          key={category.id}
                          className="px-3 py-1 text-xs font-bold text-white rounded-full shadow-lg backdrop-blur-sm"
                          style={{ backgroundColor: category.color }}
                        >
                          {category.name}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Reading Time Badge */}
                  {post.reading_time && (
                    <div className="absolute top-4 right-4 bg-black/70 backdrop-blur-sm text-white px-3 py-1 rounded-full text-xs font-medium">
                      {post.reading_time} min
                    </div>
                  )}
                </div>

                <div className="p-6">
                  {/* Title */}
                  <h3 className="text-xl font-bold mb-3 text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-2">
                    <Link to={`/blog/${post.slug}`}>
                      {post.title}
                    </Link>
                  </h3>

                  {/* Intro */}
                  <p className="text-gray-600 dark:text-gray-300 mb-4 line-clamp-3 leading-relaxed">
                    {post.intro}
                  </p>

                  {/* Author & Meta */}
                  <div className="flex items-center justify-between mb-4">
                    {post.author && (
                      <div className="flex items-center space-x-2">
                        <div className="w-6 h-6 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold text-xs">
                          {post.author.display_name.charAt(0).toUpperCase()}
                        </div>
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{post.author.display_name}</span>
                      </div>
                    )}
                    {post.date && (
                      <div className="flex items-center space-x-1 text-sm text-gray-500 dark:text-gray-400">
                        <Calendar className="h-3 w-3" />
                        <span>{formatDate(post.date)}</span>
                      </div>
                    )}
                  </div>

                  {/* Tags and AI Badge */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {post.ai_generated && (
                        <span className="px-2 py-1 text-xs font-semibold bg-gradient-to-r from-blue-100 to-purple-100 text-blue-800 dark:from-blue-900 dark:to-purple-900 dark:text-blue-200 rounded-full">
                          🤖 AI Enhanced
                        </span>
                      )}
                      {post.tags.length > 0 && (
                        <div className="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">
                          <Tag className="h-3 w-3" />
                          <span>#{post.tags.slice(0, 1)[0]}</span>
                        </div>
                      )}
                    </div>
                    <Link
                      to={`/blog/${post.slug}`}
                      className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 text-sm font-semibold transition-colors flex items-center space-x-1 group/link"
                    >
                      <span>Read more</span>
                      <ChevronRight className="h-3 w-3 transition-transform group-hover/link:translate-x-1" />
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="flex items-center justify-center space-x-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={!pagination.has_previous}
                className="flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-muted transition-colors"
              >
                <ChevronLeft className="h-4 w-4" />
                <span>Previous</span>
              </button>

              <div className="flex items-center space-x-1">
                {[...Array(pagination.total_pages)].map((_, i) => {
                  const page = i + 1
                  const isCurrentPage = page === currentPage
                  const showPage = page === 1 || page === pagination.total_pages || Math.abs(page - currentPage) <= 2

                  if (!showPage) {
                    if (page === currentPage - 3 || page === currentPage + 3) {
                      return <span key={page} className="px-2 text-muted-foreground">...</span>
                    }
                    return null
                  }

                  return (
                    <button
                      key={page}
                      onClick={() => handlePageChange(page)}
                      className={clsx(
                        'px-3 py-2 text-sm font-medium rounded-md transition-colors',
                        isCurrentPage
                          ? 'bg-primary text-primary-foreground'
                          : 'hover:bg-muted'
                      )}
                    >
                      {page}
                    </button>
                  )
                })}
              </div>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={!pagination.has_next}
                className="flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-muted transition-colors"
              >
                <span>Next</span>
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </>
      )}
      
      {posts.length === 0 && (
        <div className="text-center py-16">
          <div className="max-w-md mx-auto">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900/20 dark:to-purple-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <FileText className="h-12 w-12 text-blue-500 dark:text-blue-400" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
              {currentCategory ? 'No posts in this category' : 'No blog posts found'}
            </h3>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              {currentCategory ? (
                <>
                  Try <button onClick={() => handleCategoryFilter(null)} className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-semibold underline">viewing all posts</button> or check back later for new content.
                </>
              ) : (
                'Check back later for new tutorials and insights!'
              )}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}