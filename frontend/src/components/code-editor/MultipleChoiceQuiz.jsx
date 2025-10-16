import React, { useState, useCallback } from 'react'
import { CheckCircle, XCircle, RotateCcw, Send } from 'lucide-react'
import ProgressiveHintPanel from './ProgressiveHintPanel'
import { sanitizeHTML } from '../../utils/sanitize'

const MultipleChoiceQuiz = ({
  quizData,
  onSubmit = () => {},
  className = ''
}) => {
  const [selectedAnswers, setSelectedAnswers] = useState({})
  const [isValidated, setIsValidated] = useState(false)
  const [validationResults, setValidationResults] = useState({})
  const [score, setScore] = useState(0)
  const [timeSpent, setTimeSpent] = useState(0)
  const [wrongAttempts, setWrongAttempts] = useState(0)

  // Parse quiz questions from quizData
  const questions = quizData?.questions || []
  const totalQuestions = questions.length

  // Handle answer selection
  const handleAnswerSelect = useCallback((questionId, optionIndex) => {
    if (isValidated) return // Don't allow changes after validation

    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: optionIndex
    }))
  }, [isValidated])

  // Validate answers
  const validateAnswers = useCallback(() => {
    const results = {}
    let correctCount = 0

    questions.forEach(question => {
      const userAnswer = selectedAnswers[question.id]
      const correctAnswer = parseInt(question.correct)
      const isCorrect = userAnswer === correctAnswer

      results[question.id] = isCorrect
      if (isCorrect) correctCount++
    })

    const calculatedScore = Math.round((correctCount / totalQuestions) * 100)

    setValidationResults(results)
    setScore(calculatedScore)
    setIsValidated(true)

    // Track wrong attempts
    if (calculatedScore < 100) {
      setWrongAttempts(prev => prev + 1)
    }

    // Call parent submit handler
    onSubmit({
      answers: selectedAnswers,
      results,
      score: calculatedScore,
      correctCount,
      totalQuestions
    })
  }, [questions, selectedAnswers, totalQuestions, onSubmit])

  // Reset quiz
  const resetQuiz = useCallback(() => {
    setSelectedAnswers({})
    setIsValidated(false)
    setValidationResults({})
    setScore(0)
    setTimeSpent(0)
  }, [])

  // Check if all questions are answered
  const allQuestionsAnswered = questions.every(q => selectedAnswers[q.id] !== undefined)

  return (
    <div className={`multiple-choice-quiz ${className}`}>
      {/* Quiz Header */}
      <div className="quiz-header bg-slate-100 dark:bg-slate-800 p-4 rounded-t-lg border-b">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {quizData?.title || 'Knowledge Check'}
            </h3>
            {quizData?.description && (
              <div
                className="text-sm text-slate-600 dark:text-slate-400 mt-1 prose prose-sm dark:prose-invert max-w-none"
                dangerouslySetInnerHTML={{ __html: sanitizeHTML(quizData.description, { mode: 'rich' }) }}
              />
            )}
          </div>

          {/* Score Display */}
          {isValidated && (
            <div className="text-right">
              <div className={`text-2xl font-bold ${
                score >= 80 ? 'text-green-600 dark:text-green-400' :
                score >= 60 ? 'text-yellow-600 dark:text-yellow-400' :
                'text-red-600 dark:text-red-400'
              }`}>
                {score}%
              </div>
              <div className="text-xs text-slate-600 dark:text-slate-400">
                {Object.values(validationResults).filter(v => v).length}/{totalQuestions} correct
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Questions */}
      <div className="quiz-questions p-6 space-y-6 bg-white dark:bg-slate-900">
        {questions.map((question, qIndex) => {
          const isAnswered = selectedAnswers[question.id] !== undefined
          const isCorrect = validationResults[question.id]

          return (
            <div
              key={question.id}
              className={`question-card p-4 rounded-lg border-2 transition-all ${
                isValidated
                  ? isCorrect
                    ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                    : 'border-red-500 bg-red-50 dark:bg-red-900/20'
                  : 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800'
              }`}
            >
              {/* Question Text */}
              <div className="flex items-start space-x-3 mb-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-bold">
                  {qIndex + 1}
                </div>
                <div className="flex-1">
                  <p className="text-base font-medium text-slate-900 dark:text-slate-100">
                    {question.question}
                  </p>
                </div>
                {isValidated && (
                  <div className="flex-shrink-0">
                    {isCorrect ? (
                      <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                    ) : (
                      <XCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
                    )}
                  </div>
                )}
              </div>

              {/* Options */}
              <div className="space-y-2 ml-9">
                {question.options.map((option, optionIndex) => {
                  const isSelected = selectedAnswers[question.id] === optionIndex
                  const isCorrectOption = optionIndex === parseInt(question.correct)
                  const showCorrect = isValidated && isCorrectOption
                  const showIncorrect = isValidated && isSelected && !isCorrectOption

                  return (
                    <label
                      key={optionIndex}
                      className={`flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-all ${
                        isValidated
                          ? showCorrect
                            ? 'bg-green-100 dark:bg-green-900/30 border-2 border-green-500'
                            : showIncorrect
                            ? 'bg-red-100 dark:bg-red-900/30 border-2 border-red-500'
                            : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700'
                          : isSelected
                          ? 'bg-blue-100 dark:bg-blue-900/30 border-2 border-blue-500'
                          : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'
                      } ${isValidated ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                    >
                      <input
                        type="radio"
                        name={`question-${question.id}`}
                        value={optionIndex}
                        checked={isSelected}
                        onChange={() => handleAnswerSelect(question.id, optionIndex)}
                        disabled={isValidated}
                        className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                      />
                      <span className={`flex-1 text-sm ${
                        isValidated && showCorrect
                          ? 'font-semibold text-green-800 dark:text-green-200'
                          : isValidated && showIncorrect
                          ? 'font-semibold text-red-800 dark:text-red-200'
                          : 'text-slate-700 dark:text-slate-300'
                      }`}>
                        {option}
                      </span>
                      {showCorrect && (
                        <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                      )}
                      {showIncorrect && (
                        <XCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                      )}
                    </label>
                  )
                })}
              </div>

              {/* Explanation (if validated and incorrect) */}
              {isValidated && !isCorrect && question.explanation && (
                <div className="mt-3 ml-9 p-3 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    <span className="font-semibold">Explanation: </span>
                    {question.explanation}
                  </p>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Action Buttons */}
      <div className="quiz-actions bg-slate-100 dark:bg-slate-800 p-4 rounded-b-lg border-t flex justify-between items-center">
        <div className="text-sm text-slate-600 dark:text-slate-400">
          {allQuestionsAnswered ? (
            isValidated ? (
              <span className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4" />
                <span>Quiz completed!</span>
              </span>
            ) : (
              <span>All questions answered. Ready to submit!</span>
            )
          ) : (
            <span>{Object.keys(selectedAnswers).length}/{totalQuestions} questions answered</span>
          )}
        </div>

        <div className="flex space-x-2">
          {isValidated ? (
            <button
              onClick={resetQuiz}
              className="flex items-center space-x-2 px-4 py-2 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Retry Quiz</span>
            </button>
          ) : (
            <button
              onClick={validateAnswers}
              disabled={!allQuestionsAnswered}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-4 h-4" />
              <span>Submit Quiz</span>
            </button>
          )}
        </div>
      </div>

      {/* Progressive Hints for Quiz */}
      {quizData?.progressiveHints && (
        <ProgressiveHintPanel
          exerciseData={quizData}
          currentAnswers={selectedAnswers}
          timeSpent={timeSpent}
          wrongAttempts={wrongAttempts}
          onHintRequested={() => {}}
        />
      )}
    </div>
  )
}

export default MultipleChoiceQuiz
