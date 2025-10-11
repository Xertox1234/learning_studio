import React, { useMemo, useState } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { java } from '@codemirror/lang-java'
import { cpp } from '@codemirror/lang-cpp'
import { html } from '@codemirror/lang-html'
import { css } from '@codemirror/lang-css'
import { oneDark } from '@codemirror/theme-one-dark'
import { EditorView } from '@codemirror/view'
import { Play, Sparkles } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import SlideOutDrawer from './SlideOutDrawer'

/**
 * RunButtonCodeEditor - A minimal interactive code editor that looks identical to ReadOnlyCodeBlock
 * but includes a floating Run button and shows mock output when executed
 */
const RunButtonCodeEditor = ({ 
  code = '', 
  language = 'python',
  title = '',
  mockOutput = '',
  aiExplanation = '',
  className = '',
  showLineNumbers = true,
  ...props 
}) => {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [showOutput, setShowOutput] = useState(false)
  const [showAiHelp, setShowAiHelp] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  
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
    text: [] // Plain text, no syntax highlighting
  }), [])

  // Get the appropriate language extension
  const languageExtension = useMemo(() => {
    const normalizedLang = language.toLowerCase()
    return languageExtensions[normalizedLang] || languageExtensions.text
  }, [language, languageExtensions])

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
      },
      ".cm-selectionBackground": {
        backgroundColor: isDark ? "#264f78" : "#add6ff"
      }
    }, { dark: isDark })

    return [
      languageExtension,
      isDark ? oneDark : [],
      customTheme,
      EditorView.editable.of(false), // Make read-only
      EditorView.lineWrapping,
      ...(showLineNumbers ? [] : [EditorView.theme({ ".cm-gutters": { display: "none" } })])
    ].filter(Boolean)
  }, [languageExtension, isDark, showLineNumbers])

  // Generate mock output based on language and code
  const generateMockOutput = () => {
    if (mockOutput) return mockOutput

    switch (language.toLowerCase()) {
      case 'python':
        return `Welcome to Python Learning Studio!
Let's start learning Python together!`
      case 'javascript':
      case 'js':
        return `Welcome to Python Learning Studio!
Let's start learning Python together!`
      case 'java':
        return `Welcome to Python Learning Studio!
Let's start learning Python together!`
      default:
        return `Output:
Program executed successfully!`
    }
  }

  // Handle run button click
  const handleRun = async () => {
    setIsRunning(true)
    
    // Simulate execution delay
    await new Promise(resolve => setTimeout(resolve, 800))
    
    setIsRunning(false)
    setShowOutput(true)
  }

  // Default AI explanation
  const getAiExplanation = () => {
    if (aiExplanation) return aiExplanation
    
    return "This code demonstrates a simple example in " + language + ". The program outputs text to the console, which is a fundamental concept in programming. Click 'Run' to see the expected output!"
  }

  return (
    <div className={`run-button-code-editor relative ${className}`}>
      {/* CodeMirror Editor - identical styling to ReadOnlyCodeBlock */}
      <div className="relative">
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
        
        {/* Floating Run Button */}
        <button
          onClick={handleRun}
          disabled={isRunning}
          className={`absolute bottom-2 right-2 flex items-center space-x-1 px-2 py-1 text-xs font-medium rounded transition-all duration-200 ${
            isRunning 
              ? 'bg-gray-400 text-gray-200 cursor-not-allowed' 
              : isDark
                ? 'bg-green-600 hover:bg-green-700 text-white shadow-lg hover:shadow-xl'
                : 'bg-green-600 hover:bg-green-700 text-white shadow-lg hover:shadow-xl'
          }`}
          title="Run code"
        >
          <Play className={`h-3 w-3 ${isRunning ? 'animate-pulse' : ''}`} />
          <span>{isRunning ? 'Running...' : 'Run'}</span>
        </button>
      </div>

      {/* Output Drawer */}
      {showOutput && (
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

      {/* AI Assistance Panel */}
      {showAiHelp && showOutput && (
        <div className={`mt-2 p-4 rounded-lg border ${
          isDark 
            ? 'bg-blue-950/30 border-blue-800/50 text-blue-100' 
            : 'bg-blue-50 border-blue-200 text-blue-800'
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
    </div>
  )
}

export default RunButtonCodeEditor