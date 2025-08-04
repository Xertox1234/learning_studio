import React, { useMemo } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { java } from '@codemirror/lang-java'
import { cpp } from '@codemirror/lang-cpp'
import { html } from '@codemirror/lang-html'
import { css } from '@codemirror/lang-css'
import { oneDark } from '@codemirror/theme-one-dark'
import { EditorView } from '@codemirror/view'
import { useTheme } from '../../contexts/ThemeContext'

/**
 * ReadOnlyCodeBlock - A CodeMirror 6 component for displaying syntax-highlighted code
 * in lessons. Supports multiple programming languages with proper theme integration.
 */
const ReadOnlyCodeBlock = ({ 
  code = '', 
  language = 'text',
  className = '',
  showLineNumbers = true,
  ...props 
}) => {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  
  // Language extensions mapping
  const languageExtensions = useMemo(() => ({
    python: python(),
    javascript: javascript(),
    js: javascript(),
    java: java(),
    cpp: cpp(),
    'c++': cpp(),
    html: html(),
    css: css(),
    text: [] // Plain text, no syntax highlighting
  }), [])

  // Get the appropriate language extension
  const languageExtension = useMemo(() => {
    const normalizedLang = language.toLowerCase()
    return languageExtensions[normalizedLang] || languageExtensions.text
  }, [language, languageExtensions])

  // Create extensions with theme-aware styling
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
        backgroundColor: "transparent" // Remove active line highlighting
      },
      ".cm-activeLineGutter": {
        backgroundColor: "transparent" // Remove active line gutter highlighting
      },
      ".cm-selectionBackground": {
        backgroundColor: isDark ? "#264f78" : "#add6ff" // Selection color
      }
    }, { dark: isDark })

    return [
      languageExtension,
      isDark ? oneDark : [], // Use oneDark theme in dark mode
      customTheme,
      EditorView.editable.of(false), // Make read-only
      EditorView.lineWrapping, // Enable line wrapping
      ...(showLineNumbers ? [] : [EditorView.theme({ ".cm-gutters": { display: "none" } })])
    ].filter(Boolean)
  }, [languageExtension, isDark, showLineNumbers])

  return (
    <div className={`read-only-code-block ${className}`}>
      <CodeMirror
        value={code.trim()}
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
    </div>
  )
}

export default ReadOnlyCodeBlock