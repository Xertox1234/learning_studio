import React, { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { 
  ChevronLeft,
  ChevronRight,
  Clock,
  BookOpen,
  CheckCircle,
  Play,
  User,
  ArrowLeft,
  AlertCircle,
  Loader2,
  Code,
  FileText,
  Video
} from 'lucide-react'
import { apiRequest } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import ErrorBoundary from '../components/common/ErrorBoundary'
import { ReadOnlyCodeBlock } from '../components/code-editor'

// Skeleton Loading Component
function LessonSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-6"></div>
      <div className="space-y-4">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-4/5"></div>
        <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
      </div>
    </div>
  )
}

// Lesson Content Component with CodeMirror 6 Integration
function LessonContent({ content, contentFormat }) {
  // Enhanced markdown-style rendering with CodeMirror 6 code blocks
  const renderContent = (text) => {
    if (!text || text.trim() === '') {
      return (
        <div className="text-center py-12">
          <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            Content Coming Soon
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            This lesson content is currently being prepared. Please check back later.
          </p>
        </div>
      )
    }
    
    // Split content into sections and render appropriately
    const lines = text.split('\n')
    const elements = []
    let currentCodeBlock = []
    let currentLanguage = 'text'
    let inCodeBlock = false
    let elementKey = 0
    
    lines.forEach((line, index) => {
      if (line.trim().startsWith('```')) {
        if (inCodeBlock) {
          // End of code block - render with CodeMirror
          if (currentCodeBlock.length > 0) {
            elements.push(
              <div key={`code-${elementKey++}`} className="mb-6">
                <ReadOnlyCodeBlock
                  code={currentCodeBlock.join('\n')}
                  language={currentLanguage}
                  showLineNumbers={true}
                  className="rounded-lg"
                />
              </div>
            )
          }
          currentCodeBlock = []
          inCodeBlock = false
          currentLanguage = 'text'
        } else {
          // Start of code block - extract language
          const langMatch = line.trim().match(/^```(\w+)?/)
          currentLanguage = langMatch && langMatch[1] ? langMatch[1].toLowerCase() : 'text'
          inCodeBlock = true
        }
        return
      }
      
      if (inCodeBlock) {
        currentCodeBlock.push(line)
        return
      }
      
      // Handle markdown-style content outside code blocks
      if (line.trim().startsWith('#')) {
        const level = line.match(/^#+/)[0].length
        const text = line.replace(/^#+\s*/, '')
        const HeadingTag = `h${Math.min(level + 1, 6)}`
        elements.push(
          React.createElement(
            HeadingTag,
            {
              key: `heading-${elementKey++}`,
              className: `font-bold mb-3 mt-6 ${
                level === 1 ? 'text-2xl' : 
                level === 2 ? 'text-xl' : 
                level === 3 ? 'text-lg' : 'text-base'
              } text-gray-900 dark:text-gray-100`
            },
            text
          )
        )
      } else if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
        const text = line.replace(/^[\s\-•]+/, '')
        elements.push(
          <li key={`list-${elementKey++}`} className="ml-4 mb-1 text-gray-700 dark:text-gray-300">
            {text}
          </li>
        )
      } else if (line.trim()) {
        // Handle inline code with backticks
        const processInlineCode = (text) => {
          const parts = text.split(/(`[^`]+`)/)
          return parts.map((part, i) => {
            if (part.startsWith('`') && part.endsWith('`')) {
              const code = part.slice(1, -1)
              return (
                <code 
                  key={i} 
                  className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 text-sm font-mono rounded border"
                >
                  {code}
                </code>
              )
            }
            return part
          })
        }

        elements.push(
          <p key={`paragraph-${elementKey++}`} className="mb-4 text-gray-700 dark:text-gray-300 leading-relaxed">
            {processInlineCode(line)}
          </p>
        )
      } else if (line.trim() === '') {
        // Add spacing for empty lines
        elements.push(
          <div key={`space-${elementKey++}`} className="mb-2"></div>
        )
      }
    })
    
    // Handle case where content ends with an open code block
    if (inCodeBlock && currentCodeBlock.length > 0) {
      elements.push(
        <div key={`code-final-${elementKey++}`} className="mb-6">
          <ReadOnlyCodeBlock
            code={currentCodeBlock.join('\n')}
            language={currentLanguage}
            showLineNumbers={true}
            className="rounded-lg"
          />
        </div>
      )
    }
    
    return elements
  }
  
  return (
    <div className="prose prose-lg max-w-none dark:prose-invert">
      {renderContent(content)}
    </div>
  )
}

