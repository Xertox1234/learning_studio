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
        <h1 className="text-3xl font-bold mb-4">Python Courses</h1>
        <p className="text-lg text-muted-foreground">
          Master Python programming with our comprehensive, AI-enhanced courses
        </p>
      </div>

      {/* Search and Filters */}
      <div className="mb-8 space-y-4">
        {/* Search Bar */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search courses..."
            defaultValue={currentSearch || ''}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-10 pr-4 py-2 w-full border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 items-center">
          {/* Skill Level Filter */}
          {skillLevels.length > 0 && (
            <select
              value={currentSkillLevel || ''}
              onChange={(e) => handleFilterChange('skill_level', e.target.value)}
              className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">All Skill Levels</option>
              {skillLevels.map((level) => (
                <option key={level.id} value={level.slug}>
                  {level.name}
                </option>
              ))}
            </select>
          )}

          {/* Difficulty Filter */}
          <select
            value={currentDifficulty || ''}
            onChange={(e) => handleFilterChange('difficulty', e.target.value)}
            className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">All Difficulties</option>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>

          {/* Price Filter */}
          <select
            value={currentIsFree || ''}
            onChange={(e) => handleFilterChange('is_free', e.target.value)}
            className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">All Courses</option>
            <option value="true">Free Only</option>
            <option value="false">Premium Only</option>
          </select>

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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {courses.map((course) => (
              <article key={course.id} className="bg-card rounded-lg border hover:shadow-lg transition-shadow">
                {/* Course Image */}
                {course.course_image && (
                  <div className="aspect-video bg-muted rounded-t-lg overflow-hidden">
                    <img 
                      src={course.course_image} 
                      alt={course.title}
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}

                <div className="p-6">
                  {/* Course Code and Featured Badge */}
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
                  <h2 className="text-xl font-semibold mb-3 hover:text-primary transition-colors">
                    <Link to={`/learning/courses/${course.slug}`}>
                      {course.title}
                    </Link>
                  </h2>

                  {/* Description */}
                  <p className="text-muted-foreground mb-4 line-clamp-3">
                    {course.short_description}
                  </p>

                  {/* Course Meta */}
                  <div className="flex items-center justify-between text-sm text-muted-foreground mb-4">
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
                  <div className="flex items-center justify-between">
                    <div className="text-lg font-semibold">
                      {course.is_free ? (
                        <span className="text-green-600">Free</span>
                      ) : (
                        <span className="text-primary">${course.price}</span>
                      )}
                    </div>
                    <Link
                      to={`/learning/courses/${course.slug}`}
                      className="btn-primary text-sm"
                    >
                      View Course
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
        <div className="text-center py-12">
          <BookOpen className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-muted-foreground mb-2">
            No courses found
          </h3>
          <p className="text-muted-foreground">
            Try adjusting your filters or search terms to find more courses.
          </p>
        </div>
      )}
    </div>
  )
}