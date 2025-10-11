import React, { useState, useEffect } from 'react'
import ConfettiExplosion from 'react-confetti-explosion'
import { Trophy, Award, CheckCircle } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'

/**
 * ConfettiCelebration - Celebratory component with confetti animation
 * Used for course completion, quiz success, and other achievements
 */
const ConfettiCelebration = ({
  isVisible = false,
  onComplete = () => {},
  title = "Congratulations!",
  message = "You've completed the course successfully!",
  type = "course", // course, quiz, lesson, achievement
  autoHide = true,
  autoHideDelay = 5000,
  className = ""
}) => {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [showConfetti, setShowConfetti] = useState(false)
  const [showModal, setShowModal] = useState(false)

  // Start celebration when component becomes visible
  useEffect(() => {
    if (isVisible) {
      setShowConfetti(true)
      setShowModal(true)
      
      // Auto-hide after delay
      if (autoHide) {
        const hideTimer = setTimeout(() => {
          setShowModal(false)
          setTimeout(() => {
            onComplete()
          }, 500) // Wait for modal animation to complete
        }, autoHideDelay)
        
        return () => clearTimeout(hideTimer)
      }
    }
  }, [isVisible, autoHide, autoHideDelay, onComplete])

  // Handle confetti completion
  const handleConfettiComplete = () => {
    setShowConfetti(false)
  }

  // Get celebration icon based on type
  const getCelebrationIcon = () => {
    switch (type) {
      case 'course':
        return <Trophy className="h-16 w-16 text-yellow-500" />
      case 'quiz':
        return <Award className="h-16 w-16 text-blue-500" />
      case 'lesson':
        return <CheckCircle className="h-16 w-16 text-green-500" />
      default:
        return <Trophy className="h-16 w-16 text-yellow-500" />
    }
  }

  // Get celebration colors based on type
  const getConfettiProps = () => {
    switch (type) {
      case 'course':
        return {
          particleCount: 200,
          spread: 180,
          colors: ['#FFD700', '#FFA500', '#FF6347', '#32CD32', '#1E90FF'],
          duration: 3000,
        }
      case 'quiz':
        return {
          particleCount: 150,
          spread: 160,
          colors: ['#4169E1', '#00CED1', '#32CD32', '#FFD700'],
          duration: 2500,
        }
      case 'lesson':
        return {
          particleCount: 100,
          spread: 120,
          colors: ['#32CD32', '#90EE90', '#98FB98', '#00FF00'],
          duration: 2000,
        }
      default:
        return {
          particleCount: 200,
          spread: 180,
          colors: ['#FFD700', '#FFA500', '#FF6347', '#32CD32', '#1E90FF'],
          duration: 3000,
        }
    }
  }

  if (!isVisible) return null

  return (
    <div className={`confetti-celebration ${className}`}>
      {/* Confetti Animation */}
      {showConfetti && (
        <div className="fixed inset-0 pointer-events-none z-50 flex items-center justify-center">
          <ConfettiExplosion
            {...getConfettiProps()}
            onComplete={handleConfettiComplete}
          />
        </div>
      )}

      {/* Celebration Modal */}
      {showModal && (
        <div className="fixed inset-0 z-40 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            {/* Background overlay */}
            <div 
              className={`fixed inset-0 transition-opacity duration-300 ${
                showModal ? 'opacity-75' : 'opacity-0'
              } ${isDark ? 'bg-black' : 'bg-gray-500'}`}
              onClick={() => !autoHide && setShowModal(false)}
            />
            
            {/* Modal panel */}
            <div className={`relative transform overflow-hidden rounded-2xl shadow-2xl transition-all duration-500 ${
              showModal ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
            } ${
              isDark 
                ? 'bg-gray-800 border border-gray-600' 
                : 'bg-white border border-gray-200'
            } px-8 py-10 text-center max-w-md w-full mx-4`}>
              
              {/* Celebration Icon */}
              <div className="mx-auto mb-6 animate-bounce">
                {getCelebrationIcon()}
              </div>

              {/* Title */}
              <h2 className={`text-3xl font-bold mb-4 ${
                isDark ? 'text-white' : 'text-gray-900'
              }`}>
                {title}
              </h2>

              {/* Message */}
              <p className={`text-lg mb-8 leading-relaxed ${
                isDark ? 'text-gray-300' : 'text-gray-600'
              }`}>
                {message}
              </p>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                {!autoHide && (
                  <button
                    onClick={() => {
                      setShowModal(false)
                      setTimeout(() => onComplete(), 300)
                    }}
                    className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                      isDark
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                    } transform hover:scale-105 shadow-lg hover:shadow-xl`}
                  >
                    Continue Learning
                  </button>
                )}

                {type === 'course' && (
                  <button
                    onClick={() => {
                      // Could trigger certificate download or sharing
                      console.log('Certificate action triggered')
                    }}
                    className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                      isDark
                        ? 'bg-yellow-600 hover:bg-yellow-700 text-white border border-yellow-500'
                        : 'bg-yellow-500 hover:bg-yellow-600 text-white border border-yellow-400'
                    } transform hover:scale-105 shadow-lg hover:shadow-xl`}
                  >
                    View Certificate
                  </button>
                )}
              </div>

              {/* Progress indicator for auto-hide */}
              {autoHide && (
                <div className="mt-6">
                  <div className={`w-full h-1 rounded-full overflow-hidden ${
                    isDark ? 'bg-gray-600' : 'bg-gray-200'
                  }`}>
                    <div 
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-600 animate-pulse"
                      style={{
                        animation: `shrink ${autoHideDelay}ms linear`,
                      }}
                    />
                  </div>
                  <p className={`text-xs mt-2 ${
                    isDark ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    This will close automatically...
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Custom CSS for progress bar animation */}
      <style jsx>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  )
}

export default ConfettiCelebration