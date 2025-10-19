import React, { useState, useEffect } from 'react'
import { ChevronRight, Lightbulb, Clock, Eye, CheckCircle } from 'lucide-react'
import { sanitizeHTML } from '../../utils/sanitize'

const ProgressiveHintPanel = ({
  exerciseData,
  currentAnswers = {},
  startTime,
  wrongAttempts = 0,
  onHintRequested = () => {}
}) => {
  const [currentHintLevel, setCurrentHintLevel] = useState(0)
  const [hintsRevealed, setHintsRevealed] = useState([])
  const [autoHintTriggered, setAutoHintTriggered] = useState(false)
  const [timeSpent, setTimeSpent] = useState(0)

  // Internal timer for tracking time (doesn't affect parent component)
  useEffect(() => {
    if (!startTime) return

    // Calculate initial elapsed time
    const initialElapsed = Math.floor((Date.now() - startTime) / 1000)
    setTimeSpent(initialElapsed)

    // Update every second
    const timer = setInterval(() => {
      const newElapsed = Math.floor((Date.now() - startTime) / 1000)
      setTimeSpent(newElapsed)
    }, 1000)

    return () => clearInterval(timer)
  }, [startTime])

  // Progressive hint structure - each exercise should define these levels
  const getProgressiveHints = () => {
    const hints = exerciseData?.progressiveHints || exerciseData?.hints || []
    
    // If exercise doesn't have progressive hints, create them from regular hints
    if (!exerciseData?.progressiveHints && hints.length > 0) {
      return [
        {
          level: 1,
          type: 'conceptual',
          title: 'Think About It',
          content: hints[0] || 'Break this problem down into smaller steps.',
          triggerTime: 30, // 30 seconds
          triggerAttempts: 0
        },
        {
          level: 2, 
          type: 'approach',
          title: 'Approach Hint',
          content: hints[1] || 'Consider what operation or method you need to use.',
          triggerTime: 90, // 1.5 minutes
          triggerAttempts: 2
        },
        {
          level: 3,
          type: 'structure', 
          title: 'Code Structure',
          content: hints[2] || 'Think about the syntax and structure needed.',
          triggerTime: 180, // 3 minutes
          triggerAttempts: 3
        },
        {
          level: 4,
          type: 'near-solution',
          title: 'Almost There',
          content: 'You\'re close! Check the specific values you\'re using.',
          triggerTime: 300, // 5 minutes
          triggerAttempts: 5
        },
        {
          level: 5,
          type: 'solution',
          title: 'Complete Solution',
          content: 'Here\'s the complete solution with explanation.',
          triggerTime: 420, // 7 minutes
          triggerAttempts: 7
        }
      ]
    }
    
    return hints
  }

  const progressiveHints = getProgressiveHints()
  const maxHintLevel = progressiveHints.length

  // Auto-trigger hints based on time and attempts
  useEffect(() => {
    if (autoHintTriggered || progressiveHints.length === 0) return

    const currentHint = progressiveHints[currentHintLevel]
    if (!currentHint) return

    const shouldTrigger = (
      (timeSpent >= currentHint.triggerTime) || 
      (wrongAttempts >= currentHint.triggerAttempts)
    ) && !hintsRevealed.includes(currentHint.level)

    if (shouldTrigger) {
      setAutoHintTriggered(true)
      // Auto-reveal first hint, but let user control the rest
      if (currentHintLevel === 0) {
        handleRevealHint(currentHint.level)
      }
    }
  }, [timeSpent, wrongAttempts, currentHintLevel, hintsRevealed, autoHintTriggered, progressiveHints])

  const handleRevealHint = (level) => {
    const hint = progressiveHints.find(h => h.level === level)
    if (hint && !hintsRevealed.includes(level)) {
      setHintsRevealed([...hintsRevealed, level])
      setCurrentHintLevel(Math.max(currentHintLevel, level))
      onHintRequested(hint)
    }
  }

  const getNextHintLevel = () => {
    const revealedLevels = hintsRevealed.length
    return Math.min(revealedLevels + 1, maxHintLevel)
  }

  const canRequestNextHint = () => {
    return hintsRevealed.length < maxHintLevel
  }

  const getHintIcon = (type) => {
    switch (type) {
      case 'conceptual': return <Lightbulb className="w-4 h-4 text-yellow-500" />
      case 'approach': return <ChevronRight className="w-4 h-4 text-blue-500" />
      case 'structure': return <Eye className="w-4 h-4 text-purple-500" />
      case 'near-solution': return <Clock className="w-4 h-4 text-orange-500" />
      case 'solution': return <CheckCircle className="w-4 h-4 text-green-500" />
      default: return <Lightbulb className="w-4 h-4 text-gray-500" />
    }
  }

  if (!progressiveHints || progressiveHints.length === 0) {
    return null
  }

  return (
    <div className="progressive-hints bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Lightbulb className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <h4 className="text-lg font-semibold text-blue-800 dark:text-blue-200">
            Smart Hints
          </h4>
        </div>
        
        {/* Progress indicator */}
        <div className="flex items-center space-x-2 text-sm text-blue-600 dark:text-blue-400">
          <span>Level {hintsRevealed.length}/{maxHintLevel}</span>
          <div className="w-20 h-2 bg-blue-200 dark:bg-blue-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
              style={{ width: `${(hintsRevealed.length / maxHintLevel) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Revealed hints */}
      <div className="space-y-3 mb-4">
        {progressiveHints
          .filter(hint => hintsRevealed.includes(hint.level))
          .map((hint, index) => (
            <div 
              key={hint.level}
              className="hint-card bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm animate-in slide-in-from-right duration-300"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-0.5">
                  {getHintIcon(hint.type)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h5 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {hint.title}
                    </h5>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Level {hint.level}
                    </span>
                  </div>
                  <div
                    className="text-sm text-gray-700 dark:text-gray-300 prose prose-sm dark:prose-invert max-w-none"
                    dangerouslySetInnerHTML={{ __html: sanitizeHTML(hint.content, { mode: 'rich' }) }}
                  />
                  
                  {/* Show solution for level 5 */}
                  {hint.level === 5 && exerciseData?.solutions && (
                    <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-900 rounded border">
                      <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                        Complete Solution:
                      </p>
                      {Object.entries(exerciseData.solutions).map(([blankId, solution]) => (
                        <div key={blankId} className="text-xs text-gray-700 dark:text-gray-300">
                          <span className="font-mono text-blue-600 dark:text-blue-400">
                            BLANK_{blankId}
                          </span>
                          {' = '}
                          <span className="font-mono text-green-600 dark:text-green-400">
                            {solution}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
      </div>

      {/* Next hint button */}
      {canRequestNextHint() && (
        <div className="flex justify-center">
          <button
            onClick={() => handleRevealHint(getNextHintLevel())}
            className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg hover:from-blue-600 hover:to-purple-600 transition-all duration-200 flex items-center space-x-2 shadow-lg hover:shadow-xl"
          >
            <Lightbulb className="w-4 h-4" />
            <span>Get Next Hint (Level {getNextHintLevel()})</span>
          </button>
        </div>
      )}

      {/* Auto-hint indicator */}
      {!autoHintTriggered && progressiveHints[0] && (
        <div className="mt-3 text-xs text-center text-gray-500 dark:text-gray-400">
          {timeSpent < progressiveHints[0].triggerTime ? (
            <>Automatic hint in {progressiveHints[0].triggerTime - timeSpent} seconds</>
          ) : wrongAttempts < progressiveHints[0].triggerAttempts ? (
            <>Automatic hint after {progressiveHints[0].triggerAttempts - wrongAttempts} more attempts</>
          ) : null}
        </div>
      )}
    </div>
  )
}

export default ProgressiveHintPanel