import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { oneDark } from '@codemirror/theme-one-dark'
import { EditorView, Decoration, WidgetType, ViewPlugin, MatchDecorator } from '@codemirror/view'
import { useTheme } from '../../contexts/ThemeContext'

// BlankRegistry for managing keyboard navigation between blanks
class BlankRegistry {
  constructor() {
    this.blanks = new Map()  // blankId → input element
    this.order = []  // Sorted blank IDs
    this.submitCallback = null  // Callback to submit exercise
  }

  register(blankId, inputElement) {
    this.blanks.set(blankId, inputElement)
    // Convert blankId to number for proper sorting
    const numericId = parseInt(blankId, 10)
    if (!this.order.includes(numericId)) {
      this.order.push(numericId)
      this.order.sort((a, b) => a - b)  // Numeric sort
    }
  }

  unregister(blankId) {
    const numericId = parseInt(blankId, 10)
    this.blanks.delete(blankId)
    this.order = this.order.filter(id => id !== numericId)
  }

  getNext(currentBlankId) {
    const numericId = parseInt(currentBlankId, 10)
    const currentIndex = this.order.indexOf(numericId)
    if (currentIndex === -1 || currentIndex === this.order.length - 1) {
      return null
    }
    const nextBlankId = this.order[currentIndex + 1].toString()
    return this.blanks.get(nextBlankId)
  }

  getPrev(currentBlankId) {
    const numericId = parseInt(currentBlankId, 10)
    const currentIndex = this.order.indexOf(numericId)
    if (currentIndex === -1 || currentIndex === 0) {
      return null
    }
    const prevBlankId = this.order[currentIndex - 1].toString()
    return this.blanks.get(prevBlankId)
  }

  clear() {
    this.blanks.clear()
    this.order = []
  }

  setSubmitCallback(callback) {
    this.submitCallback = callback
  }

  submit() {
    if (this.submitCallback) {
      this.submitCallback()
    }
  }
}

// Dynamic BlankWidget that adapts to theme with keyboard navigation
class BlankWidget extends WidgetType {
  constructor(placeholder, isDark = true, onFillBlankChange = null, blankRegistry = null) {
    super()
    this.placeholder = placeholder
    this.isDark = isDark
    this.onFillBlankChange = onFillBlankChange
    this.blankRegistry = blankRegistry
    this.inputElement = null
    this.eventListeners = []
  }

  eq(other) {
    return other.placeholder === this.placeholder && other.isDark === this.isDark
  }

  // Helper method to add event listeners and track them for cleanup
  addEventListenerTracked(element, event, handler) {
    element.addEventListener(event, handler)
    this.eventListeners.push({ element, event, handler })
  }

  toDOM() {
    const input = document.createElement("input")
    input.type = "text"
    input.placeholder = this.placeholder
    input.classList.add("cm-blank-input")
    const blankId = this.placeholder.replace("BLANK_", "")
    input.dataset.blankId = blankId

    // ✅ ARIA attributes for accessibility
    input.setAttribute('role', 'textbox')
    input.setAttribute('aria-label', `Fill in blank ${blankId}`)
    input.setAttribute('aria-required', 'true')
    input.setAttribute('aria-describedby', 'blank-instructions')

    // Store reference for cleanup
    this.inputElement = input

    // Apply theme-appropriate styling
    const darkStyles = `
      background: #1e1e1e;
      border: 2px solid #3c3c3c;
      color: #d4d4d4;
    `
    const lightStyles = `
      background: #ffffff;
      border: 2px solid #d4d4d4;
      color: #333333;
    `

    input.style.cssText = `
      ${this.isDark ? darkStyles : lightStyles}
      border-radius: 4px;
      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
      font-size: 14px;
      padding: 4px 8px;
      min-width: 120px;
      outline: none;
      margin: 0 2px;
      transition: all 0.2s;
    `

    // Ensure input can receive focus and events
    input.tabIndex = 0

    // Register with BlankRegistry for keyboard navigation
    if (this.blankRegistry) {
      this.blankRegistry.register(blankId, input)
    }
    
    // ✅ Enhanced keyboard navigation
    this.addEventListenerTracked(input, 'keydown', (e) => {
      this.handleKeyDown(e, input)
      e.stopPropagation()
    })
    this.addEventListenerTracked(input, 'keyup', (e) => {
      e.stopPropagation()
    })
    this.addEventListenerTracked(input, 'keypress', (e) => {
      e.stopPropagation()
    })
    
    // Handle input changes
    this.addEventListenerTracked(input, 'input', (e) => {
      e.stopPropagation()
      
      // Notify parent component of the change
      if (this.onFillBlankChange) {
        const blankId = this.placeholder.replace("BLANK_", "")
        const value = e.target.value
        
        // Collect all current values from all inputs
        const allInputs = document.querySelectorAll('.cm-blank-input')
        const allValues = {}
        allInputs.forEach(inp => {
          const id = inp.dataset.blankId
          allValues[id] = inp.value
        })
        
        this.onFillBlankChange(blankId, value, allValues)
      }
    })
    
    // Mouse events
    this.addEventListenerTracked(input, 'mousedown', (e) => {
      e.stopPropagation()
    })
    this.addEventListenerTracked(input, 'click', (e) => {
      e.stopPropagation()
    })
    
    // ✅ Enhanced focus indicators (WCAG 2.4.7 Level AA)
    this.addEventListenerTracked(input, 'focus', (e) => {
      e.stopPropagation()
      e.target.style.outline = '3px solid #0066cc'
      e.target.style.outlineOffset = '2px'
      e.target.style.borderColor = '#0066cc'
      e.target.style.boxShadow = '0 0 0 4px rgba(0, 102, 204, 0.2)'
      e.target.style.background = this.isDark ? '#1a3a52' : '#f0f8ff'
    })
    this.addEventListenerTracked(input, 'blur', (e) => {
      const borderColor = this.isDark ? '#3c3c3c' : '#d4d4d4'
      const background = this.isDark ? '#1e1e1e' : '#ffffff'
      e.target.style.outline = 'none'
      e.target.style.outlineOffset = '0'
      e.target.style.borderColor = borderColor
      e.target.style.boxShadow = 'none'
      e.target.style.background = background
    })

    return input
  }