// Lesson Navigation Component
function LessonNavigation({ lesson, courseId }) {
  return (
    <div className="flex items-center justify-between py-6 border-t border-gray-200 dark:border-gray-700">
      <div className="flex-1">
        {lesson.previous_lesson ? (
          <Link
            to={`/courses/${courseId}/lessons/${lesson.previous_lesson.id}`}
            className="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <div className="text-left">
              <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Previous</div>
              <div className="text-sm font-medium">{lesson.previous_lesson.title}</div>
            </div>
          </Link>
        ) : (
          <div></div>
        )}
      </div>
      
      <div className="flex-1 text-right">
        {lesson.next_lesson ? (
          <Link
            to={`/courses/${courseId}/lessons/${lesson.next_lesson.id}`}
            className="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
          >
            <div className="text-right">
              <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Next</div>
              <div className="text-sm font-medium">{lesson.next_lesson.title}</div>
            </div>
            <ChevronRight className="w-4 h-4" />
          </Link>
        ) : (
          <div></div>
        )}
      </div>
    </div>
  )
}

// Main Lesson Page Component
export default function LessonPage() {
  const { courseId, lessonId } = useParams()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuth()
  
  const [lesson, setLesson] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [markingComplete, setMarkingComplete] = useState(false)

  // Fetch lesson data
  useEffect(() => {
    const fetchLesson = async () => {
      try {
        setLoading(true)
        setError(null)

        const response = await apiRequest(`/api/v1/lessons/${lessonId}/`)

        if (response.ok) {
          const lessonData = await response.json()
          setLesson(lessonData)
        } else {
          throw new Error('Failed to fetch lesson')
        }
      } catch (err) {
        console.error('Error fetching lesson:', err)
        setError('Failed to load lesson. Please try again later.')
      } finally {
        setLoading(false)
      }
    }

    if (lessonId) {
      fetchLesson()
    }
  }, [lessonId])

  // Mark lesson as complete
  const handleMarkComplete = async () => {
    if (!isAuthenticated || !lesson) return
    
    try {
      setMarkingComplete(true)
      const response = await apiRequest(`/api/v1/lessons/${lessonId}/complete/`, {
        method: 'POST'
      })

      if (response.ok) {
        setLesson(prev => ({
          ...prev,
          user_progress: { ...prev.user_progress, completed: true }
        }))
      }
    } catch (err) {
      console.error('Error marking lesson complete:', err)
    } finally {
      setMarkingComplete(false)
    }
  }

  // Helper functions
  const formatDuration = (minutes) => {
    if (!minutes) return ''
    if (minutes < 60) return `${minutes} min`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}h ${mins}min`
  }

  const getLessonTypeIcon = (type) => {
    switch (type) {
      case 'video': return <Video className="w-4 h-4" />
      case 'practical': return <Code className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  const getDifficultyColor = (level) => {
    switch (level) {
      case 'beginner': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
      case 'intermediate': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
      case 'advanced': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
    }
  }

  if (loading) {
    return (
      <div className="container-custom py-8">
        <div className="max-w-4xl mx-auto">
          <LessonSkeleton />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container-custom py-8">
        <div className="max-w-md mx-auto text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Unable to Load Lesson
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => navigate(`/courses/${courseId}`)}
              className="btn-secondary"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Course
            </button>
            <button
              onClick={() => window.location.reload()}
              className="btn-primary"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!lesson) {
    return (
      <div className="container-custom py-8">
        <div className="max-w-md mx-auto text-center">
          <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Lesson Not Found
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            The lesson you're looking for doesn't exist or has been removed.
          </p>
          <button
            onClick={() => navigate(`/courses/${courseId}`)}
            className="btn-primary"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Course
          </button>
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="container-custom py-8">
          <div className="max-w-4xl mx-auto">
            {/* Breadcrumb */}
            <nav className="mb-6">
              <ol className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                <li>
                  <Link to="/courses" className="hover:text-blue-600 dark:hover:text-blue-400">
                    Courses
                  </Link>
                </li>
                <li>
                  <ChevronRight className="w-4 h-4" />
                </li>
                <li>
                  <Link 
                    to={`/courses/${courseId}`}
                    className="hover:text-blue-600 dark:hover:text-blue-400"
                  >
                    {lesson.course.title}
                  </Link>
                </li>
                <li>
                  <ChevronRight className="w-4 h-4" />
                </li>
                <li className="text-gray-900 dark:text-gray-100 font-medium">
                  {lesson.title}
                </li>
              </ol>
            </nav>

            {/* Lesson Header */}
            <div className="card-modern p-8 mb-8">
              <div className="flex items-start justify-between mb-6">
                <div className="flex-1">
                  <h1 className="text-3xl lg:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                    {lesson.title}
                  </h1>
                  
                  {lesson.description && (
                    <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
                      {lesson.description}
                    </p>
                  )}

                  {/* Lesson Meta */}
                  <div className="flex flex-wrap items-center gap-6 text-sm text-gray-600 dark:text-gray-400">
                    <div className="flex items-center gap-2">
                      {getLessonTypeIcon(lesson.lesson_type)}
                      <span className="capitalize">{lesson.lesson_type || 'Theory'}</span>
                    </div>
                    
                    {lesson.estimated_duration && (
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        <span>{formatDuration(lesson.estimated_duration)}</span>
                      </div>
                    )}
                    
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(lesson.difficulty_level)}`}>
                      {lesson.difficulty_level || 'Beginner'}
                    </span>
                    
                    <div className="flex items-center gap-2">
                      <span>Lesson {lesson.order}</span>
                    </div>
                  </div>
                </div>
                
                {/* Completion Status */}
                {isAuthenticated && (
                  <div className="flex-shrink-0 ml-6">
                    {lesson.user_progress?.completed ? (
                      <div className="flex items-center gap-2 text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 px-4 py-2 rounded-lg">
                        <CheckCircle className="w-5 h-5" />
                        <span className="font-medium">Completed</span>
                      </div>
                    ) : (
                      <button
                        onClick={handleMarkComplete}
                        disabled={markingComplete}
                        className="btn-primary flex items-center gap-2"
                      >
                        {markingComplete ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Marking...
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-4 h-4" />
                            Mark Complete
                          </>
                        )}
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Lesson Content */}
            <div className="card-modern p-8 mb-8">
              {lesson.video_url && (
                <div className="mb-8">
                  <div className="aspect-video bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <Video className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600 dark:text-gray-400">
                        Video content would be embedded here
                      </p>
                      <a 
                        href={lesson.video_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="btn-primary mt-4 inline-flex items-center gap-2"
                      >
                        <Play className="w-4 h-4" />
                        Watch Video
                      </a>
                    </div>
                  </div>
                </div>
              )}
              
              <LessonContent 
                content={lesson.content} 
                contentFormat={lesson.content_format}
              />
            </div>

            {/* Lesson Navigation */}
            <div className="card-modern p-6">
              <LessonNavigation lesson={lesson} courseId={courseId} />
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  )
}