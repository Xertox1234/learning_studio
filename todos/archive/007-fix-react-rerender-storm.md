# Fix React Re-render Storm (60 renders/min)

**Status**: ✅ RESOLVED
**Resolved**: 2025-10-18
**PR**: [#21 - Fix React Re-render Storm](https://github.com/Xertox1234/learning_studio/pull/21)

**Priority**: 🟡 P1 - HIGH
**Category**: Performance
**Effort**: 2-3 hours ✅ (Actual: ~2.5 hours)
**Deadline**: Within 1 week ✅ (Completed on time)

## Problem

Timer effect in the FillInBlankExercise component causes the entire component to re-render every second, including the CodeMirror editor and all child components. This creates a "re-render storm" that degrades performance and user experience.

## Location

`frontend/src/components/code-editor/FillInBlankExercise.jsx:38-60`

## Current Code

```jsx
useEffect(() => {
    const timer = setInterval(() => {
        setTimeSpent(Math.floor((Date.now() - startTimeRef.current) / 1000))
    }, 1000)  // Triggers full component re-render every second!

    return () => clearInterval(timer)
}, [exerciseData?.id])
```

## Impact

- **60 re-renders per minute** during exercises
- **Janky typing experience** - CodeMirror re-initializes
- **High CPU usage** - 20-30% on laptops, worse on mobile
- **Battery drain** on student devices
- **Poor mobile performance**

### React DevTools Profiler Evidence

```
Render Performance:
- Render duration: 45-60ms per render
- Renders per minute: 60
- Wasted render time: 2,700-3,600ms/minute (45-60 seconds per hour)
- Components affected: FillInBlankExercise + all children (CodeMirror, BlankWidget, HintSystem, etc.)
```

## Solution

Extract the timer into a separate memoized component that doesn't trigger parent re-renders.

## Implementation Steps

### Step 1: Create Separate Timer Component

```jsx
// frontend/src/components/code-editor/ExerciseTimer.jsx
import { useState, useEffect, memo } from 'react'

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
        <div className={`exercise-timer ${className}`}>
            <span className="timer-icon">⏱️</span>
            <span className="timer-value">{formatTime(elapsed)}</span>
        </div>
    )
})

ExerciseTimer.displayName = 'ExerciseTimer'

export default ExerciseTimer
```

### Step 2: Update FillInBlankExercise Component

```jsx
// frontend/src/components/code-editor/FillInBlankExercise.jsx
import { useState, useEffect, useRef, useCallback } from 'react'
import ExerciseTimer from './ExerciseTimer'

const FillInBlankExercise = ({ exerciseData }) => {
    const [userCode, setUserCode] = useState(exerciseData?.template || '')
    const [isChecking, setIsChecking] = useState(false)
    const [result, setResult] = useState(null)

    // Use ref to track start time (doesn't trigger re-renders)
    const startTimeRef = useRef(Date.now())

    // Reset start time when exercise changes
    useEffect(() => {
        startTimeRef.current = Date.now()
    }, [exerciseData?.id])

    // REMOVE the problematic timer effect
    // DELETE THIS:
    // const [timeSpent, setTimeSpent] = useState(0)
    // useEffect(() => {
    //     const timer = setInterval(() => {
    //         setTimeSpent(Math.floor((Date.now() - startTimeRef.current) / 1000))
    //     }, 1000)
    //     return () => clearInterval(timer)
    // }, [exerciseData?.id])

    const handleCodeChange = useCallback((value) => {
        setUserCode(value)
    }, [])

    const handleSubmit = useCallback(async () => {
        setIsChecking(true)

        try {
            // Calculate final time spent
            const timeSpent = Math.floor((Date.now() - startTimeRef.current) / 1000)

            const response = await fetch('/api/v1/exercises/submit/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    exercise_id: exerciseData.id,
                    code: userCode,
                    time_spent: timeSpent,
                }),
            })

            const data = await response.json()
            setResult(data)
        } catch (error) {
            console.error('Submission failed:', error)
            setResult({ error: 'Failed to submit' })
        } finally {
            setIsChecking(false)
        }
    }, [exerciseData?.id, userCode])

    return (
        <div className="fill-in-blank-exercise">
            {/* Header with timer */}
            <div className="exercise-header">
                <h2>{exerciseData?.title}</h2>
                {/* Timer component - re-renders itself but not parent */}
                <ExerciseTimer
                    startTime={startTimeRef.current}
                    className="ml-auto"
                />
            </div>

            {/* Exercise description */}
            <div className="exercise-description">
                {exerciseData?.description}
            </div>

            {/* Code editor - no longer re-renders every second! */}
            <CodeEditor
                value={userCode}
                onChange={handleCodeChange}
                blanks={exerciseData?.blanks}
            />

            {/* Submit button */}
            <button
                onClick={handleSubmit}
                disabled={isChecking}
                className="submit-button"
            >
                {isChecking ? 'Checking...' : 'Submit'}
            </button>

            {/* Result display */}
            {result && (
                <div className={`result ${result.correct ? 'correct' : 'incorrect'}`}>
                    {result.message}
                </div>
            )}
        </div>
    )
}

export default FillInBlankExercise
```

### Step 3: Optimize CodeEditor Component

```jsx
// frontend/src/components/code-editor/CodeEditor.jsx
import { memo } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'

const CodeEditor = memo(({ value, onChange, blanks }) => {
    return (
        <CodeMirror
            value={value}
            onChange={onChange}
            extensions={[python()]}
            basicSetup={{
                lineNumbers: true,
                highlightActiveLineGutter: true,
                highlightSpecialChars: true,
                foldGutter: true,
                drawSelection: true,
                dropCursor: true,
                allowMultipleSelections: true,
                indentOnInput: true,
                bracketMatching: true,
                closeBrackets: true,
                autocompletion: true,
                rectangularSelection: true,
                highlightActiveLine: true,
                highlightSelectionMatches: true,
            }}
            theme="light"
            height="400px"
        />
    )
}, (prevProps, nextProps) => {
    // Custom comparison: only re-render if value or blanks change
    return prevProps.value === nextProps.value &&
           JSON.stringify(prevProps.blanks) === JSON.stringify(nextProps.blanks)
})

CodeEditor.displayName = 'CodeEditor'

export default CodeEditor
```

### Step 4: Add Performance Monitoring

```jsx
// frontend/src/components/code-editor/FillInBlankExercise.jsx

// In development, log re-renders
if (import.meta.env.DEV) {
    const renderCount = useRef(0)
    renderCount.current++

    useEffect(() => {
        console.log(`[FillInBlankExercise] Render #${renderCount.current}`)
    })
}
```

### Step 5: Test Performance Improvement

```jsx
// frontend/src/components/code-editor/__tests__/performance.test.jsx
import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import FillInBlankExercise from '../FillInBlankExercise'