  handleKeyDown(e, input) {
    const { key, shiftKey, ctrlKey, metaKey } = e
    const blankId = input.dataset.blankId

    // Tab or Right Arrow at end → Move to next blank
    if (key === 'Tab' && !shiftKey) {
      e.preventDefault()
      this.focusNextBlank(blankId)
    }
    // Shift+Tab or Left Arrow at start → Move to previous blank
    else if (key === 'Tab' && shiftKey) {
      e.preventDefault()
      this.focusPrevBlank(blankId)
    }
    // Right Arrow at end of text → Move to next blank
    else if (key === 'ArrowRight' && input.selectionStart === input.value.length && !ctrlKey && !metaKey) {
      e.preventDefault()
      this.focusNextBlank(blankId)
    }
    // Left Arrow at start of text → Move to previous blank
    else if (key === 'ArrowLeft' && input.selectionStart === 0 && !ctrlKey && !metaKey) {
      e.preventDefault()
      this.focusPrevBlank(blankId)
    }
    // Enter → Submit exercise
    else if (key === 'Enter') {
      e.preventDefault()
      this.submitExercise()
    }
    // Escape → Clear current blank
    else if (key === 'Escape') {
      e.preventDefault()
      input.value = ''
      if (this.onFillBlankChange) {
        // Update all values
        const allInputs = document.querySelectorAll('.cm-blank-input')
        const allValues = {}
        allInputs.forEach(inp => {
          const id = inp.dataset.blankId
          allValues[id] = inp.value
        })
        this.onFillBlankChange(blankId, '', allValues)
      }
    }
  }

  focusNextBlank(currentBlankId) {
    if (!this.blankRegistry) return

    const nextBlank = this.blankRegistry.getNext(currentBlankId)
    if (nextBlank) {
      nextBlank.focus()
      nextBlank.select()  // Select all text for easy replacement
    } else {
      // Last blank → focus submit button
      this.focusSubmitButton()
    }
  }

  focusPrevBlank(currentBlankId) {
    if (!this.blankRegistry) return

    const prevBlank = this.blankRegistry.getPrev(currentBlankId)
    if (prevBlank) {
      prevBlank.focus()
      prevBlank.select()
    }
  }

  submitExercise() {
    if (this.blankRegistry) {
      this.blankRegistry.submit()
    }
  }

  focusSubmitButton() {
    const submitBtn = document.querySelector('[data-testid="submit-button"]') ||
                      document.querySelector('button[type="submit"]')
    submitBtn?.focus()
  }

  // Cleanup method called when widget is destroyed
  destroy() {
    // Unregister from BlankRegistry
    if (this.blankRegistry && this.inputElement) {
      const blankId = this.inputElement.dataset.blankId
      this.blankRegistry.unregister(blankId)
    }

    // Remove all tracked event listeners
    this.eventListeners.forEach(({ element, event, handler }) => {
      element.removeEventListener(event, handler)
    })
    this.eventListeners = []
    this.inputElement = null
  }

  ignoreEvent(event) {
    // Allow all events on input elements
    return false
  }
}

// Dynamic matcher that adapts to theme with BlankRegistry
const createBlankMatcher = (isDark, onFillBlankChange, blankRegistry) => new MatchDecorator({
  // Match pattern like {{BLANK_1}} where 1 is any number
  regexp: /\{\{BLANK_(\d+)\}\}/g,
  decoration: match => Decoration.replace({
    widget: new BlankWidget(`BLANK_${match[1]}`, isDark, onFillBlankChange, blankRegistry),
    inclusive: false
  })
})

