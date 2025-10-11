import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { 
  BookOpen, Clock, Users, Award, Star, CheckCircle, PlayCircle, 
  User, Calendar, ArrowRight, ChevronRight, Target, AlertCircle 
} from 'lucide-react'
import { api } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import { generateCourseSchema, injectStructuredData } from '../utils/schema'
import clsx from 'clsx'

export default function WagtailCourseDetailPage() {
  const { courseSlug } = useParams()
  const { user, isAuthenticated } = useAuth()
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [enrollmentStatus, setEnrollmentStatus] = useState(null)
  const [enrollmentLoading, setEnrollmentLoading] = useState(false)

  useEffect(() => {
    fetchCourse()
  }, [courseSlug])

  // Check enrollment status when user is authenticated and course is loaded
  useEffect(() => {
    if (isAuthenticated && course) {
      checkEnrollmentStatus()
    }
  }, [isAuthenticated, course])

  // Add structured data for SEO when course is loaded
  useEffect(() => {
    if (course) {
      const schema = generateCourseSchema(course)
      injectStructuredData(schema)
      
      // Update page title and meta description
      document.title = `${course.title} - Python Learning Studio`
      
      // Update meta description
      const metaDescription = document.querySelector('meta[name="description"]')
      if (metaDescription) {
        metaDescription.setAttribute('content', course.short_description)
      } else {
        const meta = document.createElement('meta')
        meta.name = 'description'
        meta.content = course.short_description
        document.head.appendChild(meta)
      }
    }
    
    // Cleanup
    return () => {
      const scripts = document.querySelectorAll('script[type="application/ld+json"][data-schema]')
      scripts.forEach(script => script.remove())
    }
  }, [course])

  const fetchCourse = async () => {
    try {
      setLoading(true)
      const response = await api.get(`/learning/courses/${courseSlug}/`)
      setCourse(response.data)
      setError(null)
    } catch (err) {
      console.error('Error fetching course:', err)
      setError(err.response?.status === 404 ? 'Course not found.' : 'Failed to load course. Please try again later.')
    } finally {
      setLoading(false)
    }
  }

  const checkEnrollmentStatus = async () => {
    try {
      const response = await api.get(`/learning/courses/${courseSlug}/enrollment-status/`)
      setEnrollmentStatus(response.data)
    } catch (err) {
      console.error('Error checking enrollment status:', err)
      setEnrollmentStatus(null)
    }
  }

  const handleEnrollment = async () => {
    console.log('handleEnrollment called')
    console.log('isAuthenticated:', isAuthenticated)
    console.log('user:', user)
    
    if (!isAuthenticated) {
      console.log('User not authenticated, redirecting to login')
      // Redirect to login or show login modal
      window.location.href = '/login'
      return
    }

    try {
      setEnrollmentLoading(true)
      console.log('Making enrollment request for course:', courseSlug)
      
      // Check if we have an auth token
      const token = localStorage.getItem('authToken')
      console.log('Auth token available:', !!token)
      if (token) {
        console.log('Token preview:', token.substring(0, 20) + '...')
      }
      
      const response = await api.post(`/learning/courses/${courseSlug}/enroll/`)
      console.log('Enrollment response:', response)
      
      if (response.data.success) {
        // Update enrollment status
        setEnrollmentStatus({
          enrolled: true,
          enrollment: response.data.enrollment
        })
        
        // Show success message
        alert(response.data.message)
      }
    } catch (err) {
      console.error('Error enrolling in course:', err)
      console.error('Error details:', err.response)
      console.error('Error response data:', err.response?.data)
      console.error('Error response status:', err.response?.status)
      
      const errorMessage = err.response?.data?.error || err.response?.data?.detail || 'Failed to enroll in course. Please try again.'
      alert(errorMessage)
    } finally {
      setEnrollmentLoading(false)
    }
  }

  const handleUnenrollment = async () => {
    if (!confirm('Are you sure you want to unenroll from this course? Your progress will be saved.')) {
      return
    }

    try {
      setEnrollmentLoading(true)
      const response = await api.delete(`/learning/courses/${courseSlug}/unenroll/`)
      
      if (response.data.success) {
        // Update enrollment status
        setEnrollmentStatus({
          enrolled: false,
          enrollment: null
        })
        
        // Show success message
        alert(response.data.message)
      }
    } catch (err) {
      console.error('Error unenrolling from course:', err)
      alert(err.response?.data?.error || 'Failed to unenroll from course. Please try again.')
    } finally {
      setEnrollmentLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container-custom py-8">
        <div className="animate-pulse max-w-4xl mx-auto">
          <div className="h-6 bg-muted rounded w-32 mb-4"></div>
          <div className="h-8 bg-muted rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-muted rounded w-1/2 mb-8"></div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6">
              <div className="h-64 bg-muted rounded"></div>
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-4 bg-muted rounded w-full"></div>
                ))}
              </div>
            </div>
            <div className="space-y-4">
              <div className="h-32 bg-muted rounded"></div>
              <div className="h-48 bg-muted rounded"></div>
            </div>
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
            <h1 className="text-2xl font-semibold text-destructive mb-4">Course Not Found</h1>
            <p className="text-muted-foreground mb-6">{error}</p>
            <Link
              to="/courses"
              className="inline-flex items-center space-x-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              <ArrowRight className="h-4 w-4" />
              <span>Browse All Courses</span>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container-custom py-8">
      <div className="max-w-6xl mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center space-x-2 text-sm text-muted-foreground mb-6">
          <Link to="/courses" className="hover:text-primary transition-colors">
            Courses
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-foreground">{course.title}</span>
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Course Header */}
            <div className="mb-8">
              {/* Course Code and Featured Badge */}
              <div className="flex items-center space-x-3 mb-4">
                <span className="px-3 py-1 text-sm font-medium bg-primary/10 text-primary rounded">
                  {course.course_code}
                </span>
                {course.featured && (
                  <div className="flex items-center space-x-1 text-yellow-600">
                    <Star className="h-4 w-4 fill-current" />
                    <span className="text-sm font-medium">Featured</span>
                  </div>
                )}
                {course.skill_level && (
                  <span 
                    className="px-3 py-1 text-sm font-medium text-white rounded"
                    style={{ backgroundColor: course.skill_level.color }}
                  >
                    {course.skill_level.name}
                  </span>
                )}
              </div>

              {/* Title and Description */}
              <h1 className="text-4xl font-bold mb-4">{course.title}</h1>
              <p className="text-xl text-muted-foreground mb-6">{course.short_description}</p>

              {/* Course Meta */}
              <div className="flex flex-wrap items-center gap-6 text-sm text-muted-foreground">
                {course.instructor && (
                  <div className="flex items-center space-x-2">
                    <User className="h-4 w-4" />
                    <span>Instructor: {course.instructor.name}</span>
                  </div>
                )}
                <div className="flex items-center space-x-2">
                  <BookOpen className="h-4 w-4" />
                  <span>{course.lessons.length} lessons</span>
                </div>
                {course.estimated_duration && (
                  <div className="flex items-center space-x-2">
                    <Clock className="h-4 w-4" />
                    <span>{course.estimated_duration}</span>
                  </div>
                )}
                <div className="flex items-center space-x-2">
                  <Award className="h-4 w-4" />
                  <span className="capitalize">{course.difficulty_level}</span>
                </div>
              </div>
            </div>

            {/* Course Image */}
            {course.course_image && (
              <div className="mb-8">
                <img 
                  src={course.course_image} 
                  alt={course.title}
                  className="w-full h-64 object-cover rounded-lg"
                />
              </div>
            )}

            {/* Tabs */}
            <div className="mb-6">
              <div className="border-b">
                <nav className="-mb-px flex space-x-8">
                  {[
                    { id: 'overview', label: 'Overview' },
                    { id: 'curriculum', label: 'Curriculum' },
                    { id: 'instructor', label: 'Instructor' }
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={clsx(
                        'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                        activeTab === tab.id
                          ? 'border-primary text-primary'
                          : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted'
                      )}
                    >
                      {tab.label}
                    </button>
                  ))}
                </nav>
              </div>
            </div>

            {/* Tab Content */}
            <div className="space-y-6">
              {activeTab === 'overview' && (
                <>
                  {/* Course Description */}
                  <div>
                    <h2 className="text-2xl font-semibold mb-4">About This Course</h2>
                    <div 
                      className="prose prose-lg dark:prose-invert max-w-none"
                      dangerouslySetInnerHTML={{ __html: course.detailed_description }}
                    />
                  </div>

                  {/* Learning Objectives */}
                  {course.learning_objectives.length > 0 && (
                    <div>
                      <h2 className="text-2xl font-semibold mb-4">What You'll Learn</h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {course.learning_objectives.map((objective, index) => (
                          <div key={index} className="flex items-start space-x-3">
                            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                            <div>
                              <h3 className="font-medium">{objective.title}</h3>
                              {objective.description && (
                                <p className="text-sm text-muted-foreground mt-1">{objective.description}</p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Prerequisites */}
                  {course.prerequisites && (
                    <div>
                      <h2 className="text-2xl font-semibold mb-4">Prerequisites</h2>
                      <div 
                        className="prose dark:prose-invert max-w-none"
                        dangerouslySetInnerHTML={{ __html: course.prerequisites }}
                      />
                    </div>
                  )}

                  {/* Course Features */}
                  {course.features.length > 0 && (
                    <div>
                      <h2 className="text-2xl font-semibold mb-4">Course Features</h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {course.features.map((feature, index) => (
                          <div key={index} className="flex items-start space-x-3">
                            <div className="text-2xl">{feature.icon || '⭐'}</div>
                            <div>
                              <h3 className="font-semibold mb-1">{feature.title}</h3>
                              <p className="text-muted-foreground">{feature.description}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}

              {activeTab === 'curriculum' && (
                <div>
                  <h2 className="text-2xl font-semibold mb-4">Course Curriculum</h2>
                  
                  {/* Syllabus */}
                  {course.syllabus.length > 0 ? (
                    <div className="space-y-6">
                      {course.syllabus.map((module, moduleIndex) => (
                        <div key={moduleIndex} className="border rounded-lg p-6">
                          <h3 className="text-xl font-semibold mb-3">{module.title}</h3>
                          <div 
                            className="prose dark:prose-invert max-w-none mb-4"
                            dangerouslySetInnerHTML={{ __html: module.description }}
                          />
                          {module.lessons.length > 0 && (
                            <div className="space-y-2">
                              <h4 className="font-medium">Lessons:</h4>
                              <ul className="space-y-2">
                                {module.lessons.map((lesson, lessonIndex) => (
                                  <li key={lessonIndex} className="flex items-center justify-between p-3 bg-muted/30 rounded">
                                    <div>
                                      <div className="font-medium">{lesson.lesson_title}</div>
                                      <div className="text-sm text-muted-foreground">{lesson.lesson_description}</div>
                                    </div>
                                    {lesson.estimated_time && (
                                      <div className="text-sm text-muted-foreground flex items-center space-x-1">
                                        <Clock className="h-4 w-4" />
                                        <span>{lesson.estimated_time}</span>
                                      </div>
                                    )}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    /* Actual Lessons */
                    <div className="space-y-4">
                      {course.lessons.map((lesson, index) => (
                        <div key={lesson.id} className="border rounded-lg p-4 hover:bg-muted/30 transition-colors">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <div className="w-8 h-8 bg-primary/10 text-primary rounded-full flex items-center justify-center text-sm font-medium">
                                {lesson.lesson_number}
                              </div>
                              <div>
                                <h3 className="font-semibold">{lesson.title}</h3>
                                <p className="text-sm text-muted-foreground">{lesson.intro}</p>
                              </div>
                            </div>
                            <div className="flex items-center space-x-4">
                              {lesson.estimated_duration && (
                                <div className="text-sm text-muted-foreground flex items-center space-x-1">
                                  <Clock className="h-4 w-4" />
                                  <span>{lesson.estimated_duration}</span>
                                </div>
                              )}
                              {enrollmentStatus?.enrolled ? (
                                <Link
                                  to={`/learning/courses/${course.slug}/lessons/${lesson.slug}`}
                                  className="btn-secondary text-sm"
                                >
                                  Start Lesson
                                </Link>
                              ) : (
                                <span className="text-sm text-muted-foreground">
                                  {course.is_free ? 'Enroll to access' : 'Purchase required'}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'instructor' && course.instructor && (
                <div>
                  <h2 className="text-2xl font-semibold mb-4">Meet Your Instructor</h2>
                  <div className="bg-card border rounded-lg p-6">
                    <div className="flex items-start space-x-4">
                      <div className="w-16 h-16 bg-primary/10 text-primary rounded-full flex items-center justify-center text-xl font-semibold">
                        {course.instructor.name.charAt(0)}
                      </div>
                      <div>
                        <h3 className="text-xl font-semibold">{course.instructor.name}</h3>
                        <p className="text-muted-foreground">{course.instructor.email}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Enrollment Card */}
            <div className="bg-card border rounded-lg p-6">
              <div className="text-center mb-6">
                <div className="text-3xl font-bold text-primary mb-2">
                  {course.is_free ? 'Free' : `$${course.price}`}
                </div>
                {course.enrollment_limit && (
                  <p className="text-sm text-muted-foreground">
                    Limited to {course.enrollment_limit} students
                  </p>
                )}
              </div>

              {/* Enrollment Button */}
              {!isAuthenticated ? (
                <Link 
                  to="/login" 
                  className="w-full btn-primary mb-4 text-center inline-block"
                >
                  {course.is_free ? 'Login to Enroll for Free' : 'Login to Enroll Now'}
                </Link>
              ) : enrollmentStatus?.enrolled ? (
                <div className="space-y-3 mb-4">
                  <div className="w-full bg-green-600 text-white py-3 px-4 rounded-lg text-center font-medium">
                    ✓ Enrolled
                  </div>
                  
                  {/* Start Course / Continue Learning Button */}
                  {course.lessons.length > 0 && (
                    <Link 
                      to={`/learning/courses/${course.slug}/lessons/${course.lessons[0].slug}`}
                      className="w-full btn-primary mb-2 text-center inline-block"
                    >
                      {enrollmentStatus.enrollment?.progress_percentage > 0 ? 'Continue Learning' : 'Start Course'}
                    </Link>
                  )}
                  
                  <button 
                    onClick={handleUnenrollment}
                    disabled={enrollmentLoading}
                    className="w-full btn-secondary text-sm"
                  >
                    {enrollmentLoading ? 'Processing...' : 'Unenroll'}
                  </button>
                  {enrollmentStatus.enrollment && (
                    <div className="text-sm text-muted-foreground text-center">
                      Progress: {enrollmentStatus.enrollment.progress_percentage}%
                    </div>
                  )}
                </div>
              ) : (
                <button 
                  onClick={handleEnrollment}
                  disabled={enrollmentLoading}
                  className="w-full btn-primary mb-4"
                >
                  {enrollmentLoading 
                    ? 'Processing...' 
                    : (course.is_free ? 'Enroll for Free' : 'Enroll Now')
                  }
                </button>
              )}

              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Lessons</span>
                  <span>{course.lessons.length}</span>
                </div>
                {course.estimated_duration && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Duration</span>
                    <span>{course.estimated_duration}</span>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Difficulty</span>
                  <span className="capitalize">{course.difficulty_level}</span>
                </div>
                {course.skill_level && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Skill Level</span>
                    <span>{course.skill_level.name}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Categories */}
            {course.categories.length > 0 && (
              <div className="bg-card border rounded-lg p-6">
                <h3 className="font-semibold mb-4">Categories</h3>
                <div className="flex flex-wrap gap-2">
                  {course.categories.map((category) => (
                    <span
                      key={category.slug}
                      className="px-3 py-1 text-sm text-white rounded-full"
                      style={{ backgroundColor: category.color }}
                    >
                      {category.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Tags */}
            {course.tags.length > 0 && (
              <div className="bg-card border rounded-lg p-6">
                <h3 className="font-semibold mb-4">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {course.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 text-sm bg-muted text-muted-foreground rounded-full"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Related Courses */}
            {course.related_courses.length > 0 && (
              <div className="bg-card border rounded-lg p-6">
                <h3 className="font-semibold mb-4">Related Courses</h3>
                <div className="space-y-4">
                  {course.related_courses.map((related) => (
                    <div key={related.id} className="border rounded-lg p-4">
                      {related.course_image && (
                        <img 
                          src={related.course_image} 
                          alt={related.title}
                          className="w-full h-24 object-cover rounded mb-3"
                        />
                      )}
                      <h4 className="font-medium mb-2">
                        <Link 
                          to={`/learning/courses/${related.slug}`}
                          className="hover:text-primary transition-colors"
                        >
                          {related.title}
                        </Link>
                      </h4>
                      <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                        {related.short_description}
                      </p>
                      <div className="text-sm text-muted-foreground capitalize">
                        {related.difficulty_level}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}