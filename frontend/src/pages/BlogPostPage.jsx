import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Calendar, Clock, User, ArrowLeft, ExternalLink, Copy, Check, Tag, ChevronRight } from 'lucide-react'
import { api } from '../utils/api'
import { ReadOnlyCodeBlock } from '../components/code-editor'
import clsx from 'clsx'

export default function BlogPostPage() {
  const { slug } = useParams()
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [copiedUrl, setCopiedUrl] = useState(false)

  useEffect(() => {
    fetchPost()
  }, [slug])

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
            className="prose prose-lg dark:prose-invert max-w-none mb-6"
            dangerouslySetInnerHTML={{ __html: block.value }}
          />
        )
      
      case 'heading':
        return (
          <h2 className="text-2xl font-semibold mt-8 mb-4 first:mt-0">
            {block.value}
          </h2>
        )
      
      case 'code':
        return (
          <div className="mb-6">
            {block.value.caption && (
              <div className="text-sm text-muted-foreground mb-2 italic">
                {block.value.caption}
              </div>
            )}
            <ReadOnlyCodeBlock
              code={block.value.code}
              language={block.value.language || 'text'}
              showLineNumbers={true}
            />
          </div>
        )
      
      case 'callout':
        const calloutStyles = {
          info: 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950',
          warning: 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950',
          tip: 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950',
          danger: 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950'
        }
        
        const calloutIcons = {
          info: '💡',
          warning: '⚠️',
          tip: '✅',
          danger: '🚨'
        }
        
        return (
          <div className={clsx(
            'border-l-4 rounded-r-lg p-4 mb-6',
            calloutStyles[block.value.type] || calloutStyles.info
          )}>
            {block.value.title && (
              <div className="flex items-center font-semibold mb-2">
                <span className="mr-2">{calloutIcons[block.value.type] || calloutIcons.info}</span>
                {block.value.title}
              </div>
            )}
            <div 
              className="prose dark:prose-invert max-w-none"
              dangerouslySetInnerHTML={{ __html: block.value.text }}
            />
          </div>
        )
      
      case 'quote':
        return (
          <blockquote className="border-l-4 border-primary pl-6 py-4 mb-6 bg-muted/30 italic">
            <div className="prose dark:prose-invert max-w-none">
              {block.value.text}
            </div>
            {block.value.attribution && (
              <cite className="block mt-2 text-sm text-muted-foreground not-italic">
                — {block.value.attribution}
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
        <header className="mb-8">
          {/* Categories */}
          {post.categories.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {post.categories.map((category) => (
                <Link
                  key={category.id}
                  to={`/blog?category=${category.slug}`}
                  className="px-3 py-1 text-sm font-medium text-white rounded-full hover:opacity-80 transition-opacity"
                  style={{ backgroundColor: category.color }}
                >
                  {category.name}
                </Link>
              ))}
            </div>
          )}

          {/* Title */}
          <h1 className="text-4xl font-bold mb-4">{post.title}</h1>

          {/* Intro */}
          {post.intro && (
            <p className="text-xl text-muted-foreground mb-6">{post.intro}</p>
          )}

          {/* Meta Info */}
          <div className="flex flex-wrap items-center gap-6 pb-6 border-b">
            {post.author && (
              <div className="flex items-center space-x-2">
                <User className="h-5 w-5 text-muted-foreground" />
                <span className="font-medium">{post.author.display_name}</span>
              </div>
            )}
            
            {post.date && (
              <div className="flex items-center space-x-2 text-muted-foreground">
                <Calendar className="h-5 w-5" />
                <span>{formatDate(post.date)}</span>
              </div>
            )}
            
            {post.reading_time && (
              <div className="flex items-center space-x-2 text-muted-foreground">
                <Clock className="h-5 w-5" />
                <span>{post.reading_time} min read</span>
              </div>
            )}

            {post.ai_generated && (
              <span className="px-3 py-1 text-sm font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded-full">
                AI Enhanced Content
              </span>
            )}
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
        <div className="border-t pt-6 mb-8">
          <h3 className="text-lg font-semibold mb-4">Share this article</h3>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(post.title)}&url=${encodeURIComponent(window.location.href)}`, '_blank')}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
            >
              <ExternalLink className="h-4 w-4" />
              <span>Twitter</span>
            </button>
            
            <button
              onClick={() => window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(window.location.href)}`, '_blank')}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-700 text-white rounded-md hover:bg-blue-800 transition-colors"
            >
              <ExternalLink className="h-4 w-4" />
              <span>LinkedIn</span>
            </button>
            
            <button
              onClick={copyUrl}
              className="flex items-center space-x-2 px-4 py-2 border rounded-md hover:bg-muted transition-colors"
            >
              {copiedUrl ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              <span>{copiedUrl ? 'Copied!' : 'Copy Link'}</span>
            </button>
          </div>
        </div>

        {/* Related Posts */}
        {post.related_posts.length > 0 && (
          <div className="border-t pt-8">
            <h3 className="text-2xl font-semibold mb-6">Related Articles</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {post.related_posts.map((relatedPost) => (
                <article key={relatedPost.id} className="bg-card rounded-lg border p-4 hover:shadow-md transition-shadow">
                  <h4 className="font-semibold mb-2 hover:text-primary transition-colors">
                    <Link to={`/blog/${relatedPost.slug}`}>
                      {relatedPost.title}
                    </Link>
                  </h4>
                  <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                    {relatedPost.intro}
                  </p>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    {relatedPost.date && (
                      <span>{formatDate(relatedPost.date)}</span>
                    )}
                    {relatedPost.reading_time && (
                      <span>{relatedPost.reading_time} min read</span>
                    )}
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
  )
}