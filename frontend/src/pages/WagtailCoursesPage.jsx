import React, { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { BookOpen, Clock, Users, Star, Filter, Search, ChevronLeft, ChevronRight, Award } from 'lucide-react'
import { api } from '../utils/api'
import clsx from 'clsx'

export default function WagtailCoursesPage() {
  const [courses, setCourses] = useState([])
  const [skillLevels, setSkillLevels] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pagination, setPagination] = useState({})
  const [searchParams, setSearchParams] = useSearchParams()

  const currentSkillLevel = searchParams.get('skill_level')
  const currentCategory = searchParams.get('category')
  const currentDifficulty = searchParams.get('difficulty')
  const currentIsFree = searchParams.get('is_free')
  const currentSearch = searchParams.get('search')
  const currentPage = parseInt(searchParams.get('page')) || 1

  useEffect(() => {
    fetchCourses()
  }, [searchParams])

  const fetchCourses = async () => {
    try {
      setLoading(true)
      
      // Fetch courses and learning data in parallel
      const [coursesResponse, learningResponse] = await Promise.all([
        api.get('/learning/courses/', {
          params: {
            skill_level: currentSkillLevel,
            category: currentCategory,
            difficulty: currentDifficulty,
            is_free: currentIsFree,
            search: currentSearch,
            page: currentPage,
            page_size: 12
          }
        }),
        api.get('/learning/')
      ])

      setCourses(coursesResponse.data.courses)
      setPagination(coursesResponse.data.pagination)
      setSkillLevels(learningResponse.data.skill_levels)
      setError(null)
    } catch (err) {
      console.error('Error fetching courses:', err)
      setError('Failed to load courses. Please try again later.')
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (filterType, value) => {
    const newParams = new URLSearchParams(searchParams)
    if (value) {
      newParams.set(filterType, value)
    } else {
      newParams.delete(filterType)
    }
    newParams.delete('page') // Reset to first page
    setSearchParams(newParams)
  }

  const handleSearch = (searchTerm) => {
    const newParams = new URLSearchParams(searchParams)
    if (searchTerm) {
      newParams.set('search', searchTerm)
    } else {
      newParams.delete('search')
    }
    newParams.delete('page') // Reset to first page
    setSearchParams(newParams)
  }

  const handlePageChange = (newPage) => {
    const newParams = new URLSearchParams(searchParams)
    newParams.set('page', newPage.toString())
    setSearchParams(newParams)
  }

  const clearFilters = () => {
    setSearchParams({})
  }

  if (loading) {
    return (
      <div className="container-custom py-8">
        <div className="animate-pulse">
          {/* Header skeleton */}
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-64 mb-2"></div>
          <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-96 mb-8"></div>
          
          {/* Search Bar skeleton */}
          <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded-full w-80 mb-8"></div>
          
          {/* Category filter skeleton */}
          <div className="flex gap-2 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-8 bg-gray-200 dark:bg-gray-700 rounded-full w-20"></div>
            ))}
          </div>
          
          {/* Featured course skeleton */}
          <div className="mb-12">
            <div className="h-7 bg-gray-200 dark:bg-gray-700 rounded w-40 mb-6"></div>
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="h-64 lg:h-80 bg-gray-200 dark:bg-gray-700"></div>
                <div className="p-8 flex flex-col justify-center">
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
          
          {/* Course cards skeleton */}
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
          <BookOpen className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-destructive mb-2">Error Loading Courses</h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <button
            onClick={fetchCourses}
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
        <h1 className="text-3xl font-bold mb-4 text-gray-900 dark:text-white">Python Learning Courses</h1>
        <p className="text-lg text-gray-600 dark:text-gray-300 mb-6">
          Master Python programming with our comprehensive, AI-enhanced courses designed by experts
        </p>
        
        
        {/* Search Bar */}
        <div className="max-w-2xl">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search courses..."
              defaultValue={currentSearch || ''}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full pl-12 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-full bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm"
            />
          </div>
        </div>
      </div>

      {/* Featured Course - Only show when no filters are active */}
      {!currentSkillLevel && !currentCategory && !currentDifficulty && !currentIsFree && !currentSearch && courses.length > 0 && courses.filter(course => course.featured).length > 0 && (
        <div className="mb-12">
          <h2 className="text-2xl font-bold mb-6">Featured Course</h2>
          <article className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-blue-900/20 dark:to-purple-900/20 border border-blue-200/50 dark:border-gray-700 hover:border-blue-300/50 dark:hover:border-gray-600 transition-all duration-300 hover:shadow-2xl">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Featured Image */}
              <div className="relative overflow-hidden">
                {courses.filter(course => course.featured)[0].course_image ? (
                  <img
                    src={courses.filter(course => course.featured)[0].course_image}
                    alt={courses.filter(course => course.featured)[0].title}
                    className="w-full h-64 lg:h-80 object-cover rounded-xl lg:rounded-l-none lg:rounded-r-xl transition-transform duration-300 group-hover:scale-105"
                  />
                ) : (
                  <div className="w-full h-64 lg:h-80 bg-gradient-to-br from-blue-400 to-purple-500 rounded-xl lg:rounded-l-none lg:rounded-r-xl flex items-center justify-center">
                    <BookOpen className="h-16 w-16 text-white/80" />
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent" />
              </div>

              {/* Content */}
              <div className="p-8 flex flex-col justify-center">
                {(() => {
                  const featuredCourse = courses.filter(course => course.featured)[0];
                  return (
                    <>
                      {/* Categories */}
                      {featuredCourse.categories.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-4">
                          {featuredCourse.categories.map((category) => (
                            <span
                              key={category.slug}
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
                        <Link to={`/courses/${featuredCourse.slug}`}>
                          {featuredCourse.title}
                        </Link>
                      </h3>

                      {/* Description */}
                      <p className="text-lg text-gray-600 dark:text-gray-300 mb-6 leading-relaxed">
                        {featuredCourse.short_description}
                      </p>

                      {/* Meta Info */}
                      <div className="flex flex-wrap items-center gap-6 text-sm text-gray-500 dark:text-gray-400 mb-6">
                        {featuredCourse.instructor && (
                          <div className="flex items-center space-x-2">
                            <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                              {featuredCourse.instructor.name ? featuredCourse.instructor.name.charAt(0).toUpperCase() : 'I'}
                            </div>
                            <span className="font-medium">{featuredCourse.instructor.name || 'Expert Instructor'}</span>
                          </div>
                        )}
                        <div className="flex items-center space-x-2">
                          <BookOpen className="h-4 w-4" />
                          <span>{featuredCourse.lesson_count} lessons</span>
                        </div>
                        {featuredCourse.estimated_duration && (
                          <div className="flex items-center space-x-2">
                            <Clock className="h-4 w-4" />
                            <span>{featuredCourse.estimated_duration}</span>
                          </div>
                        )}
                      </div>

                      {/* CTA */}
                      <Link
                        to={`/courses/${featuredCourse.slug}`}
                        className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-full hover:from-blue-700 hover:to-purple-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1 w-fit"
                      >
                        Start Learning
                        <ChevronRight className="ml-2 h-4 w-4" />
                      </Link>
                    </>
                  );
                })()}
              </div>
            </div>
          </article>
        </div>
      )}

      {/* Category Filter */}
      {skillLevels.length > 0 && (
        <div className="mb-8">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleFilterChange('skill_level', '')}
              className={clsx(
                'px-4 py-2 rounded-full text-sm font-medium transition-colors',
                !currentSkillLevel
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted hover:bg-muted/80'
              )}
            >
              All Skill Levels
            </button>
            {skillLevels.map((level) => (
              <button
                key={level.id}
                onClick={() => handleFilterChange('skill_level', level.slug)}
                className={clsx(
                  'px-4 py-2 rounded-full text-sm font-medium transition-colors',
                  currentSkillLevel === level.slug
                    ? 'text-white'
                    : 'bg-muted hover:bg-muted/80'
                )}
                style={{
                  backgroundColor: currentSkillLevel === level.slug ? level.color : undefined
                }}
              >
                {level.name}
              </button>
            ))}
            
            {/* Difficulty Filter */}
            <button
              onClick={() => handleFilterChange('difficulty', '')}
              className={clsx(
                'px-4 py-2 rounded-full text-sm font-medium transition-colors',
                !currentDifficulty
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted hover:bg-muted/80'
              )}
            >
              All Difficulty
            </button>
            {['beginner', 'intermediate', 'advanced'].map((diff) => (
              <button
                key={diff}
                onClick={() => handleFilterChange('difficulty', diff)}
                className={clsx(
                  'px-4 py-2 rounded-full text-sm font-medium transition-colors capitalize',
                  currentDifficulty === diff
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted hover:bg-muted/80'
                )}
              >
                {diff}
              </button>
            ))}
            
            {/* Price Filter */}
            <button
              onClick={() => handleFilterChange('is_free', 'true')}
              className={clsx(
                'px-4 py-2 rounded-full text-sm font-medium transition-colors',
                currentIsFree === 'true'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted hover:bg-muted/80'
              )}
            >
              Free Only
            </button>
            <button
              onClick={() => handleFilterChange('is_free', 'false')}
              className={clsx(
                'px-4 py-2 rounded-full text-sm font-medium transition-colors',
                currentIsFree === 'false'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted hover:bg-muted/80'
              )}
            >
              Premium Only
            </button>
            
            {/* Clear Filters */}
            {(currentSkillLevel || currentCategory || currentDifficulty || currentIsFree || currentSearch) && (
              <button
                onClick={clearFilters}
                className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>
      )}

      {/* Results Count */}
      {pagination.total_count !== undefined && (
        <div className="mb-6">
          <p className="text-sm text-muted-foreground">
            {pagination.total_count === 0 
              ? 'No courses found'
              : `Showing ${pagination.total_count} course${pagination.total_count === 1 ? '' : 's'}`
            }
          </p>
        </div>
      )}

      {/* Courses Grid */}
      {courses.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-8">
            {courses.map((course) => (
              <article key={course.id} className="group relative overflow-hidden bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 transition-all duration-300 hover:shadow-2xl hover:-translate-y-1">
                
                {/* Course Image */}
                <div className="relative overflow-hidden">
                  {course.course_image ? (
                    <img 
                      src={course.course_image} 
                      alt={course.title}
                      className="w-full h-48 object-cover transition-transform duration-500 group-hover:scale-110"
                    />
                  ) : (
                    <div className="w-full h-48 bg-gradient-to-br from-indigo-400 via-blue-500 to-purple-600 flex items-center justify-center relative overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-br from-blue-400/20 via-transparent to-purple-600/20"></div>
                      <BookOpen className="h-16 w-16 text-white/80 relative z-10" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  
                  {/* Course Code Badge */}
                  <div className="absolute top-4 left-4">
                    <span className="px-3 py-1 text-xs font-bold text-white rounded-full shadow-lg backdrop-blur-sm"
                          style={{ backgroundColor: course.skill_level?.color || '#3b82f6' }}>
                      {course.course_code}
                    </span>
                  </div>
                  
                  {/* Featured Badge */}
                  {course.featured && (
                    <div className="absolute top-4 right-4">
                      <Star className="h-4 w-4 text-yellow-500 fill-current" />
                    </div>
                  )}
                </div>

                <div className="p-6">
                  {/* Course Code and Featured Badge Row */}
                  <div className="flex items-center justify-between mb-3">
                    <span className="px-2 py-1 text-xs font-medium bg-primary/10 text-primary rounded">
                      {course.course_code}
                    </span>
                    {course.featured && (
                      <Star className="h-4 w-4 text-yellow-500 fill-current" />
                    )}
                  </div>

                  {/* Skill Level */}
                  {course.skill_level && (
                    <div className="mb-3">
                      <span 
                        className="px-2 py-1 text-xs font-medium text-white rounded"
                        style={{ backgroundColor: course.skill_level.color }}
                      >
                        {course.skill_level.name}
                      </span>
                    </div>
                  )}

                  {/* Title */}
                  <h2 className="text-xl font-bold mb-3 text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-2">
                    <Link to={`/courses/${course.slug}`}>
                      {course.title}
                    </Link>
                  </h2>

                  {/* Description */}
                  <p className="text-gray-600 dark:text-gray-300 mb-4 line-clamp-3 leading-relaxed">
                    {course.short_description}
                  </p>

                  {/* Course Meta */}
                  <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-4">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-1">
                        <BookOpen className="h-4 w-4" />
                        <span>{course.lesson_count} lessons</span>
                      </div>
                      {course.estimated_duration && (
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4" />
                          <span>{course.estimated_duration}</span>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center space-x-1">
                      <Award className="h-4 w-4" />
                      <span className="capitalize">{course.difficulty_level}</span>
                    </div>
                  </div>

                  {/* Price and CTA */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="text-lg font-semibold">
                      {course.is_free ? (
                        <span className="text-green-600">Free</span>
                      ) : (
                        <span className="text-primary">${course.price}</span>
                      )}
                    </div>
                    <Link
                      to={`/courses/${course.slug}`}
                      className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 text-sm font-semibold transition-colors flex items-center space-x-1 group/link"
                    >
                      <span>View Course</span>
                      <ChevronRight className="h-3 w-3 transition-transform group-hover/link:translate-x-1" />
                    </Link>
                  </div>

                  {/* Categories */}
                  {course.categories.length > 0 && (
                    <div className="mt-4 pt-4 border-t">
                      <div className="flex flex-wrap gap-2">
                        {course.categories.slice(0, 2).map((category) => (
                          <span
                            key={category.slug}
                            className="px-2 py-1 text-xs text-white rounded"
                            style={{ backgroundColor: category.color }}
                          >
                            {category.name}
                          </span>
                        ))}
                        {course.categories.length > 2 && (
                          <span className="px-2 py-1 text-xs bg-muted text-muted-foreground rounded">
                            +{course.categories.length - 2} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
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
        <div className="text-center py-16">
          <div className="max-w-md mx-auto">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900/20 dark:to-purple-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <BookOpen className="h-12 w-12 text-blue-500 dark:text-blue-400" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
              No courses found
            </h3>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Try adjusting your filters or search terms to find more courses.
            </p>
            <button
              onClick={clearFilters}
              className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-semibold underline"
            >
              Clear all filters
            </button>
          </div>
        </div>
      )}
    </div>
  )
}