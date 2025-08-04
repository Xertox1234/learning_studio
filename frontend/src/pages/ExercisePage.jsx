import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { FillInBlankExercise, InteractiveCodeEditor } from '../components/code-editor'
import { submitExercise } from '../utils/api'
import { CheckCircle, XCircle, Play } from 'lucide-react'

export default function ExercisePage() {
  const { exerciseId } = useParams()
  const [exercise, setExercise] = useState(null)
  const [loading, setLoading] = useState(true)
  const [results, setResults] = useState(null)

  // Sample exercise data (in real app, this would come from API)
  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setExercise({
        id: exerciseId,
        title: "Complete the Python Function",
        description: "Fill in the missing parts to create a function that calculates the area of a rectangle.",
        type: "fill-in-blank",
        template: `def calculate_area({{BLANK_1}}, {{BLANK_2}}):
    """Calculate the area of a rectangle."""
    area = {{BLANK_3}}
    return {{BLANK_4}}

# Test your function
length = 5
width = 3
result = calculate_area(length, width)
print(f"The area is: {result}")`,
        solutions: {
          "1": "length",
          "2": "width", 
          "3": "length * width",
          "4": "area"
        },
        alternativeSolutions: {
          "1": ["length", "l", "len"],
          "2": ["width", "w", "wid"],
          "3": ["length * width", "width * length", "l * w", "w * l"],
          "4": ["area", "result", "calculation"]
        },
        hints: [
          "The function should take two parameters representing the dimensions",
          "Area of rectangle = length × width", 
          "Don't forget to return the calculated value"
        ],
        progressiveHints: [
          {
            level: 1,
            type: 'conceptual',
            title: 'Think About It',
            content: 'What two pieces of information do you need to calculate the area of a rectangle?',
            triggerTime: 30,
            triggerAttempts: 0
          },
          {
            level: 2,
            type: 'approach', 
            title: 'Function Parameters',
            content: 'The function should take two parameters representing the dimensions of the rectangle.',
            triggerTime: 90,
            triggerAttempts: 2
          },
          {
            level: 3,
            type: 'structure',
            title: 'Mathematical Operation',
            content: 'Area of rectangle = length × width. You need to multiply the two parameters together.',
            triggerTime: 180,
            triggerAttempts: 3
          },
          {
            level: 4,
            type: 'near-solution',
            title: 'Almost There',
            content: 'You need to store the result in a variable and return it. The variable should be the product of your two parameters.',
            triggerTime: 300,
            triggerAttempts: 5
          },
          {
            level: 5,
            type: 'solution',
            title: 'Complete Solution',
            content: 'Here\'s the step-by-step solution: Take length and width as parameters, multiply them to get the area, and return the result.',
            triggerTime: 420,
            triggerAttempts: 7
          }
        ],
        language: "python"
      })
      setLoading(false)
    }, 1000)
  }, [exerciseId])

  const handleSubmit = async (code, executionResult, answers) => {
    console.log('Exercise submitted:', { code, executionResult, answers })
    
    try {
      const result = await submitExercise(exerciseId, {
        answers,
        completed_code: code,
        execution_result: executionResult
      })
      
      setResults(result)
    } catch (error) {
      console.error('Failed to submit exercise:', error)
      
      // Fallback result
      const fallbackResult = {
        success: false,
        message: "Submission failed, but your work is saved locally",
        score: 0,
        error: error.message
      }
      setResults(fallbackResult)
    }
  }

  const handleValidate = (validationResults, answers) => {
    console.log('Validation results:', validationResults, answers)
    setResults({ validation: validationResults, answers })
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    )
  }

  if (!exercise) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <XCircle className="mx-auto h-16 w-16 text-red-500 mb-4" />
          <h2 className="text-2xl font-semibold mb-2">Exercise Not Found</h2>
          <p className="text-muted-foreground">The exercise you're looking for doesn't exist.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center space-x-2 text-sm text-muted-foreground mb-2">
          <span>Exercise</span>
          <span>•</span>
          <span>#{exerciseId}</span>
        </div>
        <h1 className="text-3xl font-bold text-foreground mb-2">{exercise.title}</h1>
        <p className="text-muted-foreground text-lg">{exercise.description}</p>
      </div>

      {/* Exercise Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Exercise */}
        <div className="lg:col-span-2">
          {exercise.type === 'fill-in-blank' ? (
            <FillInBlankExercise
              exerciseData={exercise}
              onSubmit={handleSubmit}
              onValidate={handleValidate}
              className="h-full"
            />
          ) : (
            <div className="bg-card rounded-lg p-6">
              <InteractiveCodeEditor
                value={exercise.template || '# Start coding here...'}
                language={exercise.language || 'python'}
                className="min-h-[400px]"
              />
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Instructions */}
          <div className="bg-card p-6 rounded-lg">
            <h3 className="font-semibold text-lg mb-3">Instructions</h3>
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>Complete the missing parts of the code by filling in the blanks.</p>
              <p>Click "Validate" to check your answers.</p>
              <p>Click "Run Code" to test your solution.</p>
            </div>
          </div>

          {/* Results */}
          {results && (
            <div className="bg-card p-6 rounded-lg">
              <h3 className="font-semibold text-lg mb-3">Results</h3>
              
              {/* Validation Results */}
              {results.validation && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium mb-2">Validation:</h4>
                  <div className="space-y-2">
                    {Object.entries(results.validation).map(([key, isCorrect]) => (
                      <div key={key} className="flex items-center space-x-2">
                        {isCorrect ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                        <span className="text-sm">
                          {key}: {results.answers?.[key] || '(empty)'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Code Execution Results */}
              {results.output && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium mb-2">Code Output:</h4>
                  <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded-lg">
                    <pre className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
                      {results.output}
                    </pre>
                    {results.execution_time && (
                      <div className="text-xs text-gray-500 mt-2">
                        Execution time: {results.execution_time}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* General Messages */}
              {results.message && (
                <div className={`p-3 rounded-lg ${
                  results.success 
                    ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-200'
                    : 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-200'
                }`}>
                  <div className="flex items-center space-x-2">
                    {results.success ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <XCircle className="h-4 w-4" />
                    )}
                    <span className="text-sm">{results.message}</span>
                  </div>
                  {results.score !== undefined && (
                    <div className="text-xs mt-1">Score: {results.score}/100</div>
                  )}
                </div>
              )}

              {/* Error Display */}
              {results.error && (
                <div className="bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-200 p-3 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <XCircle className="h-4 w-4" />
                    <span className="text-sm font-medium">Error:</span>
                  </div>
                  <pre className="text-xs mt-2 whitespace-pre-wrap">{results.error}</pre>
                </div>
              )}
            </div>
          )}

          {/* Hints */}
          {exercise.hints && exercise.hints.length > 0 && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 p-6 rounded-lg border border-yellow-200 dark:border-yellow-800">
              <h3 className="font-semibold text-lg mb-3 text-yellow-800 dark:text-yellow-200">
                Hints
              </h3>
              <ul className="space-y-2 text-sm text-yellow-700 dark:text-yellow-300">
                {exercise.hints.map((hint, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="font-medium">{index + 1}.</span>
                    <span>{hint}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}