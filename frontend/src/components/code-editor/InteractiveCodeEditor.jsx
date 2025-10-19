import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { oneDark } from '@codemirror/theme-one-dark'
import { EditorView, Decoration, WidgetType, ViewPlugin, MatchDecorator } from '@codemirror/view'
import { useTheme } from '../../contexts/ThemeContext'

// Dynamic BlankWidget that adapts to theme
class BlankWidget extends WidgetType {
  constructor(placeholder, isDark = true, onFillBlankChange = null) {
    super()
    this.placeholder = placeholder
    this.isDark = isDark
    this.onFillBlankChange = onFillBlankChange
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
    input.dataset.blankId = this.placeholder.replace("BLANK_", "")
    
    // Store reference for cleanup
    this.inputElement = input
    
    // Apply theme-appropriate styling
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
    
    input.style.cssText = `
      ${this.isDark ? darkStyles : lightStyles}
      border-radius: 4px;
      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
      font-size: 14px;
      padding: 4px 8px;
      min-width: 120px;
      outline: none;
      margin: 0 2px;
    `
    
    // Ensure input can receive focus and events
    input.tabIndex = 0
    
    // Prevent all keyboard events from bubbling to CodeMirror
    this.addEventListenerTracked(input, 'keydown', (e) => {
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
    
    // Focus/blur for styling
    this.addEventListenerTracked(input, 'focus', (e) => {
      e.stopPropagation()
      e.target.style.borderColor = '#007acc'
      e.target.style.boxShadow = '0 0 0 2px rgba(0, 122, 204, 0.2)'
    })
    this.addEventListenerTracked(input, 'blur', (e) => {
      const borderColor = this.isDark ? '#3c3c3c' : '#d4d4d4'
      e.target.style.borderColor = borderColor
      e.target.style.boxShadow = 'none'
    })
    
    return input
  }

  // Cleanup method called when widget is destroyed
  destroy() {
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

// Dynamic matcher that adapts to theme
const createBlankMatcher = (isDark, onFillBlankChange) => new MatchDecorator({
  // Match pattern like {{BLANK_1}} where 1 is any number
  regexp: /\{\{BLANK_(\d+)\}\}/g,
  decoration: match => Decoration.replace({
    widget: new BlankWidget(`BLANK_${match[1]}`, isDark, onFillBlankChange),
    inclusive: false
  })
})

// Dynamic ViewPlugin that adapts to theme
const createBlankPlugin = (isDark, onFillBlankChange) => {
  const matcher = createBlankMatcher(isDark, onFillBlankChange)
  
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
    
    // Provide CSS used by all blank widgets
    provide: plugin => EditorView.baseTheme({
      ".cm-blank-input": {
        transition: "border-color 0.2s",
      },
      ".cm-blank-input.correct": {
        borderColor: "#10B981 !important", // Green for correct answers
      },
      ".cm-blank-input.incorrect": {
        borderColor: "#EF4444 !important", // Red for incorrect answers
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
  ...props 
}) => {
  // Get theme from context
  const { theme: contextTheme } = useTheme()
  const isDark = contextTheme === 'dark'
  
  // Language extensions mapping
  const languageExtensions = {
    python: python(),
    javascript: javascript(),
  }

  // Memoize extensions to avoid recreating on every render
  const extensions = useMemo(() => {
    // Create theme-responsive blank plugin
    const blankPlugin = createBlankPlugin(isDark, onFillBlankChange)
    
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