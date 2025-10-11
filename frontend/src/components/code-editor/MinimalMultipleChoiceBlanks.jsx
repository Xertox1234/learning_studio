import React, { useMemo, useState, useCallback } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { java } from '@codemirror/lang-java'
import { cpp } from '@codemirror/lang-cpp'
import { html } from '@codemirror/lang-html'
import { css } from '@codemirror/lang-css'
import { oneDark } from '@codemirror/theme-one-dark'
import { EditorView, Decoration, WidgetType, ViewPlugin, MatchDecorator } from '@codemirror/view'
import { CheckCircle, XCircle, Sparkles } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import SlideOutDrawer from './SlideOutDrawer'

// Minimal Multiple Choice Widget for dropdowns
class MinimalChoiceWidget extends WidgetType {
  constructor(blankId, choices, isDark, selectedValue = '', isCorrect = null, onSelectionChange = null) {
    super()
    this.blankId = blankId
    this.choices = choices
    this.isDark = isDark
    this.selectedValue = selectedValue
    this.isCorrect = isCorrect
    this.onSelectionChange = onSelectionChange
  }

  eq(other) {
    return other.blankId === this.blankId && 
           other.isDark === this.isDark && 
           other.selectedValue === this.selectedValue &&
           other.isCorrect === this.isCorrect
  }

  toDOM() {
    const wrapper = document.createElement("span")
    wrapper.className = "inline-block relative"
    
    const select = document.createElement("select")
    select.className = `cm-choice-select text-sm px-1 py-0 border-b-2 bg-transparent outline-none transition-colors appearance-none cursor-pointer ${
      this.isCorrect === true 
        ? 'border-green-500 text-green-600' 
        : this.isCorrect === false 
        ? 'border-red-500 text-red-600'
        : this.isDark 
        ? 'border-gray-500 text-gray-300 focus:border-blue-400' 
        : 'border-gray-400 text-gray-700 focus:border-blue-600'
    }`
    
    // Add default option
    const defaultOption = document.createElement("option")
    defaultOption.value = ""
    defaultOption.textContent = "?"
    defaultOption.disabled = true
    defaultOption.selected = !this.selectedValue
    select.appendChild(defaultOption)
    
    // Add choices
    this.choices.forEach((choice, index) => {
      const option = document.createElement("option")
      option.value = choice
      option.textContent = choice
      option.selected = this.selectedValue === choice
      select.appendChild(option)
    })

    // Calculate width based on longest choice
    const maxLength = Math.max(...this.choices.map(c => c.length), 1)
    select.style.width = `${maxLength + 2}ch`
    select.style.minWidth = '3ch'
    select.style.maxWidth = '15ch'

    // Add event listener for selection changes
    if (this.onSelectionChange) {
      select.addEventListener('change', (e) => {
        this.onSelectionChange(this.blankId, e.target.value)
      })
    }

    // Add small dropdown arrow indicator
    const arrow = document.createElement("span")
    arrow.innerHTML = "▼"
    arrow.className = `absolute right-0 top-0 text-xs pointer-events-none ${
      this.isDark ? 'text-gray-500' : 'text-gray-400'
    }`
    arrow.style.fontSize = '8px'
    arrow.style.marginTop = '1px'
    
    wrapper.appendChild(select)
    wrapper.appendChild(arrow)
    return wrapper
  }

  ignoreEvent() {
    return true
  }
}

/**
 * MinimalMultipleChoiceBlanks - Ultra-minimal multiple choice fill-in-the-blanks
 * Looks identical to ReadOnlyCodeBlock but with dropdown choice fields
 */
