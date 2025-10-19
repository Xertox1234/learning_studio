import { useState, useEffect, memo } from 'react'
import { Clock } from 'lucide-react'

const ExerciseTimer = memo(({ startTime, className = '' }) => {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    // Calculate initial elapsed time
    const initialElapsed = Math.floor((Date.now() - startTime) / 1000)
    setElapsed(initialElapsed)

    // Update every second
    const timer = setInterval(() => {
      const newElapsed = Math.floor((Date.now() - startTime) / 1000)
      setElapsed(newElapsed)
    }, 1000)

    return () => clearInterval(timer)
  }, [startTime])

  // Format time as MM:SS
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className={`flex items-center space-x-2 text-sm text-slate-600 dark:text-slate-400 ${className}`}>
      <Clock className="w-4 h-4" />
      <span className="font-mono">{formatTime(elapsed)}</span>
    </div>
  )
})

ExerciseTimer.displayName = 'ExerciseTimer'

export default ExerciseTimer
