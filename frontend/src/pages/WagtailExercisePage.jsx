import React, { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import FillInBlankExercise from '../components/code-editor/FillInBlankExercise'
import InteractiveCodeEditor from '../components/code-editor/InteractiveCodeEditor'
import RunButtonCodeEditor from '../components/code-editor/RunButtonCodeEditor'
import ConfettiCelebration from '../components/common/ConfettiCelebration'
import { 
  BookOpen, 
  Clock, 
  Trophy, 
  ChevronLeft, 
  ArrowRight, 
  CheckCircle, 
  XCircle,
  Code,
  Target,
  Lightbulb
} from 'lucide-react'

const WagtailExercisePage = () => {
  const { exerciseSlug } = useParams()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const { theme } = useTheme()
  
  const [exercise, setExercise] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [completed, setCompleted] = useState(false)
  const [showCelebration, setShowCelebration] = useState(false)
  const [submissionResults, setSubmissionResults] = useState(null)
  const [validationResults, setValidationResults] = useState(null)

  // Fetch exercise data
  useEffect(() => {
    const fetchExercise = async () => {
      try {
        setLoading(true)
        const baseUrl = process.env.NODE_ENV === 'development' 
          ? 'http://localhost:8000' 
          : ''
        
        const response = await fetch(`${baseUrl}/api/v1/wagtail/exercises/${exerciseSlug}/`)
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const data = await response.json()
        setExercise(data)
      } catch (err) {
        console.error('Failed to fetch exercise:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (exerciseSlug) {
      fetchExercise()
    }
  }, [exerciseSlug])

  // Handle exercise submission
  const handleExerciseSubmit = async (code, executionResult, answers = null) => {
    console.log('Exercise submitted:', { code, executionResult, answers })
    
    setSubmissionResults({
      code,
      executionResult,
      answers,
      success: !executionResult.error,
      message: executionResult.error ? 'Code execution failed' : 'Code executed successfully!'
    })
    
    // Check if all validation passed for completion
    if (validationResults && Object.values(validationResults).every(result => result === true)) {
      setCompleted(true)
      setShowCelebration(true)
      
      // Hide celebration after 4 seconds
      setTimeout(() => {
        setShowCelebration(false)
      }, 4000)
    }
  }

  // Handle validation results
  const handleValidation = (results, answers) => {
    console.log('Validation results:', results, answers)
    setValidationResults(results)
    
    // Check if all answers are correct
    const allCorrect = Object.values(results).every(result => result === true)
    if (allCorrect && !completed) {
      setCompleted(true)
      setShowCelebration(true)
      
      setTimeout(() => {
        setShowCelebration(false)
      }, 4000)
    }
  }

  // Render exercise based on type
  const renderExercise = () => {
    if (!exercise) return null

    switch (exercise.layout_type) {
      case 'fullscreen':
        return (
          <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
            {exercise.exercise_type === 'fill_blank' ? (
              <FillInBlankExercise
                exerciseData={exercise}
                onSubmit={handleExerciseSubmit}
                onValidate={handleValidation}
                className="h-screen"
              />
            ) : (
              <RunButtonCodeEditor
                initialCode={exercise.starter_code || '# Start coding here...'}
                language={exercise.programming_language}
                onSubmit={handleExerciseSubmit}
                height="100vh"
                showSubmitButton={true}
              />
            )}
          </div>
        )
      
      default:
        return (
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg overflow-hidden">
            {exercise.exercise_type === 'fill_blank' ? (
              <FillInBlankExercise
                exerciseData={exercise}
                onSubmit={handleExerciseSubmit}
                onValidate={handleValidation}
                className="min-h-[500px]"
              />
            ) : (
              <div className="p-6">
                <RunButtonCodeEditor
                  initialCode={exercise.starter_code || '# Start coding here...'}
                  language={exercise.programming_language}
                  onSubmit={handleExerciseSubmit}
                  height={exercise.code_editor_height || '400px'}
                  showSubmitButton={true}
                />
              </div>
            )}
          </div>
        )
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-96">
            <div className="flex flex-col items-center space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="text-slate-600 dark:text-slate-400">Loading exercise...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error || !exercise) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-2xl mx-auto text-center">
            <XCircle className="mx-auto h-16 w-16 text-red-500 mb-4" />
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
              Exercise Not Found
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mb-8">
              {error || "The exercise you are looking for does not exist or could not be loaded."}
            </p>
            <Link
              to="/exercises"
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              <ChevronLeft className="w-4 h-4 mr-2" />
              Back to Exercises
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // Fullscreen layout
  if (exercise.layout_type === 'fullscreen') {
    return (
      <div className="relative">
        {showCelebration && <ConfettiCelebration />}
        {renderExercise()}
      </div>
    )
  }

  // Standard layout with consistent design
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Confetti Celebration */}
        {showCelebration && <ConfettiCelebration />}
        
        {/* Breadcrumb Navigation */}
        <div className="flex items-center space-x-2 text-sm text-slate-600 dark:text-slate-400 mb-6">
          <Link to="/exercises" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
            Exercises
          </Link>
          {exercise.course && (
            <>
              <span>•</span>
              <Link 
                to={`/courses/${exercise.course.slug}`}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                {exercise.course.title}
              </Link>
            </>
          )}
          {exercise.lesson && (
            <>
              <span>•</span>
              <Link 
                to={`/courses/${exercise.course.slug}/lessons/${exercise.lesson.slug}`}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                {exercise.lesson.title}
              </Link>
            </>
          )}
          <span>•</span>
          <span className="text-slate-900 dark:text-white font-medium">{exercise.title}</span>
        </div>

        {/* Header Section */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-8 mb-8">
          <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <div className={`p-2 rounded-lg ${
                  exercise.difficulty === 'easy' ? 'bg-green-100 dark:bg-green-900/20' :
                  exercise.difficulty === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/20' :
                  'bg-red-100 dark:bg-red-900/20'
                }`}>
                  <Target className={`w-5 h-5 ${
                    exercise.difficulty === 'easy' ? 'text-green-600 dark:text-green-400' :
                    exercise.difficulty === 'medium' ? 'text-yellow-600 dark:text-yellow-400' :
                    'text-red-600 dark:text-red-400'
                  }`} />
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  exercise.difficulty === 'easy' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300' :
                  exercise.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300' :
                  'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300'
                }`}>
                  {exercise.difficulty.charAt(0).toUpperCase() + exercise.difficulty.slice(1)}
                </span>
                <span className="px-3 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300 rounded-full text-sm font-medium capitalize">
                  {exercise.exercise_type.replace('_', ' ')}
                </span>
              </div>
              
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
                {exercise.title}
              </h1>
              
              <div 
                className="text-slate-600 dark:text-slate-300 prose dark:prose-invert max-w-none"
                dangerouslySetInnerHTML={{ __html: exercise.description }}
              />
            </div>
            
            {/* Exercise Stats */}
            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-6 lg:w-80">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Trophy className="w-5 h-5 text-yellow-500" />
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Points</span>
                  </div>
                  <span className="text-lg font-bold text-slate-900 dark:text-white">{exercise.points}</span>
                </div>
                
                {exercise.time_limit && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Clock className="w-5 h-5 text-blue-500" />
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Time Limit</span>
                    </div>
                    <span className="text-lg font-bold text-slate-900 dark:text-white">{exercise.time_limit}m</span>
                  </div>
                )}
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Code className="w-5 h-5 text-purple-500" />
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Language</span>
                  </div>
                  <span className="text-lg font-bold text-slate-900 dark:text-white capitalize">
                    {exercise.programming_language}
                  </span>
                </div>

                {completed && (
                  <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-600">
                    <div className="flex items-center space-x-2 text-green-600 dark:text-green-400">
                      <CheckCircle className="w-5 h-5" />
                      <span className="font-medium">Completed!</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Exercise Content */}
        <div className={`${exercise.show_sidebar ? 'grid grid-cols-1 lg:grid-cols-3 gap-8' : ''}`}>
          {/* Main Exercise */}
          <div className={`${exercise.show_sidebar ? 'lg:col-span-2' : ''}`}>
            {renderExercise()}
          </div>

          {/* Sidebar */}
          {exercise.show_sidebar && (
            <div className="space-y-6">
              {/* Instructions */}
              {exercise.exercise_content && exercise.exercise_content.length > 0 && (
                <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center">
                    <BookOpen className="w-5 h-5 mr-2 text-blue-500" />
                    Instructions
                  </h3>
                  <div className="space-y-4">
                    {exercise.exercise_content.map((block, index) => (
                      <div key={index}>
                        {block.type === 'instruction' && (
                          <div 
                            className="text-slate-600 dark:text-slate-300 prose dark:prose-invert prose-sm max-w-none"
                            dangerouslySetInnerHTML={{ __html: block.value }}
                          />
                        )}
                        {block.type === 'code_example' && (
                          <div className="bg-slate-100 dark:bg-slate-700 rounded-lg p-4">
                            <h4 className="font-medium text-slate-900 dark:text-white mb-2">
                              {block.title}
                            </h4>
                            <pre className="text-sm text-slate-800 dark:text-slate-200 overflow-x-auto">
                              <code>{block.code}</code>
                            </pre>
                            {block.explanation && (
                              <div 
                                className="mt-2 text-sm text-slate-600 dark:text-slate-400"
                                dangerouslySetInnerHTML={{ __html: block.explanation }}
                              />
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Submission Results */}
              {submissionResults && (
                <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                    Results
                  </h3>
                  
                  <div className={`p-4 rounded-lg mb-4 ${
                    submissionResults.success
                      ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-200'
                      : 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-200'
                  }`}>
                    <div className="flex items-center space-x-2">
                      {submissionResults.success ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : (
                        <XCircle className="w-5 h-5" />
                      )}
                      <span className="font-medium">{submissionResults.message}</span>
                    </div>
                  </div>

                  {submissionResults.executionResult?.output && (
                    <div className="bg-slate-100 dark:bg-slate-700 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-slate-900 dark:text-white mb-2">
                        Output:
                      </h4>
                      <pre className="text-sm text-slate-800 dark:text-slate-200 whitespace-pre-wrap">
                        {submissionResults.executionResult.output}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {/* Hints */}
              {exercise.hints && exercise.hints.length > 0 && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-2xl shadow-lg p-6 border border-yellow-200 dark:border-yellow-800">
                  <h3 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-4 flex items-center">
                    <Lightbulb className="w-5 h-5 mr-2" />
                    Hints
                  </h3>
                  <div className="space-y-3">
                    {exercise.hints.map((hint, index) => (
                      <div key={index} className="text-sm text-yellow-700 dark:text-yellow-300">
                        <span className="font-medium">{index + 1}.</span>{' '}
                        <span dangerouslySetInnerHTML={{ __html: hint.hint_text }} />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="mt-8 flex justify-between items-center">
          <Link
            to="/exercises"
            className="inline-flex items-center px-6 py-3 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 border border-slate-200 dark:border-slate-600"
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Back to Exercises
          </Link>

          {exercise.lesson && (
            <Link
              to={`/courses/${exercise.course.slug}/lessons/${exercise.lesson.slug}`}
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg shadow-lg hover:shadow-xl hover:bg-blue-700 transition-all duration-200"
            >
              Continue Lesson
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}

export default WagtailExercisePage