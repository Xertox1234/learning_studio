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

  const currentCategory = searchParams.get('category')
  const currentPage = parseInt(searchParams.get('page')) || 1

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
          <div className="h-8 bg-muted rounded w-48 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-card rounded-lg border p-6">
                <div className="h-4 bg-muted rounded w-3/4 mb-4"></div>
                <div className="h-3 bg-muted rounded w-full mb-2"></div>
                <div className="h-3 bg-muted rounded w-2/3"></div>
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
        <h1 className="text-3xl font-bold mb-4">Python Learning Blog</h1>
        <p className="text-lg text-muted-foreground">
          Discover tutorials, insights, and AI-powered learning strategies for Python development
        </p>
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

      {/* Blog Posts Grid */}
      {posts.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {posts.map((post) => (
              <article key={post.id} className="bg-card rounded-lg border hover:shadow-lg transition-shadow">
                <div className="p-6">
                  {/* Categories */}
                  {post.categories.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                      {post.categories.map((category) => (
                        <span
                          key={category.id}
                          className="px-2 py-1 text-xs font-medium text-white rounded"
                          style={{ backgroundColor: category.color }}
                        >
                          {category.name}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Title */}
                  <h2 className="text-xl font-semibold mb-3 hover:text-primary transition-colors">
                    <Link to={`/blog/${post.slug}`}>
                      {post.title}
                    </Link>
                  </h2>

                  {/* Intro */}
                  <p className="text-muted-foreground mb-4 line-clamp-3">
                    {post.intro}
                  </p>

                  {/* Meta Info */}
                  <div className="flex items-center justify-between text-sm text-muted-foreground mb-4">
                    <div className="flex items-center space-x-4">
                      {post.author && (
                        <div className="flex items-center space-x-1">
                          <User className="h-4 w-4" />
                          <span>{post.author.display_name}</span>
                        </div>
                      )}
                      {post.date && (
                        <div className="flex items-center space-x-1">
                          <Calendar className="h-4 w-4" />
                          <span>{formatDate(post.date)}</span>
                        </div>
                      )}
                    </div>
                    {post.reading_time && (
                      <div className="flex items-center space-x-1">
                        <Clock className="h-4 w-4" />
                        <span>{post.reading_time} min read</span>
                      </div>
                    )}
                  </div>

                  {/* AI Badge and Tags */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {post.ai_generated && (
                        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded">
                          AI Enhanced
                        </span>
                      )}
                      {post.tags.length > 0 && (
                        <div className="flex items-center space-x-1">
                          <Tag className="h-3 w-3" />
                          <span className="text-xs">{post.tags.slice(0, 2).join(', ')}</span>
                        </div>
                      )}
                    </div>
                    <Link
                      to={`/blog/${post.slug}`}
                      className="text-primary hover:text-primary/80 text-sm font-medium"
                    >
                      Read more →
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
      ) : (
        <div className="text-center py-12">
          <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-muted-foreground mb-2">
            {currentCategory ? 'No posts in this category' : 'No blog posts found'}
          </h3>
          <p className="text-muted-foreground">
            {currentCategory ? (
              <>
                Try <button onClick={() => handleCategoryFilter(null)} className="text-primary hover:underline">viewing all posts</button> or check back later for new content.
              </>
            ) : (
              'Check back later for new tutorials and insights!'
            )}
          </p>
        </div>
      )}
    </div>
  )
}