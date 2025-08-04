import React, { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { 
  Play,
  Clock,
  Users,
  Star,
  BookOpen,
  ChevronRight,
  Award,
  Download,
  Share2,
  Heart,
  CheckCircle,
  Lock,
  AlertCircle,
  Loader2,
  ArrowLeft
} from 'lucide-react'
import { apiRequest } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import ErrorBoundary from '../components/common/ErrorBoundary'

// Skeleton Loading Components
function CourseHeaderSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3 mb-4"></div>
      <div className="flex gap-4 mb-6">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
      </div>
    </div>
  )
}

function LessonSkeleton() {
  return (
    <div className="animate-pulse p-4 border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-4">
        <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
        <div className="flex-1">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
        </div>
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-12"></div>
      </div>
    </div>
  )
}

// Lesson Item Component
function LessonItem({ lesson, courseId, isEnrolled, userProgress }) {
  const isCompleted = userProgress?.completed_lessons?.includes(lesson.id)
  const isAccessible = isEnrolled || lesson.is_preview
  
  const formatDuration = (seconds) => {
    if (!seconds) return ''
    const minutes = Math.floor(seconds / 60)
    return `${minutes} min`
  }

  const getLessonIcon = () => {
    if (isCompleted) {
      return <CheckCircle className="w-5 h-5 text-green-500" />
    } else if (!isAccessible) {
      return <Lock className="w-5 h-5 text-gray-400" />
    } else {
      return <Play className="w-5 h-5 text-blue-500" />
    }
  }

  const content = (
    <div className="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
      <div className="flex-shrink-0">
        {getLessonIcon()}
      </div>
      
      <div className="flex-1 min-w-0">
        <h3 className={`font-medium ${
          isAccessible 
            ? 'text-gray-900 dark:text-gray-100' 
            : 'text-gray-500 dark:text-gray-400'
        }`}>
          {lesson.title}
        </h3>
        {lesson.description && (
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
            {lesson.description}
          </p>
        )}
      </div>
      
      <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
        {lesson.duration && (
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>{formatDuration(lesson.duration)}</span>
          </div>
        )}
        
        {lesson.is_preview && (
          <span className="bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 px-2 py-1 rounded-full text-xs font-medium">
            Preview
          </span>
        )}
        
        {isAccessible && <ChevronRight className="w-4 h-4" />}
      </div>
    </div>
  )

  if (!isAccessible) {
    return <div className="border-b border-gray-200 dark:border-gray-700 last:border-b-0">{content}</div>
  }

  return (
    <Link 
      to={`/courses/${courseId}/lessons/${lesson.id}`}
      className="block border-b border-gray-200 dark:border-gray-700 last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
    >
      {content}
    </Link>
  )
}

