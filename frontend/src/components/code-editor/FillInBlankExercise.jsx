import React, { useState, useCallback, useEffect, useRef } from 'react'
import InteractiveCodeEditor from './InteractiveCodeEditor'
import ProgressiveHintPanel from './ProgressiveHintPanel'
import AIFloatingAssistant from '../ai/AIFloatingAssistant'
import CodeEditorErrorBoundary from './CodeEditorErrorBoundary'
import AIErrorBoundary from '../ai/AIErrorBoundary'
import { executeCode } from '../../utils/api'
import { useAuth } from '../../contexts/AuthContext'
import { sanitizeHTML } from '../../utils/sanitize'
import { Play, RotateCcw, CheckCircle, XCircle } from 'lucide-react'

const FillInBlankExercise = ({
  exerciseData,
  onSubmit = () => {},
  onValidate = () => {},
  className = ''
}) => {
  const [code, setCode] = useState(exerciseData?.template || '')
  const [fillBlankValues, setFillBlankValues] = useState({})
  const [isValidated, setIsValidated] = useState(false)
  const [validationResults, setValidationResults] = useState({})
  const [isRunning, setIsRunning] = useState(false)
  const [executionOutput, setExecutionOutput] = useState(null)
  const [showSuccessMessage, setShowSuccessMessage] = useState(false)

  // Progressive hint tracking
  const [timeSpent, setTimeSpent] = useState(0)
  const [wrongAttempts, setWrongAttempts] = useState(0)
  const [hintLevel, setHintLevel] = useState(0)
  const startTimeRef = useRef(Date.now())
  const timerRef = useRef(null)

  // No need to parse positions - the MatchDecorator handles this automatically
  // We just need to track which blanks exist and their solutions

  const { isAuthenticated, user } = useAuth()

  // Timer effect for tracking time spent
  useEffect(() => {
    // Only start timer if we have exercise data
    if (!exerciseData?.id) return
    
    startTimeRef.current = Date.now()
    setTimeSpent(0) // Reset time counter
    
    const timer = setInterval(() => {
      if (startTimeRef.current) {
        setTimeSpent(Math.floor((Date.now() - startTimeRef.current) / 1000))
      }
    }, 1000)
    
    timerRef.current = timer

    return () => {
      if (timer) {
        clearInterval(timer)
      }
      timerRef.current = null
    }
  }, [exerciseData?.id]) // Restart timer when exercise changes

  // Cleanup timer on component unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [])

  // Handle fill-in-blank changes
  const handleFillBlankChange = useCallback((blankId, value, allValues) => {
    setFillBlankValues(allValues)
    setIsValidated(false)
  }, [])

  // Validate fill-in-blank answers using DOM queries like the original pattern
  const validateAnswers = useCallback(async () => {
    setIsValidated(true)

    const inputs = document.querySelectorAll('.cm-blank-input')
    const results = {}
    const values = {}
    const solutions = exerciseData?.solutions || {}
    const alternativeSolutions = exerciseData?.alternativeSolutions || {}

    inputs.forEach(input => {
      const blankId = input.dataset.blankId
      const userInput = input.value.trim()
      const expectedSolution = solutions[blankId]
      const alternatives = alternativeSolutions[blankId] || []

      values[blankId] = userInput

      let isCorrect = false

      // Special validation for string literals
      // Only accept "any quoted string" if the solution is a name/identifier pattern
      // (contains letters or is a common variable name pattern)
      const isNamePattern = expectedSolution &&
        (expectedSolution.match(/^["'][A-Z][a-z]+["']$/) || // Capitalized name like "William"
         expectedSolution.match(/^["'][a-z_][a-z0-9_]*["']$/)) // Variable name pattern

      if (isNamePattern) {
        // Accept any quoted string for name-like patterns
        if (expectedSolution.startsWith('"') && expectedSolution.endsWith('"')) {
          if (userInput.startsWith('"') && userInput.endsWith('"') && userInput.length > 2) {
            isCorrect = true
          } else if (userInput.startsWith("'") && userInput.endsWith("'") && userInput.length > 2) {
            isCorrect = true
          }
        } else if (expectedSolution.startsWith("'") && expectedSolution.endsWith("'")) {
          if (userInput.startsWith('"') && userInput.endsWith('"') && userInput.length > 2) {
            isCorrect = true
          } else if (userInput.startsWith("'") && userInput.endsWith("'") && userInput.length > 2) {
            isCorrect = true
          }
        }
      }

      // Check if input matches solution or alternatives exactly
      if (!isCorrect && (userInput === expectedSolution || alternatives.includes(userInput))) {
        isCorrect = true
      }

      results[blankId] = isCorrect

      // Add visual feedback like the original
      input.classList.remove('correct', 'incorrect')
      input.classList.add(isCorrect ? 'correct' : 'incorrect')
    })

    setValidationResults(results)
    setFillBlankValues(values)

    // Check if all correct - show success message
    const allCorrect = Object.values(results).every(result => result === true)

    console.log('Validation Results:', results)
    console.log('All Correct?', allCorrect)
    console.log('Values:', values)

    if (allCorrect) {
      setShowSuccessMessage(true)
      setTimeout(() => {
        setShowSuccessMessage(false)
      }, 3000)
    }

    // Track wrong attempts for progressive hints
    const hasErrors = Object.values(results).some(result => !result)
    if (hasErrors) {
      setWrongAttempts(prev => prev + 1)
    }

    onValidate(results, values)

    return results
  }, [exerciseData, onValidate])

  // Generate complete code with fill-in-blank values using {{BLANK_N}} pattern
  const generateCompleteCode = useCallback(() => {
    let completeCode = exerciseData?.template || ''
    
    // Replace {{BLANK_N}} patterns with user values
    Object.keys(fillBlankValues).forEach(blankId => {
      const value = fillBlankValues[blankId] || ''
      const blankPattern = new RegExp(`\\{\\{BLANK_${blankId}\\}\\}`, 'g')
      completeCode = completeCode.replace(blankPattern, value)
    })
    
    return completeCode
  }, [exerciseData, fillBlankValues])

  // Run the code
  const runCode = useCallback(async () => {
    setIsRunning(true)
    setExecutionOutput(null)

    try {
      const completeCode = generateCompleteCode()
      const result = await executeCode(completeCode, exerciseData?.language || 'python')
      setExecutionOutput(result)
      onSubmit(completeCode, result, fillBlankValues)
    } catch (error) {
      console.error('Error running code:', error)
      // executeCode already handles errors and returns mock results
      const errorResult = {
        output: `# Unexpected error occurred\n# Your code:\n${generateCompleteCode()}`,
        success: false,
        error: error.message || "Unexpected error"
      }
      setExecutionOutput(errorResult)
      onSubmit(generateCompleteCode(), errorResult, fillBlankValues)
    } finally {
      setIsRunning(false)
    }
  }, [generateCompleteCode, exerciseData, fillBlankValues, onSubmit])

  // Handle hint requests
  const handleHintRequested = useCallback((hint) => {
    setHintLevel(hint.level)
    // Could track hint usage analytics here
    console.log(`Hint level ${hint.level} requested:`, hint)
  }, [])

  // Reset exercise
  const resetExercise = useCallback(() => {
    setFillBlankValues({})
    setIsValidated(false)
    setValidationResults({})
    setCode(exerciseData?.template || '')
    setExecutionOutput(null)
    setTimeSpent(0)
    setWrongAttempts(0)
    setHintLevel(0)
    startTimeRef.current = Date.now()
  }, [exerciseData])

  // Get expected blanks from solutions
  const expectedBlanks = Object.keys(exerciseData?.solutions || {})

  // Check if all blanks are filled (if no blanks, always true for run-only exercises)
  const allBlanksFilled = expectedBlanks.length === 0 ? true : expectedBlanks.every(blankId =>
    fillBlankValues[blankId]?.trim()
  )

  // Calculate progress
  const progress = expectedBlanks.length > 0 
    ? (Object.keys(fillBlankValues).filter(key => 
        fillBlankValues[key]?.trim()
      ).length / expectedBlanks.length) * 100 
    : 0

  return (
    <div className={`fill-blank-exercise ${className}`}>
      {/* Exercise Header */}
      <div className="exercise-header bg-slate-100 dark:bg-slate-800 p-4 rounded-t-lg border-b">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {exerciseData?.title || 'Fill in the Blanks'}
            </h3>
            <div
              className="text-sm text-slate-600 dark:text-slate-400 mt-1 prose prose-sm dark:prose-invert max-w-none"
              dangerouslySetInnerHTML={{
                __html: sanitizeHTML(exerciseData?.description || 'Complete the code by filling in the missing parts', { mode: 'rich' })
              }}
            />
            {isAuthenticated && user && (
              <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                ✓ Logged in as {user.username || user.email}
              </p>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Progress indicator */}
            <div className="text-sm text-slate-600 dark:text-slate-400">
              Progress: {Math.round(progress)}%
            </div>
            <div className="w-20 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Code Editor */}
      <div className="editor-container">
        <CodeEditorErrorBoundary>
          <InteractiveCodeEditor
            value={code}
            onChange={setCode}
            language={exerciseData?.language || 'python'}
            onFillBlankChange={handleFillBlankChange}
            readOnly={true}
            className="min-h-[300px]"
          />
        </CodeEditorErrorBoundary>
      </div>

      {/* Validation Results */}
      {isValidated && (
        <div className="validation-results bg-slate-50 dark:bg-slate-900 p-4 border-t">
          <h4 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">
            Validation Results:
          </h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(validationResults).map(([blankId, isCorrect]) => (
              <div
                key={blankId}
                className={`flex items-center space-x-1 px-2 py-1 rounded text-sm ${
                  isCorrect
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                }`}
              >
                {isCorrect ? (
                  <CheckCircle className="w-3 h-3" />
                ) : (
                  <XCircle className="w-3 h-3" />
                )}
                <span>{blankId}: {fillBlankValues[blankId] || '(empty)'}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Code Execution Output */}
      {executionOutput && (
        <div className="execution-output bg-slate-50 dark:bg-slate-900 p-4 border-t">
          <h4 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">
            Output:
          </h4>
          <div className={`p-3 rounded font-mono text-sm ${
            executionOutput.success
              ? 'bg-green-50 dark:bg-green-900/20 text-green-900 dark:text-green-100 border border-green-200 dark:border-green-800'
              : 'bg-red-50 dark:bg-red-900/20 text-red-900 dark:text-red-100 border border-red-200 dark:border-red-800'
          }`}>
            {executionOutput.error ? (
              <div>
                <div className="font-bold text-red-700 dark:text-red-300 mb-1">Error:</div>
                <div className="whitespace-pre-wrap">{executionOutput.error}</div>
              </div>
            ) : (
              <div className="whitespace-pre-wrap">{executionOutput.output || '(no output)'}</div>
            )}
          </div>
        </div>
      )}

      {/* Success Message Toast */}
      {showSuccessMessage && (
        <div className="fixed bottom-8 right-8 z-50 animate-in slide-in-from-bottom duration-300">
          <div className="bg-green-600 text-white px-6 py-4 rounded-lg shadow-lg flex items-center space-x-3">
            <CheckCircle className="w-6 h-6" />
            <div>
              <div className="font-semibold">{exerciseData?.success_message || 'Great job!'}</div>
              <div className="text-sm text-green-100">All answers are correct!</div>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="exercise-actions bg-slate-100 dark:bg-slate-800 p-4 rounded-b-lg border-t flex justify-between items-center">
        <div className="flex space-x-2">
          <button
            onClick={validateAnswers}
            disabled={!allBlanksFilled}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <CheckCircle className="w-4 h-4" />
            <span>Validate</span>
          </button>
          
          <button
            onClick={runCode}
            disabled={!allBlanksFilled || isRunning}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Play className="w-4 h-4" />
            <span>{isRunning ? 'Running...' : 'Run Code'}</span>
          </button>
        </div>
        
        <button
          onClick={resetExercise}
          className="flex items-center space-x-2 px-4 py-2 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Reset</span>
        </button>
      </div>

      {/* Progressive Hints */}
      <ProgressiveHintPanel
        exerciseData={exerciseData}
        currentAnswers={fillBlankValues}
        timeSpent={timeSpent}
        wrongAttempts={wrongAttempts}
        onHintRequested={handleHintRequested}
      />

      {/* AI Floating Assistant */}
      <AIErrorBoundary>
        <AIFloatingAssistant
          exerciseContext={exerciseData}
          studentCode={generateCompleteCode()}
        />
      </AIErrorBoundary>
    </div>
  )
}

export default FillInBlankExercise