// Dynamic ViewPlugin that adapts to theme with BlankRegistry
const createBlankPlugin = (isDark, onFillBlankChange, blankRegistry) => {
  const matcher = createBlankMatcher(isDark, onFillBlankChange, blankRegistry)
  
  return ViewPlugin.fromClass(class {
    constructor(view) {
      this.decorations = matcher.createDeco(view)
    }
    
    update(update) {
      if (update.docChanged || update.viewportChanged) {
        this.decorations = matcher.updateDeco(update, this.decorations)
      }
    }
  }, {
    decorations: instance => instance.decorations,
    
    // Provide CSS used by all blank widgets with accessibility support
    provide: plugin => EditorView.baseTheme({
      ".cm-blank-input": {
        transition: "all 0.2s",
      },
      ".cm-blank-input.correct": {
        borderColor: "#10B981 !important", // Green for correct answers
      },
      ".cm-blank-input.incorrect": {
        borderColor: "#EF4444 !important", // Red for incorrect answers
      },
      // ✅ High contrast mode support
      "@media (prefers-contrast: high)": {
        ".cm-blank-input:focus": {
          outline: "4px solid currentColor !important",
          outlineOffset: "2px !important",
        }
      },
      // ✅ Reduced motion support
      "@media (prefers-reduced-motion: reduce)": {
        ".cm-blank-input": {
          transition: "none !important",
        }
      }
    })
  })
}

const InteractiveCodeEditor = ({
  value = '',
  onChange = () => {},
  language = 'python',
  theme = 'dark',
  onFillBlankChange = () => {},
  readOnly = false,
  className = '',
  onValidate = null,  // Callback for validate button
  ...props
}) => {
  // Get theme from context
  const { theme: contextTheme } = useTheme()
  const isDark = contextTheme === 'dark'

  // Create BlankRegistry instance (persists across renders)
  const blankRegistryRef = useRef(new BlankRegistry())

  // Set submit callback when validate function changes
  useEffect(() => {
    if (onValidate) {
      blankRegistryRef.current.setSubmitCallback(onValidate)
    }
  }, [onValidate])

  // Clear registry when value changes (new template)
  useEffect(() => {
    blankRegistryRef.current.clear()
  }, [value])

  // Language extensions mapping
  const languageExtensions = {
    python: python(),
    javascript: javascript(),
  }

  // Memoize extensions to avoid recreating on every render
  const extensions = useMemo(() => {
    // Create theme-responsive blank plugin with BlankRegistry
    const blankPlugin = createBlankPlugin(isDark, onFillBlankChange, blankRegistryRef.current)
    
    // Additional theme overrides to ensure proper theming
    const customTheme = EditorView.theme({
      "&": {
        backgroundColor: isDark ? "#1e1e1e" : "#ffffff",
        color: isDark ? "#d4d4d4" : "#24292e"
      },
      ".cm-content": {
        cursor: "default", // Show template is not editable
        backgroundColor: isDark ? "#1e1e1e" : "#ffffff",
        color: isDark ? "#d4d4d4" : "#24292e",
        padding: "10px"
      },
      ".cm-editor": {
        backgroundColor: isDark ? "#1e1e1e" : "#ffffff",
        fontSize: "14px"
      },
      ".cm-focused": {
        outline: "none"
      },
      ".cm-scroller": {
        backgroundColor: isDark ? "#1e1e1e" : "#ffffff",
        color: isDark ? "#d4d4d4" : "#24292e"
      },
      ".cm-blank-input": {
        cursor: "text !important" // But inputs are editable
      }
    })
    
    return [
      languageExtensions[language] || languageExtensions.python,
      isDark ? oneDark : [], // Use oneDark only in dark mode
      customTheme, // Our custom theme overrides
      blankPlugin, // Our blank widget plugin
      EditorView.editable.of(false) // Template is READ-ONLY
    ].filter(Boolean)
  }, [language, isDark, languageExtensions, onFillBlankChange])

  return (
    <div className={`interactive-code-editor ${className}`}>
      <CodeMirror
        value={value}
        onChange={onChange}
        extensions={extensions}
        theme={isDark ? 'dark' : 'light'} // Explicitly set theme prop for @uiw/react-codemirror
        basicSetup={true} // Enable basicSetup like working version
        {...props}
      />
    </div>
  )
}

// Memoize component to prevent unnecessary re-renders
// Only re-render when value or onFillBlankChange actually changes
export default React.memo(InteractiveCodeEditor, (prevProps, nextProps) => {
  // Return true if props are equal (component should NOT re-render)
  // Return false if props are different (component SHOULD re-render)
  return (
    prevProps.value === nextProps.value &&
    prevProps.onChange === nextProps.onChange &&
    prevProps.language === nextProps.language &&
    prevProps.readOnly === nextProps.readOnly &&
    prevProps.className === nextProps.className &&
    prevProps.onFillBlankChange === nextProps.onFillBlankChange
  )
})