const MinimalMultipleChoiceBlanks = ({ 
  template = '',
  choices = {}, // { "1": ["option1", "option2", "option3"], "2": ["optionA", "optionB"] }
  solutions = {}, // { "1": "option1", "2": "optionA" }
  language = 'python',
  title = '',
  aiExplanations = {},
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

  // Handle selection changes
  const handleSelectionChange = useCallback((blankId, value) => {
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
      const userAnswer = answers[blankId] || ''
      const correctAnswer = solutions[blankId]
      
      newValidation[blankId] = userAnswer === correctAnswer
    })
    
    setValidation(newValidation)
    setHasChecked(true)
    
    // Show output drawer immediately if all correct
    const allAnswersCorrect = Object.values(newValidation).every(isCorrect => isCorrect === true)
    if (allAnswersCorrect) {
      setShowOutput(true)
    }
    
    return newValidation
  }, [answers, solutions])

  // Create widget decorator
  const choiceDecorator = useMemo(() => {
    return new MatchDecorator({
      regexp: /\{\{CHOICE_(\d+)\}\}/g,
      decoration: (match, view, pos) => {
        const blankId = match[1]
        const blankChoices = choices[blankId] || ['option1', 'option2']
        const selectedValue = answers[blankId] || ''
        const isCorrect = validation[blankId]
        
        return Decoration.replace({
          widget: new MinimalChoiceWidget(
            blankId, 
            blankChoices, 
            isDark, 
            selectedValue, 
            isCorrect,
            handleSelectionChange
          ),
          inclusive: true
        })
      }
    })
  }, [isDark, choices, answers, validation, handleSelectionChange])

  // Create decorations plugin
  const decorationsPlugin = useMemo(() => {
    return ViewPlugin.fromClass(
      class {
        constructor(view) {
          this.decorations = choiceDecorator.createDeco(view)
        }
        
        update(update) {
          this.decorations = choiceDecorator.updateDeco(update, this.decorations)
        }
      },
      {
        decorations: v => v.decorations
      }
    )
  }, [choiceDecorator])

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

  // Generate mock output for multiple choice
  const generateMockOutput = () => {
    if (!hasChecked || !allCorrect) return ''
    
    switch (language.toLowerCase()) {
      case 'python':
        return `Output:\nFantastic! Your code choices result in:\n"Welcome to Python Learning!"`
      case 'javascript':
      case 'js':
        return `Output:\nPerfect! Your JavaScript selections output:\n"Welcome to Python Learning!"`
      case 'java':
        return `Output:\nExcellent! Your Java choices produce:\nWelcome to Python Learning!`
      default:
        return `Output:\nGreat choices! Your code runs successfully!`
    }
  }

  // Get AI explanation for answers
  const getAiExplanation = () => {
    if (allCorrect) {
      return "Excellent! You've chosen all the correct options. These choices work together to create proper, functional code."
    }
    
    const incorrectBlanks = Object.entries(validation).filter(([_, isCorrect]) => isCorrect === false)
    if (incorrectBlanks.length === 0) return ''
    
    const blankId = incorrectBlanks[0][0]
    const correctAnswer = solutions[blankId]
    const selectedAnswer = answers[blankId]
    
    return aiExplanations[blankId] || 
           `For choice ${blankId}, "${correctAnswer}" is the correct option. ${selectedAnswer ? `"${selectedAnswer}" is not quite right because it doesn't fit the context properly.` : 'Make sure to select an option that makes logical sense in this code context.'}`
  }

  return (
    <div className={`minimal-multiple-choice-blanks relative ${className}`}>
      {/* CodeMirror Editor with multiple choice dropdowns */}
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

        {/* Floating Check Choices Button */}
        <button
          onClick={validateAnswers}
          className={`absolute bottom-2 right-2 flex items-center space-x-1 px-3 py-1 text-sm font-medium rounded transition-all duration-200 shadow-lg hover:shadow-xl ${
            isDark
              ? 'bg-purple-600 hover:bg-purple-700 text-white'
              : 'bg-purple-600 hover:bg-purple-700 text-white'
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
              <span>Review</span>
            </>
          ) : (
            <span>Check Choices</span>
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

      {/* AI Explanation Panel for Incorrect Answers */}
      {showAiHelp && hasIncorrect && (
        <div className={`mt-3 p-3 rounded-lg border ${
          isDark 
            ? 'bg-orange-950/30 border-orange-800/50 text-orange-100' 
            : 'bg-orange-50 border-orange-200 text-orange-800'
        }`}>
          <div className="flex items-start space-x-2">
            <Sparkles className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-medium mb-1">AI Explanation</h4>
              <p className="text-xs leading-relaxed">{getAiExplanation()}</p>
            </div>
          </div>
        </div>
      )}

      {/* AI Assistance Panel for Output */}
      {showAiHelp && allCorrect && (
        <div className={`mt-2 p-4 rounded-lg border ${
          isDark 
            ? 'bg-green-950/30 border-green-800/50 text-green-100' 
            : 'bg-green-50 border-green-200 text-green-800'
        }`}>
          <div className="flex items-start space-x-2">
            <Sparkles className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-medium mb-1">AI Explanation</h4>
              <p className="text-xs leading-relaxed">
                Outstanding work! You've made all the correct choices for this exercise. 
                Your understanding of {language} syntax and logic is progressing excellently. 
                These selections demonstrate solid programming fundamentals.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MinimalMultipleChoiceBlanks