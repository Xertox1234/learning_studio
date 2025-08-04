import React, { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { 
  Search, 
  Filter, 
  SortAsc, 
  Star, 
  Clock, 
  Users, 
  BookOpen,
  ChevronDown,
  X,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { apiRequest } from '../utils/api'
import ErrorBoundary from '../components/common/ErrorBoundary'

// Skeleton Loading Component
function CourseSkeleton() {
  return (
    <div className="card-modern p-6 animate-pulse">
      <div className="aspect-video bg-gray-200 dark:bg-gray-700 rounded-lg mb-4"></div>
      <div className="space-y-3">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
        <div className="flex justify-between items-center pt-2">
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
        </div>
      </div>
    </div>
  )
}

// Course Card Component
function CourseCard({ course }) {
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

  return (
    <Link 
      to={`/courses/${course.id}`}
      className="group block"
    >
      <div className="card-modern p-6 h-full transition-all duration-200 hover:shadow-lg hover:scale-[1.02] group-hover:border-blue-500/50">
        {/* Course Thumbnail */}
        <div className="aspect-video bg-gradient-to-br from-blue-50 to-blue-100 dark:from-gray-800 dark:to-gray-700 rounded-lg mb-4 overflow-hidden">
          {course.thumbnail ? (
            <img 
              src={course.thumbnail} 
              alt={course.title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <BookOpen className="w-12 h-12 text-blue-400 dark:text-blue-300" />
            </div>
          )}
          
          {/* Category Badge */}
          <div className="relative -mt-6 ml-4">
            <span 
              className="inline-block px-3 py-1 rounded-full text-xs font-medium text-white shadow-sm"
              style={{ backgroundColor: course.category.color }}
            >
              {course.category.name}
            </span>
          </div>
        </div>

        {/* Course Info */}
        <div className="space-y-3">
          {/* Title and Featured Badge */}
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-2">
              {course.title}
            </h3>
            {course.is_featured && (
              <span className="flex-shrink-0 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
                Featured
              </span>
            )}
          </div>

          {/* Description */}
          <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
            {course.short_description || course.description}
          </p>

          {/* Instructor */}
          {course.instructor && (
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center">
                <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                  {course.instructor.first_name?.[0] || course.instructor.username?.[0]?.toUpperCase() || '?'}
                </span>
              </div>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {course.instructor.first_name && course.instructor.last_name 
                  ? `${course.instructor.first_name} ${course.instructor.last_name}`
                  : course.instructor.username || 'Unknown Instructor'
                }
              </span>
            </div>
          )}

          {/* Rating and Reviews */}
          {course.total_reviews > 0 && course.average_rating && (
            <div className="flex items-center gap-2">
              <div className="flex">
                {renderStars(parseFloat(course.average_rating))}
              </div>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {parseFloat(course.average_rating).toFixed(1)} ({course.total_reviews} reviews)
              </span>
            </div>
          )}

          {/* Stats */}
          <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                <span>{formatDuration(course.estimated_duration)}</span>
              </div>
              <div className="flex items-center gap-1">
                <Users className="w-4 h-4" />
                <span>{course.enrollment_count}</span>
              </div>
            </div>
            
            {/* Difficulty Badge */}
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(course.difficulty_level)}`}>
              {course.difficulty_level}
            </span>
          </div>

          {/* Price */}
          <div className="flex items-center justify-between pt-2 border-t border-gray-200 dark:border-gray-700">
            <div className="text-lg font-bold">
              {course.is_free ? (
                <span className="text-green-600 dark:text-green-400">Free</span>
              ) : (
                <span className="text-gray-900 dark:text-gray-100">${course.price}</span>
              )}
            </div>
            
            {course.user_enrolled && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                Enrolled
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  )
}

// Search and Sort Component
function SearchAndSort({ searchTerm, setSearchTerm, sortBy, setSortBy }) {
  const sortOptions = [
    { value: 'featured', label: 'Featured First' },
    { value: 'newest', label: 'Newest' },
    { value: 'popular', label: 'Most Popular' },
    { value: 'rating', label: 'Highest Rated' },
    { value: 'price_low', label: 'Price: Low to High' },
    { value: 'price_high', label: 'Price: High to Low' },
  ]

  return (
    <div className="flex flex-col sm:flex-row gap-4 mb-6">
      {/* Search Bar */}
      <div className="flex-1 relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search courses..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        />
        {searchTerm && (
          <button
            onClick={() => setSearchTerm('')}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Sort Dropdown */}
      <div className="relative">
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="appearance-none bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 pr-8 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {sortOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
      </div>
    </div>
  )
}

// Filters Component
function CourseFilters({ 
  categories, 
  selectedCategory, 
  setSelectedCategory,
  selectedDifficulty,
  setSelectedDifficulty,
  selectedPrice,
  setSelectedPrice,
  showFeatured,
  setShowFeatured
}) {
  const [showFilters, setShowFilters] = useState(false)
  
  const difficulties = ['beginner', 'intermediate', 'advanced']
  const priceOptions = [
    { value: 'all', label: 'All Courses' },
    { value: 'free', label: 'Free Only' },
    { value: 'paid', label: 'Paid Only' }
  ]

  const activeFiltersCount = [
    selectedCategory !== 'all',
    selectedDifficulty !== 'all',
    selectedPrice !== 'all',
    showFeatured
  ].filter(Boolean).length

  return (
    <div className="mb-6">
      {/* Filter Toggle Button (Mobile) */}
      <button
        onClick={() => setShowFilters(!showFilters)}
        className="sm:hidden flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-gray-700 dark:text-gray-300 mb-4"
      >
        <Filter className="w-4 h-4" />
        Filters
        {activeFiltersCount > 0 && (
          <span className="bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {activeFiltersCount}
          </span>
        )}
      </button>

      {/* Filters */}
      <div className={`space-y-4 sm:space-y-0 sm:flex sm:items-center sm:gap-6 ${showFilters || 'hidden sm:flex'}`}>
        {/* Category Filter */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
            Category:
          </label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-1 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Categories</option>
            {categories.map(category => (
              <option key={category.id} value={category.slug}>
                {category.name} ({category.course_count})
              </option>
            ))}
          </select>
        </div>

        {/* Difficulty Filter */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
            Difficulty:
          </label>
          <select
            value={selectedDifficulty}
            onChange={(e) => setSelectedDifficulty(e.target.value)}
            className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-1 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Levels</option>
            {difficulties.map(level => (
              <option key={level} value={level}>
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Price Filter */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
            Price:
          </label>
          <select
            value={selectedPrice}
            onChange={(e) => setSelectedPrice(e.target.value)}
            className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-1 text-sm text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {priceOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Featured Toggle */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showFeatured}
            onChange={(e) => setShowFeatured(e.target.checked)}
            className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700 dark:text-gray-300">Featured only</span>
        </label>

        {/* Clear Filters */}
        {activeFiltersCount > 0 && (
          <button
            onClick={() => {
              setSelectedCategory('all')
              setSelectedDifficulty('all')
              setSelectedPrice('all')
              setShowFeatured(false)
            }}
            className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 underline"
          >
            Clear all
          </button>
        )}
      </div>
    </div>
  )
}

// Main Courses Page Component
export default function CoursesPage() {
  const [courses, setCourses] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Filter and search state
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedDifficulty, setSelectedDifficulty] = useState('all')
  const [selectedPrice, setSelectedPrice] = useState('all')
  const [showFeatured, setShowFeatured] = useState(false)
  const [sortBy, setSortBy] = useState('featured')

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)

        const [coursesResponse, categoriesResponse] = await Promise.all([
          apiRequest('/api/v1/courses/'),
          apiRequest('/api/v1/categories/')
        ])

        if (coursesResponse.ok && categoriesResponse.ok) {
          const coursesData = await coursesResponse.json()
          const categoriesData = await categoriesResponse.json()
          
          setCourses(coursesData.results || coursesData)
          setCategories(categoriesData.results || categoriesData)
        } else {
          throw new Error('Failed to fetch data')
        }
      } catch (err) {
        console.error('Error fetching courses:', err)
        setError('Failed to load courses. Please try again later.')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // Filter and sort courses
  const filteredAndSortedCourses = useMemo(() => {
    let filtered = courses.filter(course => {
      // Search filter
      if (searchTerm && !course.title.toLowerCase().includes(searchTerm.toLowerCase()) && 
          !course.description.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false
      }

      // Category filter
      if (selectedCategory !== 'all' && course.category.slug !== selectedCategory) {
        return false
      }

      // Difficulty filter
      if (selectedDifficulty !== 'all' && course.difficulty_level !== selectedDifficulty) {
        return false
      }

      // Price filter
      if (selectedPrice === 'free' && !course.is_free) {
        return false
      }
      if (selectedPrice === 'paid' && course.is_free) {
        return false
      }

      // Featured filter
      if (showFeatured && !course.is_featured) {
        return false
      }

      return true
    })

    // Sort courses
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'featured':
          if (a.is_featured !== b.is_featured) {
            return b.is_featured - a.is_featured
          }
          return new Date(b.created_at) - new Date(a.created_at)
        
        case 'newest':
          return new Date(b.created_at) - new Date(a.created_at)
        
        case 'popular':
          return b.enrollment_count - a.enrollment_count
        
        case 'rating':
          return parseFloat(b.average_rating) - parseFloat(a.average_rating)
        
        case 'price_low':
          if (a.is_free !== b.is_free) {
            return b.is_free - a.is_free // Free courses first
          }
          return parseFloat(a.price) - parseFloat(b.price)
        
        case 'price_high':
          if (a.is_free !== b.is_free) {
            return a.is_free - b.is_free // Paid courses first
          }
          return parseFloat(b.price) - parseFloat(a.price)
        
        default:
          return 0
      }
    })

    return filtered
  }, [courses, searchTerm, selectedCategory, selectedDifficulty, selectedPrice, showFeatured, sortBy])

  if (error) {
    return (
      <div className="container-custom py-8">
        <div className="max-w-md mx-auto text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Unable to Load Courses
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="container-custom py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl lg:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            Explore Courses
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Discover our comprehensive Python programming courses designed for all skill levels
          </p>
        </div>

        {/* Search and Sort */}
        <SearchAndSort
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          sortBy={sortBy}
          setSortBy={setSortBy}
        />

        {/* Filters */}
        <CourseFilters
          categories={categories}
          selectedCategory={selectedCategory}
          setSelectedCategory={setSelectedCategory}
          selectedDifficulty={selectedDifficulty}
          setSelectedDifficulty={setSelectedDifficulty}
          selectedPrice={selectedPrice}
          setSelectedPrice={setSelectedPrice}
          showFeatured={showFeatured}
          setShowFeatured={setShowFeatured}
        />

        {/* Results Count */}
        {!loading && (
          <div className="mb-6">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {filteredAndSortedCourses.length} course{filteredAndSortedCourses.length !== 1 ? 's' : ''} found
              {searchTerm && ` for "${searchTerm}"`}
            </p>
          </div>
        )}

        {/* Course Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, index) => (
              <CourseSkeleton key={index} />
            ))}
          </div>
        ) : filteredAndSortedCourses.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              No courses found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Try adjusting your search or filter criteria
            </p>
            <button
              onClick={() => {
                setSearchTerm('')
                setSelectedCategory('all')
                setSelectedDifficulty('all')
                setSelectedPrice('all')
                setShowFeatured(false)
              }}
              className="btn-secondary"
            >
              Clear all filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAndSortedCourses.map(course => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
}