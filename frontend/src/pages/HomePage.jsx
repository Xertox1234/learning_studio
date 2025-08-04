import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Code2, BookOpen, Users, Zap, Award, ArrowRight, Calendar, Clock } from 'lucide-react'
import { api } from '../utils/api'

export default function HomePage() {
  const [homepageData, setHomepageData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchHomepageData()
  }, [])

  const fetchHomepageData = async () => {
    try {
      const response = await api.get('/wagtail/homepage/')
      setHomepageData(response.data)
    } catch (err) {
      console.error('Error fetching homepage data:', err)
      // Use fallback data if API fails
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
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary/10 via-primary/5 to-background py-20 lg:py-32">
        <div className="container-custom">
          <div className="max-w-3xl">
            <h1 className="text-5xl lg:text-6xl font-bold mb-6 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              {homepageData?.hero_title || "Master Python with AI-Powered Learning"}
            </h1>
            <p className="text-xl text-muted-foreground mb-8">
              {homepageData?.hero_subtitle || "Join thousands mastering Python through interactive lessons, real-time code execution, and AI-powered assistance."}
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/register" className="btn-primary text-center">
                Start Learning Free
              </Link>
              <Link to="/courses" className="btn-secondary text-center">
                Browse Courses
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      {homepageData?.stats && homepageData.stats.length > 0 && (
        <section className="py-16 bg-muted/30">
          <div className="container-custom">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              {homepageData.stats.map((stat, index) => (
                <div key={index} className="space-y-2">
                  <div className="text-3xl font-bold text-primary">{stat.number}</div>
                  <div className="text-sm font-medium">{stat.label}</div>
                  {stat.description && (
                    <div className="text-xs text-muted-foreground">{stat.description}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Features */}
      <section className="py-20">
        <div className="container-custom">
          <h2 className="text-3xl font-bold text-center mb-12">
            {homepageData?.features_title || "Why Choose Python Learning Studio?"}
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {homepageData?.features && homepageData.features.length > 0 ? (
              homepageData.features.map((feature, index) => (
                <div key={index} className="card-modern p-6">
                  <div className="text-4xl mb-4">{feature.icon || '⭐'}</div>
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </div>
              ))
            ) : (
              // Fallback features
              <>
                <div className="card-modern p-6">
                  <Code2 className="h-12 w-12 text-primary mb-4" />
                  <h3 className="text-xl font-semibold mb-2">Interactive Coding</h3>
                  <p className="text-muted-foreground">
                    Write and run Python code directly in your browser with our advanced code editor.
                  </p>
                </div>
                <div className="card-modern p-6">
                  <Zap className="h-12 w-12 text-primary mb-4" />
                  <h3 className="text-xl font-semibold mb-2">AI-Powered Learning</h3>
                  <p className="text-muted-foreground">
                    Get instant feedback and personalized hints from our AI tutor as you code.
                  </p>
                </div>
                <div className="card-modern p-6">
                  <Users className="h-12 w-12 text-primary mb-4" />
                  <h3 className="text-xl font-semibold mb-2">Community Support</h3>
                  <p className="text-muted-foreground">
                    Join thousands of learners in our active forum to share knowledge and get help.
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Recent Blog Posts */}
      {homepageData?.recent_posts && homepageData.recent_posts.length > 0 && (
        <section className="py-20 bg-muted/30">
          <div className="container-custom">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">Latest from Our Blog</h2>
              <p className="text-lg text-muted-foreground">
                Stay updated with the latest Python tutorials and AI-powered learning insights
              </p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-8">
              {homepageData.recent_posts.map((post) => (
                <article key={post.id} className="bg-card rounded-lg border hover:shadow-lg transition-shadow">
                  <div className="p-6">
                    <h3 className="text-xl font-semibold mb-3 hover:text-primary transition-colors">
                      <Link to={`/blog/${post.slug}`}>
                        {post.title}
                      </Link>
                    </h3>
                    <p className="text-muted-foreground mb-4 line-clamp-3">
                      {post.intro}
                    </p>
                    <div className="flex items-center justify-between text-sm text-muted-foreground mb-4">
                      {post.date && (
                        <div className="flex items-center space-x-1">
                          <Calendar className="h-4 w-4" />
                          <span>{formatDate(post.date)}</span>
                        </div>
                      )}
                      {post.reading_time && (
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4" />
                          <span>{post.reading_time} min read</span>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center justify-between">
                      {post.ai_generated && (
                        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded">
                          AI Enhanced
                        </span>
                      )}
                      <Link
                        to={`/blog/${post.slug}`}
                        className="text-primary hover:text-primary/80 text-sm font-medium flex items-center space-x-1"
                      >
                        <span>Read more</span>
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                    </div>
                  </div>
                </article>
              ))}
            </div>
            
            <div className="text-center mt-12">
              <Link
                to="/blog"
                className="btn-secondary inline-flex items-center space-x-2"
              >
                <span>View All Posts</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* Call to Action */}
      <section className="py-20 bg-primary text-primary-foreground">
        <div className="container-custom text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Start Your Python Journey?</h2>
          <p className="text-xl mb-8 opacity-90">
            Join our community of learners and start building amazing things with Python today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register" className="btn-secondary bg-white text-primary hover:bg-white/90">
              Get Started Free
            </Link>
            <Link to="/courses" className="btn-outline border-white text-white hover:bg-white hover:text-primary">
              Explore Courses
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}