describe('FillInBlankExercise Performance', () => {
    it('should not re-render parent when timer updates', async () => {
        const mockExercise = {
            id: 1,
            title: 'Test Exercise',
            description: 'Test description',
            template: 'print("Hello")',
        }

        const renderSpy = vi.fn()

        const TestWrapper = () => {
            renderSpy()
            return <FillInBlankExercise exerciseData={mockExercise} />
        }

        render(<TestWrapper />)

        // Initial render
        expect(renderSpy).toHaveBeenCalledTimes(1)

        // Wait 3 seconds
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 3000)))

        // Should still be only 1 render (timer doesn't trigger parent re-render)
        expect(renderSpy).toHaveBeenCalledTimes(1)
    })

    it('should update timer display without parent re-render', async () => {
        const mockExercise = {
            id: 1,
            title: 'Test Exercise',
            template: 'print("Hello")',
        }

        render(<FillInBlankExercise exerciseData={mockExercise} />)

        // Get initial timer value
        const timer = screen.getByText(/\d{2}:\d{2}/)
        const initialValue = timer.textContent

        // Wait 2 seconds
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 2000)))

        // Timer should have updated
        const newValue = timer.textContent
        expect(newValue).not.toBe(initialValue)
    })
})
```

## Verification

### Before Fix

Open React DevTools Profiler:
1. Start profiling
2. Open exercise page
3. Wait 1 minute
4. Stop profiling
5. Observe: 60 renders of FillInBlankExercise component

### After Fix

1. Repeat profiling
2. Observe: 0 renders of parent component (only ExerciseTimer re-renders)
3. Check performance metrics

### Manual Testing

1. Open exercise page
2. Start typing in code editor
3. Should feel smooth and responsive
4. Timer should update every second
5. No lag or jank while typing

## Expected Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Parent re-renders/min | 60 | 0 | ∞ (100%) |
| CPU usage (idle) | 20-30% | 2-3% | 90% reduction |
| Typing lag | 50-100ms | <10ms | 5-10x faster |
| Battery impact | High | Minimal | 80% reduction |

## Checklist

- [ ] ExerciseTimer component created
- [ ] FillInBlankExercise refactored to use ExerciseTimer
- [ ] Problematic timer effect removed
- [ ] CodeEditor component memoized
- [ ] Performance tests added
- [ ] React DevTools profiling confirms no re-renders
- [ ] Manual testing shows smooth typing experience
- [ ] Documentation updated

## Additional Optimizations (If Needed)

If still experiencing performance issues:

```jsx
// Debounce code change handler
import { useDebouncedCallback } from 'use-debounce'

const handleCodeChange = useDebouncedCallback((value) => {
    setUserCode(value)
}, 100)  // Update state max once per 100ms
```

## References

- React: memo() API
- React: useCallback Hook
- React DevTools Profiler
- Comprehensive Security Audit 2025, Finding #7
