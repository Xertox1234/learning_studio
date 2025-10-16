import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Calendar, Clock, User, ArrowLeft, ExternalLink, Copy, Check, Tag, ChevronRight } from 'lucide-react'
import { api } from '../utils/api'
import { ReadOnlyCodeBlock } from '../components/code-editor'
import { sanitizeHTML } from '../utils/sanitize'
import clsx from 'clsx'

export default function BlogPostPage() {
  const { slug } = useParams()
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [copiedUrl, setCopiedUrl] = useState(false)
  const [readingProgress, setReadingProgress] = useState(0)

  useEffect(() => {
    fetchPost()
  }, [slug])

  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY
      const docHeight = document.documentElement.scrollHeight - window.innerHeight
      const progress = scrollTop / docHeight
      setReadingProgress(Math.min(progress, 1))
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const fetchPost = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/blog/${slug}/`)
      setPost(response.data)
      setError(null)
    } catch (err) {
      console.error('Error fetching blog post:', err)
      setError(err.response?.status === 404 ? 'Blog post not found.' : 'Failed to load blog post. Please try again later.')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const copyUrl = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopiedUrl(true)
      setTimeout(() => setCopiedUrl(false), 2000)
    } catch (err) {
      console.error('Failed to copy URL:', err)
    }
  }

  const renderBlockContent = (block) => {
    switch (block.type) {
      case 'paragraph':
        return (
          <div
            className="prose prose-lg dark:prose-invert max-w-none mb-6 text-gray-700 dark:text-gray-300 leading-relaxed"
            dangerouslySetInnerHTML={{ __html: sanitizeHTML(block.value, { mode: 'rich' }) }}
          />
        )
      
      case 'heading':
        return (
          <h2 className="text-3xl font-bold mt-12 mb-6 first:mt-0 text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 pb-3">
            {block.value}
          </h2>
        )
      
      case 'code':
        return (
          <div className="mb-8">
            {block.value.caption && (
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-3 font-medium flex items-center">
                <span className="mr-2">📝</span>
                {block.value.caption}
              </div>
            )}
            <div className="relative rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 shadow-lg">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-2 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {block.value.language || 'code'}
                </span>
                <div className="flex space-x-1">
                  <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                  <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                </div>
              </div>
              <ReadOnlyCodeBlock
                code={block.value.code}
                language={block.value.language || 'text'}
                showLineNumbers={true}
              />
            </div>
          </div>
        )
      
      case 'callout':
        const calloutStyles = {
          info: 'bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20 border-blue-200 dark:border-blue-800',
          warning: 'bg-gradient-to-r from-amber-50 to-yellow-50 dark:from-amber-950/20 dark:to-yellow-950/20 border-amber-200 dark:border-amber-800',
          tip: 'bg-gradient-to-r from-emerald-50 to-green-50 dark:from-emerald-950/20 dark:to-green-950/20 border-emerald-200 dark:border-emerald-800',
          danger: 'bg-gradient-to-r from-red-50 to-pink-50 dark:from-red-950/20 dark:to-pink-950/20 border-red-200 dark:border-red-800'
        }
        
        const calloutIcons = {
          info: '💡',
          warning: '⚠️',
          tip: '✨',
          danger: '⚡'
        }
        
        const calloutColors = {
          info: 'text-blue-800 dark:text-blue-200',
          warning: 'text-amber-800 dark:text-amber-200',
          tip: 'text-emerald-800 dark:text-emerald-200',
          danger: 'text-red-800 dark:text-red-200'
        }
        
        return (
          <div className={clsx(
            'border-l-4 rounded-lg p-6 mb-8 shadow-sm',
            calloutStyles[block.value.type] || calloutStyles.info
          )}>
            {block.value.title && (
              <div className={clsx(
                'flex items-center font-bold mb-3 text-lg',
                calloutColors[block.value.type] || calloutColors.info
              )}>
                <span className="mr-3 text-xl">{calloutIcons[block.value.type] || calloutIcons.info}</span>
                {block.value.title}
              </div>
            )}
            <div
              className="prose dark:prose-invert max-w-none text-gray-700 dark:text-gray-300"
              dangerouslySetInnerHTML={{ __html: sanitizeHTML(block.value.text, { mode: 'rich' }) }}
            />
          </div>
        )
      
      case 'quote':
        return (
          <blockquote className="relative border-l-4 border-gradient-to-b from-blue-500 to-purple-500 pl-8 py-6 mb-8 bg-gradient-to-r from-gray-50 to-blue-50/30 dark:from-gray-800 dark:to-blue-900/10 rounded-r-lg shadow-sm">
            <div className="absolute top-4 left-2 text-blue-500 text-4xl font-serif">“</div>
            <div className="prose prose-lg dark:prose-invert max-w-none text-gray-700 dark:text-gray-300 italic font-medium leading-relaxed">
              {block.value.text}
            </div>
            {block.value.attribution && (
              <cite className="block mt-4 text-sm font-semibold text-blue-600 dark:text-blue-400 not-italic flex items-center">
                <span className="mr-2">—</span>
                {block.value.attribution}
              </cite>
            )}
          </blockquote>
        )
      
      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className="container-custom py-8">
        <div className="animate-pulse max-w-4xl mx-auto">
          <div className="h-4 bg-muted rounded w-32 mb-4"></div>
          <div className="h-8 bg-muted rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-muted rounded w-1/2 mb-8"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-4 bg-muted rounded w-full"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container-custom py-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-8">
            <h1 className="text-2xl font-semibold text-destructive mb-4">Post Not Found</h1>
            <p className="text-muted-foreground mb-6">{error}</p>
            <Link
              to="/blog"
              className="inline-flex items-center space-x-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Blog</span>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      {/* Reading Progress Bar */}
      <div className="fixed top-0 left-0 w-full h-1 bg-gray-200 dark:bg-gray-700 z-50">
        <div 
          className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-150 ease-out"
          style={{ width: `${readingProgress * 100}%` }}
        />
      </div>
      
      <div className="container-custom py-8">
        <div className="max-w-4xl mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center space-x-2 text-sm text-muted-foreground mb-6">
          <Link to="/blog" className="hover:text-primary transition-colors">
            Blog
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-foreground">{post.title}</span>
        </nav>

        {/* Post Header */}
        <header className="mb-12">
          {/* Categories */}
          {post.categories.length > 0 && (
            <div className="flex flex-wrap gap-3 mb-6">
              {post.categories.map((category) => (
                <Link
                  key={category.id}
                  to={`/blog?category=${category.slug}`}
                  className="px-4 py-2 text-sm font-bold text-white rounded-full hover:opacity-90 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                  style={{ backgroundColor: category.color }}
                >
                  {category.name}
                </Link>
              ))}
            </div>
          )}

          {/* Title */}
          <h1 className="text-5xl font-extrabold mb-6 text-gray-900 dark:text-white leading-tight">
            {post.title}
          </h1>

          {/* Intro */}
          {post.intro && (
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 leading-relaxed font-medium">
              {post.intro}
            </p>
          )}

          {/* Meta Info */}
          <div className="flex flex-wrap items-center gap-8 pb-8 border-b border-gray-200 dark:border-gray-700">
            {post.author && (
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg">
                  {post.author.display_name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="font-bold text-gray-900 dark:text-white">
                    {post.author.display_name}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Author</div>
                </div>
              </div>
            )}
            
            <div className="flex flex-wrap items-center gap-6 text-gray-600 dark:text-gray-400">
              {post.date && (
                <div className="flex items-center space-x-2">
                  <Calendar className="h-5 w-5" />
                  <span className="font-medium">{formatDate(post.date)}</span>
                </div>
              )}
              
              {post.reading_time && (
                <div className="flex items-center space-x-2">
                  <Clock className="h-5 w-5" />
                  <span className="font-medium">
                    {post.reading_time} min read
                    {readingProgress > 0 && (
                      <span className="text-blue-600 dark:text-blue-400 ml-2">
                        ({Math.max(1, Math.round(post.reading_time * (1 - readingProgress)))} min left)
                      </span>
                    )}
                  </span>
                </div>
              )}

              {post.ai_generated && (
                <div className="flex items-center px-4 py-2 bg-gradient-to-r from-blue-100 to-purple-100 dark:from-blue-900/30 dark:to-purple-900/30 text-blue-800 dark:text-blue-200 rounded-full font-semibold text-sm border border-blue-200 dark:border-blue-700">
                  <span className="mr-2">🤖</span>
                  AI Enhanced
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Post Content */}
        <article className="mb-8">
          {post.body.map((block, index) => (
            <div key={index}>
              {renderBlockContent(block)}
            </div>
          ))}
        </article>

        {/* AI Summary */}
        {post.ai_summary && (
          <div className="bg-muted/50 rounded-lg p-6 mb-8">
            <h3 className="flex items-center text-lg font-semibold mb-3">
              <span className="mr-2">🤖</span>
              AI Summary
            </h3>
            <p className="text-muted-foreground">{post.ai_summary}</p>
          </div>
        )}

        {/* Tags */}
        {post.tags.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-3">Tags</h3>
            <div className="flex flex-wrap gap-2">
              {post.tags.map((tag, index) => (
                <span
                  key={index}
                  className="flex items-center space-x-1 px-3 py-1 text-sm bg-muted rounded-full"
                >
                  <Tag className="h-3 w-3" />
                  <span>#{tag}</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Share Section */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-8 mb-12">
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-700 rounded-2xl p-8">
            <h3 className="text-2xl font-bold mb-2 text-gray-900 dark:text-white">Share this article</h3>
            <p className="text-gray-600 dark:text-gray-300 mb-6">Help others discover this content</p>
            
            <div className="flex flex-wrap gap-4">
              <button
                onClick={() => window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(post.title)}&url=${encodeURIComponent(window.location.href)}`, '_blank')}
                className="flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-blue-400 to-blue-600 text-white rounded-full hover:from-blue-500 hover:to-blue-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1 font-semibold"
              >
                <ExternalLink className="h-5 w-5" />
                <span>Share on Twitter</span>
              </button>
              
              <button
                onClick={() => window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(window.location.href)}`, '_blank')}
                className="flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-800 text-white rounded-full hover:from-blue-700 hover:to-blue-900 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1 font-semibold"
              >
                <ExternalLink className="h-5 w-5" />
                <span>Share on LinkedIn</span>
              </button>
              
              <button
                onClick={() => window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(window.location.href)}`, '_blank')}
                className="flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-700 text-white rounded-full hover:from-blue-600 hover:to-blue-800 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1 font-semibold"
              >
                <ExternalLink className="h-5 w-5" />
                <span>Share on Facebook</span>
              </button>
              
              <button
                onClick={copyUrl}
                className={clsx(
                  "flex items-center space-x-3 px-6 py-3 rounded-full transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1 font-semibold",
                  copiedUrl 
                    ? "bg-gradient-to-r from-green-500 to-green-600 text-white" 
                    : "bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-2 border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500"
                )}
              >
                {copiedUrl ? (
                  <>
                    <Check className="h-5 w-5" />
                    <span>Link Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-5 w-5" />
                    <span>Copy Link</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Related Posts */}
        {post.related_posts.length > 0 && (
          <div className="border-t border-gray-200 dark:border-gray-700 pt-12">
            <h3 className="text-3xl font-bold mb-2 text-gray-900 dark:text-white">Continue Reading</h3>
            <p className="text-gray-600 dark:text-gray-300 mb-8">Explore more articles on similar topics</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {post.related_posts.map((relatedPost) => (
                <article key={relatedPost.id} className="group bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 transition-all duration-300 hover:shadow-2xl hover:-translate-y-2 overflow-hidden">
                  {/* Image placeholder */}
                  <div className="h-32 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-gray-700 dark:to-gray-600 relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-400/20 to-purple-400/20"></div>
                    <div className="absolute top-2 right-2 bg-white/90 dark:bg-gray-800/90 text-gray-700 dark:text-gray-300 px-2 py-1 rounded-full text-xs font-medium">
                      {relatedPost.reading_time ? `${relatedPost.reading_time} min` : 'Quick read'}
                    </div>
                  </div>
                  
                  <div className="p-6">
                    <h4 className="font-bold mb-3 text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-2 leading-snug">
                      <Link to={`/blog/${relatedPost.slug}`}>
                        {relatedPost.title}
                      </Link>
                    </h4>
                    <p className="text-gray-600 dark:text-gray-300 mb-4 line-clamp-3 text-sm leading-relaxed">
                      {relatedPost.intro}
                    </p>
                    <div className="flex items-center justify-between">
                      {relatedPost.date && (
                        <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                          <Calendar className="h-3 w-3 mr-1" />
                          <span>{formatDate(relatedPost.date)}</span>
                        </div>
                      )}
                      <Link
                        to={`/blog/${relatedPost.slug}`}
                        className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 text-sm font-semibold flex items-center space-x-1 group/link"
                      >
                        <span>Read more</span>
                        <ChevronRight className="h-3 w-3 transition-transform group-hover/link:translate-x-1" />
                      </Link>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>
        )}

        {/* Back to Blog */}
        <div className="mt-12 pt-8 border-t">
          <Link
            to="/blog"
            className="inline-flex items-center space-x-2 text-primary hover:text-primary/80 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to all posts</span>
          </Link>
        </div>
        </div>
      </div>
    </>
  )
}