import React, { useMemo, useState, useCallback, useEffect, useRef } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { java } from '@codemirror/lang-java'
import { cpp } from '@codemirror/lang-cpp'
import { html } from '@codemirror/lang-html'
import { css } from '@codemirror/lang-css'
import { oneDark } from '@codemirror/theme-one-dark'
import { EditorView, Decoration, WidgetType, ViewPlugin, MatchDecorator } from '@codemirror/view'
import { CheckCircle, XCircle, Sparkles, Play } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import SlideOutDrawer from './SlideOutDrawer'

// Minimal Blank Widget for fill-in-blanks
class MinimalBlankWidget extends WidgetType {
  constructor(blankId, placeholder, isDark, value = '', isCorrect = null, onInputChange = null) {
    super()
    this.blankId = blankId
    this.placeholder = placeholder
    this.isDark = isDark
    this.value = value
    this.isCorrect = isCorrect
    this.onInputChange = onInputChange
  }

  eq(other) {
    return other.blankId === this.blankId && 
           other.isDark === this.isDark && 
           other.value === this.value &&
           other.isCorrect === this.isCorrect &&
           other.placeholder === this.placeholder
  }

  toDOM() {
    const wrapper = document.createElement("span")
    wrapper.className = "inline-block relative"
    
    const input = document.createElement("input")
    input.type = "text"
    input.value = this.value
    input.placeholder = this.placeholder
    input.classList.add("cm-blank-input")
    input.dataset.blankId = this.blankId
    
    // Apply theme-appropriate styling (same as full-size editor)
    const darkStyles = `
      background: #1e1e1e;
      border: 1px solid #3c3c3c;
      color: #d4d4d4;
    `
    const lightStyles = `
      background: #ffffff;
      border: 1px solid #d4d4d4;
      color: #333333;
    `
    
    // Apply validation-specific styling
    let validationStyles = ''
    if (this.isCorrect === true) {
      validationStyles = `
        border-color: #10B981 !important;
        color: ${this.isDark ? '#34D399' : '#059669'};
      `
    } else if (this.isCorrect === false) {
      validationStyles = `
        border-color: #EF4444 !important;
        color: ${this.isDark ? '#F87171' : '#DC2626'};
      `
    }
    
    input.style.cssText = `
      ${this.isDark ? darkStyles : lightStyles}
      ${validationStyles}
      border-radius: 4px;
      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
      font-size: 14px;
      padding: 4px 8px;
      min-width: 120px;
      outline: none;
      margin: 0 2px;
      transition: border-color 0.2s, box-shadow 0.2s;
    `
    
    // Set width based on content or placeholder (but respect min-width)
    const width = Math.max(this.value.length || this.placeholder.length || 8, 4)
    const calculatedWidth = `${width + 2}ch`
    if (parseFloat(calculatedWidth) > 120) { // Only override if larger than min-width
      input.style.width = calculatedWidth
    }
    input.style.maxWidth = '20ch'

    // Add event listeners
    if (this.onInputChange) {
      input.addEventListener('input', (e) => {
        this.onInputChange(this.blankId, e.target.value)
      })
    }
    
    // Focus/blur styling (same as full-size editor)
    input.addEventListener('focus', (e) => {
      e.stopPropagation()
      e.target.style.borderColor = '#007acc'
      e.target.style.boxShadow = '0 0 0 2px rgba(0, 122, 204, 0.2)'
    })
    
    input.addEventListener('blur', (e) => {
      const borderColor = this.isCorrect === true 
        ? '#10B981' 
        : this.isCorrect === false 
        ? '#EF4444' 
        : this.isDark 
        ? '#3c3c3c' 
        : '#d4d4d4'
      e.target.style.borderColor = borderColor
      e.target.style.boxShadow = 'none'
    })
    
    // Prevent event bubbling
    input.addEventListener('keydown', (e) => e.stopPropagation())
    input.addEventListener('keyup', (e) => e.stopPropagation())
    input.addEventListener('keypress', (e) => e.stopPropagation())
    input.addEventListener('mousedown', (e) => e.stopPropagation())
    input.addEventListener('click', (e) => e.stopPropagation())

    wrapper.appendChild(input)
    return wrapper
  }

  ignoreEvent() {
    return true
  }
}

/**
 * MinimalFillBlankEditor - Ultra-minimal fill-in-the-blanks code editor
 * Looks identical to ReadOnlyCodeBlock but with interactive input fields
 */
