import React, { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { sanitizeHTML } from '../utils/sanitize'
import FillInBlankExercise from '../components/code-editor/FillInBlankExercise'
import RunButtonCodeEditor from '../components/code-editor/RunButtonCodeEditor'
import MultipleChoiceQuiz from '../components/code-editor/MultipleChoiceQuiz'
import ConfettiCelebration from '../components/common/ConfettiCelebration'
import {
  BookOpen,
  Clock,
  Trophy,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  XCircle,
  Code,
  Target,
  Lightbulb,
  Lock,
  Unlock,
  StepForward,
  Award
} from 'lucide-react'

const StepBasedExercisePage = () => {
  const { exerciseSlug } = useParams()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const { theme } = useTheme()
  
  const [exercise, setExercise] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [stepCompletion, setStepCompletion] = useState({})
  const [showCelebration, setShowCelebration] = useState(false)
  const [stepResults, setStepResults] = useState({})
  const [totalPoints, setTotalPoints] = useState(0)

  // Fetch exercise data
  useEffect(() => {
    const fetchExercise = async () => {
      try {
        setLoading(true)
        const baseUrl = process.env.NODE_ENV === 'development' 
          ? 'http://localhost:8000' 
          : ''
        
        const response = await fetch(`${baseUrl}/api/v1/wagtail/step-exercises/${exerciseSlug}/`)
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const data = await response.json()
        setExercise(data)
        
        // Initialize step completion status
        const initialCompletion = {}
        data.steps.forEach((step, index) => {
          initialCompletion[index] = false
        })
        setStepCompletion(initialCompletion)
      } catch (err) {
        console.error('Failed to fetch step-based exercise:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (exerciseSlug) {
      fetchExercise()
    }
  }, [exerciseSlug])

  // Handle step submission
  const handleStepSubmit = (stepIndex, code, executionResult, answers = null) => {
    const step = exercise.steps[stepIndex]
    const success = !executionResult.error
    
    // Update step results
    setStepResults(prev => ({
      ...prev,
      [stepIndex]: {
        code,
        executionResult,
        answers,
        success,
        points: success ? step.points : 0
      }
    }))
    
    // Mark step as completed if successful
    if (success) {
      setStepCompletion(prev => ({
        ...prev,
        [stepIndex]: true
      }))
      
      // Add points to total
      setTotalPoints(prev => prev + step.points)
      
      // Check if all steps are completed
      const allCompleted = Object.keys(stepCompletion).every(
        key => key == stepIndex || stepCompletion[key]
      )
      
      if (allCompleted && stepIndex === exercise.steps.length - 1) {
        // Show celebration for completing all steps
        setShowCelebration(true)
        setTimeout(() => {
          setShowCelebration(false)
        }, 4000)
      }
    }
  }

  // Handle step validation (for fill-in-blank)
  const handleStepValidation = (stepIndex, results, answers) => {
    console.log('handleStepValidation called:', { stepIndex, results, answers })
    const allCorrect = Object.values(results).every(result => result === true)
    console.log('All correct in step?', allCorrect)

    if (allCorrect) {
      const step = exercise.steps[stepIndex]
      console.log('Marking step', stepIndex, 'as completed')

      // Mark step as completed
      setStepCompletion(prev => {
        const updated = {
          ...prev,
          [stepIndex]: true
        }
        console.log('Updated stepCompletion:', updated)
        return updated
      })

      // Add points to total
      setTotalPoints(prev => prev + step.points)
      
      // Auto-advance to next step if not the last one
      if (stepIndex < exercise.steps.length - 1 && exercise.require_sequential) {
        setTimeout(() => {
          setCurrentStep(stepIndex + 1)
        }, 1500)
      }
      
      // Check if all steps are completed
      const allCompleted = Object.keys(stepCompletion).every(
        key => key == stepIndex || stepCompletion[key]
      )
      
      if (allCompleted && stepIndex === exercise.steps.length - 1) {
        setShowCelebration(true)
        setTimeout(() => {
          setShowCelebration(false)
        }, 4000)
      }
    }
  }

  // Navigate to specific step
  const goToStep = (stepIndex) => {
    // Check if step is accessible
    if (exercise.require_sequential) {
      // Can only access completed steps or the next uncompleted step
      const canAccess = stepIndex === 0 || 
                       stepCompletion[stepIndex - 1] || 
                       stepCompletion[stepIndex]
      
      if (canAccess) {
        setCurrentStep(stepIndex)
      }
    } else {
      // All steps are accessible
      setCurrentStep(stepIndex)
    }
  }

  // Handle quiz submission
  const handleQuizSubmit = (stepIndex, quizResult) => {
    const { score, correctCount, totalQuestions, results } = quizResult

    // Mark step as completed if score is >= 60%
    if (score >= 60) {
      const step = exercise.steps[stepIndex]

      setStepCompletion(prev => ({
        ...prev,
        [stepIndex]: true
      }))

      // Add points proportional to score
      const earnedPoints = Math.round((step.points * score) / 100)
      setTotalPoints(prev => prev + earnedPoints)

      // Store quiz results
      setStepResults(prev => ({
        ...prev,
        [stepIndex]: quizResult
      }))

      // Check if all steps are completed
      const allCompleted = Object.keys(stepCompletion).every(
        key => key == stepIndex || stepCompletion[key]
      )

      if (allCompleted && stepIndex === exercise.steps.length - 1) {
        setShowCelebration(true)
        setTimeout(() => {
          setShowCelebration(false)
        }, 4000)
      }
    }
  }

  // Render step content
  const renderStepContent = (step, stepIndex) => {
    // Parse progressive hints if they exist
    let progressiveHints = []
    if (step.progressive_hints) {
      try {
        progressiveHints = typeof step.progressive_hints === 'string'
          ? JSON.parse(step.progressive_hints)
          : step.progressive_hints
      } catch (e) {
        console.error('Failed to parse progressive hints:', e)
        progressiveHints = []
      }
    }

    const stepData = {
      ...step,
      exercise_type: step.exercise_type,
      template_code: step.template,
      template: step.template,
      solutions: step.solutions || {},
      progressiveHints: progressiveHints,
      programming_language: 'python'
    }

    switch (step.exercise_type) {
      case 'fill_blank':
        return (
          <FillInBlankExercise
            exerciseData={stepData}
            onSubmit={(code, executionResult, answers) =>
              handleStepSubmit(stepIndex, code, executionResult, answers)
            }
            onValidate={(results, answers) =>
              handleStepValidation(stepIndex, results, answers)
            }
            className="min-h-[400px]"
          />
        )

      case 'quiz':
      case 'multiple_choice':
        // Parse quiz data from solutions field
        let quizData = {}
        try {
          quizData = typeof step.solutions === 'string'
            ? JSON.parse(step.solutions)
            : step.solutions
        } catch (e) {
          console.error('Failed to parse quiz data:', e)
          quizData = { questions: [] }
        }

        return (
          <MultipleChoiceQuiz
            quizData={{
              ...quizData,
              title: step.title,
              description: step.description
            }}
            onSubmit={(quizResult) => handleQuizSubmit(stepIndex, quizResult)}
            className="min-h-[400px]"
          />
        )

      case 'code':
      default:
        // Check if this is an informational step (no code) or actual code exercise
        const hasCode = step.template && step.template.trim().length > 0

        return (
          <div className="p-6">
            {/* Description */}
            <div className="mb-4">
              <div className="prose dark:prose-invert max-w-none"
                   dangerouslySetInnerHTML={{ __html: sanitizeHTML(step.description, { mode: 'rich' }) }} />
            </div>

            {/* Code Editor (only if there's actual code) */}
            {hasCode && (
              <div>
                <RunButtonCodeEditor
                  code={step.template}
                  language="python"
                  mockOutput=""
                  aiExplanation={step.hint || ''}
                  className="min-h-[300px]"
                />

                {/* Mark as complete button for demo/educational code steps */}
                {!stepCompletion[currentStep] && (
                  <div className="mt-4 flex justify-end">
                    <button
                      onClick={() => {
                        setStepCompletion(prev => ({ ...prev, [currentStep]: true }))
                      }}
                      className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    >
                      ✓ I understand, continue
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Hint (show below code or description) */}
            {step.hint && (
              <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                <div className="flex items-start space-x-2">
                  <Lightbulb className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-1" />
                  <p className="text-sm text-yellow-700 dark:text-yellow-300">{step.hint}</p>
                </div>
              </div>
            )}

            {/* Next button for informational steps */}
            {!hasCode && (
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => {
                    // Mark step as complete and move to next
                    setStepCompletion(prev => ({ ...prev, [currentStep]: true }))
                    if (currentStep < exercise.steps.length - 1) {
                      setCurrentStep(currentStep + 1)
                    }
                  }}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Continue →
                </button>
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

  const currentStepData = exercise.steps[currentStep]
  const isLastStep = currentStep === exercise.steps.length - 1
  const isFirstStep = currentStep === 0
  const canNavigateNext = !exercise.require_sequential || stepCompletion[currentStep]
  const allStepsCompleted = Object.values(stepCompletion).every(completed => completed)

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
          <span>•</span>
          <span className="text-slate-900 dark:text-white font-medium">{exercise.title}</span>
        </div>

        {/* Header Section */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-8 mb-8">
          <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/20">
                  <StepForward className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                </div>
                <span className="px-3 py-1 bg-indigo-100 text-indigo-800 dark:bg-indigo-900/20 dark:text-indigo-300 rounded-full text-sm font-medium">
                  Multi-Step Exercise
                </span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  exercise.difficulty === 'easy' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300' :
                  exercise.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300' :
                  'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300'
                }`}>
                  {exercise.difficulty.charAt(0).toUpperCase() + exercise.difficulty.slice(1)}
                </span>
              </div>
              
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
                {exercise.title}
              </h1>
              
              {/* Progress Bar */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    Step {currentStep + 1} of {exercise.steps.length}
                  </span>
                  <span className="text-sm font-medium text-slate-900 dark:text-white">
                    {totalPoints} / {exercise.total_points} points
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-indigo-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${((currentStep + 1) / exercise.steps.length) * 100}%` }}
                  />
                </div>
              </div>
            </div>
            
            {/* Exercise Stats */}
            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-6 lg:w-80">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Trophy className="w-5 h-5 text-yellow-500" />
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Total Points</span>
                  </div>
                  <span className="text-lg font-bold text-slate-900 dark:text-white">{exercise.total_points}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-5 h-5 text-blue-500" />
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Est. Time</span>
                  </div>
                  <span className="text-lg font-bold text-slate-900 dark:text-white">{exercise.estimated_time}m</span>
                </div>
                
                {exercise.require_sequential && (
                  <div className="flex items-center space-x-2 text-indigo-600 dark:text-indigo-400">
                    <Lock className="w-4 h-4" />
                    <span className="text-sm font-medium">Sequential completion required</span>
                  </div>
                )}
                
                {allStepsCompleted && (
                  <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-600">
                    <div className="flex items-center space-x-2 text-green-600 dark:text-green-400">
                      <Award className="w-5 h-5" />
                      <span className="font-medium">All Steps Completed!</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Step Navigation Tabs */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-4 mb-8">
          <div className="flex space-x-2 overflow-x-auto">
            {exercise.steps.map((step, index) => {
              const isCompleted = stepCompletion[index]
              const isCurrent = index === currentStep
              const isLocked = exercise.require_sequential && 
                           index > 0 && 
                           !stepCompletion[index - 1] && 
                           !isCompleted
              
              return (
                <button
                  key={index}
                  onClick={() => goToStep(index)}
                  disabled={isLocked}
                  className={`
                    flex items-center px-4 py-2 rounded-lg font-medium transition-all
                    ${isCurrent 
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : isCompleted
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-900/30'
                        : isLocked
                          ? 'bg-slate-100 text-slate-400 dark:bg-slate-700 dark:text-slate-500 cursor-not-allowed'
                          : 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
                    }
                  `}
                >
                  {isCompleted ? (
                    <CheckCircle className="w-4 h-4 mr-2" />
                  ) : isLocked ? (
                    <Lock className="w-4 h-4 mr-2" />
                  ) : (
                    <Unlock className="w-4 h-4 mr-2" />
                  )}
                  Step {index + 1}
                </button>
              )
            })}
          </div>
        </div>

        {/* Current Step Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg overflow-hidden">
              <div className="p-6 border-b border-slate-200 dark:border-slate-700">
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white flex items-center">
                  <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 mr-3">
                    {currentStep + 1}
                  </span>
                  {currentStepData.title}
                </h2>
                {currentStepData.points && (
                  <div className="mt-2 flex items-center text-sm text-slate-600 dark:text-slate-400">
                    <Trophy className="w-4 h-4 mr-1 text-yellow-500" />
                    {currentStepData.points} points
                  </div>
                )}
              </div>
              
              {renderStepContent(currentStepData, currentStep)}
              
              {/* Success Message */}
              {stepCompletion[currentStep] && (
                <div className="p-6 bg-green-50 dark:bg-green-900/20 border-t border-green-200 dark:border-green-800">
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                    <div>
                      <p className="font-medium text-green-800 dark:text-green-200">
                        {currentStepData.success_message || "Great job! You've completed this step."}
                      </p>
                      <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                        You earned {currentStepData.points} points!
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Navigation Buttons */}
            <div className="mt-6 flex justify-between">
              <button
                onClick={() => goToStep(currentStep - 1)}
                disabled={isFirstStep}
                className={`
                  inline-flex items-center px-6 py-3 font-medium rounded-lg transition-all
                  ${isFirstStep
                    ? 'bg-slate-200 text-slate-400 dark:bg-slate-700 dark:text-slate-500 cursor-not-allowed'
                    : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 shadow-lg hover:shadow-xl border border-slate-200 dark:border-slate-600'
                  }
                `}
              >
                <ChevronLeft className="w-4 h-4 mr-2" />
                Previous Step
              </button>

              {!isLastStep ? (
                <button
                  onClick={() => goToStep(currentStep + 1)}
                  disabled={!canNavigateNext}
                  className={`
                    inline-flex items-center px-6 py-3 font-medium rounded-lg transition-all
                    ${canNavigateNext
                      ? 'bg-blue-600 text-white shadow-lg hover:shadow-xl hover:bg-blue-700'
                      : 'bg-slate-200 text-slate-400 dark:bg-slate-700 dark:text-slate-500 cursor-not-allowed'
                    }
                  `}
                >
                  Next Step
                  <ChevronRight className="w-4 h-4 ml-2" />
                </button>
              ) : allStepsCompleted ? (
                <Link
                  to="/exercises"
                  className="inline-flex items-center px-6 py-3 bg-green-600 text-white font-medium rounded-lg shadow-lg hover:shadow-xl hover:bg-green-700 transition-all"
                >
                  Complete Exercise
                  <Award className="w-4 h-4 ml-2" />
                </Link>
              ) : (
                <button
                  disabled
                  className="inline-flex items-center px-6 py-3 bg-slate-200 text-slate-400 dark:bg-slate-700 dark:text-slate-500 font-medium rounded-lg cursor-not-allowed"
                >
                  Complete All Steps
                  <Lock className="w-4 h-4 ml-2" />
                </button>
              )}
            </div>
          </div>

          {/* Sidebar - General Hints */}
          <div className="space-y-6">
            {/* General Hints */}
            {exercise.general_hints && exercise.general_hints.length > 0 && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-2xl shadow-lg p-6 border border-yellow-200 dark:border-yellow-800">
                <h3 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-4 flex items-center">
                  <Lightbulb className="w-5 h-5 mr-2" />
                  General Hints
                </h3>
                <div className="space-y-3">
                  {exercise.general_hints
                    .filter(hint => hint.show_after_step <= currentStep)
                    .map((hint, index) => (
                      <div key={index} className="text-sm text-yellow-700 dark:text-yellow-300">
                        <div dangerouslySetInnerHTML={{ __html: sanitizeHTML(hint.hint_text, { mode: 'rich' }) }} />
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Step Progress Summary */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                Progress Summary
              </h3>
              <div className="space-y-2">
                {exercise.steps.map((step, index) => (
                  <div 
                    key={index}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50"
                  >
                    <div className="flex items-center space-x-2">
                      {stepCompletion[index] ? (
                        <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border-2 border-slate-300 dark:border-slate-500" />
                      )}
                      <span className="text-sm text-slate-700 dark:text-slate-300">
                        Step {index + 1}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-slate-900 dark:text-white">
                      {stepCompletion[index] ? step.points : 0} / {step.points}
                    </span>
                  </div>
                ))}
                <div className="pt-2 mt-2 border-t border-slate-200 dark:border-slate-600">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-900 dark:text-white">Total</span>
                    <span className="font-bold text-lg text-blue-600 dark:text-blue-400">
                      {totalPoints} / {exercise.total_points}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StepBasedExercisePage