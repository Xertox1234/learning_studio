import React, { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { 
  Search, 
  Filter, 
  BookOpen, 
  Clock, 
  Trophy, 
  Target,
  Code,
  ChevronRight,
  ChevronDown,
  Users,
  Calendar,
  CheckCircle
} from 'lucide-react'

const WagtailExerciseListPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const { isAuthenticated } = useAuth()
  
  const [exercises, setExercises] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pagination, setPagination] = useState({})
  
  // Filter states
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '')
  const [selectedDifficulty, setSelectedDifficulty] = useState(searchParams.get('difficulty') || '')
  const [selectedType, setSelectedType] = useState(searchParams.get('type') || '')
  const [selectedLanguage, setSelectedLanguage] = useState(searchParams.get('language') || '')
  const [showFilters, setShowFilters] = useState(false)

  // Fetch exercises
  const fetchExercises = async (params = {}) => {
    try {
      setLoading(true)
      setError(null)
      
      const baseUrl = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000' 
        : ''
      
      const queryParams = new URLSearchParams({
        page: params.page || searchParams.get('page') || '1',
        page_size: '12',
        ...(params.search && { search: params.search }),
        ...(params.difficulty && { difficulty: params.difficulty }),
        ...(params.type && { type: params.type }),
        ...(params.language && { language: params.language })
      })

      const response = await fetch(`${baseUrl}/api/v1/wagtail/exercises/?${queryParams}`)
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      setExercises(data.exercises || [])
      setPagination(data.pagination || {})
    } catch (err) {
      console.error('Failed to fetch exercises:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Initial load and search param changes
  useEffect(() => {
    fetchExercises()
  }, [searchParams])

  // Handle search
  const handleSearch = (e) => {
    e.preventDefault()
    updateSearchParams({ search: searchQuery, page: 1 })
  }

  // Update URL search parameters
  const updateSearchParams = (newParams) => {
    const params = new URLSearchParams(searchParams)
    
    Object.entries(newParams).forEach(([key, value]) => {
      if (value) {
        params.set(key, value)
      } else {
        params.delete(key)
      }
    })
    
    setSearchParams(params)
  }

  // Handle filter changes
  const handleFilterChange = (filterType, value) => {
    switch (filterType) {
      case 'difficulty':
        setSelectedDifficulty(value)
        updateSearchParams({ difficulty: value, page: 1 })
        break
      case 'type':
        setSelectedType(value)
        updateSearchParams({ type: value, page: 1 })
        break
      case 'language':
        setSelectedLanguage(value)
        updateSearchParams({ language: value, page: 1 })
        break
    }
  }

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery('')
    setSelectedDifficulty('')
    setSelectedType('')
    setSelectedLanguage('')
    setSearchParams({})
  }

  // Handle pagination
  const handlePageChange = (page) => {
    updateSearchParams({ page })
  }

  // Render exercise card
  const renderExerciseCard = (exercise) => (
    <Link
      key={exercise.id}
      to={`/exercises/${exercise.slug}`}
      className="group bg-white dark:bg-slate-800 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-200 overflow-hidden border border-slate-200 dark:border-slate-700"
    >
      <div className="p-6">
        {/* Exercise Type & Difficulty Badges */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300 rounded-full text-sm font-medium capitalize">
              {exercise.exercise_type.replace('_', ' ')}
            </span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              exercise.difficulty === 'easy' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300' :
              exercise.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300' :
              'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300'
            }`}>
              {exercise.difficulty.charAt(0).toUpperCase() + exercise.difficulty.slice(1)}
            </span>
          </div>
          
          <div className={`p-2 rounded-lg ${
            exercise.difficulty === 'easy' ? 'bg-green-100 dark:bg-green-900/20' :
            exercise.difficulty === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/20' :
            'bg-red-100 dark:bg-red-900/20'
          }`}>
            <Target className={`w-4 h-4 ${
              exercise.difficulty === 'easy' ? 'text-green-600 dark:text-green-400' :
              exercise.difficulty === 'medium' ? 'text-yellow-600 dark:text-yellow-400' :
              'text-red-600 dark:text-red-400'
            }`} />
          </div>
        </div>

        {/* Title */}
        <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-3 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
          {exercise.title}
        </h3>

        {/* Description */}
        <p className="text-slate-600 dark:text-slate-300 mb-4 line-clamp-2">
          {exercise.description.replace(/<[^>]*>/g, '').substring(0, 150)}...
        </p>

        {/* Exercise Stats */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <Trophy className="w-4 h-4 text-yellow-500" />
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-white">
              {exercise.points}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">points</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <Code className="w-4 h-4 text-purple-500" />
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-white capitalize">
              {exercise.programming_language}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">language</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <Clock className="w-4 h-4 text-blue-500" />
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-white">
              {exercise.time_limit || '∞'}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">
              {exercise.time_limit ? 'minutes' : 'unlimited'}
            </div>
          </div>
        </div>

        {/* Context Information */}
        {(exercise.lesson_title || exercise.course_title) && (
          <div className="border-t border-slate-200 dark:border-slate-600 pt-3 mt-4">
            <div className="flex items-center text-sm text-slate-500 dark:text-slate-400">
              <BookOpen className="w-3 h-3 mr-1" />
              {exercise.course_title && (
                <span>{exercise.course_title}</span>
              )}
              {exercise.lesson_title && exercise.course_title && <span className="mx-1">•</span>}
              {exercise.lesson_title && (
                <span>{exercise.lesson_title}</span>
              )}
            </div>
          </div>
        )}

        {/* Special indicators */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center space-x-2">
            {exercise.has_template && (
              <span className="inline-flex items-center px-2 py-1 bg-purple-100 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 text-xs rounded-full">
                Fill-in-blank
              </span>
            )}
            {exercise.has_hints && (
              <span className="inline-flex items-center px-2 py-1 bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300 text-xs rounded-full">
                Hints available
              </span>
            )}
          </div>
          
          <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-blue-500 group-hover:translate-x-1 transition-all duration-200" />
        </div>
      </div>
    </Link>
  )

  // Render step-based exercise card
  const renderStepExerciseCard = (exercise) => (
    <Link
      key={exercise.id}
      to={`/step-exercises/${exercise.slug}`}
      className="group bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-200 overflow-hidden border border-indigo-200 dark:border-indigo-700/50"
    >
      <div className="p-6">
        {/* Step-based indicator */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-indigo-100 text-indigo-800 dark:bg-indigo-900/20 dark:text-indigo-300 rounded-full text-sm font-medium">
              Multi-step
            </span>
            <span className="px-3 py-1 bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300 rounded-full text-sm font-medium">
              {exercise.step_count} steps
            </span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              exercise.difficulty === 'easy' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300' :
              exercise.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300' :
              'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300'
            }`}>
              {exercise.difficulty.charAt(0).toUpperCase() + exercise.difficulty.slice(1)}
            </span>
          </div>
          
          <Users className="w-5 h-5 text-indigo-500" />
        </div>

        {/* Title */}
        <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-3 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
          {exercise.title}
        </h3>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <Trophy className="w-4 h-4 text-yellow-500" />
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-white">
              {exercise.points}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">total points</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <Clock className="w-4 h-4 text-blue-500" />
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-white">
              {exercise.estimated_time}m
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400">estimated</div>
          </div>
        </div>

        {/* Progressive indicator */}
        {exercise.require_sequential && (
          <div className="flex items-center text-sm text-indigo-600 dark:text-indigo-400 mb-4">
            <CheckCircle className="w-4 h-4 mr-2" />
            <span>Sequential completion required</span>
          </div>
        )}

        {/* Context Information */}
        {(exercise.lesson_title || exercise.course_title) && (
          <div className="border-t border-indigo-200 dark:border-indigo-600 pt-3 mt-4">
            <div className="flex items-center text-sm text-slate-500 dark:text-slate-400">
              <BookOpen className="w-3 h-3 mr-1" />
              {exercise.course_title && (
                <span>{exercise.course_title}</span>
              )}
              {exercise.lesson_title && exercise.course_title && <span className="mx-1">•</span>}
              {exercise.lesson_title && (
                <span>{exercise.lesson_title}</span>
              )}
            </div>
          </div>
        )}

        <div className="flex items-center justify-end mt-4">
          <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-indigo-500 group-hover:translate-x-1 transition-all duration-200" />
        </div>
      </div>
    </Link>
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 dark:text-white mb-4">
            Interactive Exercises
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
            Practice your programming skills with hands-on exercises, step-by-step tutorials, and instant feedback
          </p>
        </div>

        {/* Search and Filters */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center gap-4">
            {/* Search Bar */}
            <form onSubmit={handleSearch} className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search exercises..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                />
              </div>
            </form>

            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="inline-flex items-center px-4 py-3 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            >
              <Filter className="w-5 h-5 mr-2" />
              Filters
              <ChevronDown className={`w-4 h-4 ml-2 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
            </button>
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-600">
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Difficulty
                  </label>
                  <select
                    value={selectedDifficulty}
                    onChange={(e) => handleFilterChange('difficulty', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All levels</option>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Exercise Type
                  </label>
                  <select
                    value={selectedType}
                    onChange={(e) => handleFilterChange('type', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All types</option>
                    <option value="coding">Coding Exercise</option>
                    <option value="fill_blank">Fill in the Blanks</option>
                    <option value="multiple_choice">Multiple Choice</option>
                    <option value="project">Project Exercise</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Language
                  </label>
                  <select
                    value={selectedLanguage}
                    onChange={(e) => handleFilterChange('language', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All languages</option>
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="html">HTML</option>
                    <option value="css">CSS</option>
                    <option value="sql">SQL</option>
                  </select>
                </div>

                <div className="flex items-end">
                  <button
                    onClick={clearFilters}
                    className="w-full px-4 py-2 bg-slate-200 dark:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-500 transition-colors"
                  >
                    Clear Filters
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-flex items-center space-x-2">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="text-slate-600 dark:text-slate-400">Loading exercises...</span>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="text-center py-12">
            <div className="bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-2xl p-8 max-w-md mx-auto">
              <h3 className="text-lg font-semibold text-red-800 dark:text-red-300 mb-2">
                Failed to load exercises
              </h3>
              <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
              <button
                onClick={() => fetchExercises()}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Exercises Grid */}
        {!loading && !error && (
          <>
            {exercises.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {exercises.map((exercise) => (
                  exercise.type === 'step_based' 
                    ? renderStepExerciseCard(exercise)
                    : renderExerciseCard(exercise)
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <BookOpen className="mx-auto h-16 w-16 text-slate-400 mb-4" />
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                  No exercises found
                </h3>
                <p className="text-slate-600 dark:text-slate-400 mb-4">
                  Try adjusting your search terms or filters
                </p>
                <button
                  onClick={clearFilters}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Clear all filters
                </button>
              </div>
            )}

            {/* Pagination */}
            {pagination.total_pages > 1 && (
              <div className="mt-12 flex justify-center">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handlePageChange(pagination.current_page - 1)}
                    disabled={!pagination.has_previous}
                    className="px-4 py-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  
                  {[...Array(pagination.total_pages)].map((_, i) => (
                    <button
                      key={i + 1}
                      onClick={() => handlePageChange(i + 1)}
                      className={`px-4 py-2 rounded-lg ${
                        pagination.current_page === i + 1
                          ? 'bg-blue-600 text-white'
                          : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
                      }`}
                    >
                      {i + 1}
                    </button>
                  ))}
                  
                  <button
                    onClick={() => handlePageChange(pagination.current_page + 1)}
                    disabled={!pagination.has_next}
                    className="px-4 py-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default WagtailExerciseListPage