// Main Course Detail Component
export default function CourseDetailPage() {
  const { courseId } = useParams()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuth()
  
  const [course, setCourse] = useState(null)
  const [lessons, setLessons] = useState([])
  const [userProgress, setUserProgress] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [enrolling, setEnrolling] = useState(false)
  const [isWishlisted, setIsWishlisted] = useState(false)

  // Fetch course data
  useEffect(() => {
    const fetchCourseData = async () => {
      try {
        setLoading(true)
        setError(null)

        const [courseResponse, lessonsResponse] = await Promise.all([
          apiRequest(`/api/v1/courses/${courseId}/`),
          apiRequest(`/api/v1/courses/${courseId}/lessons/`)
        ])

        if (courseResponse.ok && lessonsResponse.ok) {
          const courseData = await courseResponse.json()
          const lessonsData = await lessonsResponse.json()
          
          setCourse(courseData)
          setLessons(lessonsData.results || lessonsData)
          
          // Fetch user progress if authenticated and enrolled
          if (isAuthenticated && courseData.user_enrolled) {
            try {
              const progressResponse = await apiRequest(`/api/v1/courses/${courseId}/progress/`)
              if (progressResponse.ok) {
                const progressData = await progressResponse.json()
                setUserProgress(progressData)
              }
            } catch (err) {
              console.warn('Could not fetch user progress:', err)
            }
          }
        } else {
          throw new Error('Failed to fetch course data')
        }
      } catch (err) {
        console.error('Error fetching course:', err)
        setError('Failed to load course. Please try again later.')
      } finally {
        setLoading(false)
      }
    }

    if (courseId) {
      fetchCourseData()
    }
  }, [courseId, isAuthenticated])

  // Handle course enrollment
  const handleEnroll = async () => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    try {
      setEnrolling(true)
      const response = await apiRequest(`/api/v1/courses/${courseId}/enroll/`, {
        method: 'POST'
      })

      if (response.ok) {
        setCourse(prev => ({ ...prev, user_enrolled: true }))
      } else {
        throw new Error('Enrollment failed')
      }
    } catch (err) {
      console.error('Enrollment error:', err)
      alert('Failed to enroll. Please try again.')
    } finally {
      setEnrolling(false)
    }
  }

  // Handle wishlist toggle
  const handleWishlistToggle = async () => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    try {
      const response = await apiRequest(`/api/v1/courses/${courseId}/wishlist/`, {
        method: isWishlisted ? 'DELETE' : 'POST'
      })

      if (response.ok) {
        setIsWishlisted(!isWishlisted)
      }
    } catch (err) {
      console.error('Wishlist error:', err)
    }
  }

  // Helper functions
  const renderStars = (rating) => {
    const stars = []
    const fullStars = Math.floor(rating)
    const hasHalfStar = rating % 1 !== 0

    for (let i = 0; i < 5; i++) {
      if (i < fullStars) {
        stars.push(
          <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
        )
      } else if (i === fullStars && hasHalfStar) {
        stars.push(
          <Star key={i} className="w-4 h-4 fill-yellow-400/50 text-yellow-400" />
        )
      } else {
        stars.push(
          <Star key={i} className="w-4 h-4 text-gray-300 dark:text-gray-600" />
        )
      }
    }
    return stars
  }

  const getDifficultyColor = (level) => {
    switch (level) {
      case 'beginner': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
      case 'intermediate': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
      case 'advanced': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
    }
  }

  const formatDuration = (hours) => {
    if (hours < 1) return `${Math.round(hours * 60)} min`
    return `${hours}h`
  }

  const getCompletionPercentage = () => {
    if (!userProgress || !lessons.length) return 0
    const completedCount = userProgress.completed_lessons?.length || 0
    return Math.round((completedCount / lessons.length) * 100)
  }

  if (loading) {
    return (
      <div className="container-custom py-8">
        <div className="max-w-4xl mx-auto">
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <CourseHeaderSkeleton />
              <div className="space-y-0 border border-gray-200 dark:border-gray-700 rounded-lg">
                {Array.from({ length: 5 }).map((_, index) => (
                  <LessonSkeleton key={index} />
                ))}
              </div>
            </div>
            <div className="lg:col-span-1">
              <div className="card-modern p-6 animate-pulse">
                <div className="aspect-video bg-gray-200 dark:bg-gray-700 rounded-lg mb-4"></div>
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
                <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
              </div>
            </div>
          </div>
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
            Unable to Load Course
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => navigate('/courses')}
              className="btn-secondary"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Courses
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

  if (!course) {
    return (
      <div className="container-custom py-8">
        <div className="max-w-md mx-auto text-center">
          <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Course Not Found
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            The course you're looking for doesn't exist or has been removed.
          </p>
          <button
            onClick={() => navigate('/courses')}
            className="btn-primary"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Courses
          </button>
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="container-custom py-8">
        <div className="max-w-6xl mx-auto">
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
                  to={`/courses?category=${course.category.slug}`}
                  className="hover:text-blue-600 dark:hover:text-blue-400"
                >
                  {course.category.name}
                </Link>
              </li>
              <li>
                <ChevronRight className="w-4 h-4" />
              </li>
              <li className="text-gray-900 dark:text-gray-100 font-medium">
                {course.title}
              </li>
            </ol>
          </nav>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-8">
              {/* Course Header */}
              <div>
                <div className="flex items-start gap-4 mb-4">
                  <h1 className="text-3xl lg:text-4xl font-bold text-gray-900 dark:text-gray-100">
                    {course.title}
                  </h1>
                  {course.is_featured && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
                      Featured
                    </span>
                  )}
                </div>
                
                <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
                  {course.description}
                </p>

                {/* Course Meta */}
                <div className="flex flex-wrap items-center gap-6 text-sm text-gray-600 dark:text-gray-400 mb-6">
                  {course.instructor && (
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
                          {course.instructor.first_name?.[0] || course.instructor.username?.[0]?.toUpperCase() || '?'}
                        </span>
                      </div>
                      <span>
                        {course.instructor.first_name && course.instructor.last_name 
                          ? `${course.instructor.first_name} ${course.instructor.last_name}`
                          : course.instructor.username || 'Unknown Instructor'
                        }
                      </span>
                    </div>
                  )}
                  
                  {course.average_rating && course.total_reviews > 0 && (
                    <div className="flex items-center gap-2">
                      <div className="flex">
                        {renderStars(parseFloat(course.average_rating))}
                      </div>
                      <span>
                        {parseFloat(course.average_rating).toFixed(1)} ({course.total_reviews} reviews)
                      </span>
                    </div>
                  )}
                  
                  <div className="flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    <span>{course.enrollment_count} students</span>
                  </div>
                  
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>{formatDuration(course.estimated_duration)}</span>
                  </div>
                  
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(course.difficulty_level)}`}>
                    {course.difficulty_level}
                  </span>
                </div>

                {/* User Progress */}
                {course.user_enrolled && userProgress && (
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                        Your Progress
                      </span>
                      <span className="text-sm text-blue-700 dark:text-blue-300">
                        {getCompletionPercentage()}% complete
                      </span>
                    </div>
                    <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${getCompletionPercentage()}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>

              {/* Course Content */}
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                  Course Content
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {lessons.length} lesson{lessons.length !== 1 ? 's' : ''}
                  {course.estimated_duration && ` • ${formatDuration(course.estimated_duration)} total length`}
                </p>
                
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  {lessons.length > 0 ? (
                    lessons.map((lesson, index) => (
                      <LessonItem 
                        key={lesson.id}
                        lesson={lesson}
                        courseId={courseId}
                        isEnrolled={course.user_enrolled}
                        userProgress={userProgress}
                      />
                    ))
                  ) : (
                    <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                      <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>No lessons available yet.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="lg:col-span-1">
              <div className="card-modern p-6 sticky top-6">
                {/* Course Preview */}
                <div className="aspect-video bg-gradient-to-br from-blue-50 to-blue-100 dark:from-gray-800 dark:to-gray-700 rounded-lg mb-6 overflow-hidden">
                  {course.thumbnail ? (
                    <img 
                      src={course.thumbnail} 
                      alt={course.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <BookOpen className="w-16 h-16 text-blue-400 dark:text-blue-300" />
                    </div>
                  )}
                </div>

                {/* Price */}
                <div className="mb-6">
                  <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    {course.is_free ? (
                      <span className="text-green-600 dark:text-green-400">Free</span>
                    ) : (
                      <span>${course.price}</span>
                    )}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="space-y-3 mb-6">
                  {course.user_enrolled ? (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 px-4 py-2 rounded-lg">
                        <CheckCircle className="w-5 h-5" />
                        <span className="font-medium">Enrolled</span>
                      </div>
                      {lessons.length > 0 && (
                        <Link 
                          to={`/courses/${courseId}/lessons/${lessons[0].id}`}
                          className="btn-primary w-full text-center"
                        >
                          Continue Learning
                        </Link>
                      )}
                    </div>
                  ) : (
                    <button
                      onClick={handleEnroll}
                      disabled={enrolling}
                      className="btn-primary w-full flex items-center justify-center gap-2"
                    >
                      {enrolling ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Enrolling...
                        </>
                      ) : (
                        course.is_free ? 'Enroll for Free' : 'Enroll Now'
                      )}
                    </button>
                  )}
                  
                  <div className="flex gap-2">
                    <button
                      onClick={handleWishlistToggle}
                      className="btn-secondary flex-1 flex items-center justify-center gap-2"
                    >
                      <Heart className={`w-4 h-4 ${isWishlisted ? 'fill-red-500 text-red-500' : ''}`} />
                      {isWishlisted ? 'Wishlisted' : 'Wishlist'}
                    </button>
                    <button className="btn-secondary flex items-center justify-center">
                      <Share2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Course Includes */}
                <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    This course includes:
                  </h3>
                  <ul className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
                    <li className="flex items-center gap-3">
                      <BookOpen className="w-4 h-4 text-blue-500" />
                      <span>{lessons.length} lesson{lessons.length !== 1 ? 's' : ''}</span>
                    </li>
                    {course.estimated_duration && (
                      <li className="flex items-center gap-3">
                        <Clock className="w-4 h-4 text-blue-500" />
                        <span>{formatDuration(course.estimated_duration)} of content</span>
                      </li>
                    )}
                    <li className="flex items-center gap-3">
                      <Award className="w-4 h-4 text-blue-500" />
                      <span>Certificate of completion</span>
                    </li>
                    <li className="flex items-center gap-3">
                      <Download className="w-4 h-4 text-blue-500" />
                      <span>Downloadable resources</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  )
}