const MinimalFillBlankEditor = ({ 
  template = '',
  solutions = {},
  alternativeSolutions = {},
  language = 'python',
  title = '',
  aiHints = {},
  className = '',
  showLineNumbers = true,
  onAnswersChange = null,
  ...props 
}) => {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [answers, setAnswers] = useState({})
  const [validation, setValidation] = useState({})
  const [showAiHelp, setShowAiHelp] = useState(false)
  const [hasChecked, setHasChecked] = useState(false)
  const [showOutput, setShowOutput] = useState(false)
  
  // Language extensions mapping (same as ReadOnlyCodeBlock)
  const languageExtensions = useMemo(() => ({
    python: python(),
    javascript: javascript(),
    js: javascript(),
    java: java(),
    cpp: cpp(),
    'c++': cpp(),
    html: html(),
    css: css(),
    text: []
  }), [])

  const languageExtension = useMemo(() => {
    const normalizedLang = language.toLowerCase()
    return languageExtensions[normalizedLang] || languageExtensions.text
  }, [language, languageExtensions])

  // Handle input changes
  const handleInputChange = useCallback((blankId, value) => {
    setAnswers(prev => ({
      ...prev,
      [blankId]: value
    }))
    
    if (onAnswersChange) {
      onAnswersChange({
        ...answers,
        [blankId]: value
      })
    }
  }, [answers, onAnswersChange])

  // Validate answers
  const validateAnswers = useCallback(() => {
    const newValidation = {}
    
    Object.keys(solutions).forEach(blankId => {
      const userAnswer = (answers[blankId] || '').trim().toLowerCase()
      const correctAnswer = solutions[blankId].toLowerCase()
      const alternatives = alternativeSolutions[blankId] || []
      
      const isCorrect = userAnswer === correctAnswer || 
                       alternatives.some(alt => alt.toLowerCase() === userAnswer)
      
      newValidation[blankId] = isCorrect
    })
    
    setValidation(newValidation)
    setHasChecked(true)
    
    // Show output drawer immediately if all correct
    const allAnswersCorrect = Object.values(newValidation).every(isCorrect => isCorrect === true)
    if (allAnswersCorrect) {
      setShowOutput(true)
    }
    
    return newValidation
  }, [answers, solutions, alternativeSolutions])

  // Create widget decorator
  const blankDecorator = useMemo(() => {
    return new MatchDecorator({
      regexp: /\{\{BLANK_(\d+)\}\}/g,
      decoration: (match, view, pos) => {
        const blankId = match[1]
        const placeholder = `blank_${blankId}`
        const value = answers[blankId] || ''
        const isCorrect = validation[blankId]
        
        return Decoration.replace({
          widget: new MinimalBlankWidget(
            blankId, 
            placeholder, 
            isDark, 
            value, 
            isCorrect,
            handleInputChange
          ),
          inclusive: true
        })
      }
    })
  }, [isDark, answers, validation, handleInputChange])

  // Create decorations plugin
  const decorationsPlugin = useMemo(() => {
    return ViewPlugin.fromClass(
      class {
        constructor(view) {
          this.decorations = blankDecorator.createDeco(view)
        }
        
        update(update) {
          this.decorations = blankDecorator.updateDeco(update, this.decorations)
        }
      },
      {
        decorations: v => v.decorations
      }
    )
  }, [blankDecorator])

  // Create extensions with theme-aware styling (identical to ReadOnlyCodeBlock)
  const extensions = useMemo(() => {
    const customTheme = EditorView.theme({
      "&": {
        backgroundColor: isDark ? "#1e1e1e" : "#f8f9fa",
        border: isDark ? "1px solid #374151" : "1px solid #e5e7eb",
        borderRadius: "8px",
        fontSize: "14px",
        fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace"
      },
      ".cm-content": {
        backgroundColor: isDark ? "#1e1e1e" : "#f8f9fa",
        color: isDark ? "#d4d4d4" : "#1f2937",
        padding: "16px",
        cursor: "default",
        minHeight: "auto"
      },
      ".cm-editor": {
        backgroundColor: isDark ? "#1e1e1e" : "#f8f9fa"
      },
      ".cm-focused": {
        outline: "none"
      },
      ".cm-scroller": {
        backgroundColor: isDark ? "#1e1e1e" : "#f8f9fa",
        fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace"
      },
      ".cm-gutters": {
        backgroundColor: isDark ? "#262626" : "#f3f4f6",
        borderRight: isDark ? "1px solid #374151" : "1px solid #e5e7eb",
        color: isDark ? "#6b7280" : "#9ca3af"
      },
      ".cm-lineNumbers": {
        color: isDark ? "#6b7280" : "#9ca3af",
        fontSize: "13px"
      },
      ".cm-activeLine": {
        backgroundColor: "transparent"
      },
      ".cm-activeLineGutter": {
        backgroundColor: "transparent"
      }
    }, { dark: isDark })

    return [
      languageExtension,
      isDark ? oneDark : [],
      customTheme,
      EditorView.editable.of(false),
      EditorView.lineWrapping,
      decorationsPlugin,
      ...(showLineNumbers ? [] : [EditorView.theme({ ".cm-gutters": { display: "none" } })])
    ].filter(Boolean)
  }, [languageExtension, isDark, showLineNumbers, decorationsPlugin])

  // Check if all answers are correct
  const allCorrect = hasChecked && Object.values(validation).every(isCorrect => isCorrect === true)
  const hasIncorrect = hasChecked && Object.values(validation).some(isCorrect => isCorrect === false)

  // Generate mock output for fill-in-blank
  const generateMockOutput = () => {
    if (!hasChecked || !allCorrect) return ''
    
    switch (language.toLowerCase()) {
      case 'python':
        return `Output:\nGreat job! Your code would output:\n"Hello, Python Learning Studio!"`
      case 'javascript':
      case 'js':
        return `Output:\nPerfect! Your JavaScript would output:\n"Hello, Python Learning Studio!"`
      case 'java':
        return `Output:\nExcellent! Your Java program would output:\nHello, Python Learning Studio!`
      default:
        return `Output:\nWell done! Your code executed successfully!`
    }
  }

  // Get AI hint for incorrect answers
  const getAiHint = () => {
    const incorrectBlanks = Object.entries(validation).filter(([_, isCorrect]) => isCorrect === false)
    if (incorrectBlanks.length === 0) return ''
    
    const blankId = incorrectBlanks[0][0]
    return aiHints[blankId] || `Think about what should go in blank ${blankId}. The answer is related to the code's functionality.`
  }

  return (
    <div className={`minimal-fill-blank-editor relative ${className}`}>
      {/* CodeMirror Editor with fill-in-blanks */}
      <div className="relative">
        <CodeMirror
          value={template.trim()}
          extensions={extensions}
          theme={isDark ? 'dark' : 'light'}
          basicSetup={{
            lineNumbers: showLineNumbers,
            foldGutter: false,
            dropCursor: false,
            allowMultipleSelections: false,
            indentOnInput: false,
            bracketMatching: true,
            closeBracketsKeymap: false,
            searchKeymap: false,
            completionKeymap: false,
            lintKeymap: false
          }}
          readOnly={true}
          {...props}
        />

        {/* Floating Check Answers Button */}
        <button
          onClick={validateAnswers}
          className={`absolute bottom-2 right-2 flex items-center space-x-1 px-3 py-1 text-sm font-medium rounded transition-all duration-200 shadow-lg hover:shadow-xl ${
            isDark
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {allCorrect ? (
            <>
              <CheckCircle className="h-4 w-4" />
              <span>Perfect!</span>
            </>
          ) : hasIncorrect ? (
            <>
              <XCircle className="h-4 w-4" />
              <span>Try again</span>
            </>
          ) : (
            <span>Check Answers</span>
          )}
        </button>
      </div>

      {/* Output Drawer for Correct Answers */}
      {allCorrect && (
        <SlideOutDrawer
          isOpen={showOutput}
          onToggle={() => setShowOutput(!showOutput)}
          title="Output"
          className="mt-4"
        >
          <pre className={`text-sm font-mono p-3 rounded ${
            isDark ? 'bg-gray-900 text-green-400' : 'bg-white text-green-600'
          }`}>
            {generateMockOutput()}
          </pre>
          
          {/* AI Assistance Button */}
          <div className="mt-3 flex justify-end">
            <button
              onClick={() => setShowAiHelp(!showAiHelp)}
              className={`flex items-center space-x-1 px-2 py-1 text-xs rounded transition-colors ${
                isDark 
                  ? 'text-blue-400 hover:text-blue-300 hover:bg-gray-700' 
                  : 'text-blue-600 hover:text-blue-800 hover:bg-blue-50'
              }`}
            >
              <Sparkles className="h-3 w-3" />
              <span>AI Help</span>
            </button>
          </div>
        </SlideOutDrawer>
      )}

      {/* AI Hint Panel for Incorrect Answers */}
      {showAiHelp && hasIncorrect && (
        <div className={`mt-3 p-3 rounded-lg border ${
          isDark 
            ? 'bg-yellow-950/30 border-yellow-800/50 text-yellow-100' 
            : 'bg-yellow-50 border-yellow-200 text-yellow-800'
        }`}>
          <div className="flex items-start space-x-2">
            <Sparkles className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-medium mb-1">AI Hint</h4>
              <p className="text-xs leading-relaxed">{getAiHint()}</p>
            </div>
          </div>
        </div>
      )}

      {/* AI Assistance Panel for Output */}
      {showAiHelp && allCorrect && (
        <div className={`mt-2 p-4 rounded-lg border ${
          isDark 
            ? 'bg-blue-950/30 border-blue-800/50 text-blue-100' 
            : 'bg-blue-50 border-blue-200 text-blue-800'
        }`}>
          <div className="flex items-start space-x-2">
            <Sparkles className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-medium mb-1">AI Explanation</h4>
              <p className="text-xs leading-relaxed">
                Excellent work! You've successfully completed the fill-in-the-blank exercise. 
                Your understanding of {language} syntax is showing great progress. 
                The completed code demonstrates proper use of programming fundamentals.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MinimalFillBlankEditor