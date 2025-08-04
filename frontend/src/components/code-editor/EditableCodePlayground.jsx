import React, { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { java } from '@codemirror/lang-java'
import { cpp } from '@codemirror/lang-cpp'
import { html } from '@codemirror/lang-html'
import { css } from '@codemirror/lang-css'
import { oneDark } from '@codemirror/theme-one-dark'
import { EditorView } from '@codemirror/view'
import { EditorState } from '@codemirror/state'
import { useTheme } from '../../contexts/ThemeContext'
import { Play, Save, Download, Upload, Settings, Terminal, Eye, EyeOff } from 'lucide-react'

/**
 * EditableCodePlayground - A fully editable CodeMirror 6 based playground
 * with execution, save/load functionality, and settings
 */
const EditableCodePlayground = ({
  initialCode = '',
  language = 'python',
  onSave = () => {},
  onExecute = () => {},
  className = '',
  enableFileOperations = true,
  enableAutoSave = true,
  enableMultipleLanguages = true
}) => {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  
  const [code, setCode] = useState(initialCode)
  const [currentLanguage, setCurrentLanguage] = useState(language)
  const [output, setOutput] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [settings, setSettings] = useState({
    theme: isDark ? 'dark' : 'light',
    fontSize: 14,
    wordWrap: false,
    showLineNumbers: true,
    showOutput: true,
    autoSave: enableAutoSave
  })
  const fileInputRef = useRef(null)

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
    const normalizedLang = currentLanguage.toLowerCase()
    return languageExtensions[normalizedLang] || languageExtensions.python
  }, [currentLanguage, languageExtensions])

  // Create extensions with theme-aware styling
  const extensions = useMemo(() => {
    const customTheme = EditorView.theme({
      "&": {
        backgroundColor: isDark ? "#1e1e1e" : "#ffffff",
        color: isDark ? "#d4d4d4" : "#24292e",
        fontSize: `${settings.fontSize}px`
      },
      ".cm-content": {
        backgroundColor: isDark ? "#1e1e1e" : "#ffffff",
        color: isDark ? "#d4d4d4" : "#24292e",
        padding: "16px",
        lineHeight: "1.5"
      },
      ".cm-editor": {
        backgroundColor: isDark ? "#1e1e1e" : "#ffffff",
        borderRadius: "8px",
        border: isDark ? "1px solid #3c3c3c" : "1px solid #e1e5e9"
      },
      ".cm-focused": {
        outline: isDark ? "2px solid #007acc" : "2px solid #0969da",
        outlineOffset: "-1px"
      },
      ".cm-scroller": {
        backgroundColor: isDark ? "#1e1e1e" : "#ffffff",
        color: isDark ? "#d4d4d4" : "#24292e"
      },
      ".cm-gutters": {
        backgroundColor: isDark ? "#252526" : "#f6f8fa",
        color: isDark ? "#858585" : "#656d76",
        border: "none"
      },
      ".cm-activeLine": {
        backgroundColor: isDark ? "#2a2d2e" : "#f6f8fa"
      },
      ".cm-activeLineGutter": {
        backgroundColor: isDark ? "#2a2d2e" : "#f6f8fa"
      }
    })
    
    return [
      languageExtension,
      isDark ? oneDark : [],
      customTheme,
      settings.wordWrap ? EditorView.lineWrapping : [],
      // Editor is fully editable
      EditorView.editable.of(true)
    ].filter(Boolean)
  }, [languageExtension, isDark, settings.fontSize, settings.wordWrap])

  // Execute code
  const executeCode = useCallback(async () => {
    setIsRunning(true)
    setOutput('Running...')
    
    try {
      const response = await fetch('/api/v1/execute/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}` // Use correct token key
        },
        body: JSON.stringify({
          code,
          language: currentLanguage
        })
      })
      
      const result = await response.json()
      
      if (result.success) {
        setOutput(result.output || 'Code executed successfully!')
      } else {
        setOutput(`Error: ${result.error || 'Unknown error occurred'}`)
      }
      
      onExecute(code, result)
      
    } catch (error) {
      console.error('Code execution error:', error)
      // Provide a demo output for development
      setOutput(`# Demo Mode - Code would execute here
# Your code:
${code}

# Result: Code execution simulated (${currentLanguage})
# Output would appear here in production mode`)
    } finally {
      setIsRunning(false)
    }
  }, [code, currentLanguage, onExecute])

  // Save code
  const saveCode = useCallback(() => {
    const codeData = {
      code,
      language: currentLanguage,
      settings,
      timestamp: new Date().toISOString()
    }
    
    onSave(codeData)
    
    // Also save to localStorage as backup
    localStorage.setItem('playground_backup', JSON.stringify(codeData))
    
    // Show temporary feedback
    setOutput(prevOutput => prevOutput + '\n\n✅ Code saved successfully!')
  }, [code, currentLanguage, settings, onSave])

  // Load code from file
  const loadCode = useCallback((event) => {
    const file = event.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result)
          setCode(data.code || e.target.result)
          setCurrentLanguage(data.language || currentLanguage)
          setSettings(prev => ({ ...prev, ...data.settings }))
        } catch {
          // If not JSON, treat as plain text
          setCode(e.target.result)
        }
      }
      reader.readAsText(file)
    }
  }, [currentLanguage])

  // Download code
  const downloadCode = useCallback(() => {
    const codeData = {
      code,
      language: currentLanguage,
      settings,
      timestamp: new Date().toISOString()
    }
    
    const blob = new Blob([JSON.stringify(codeData, null, 2)], {
      type: 'application/json'
    })
    
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `playground_${new Date().toISOString().slice(0, 19)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }, [code, currentLanguage, settings])

  // Auto-save functionality
  useEffect(() => {
    if (settings.autoSave && code !== initialCode) {
      const timer = setTimeout(saveCode, 2000) // Auto-save after 2 seconds of inactivity
      return () => clearTimeout(timer)
    }
  }, [code, settings.autoSave, saveCode, initialCode])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 's':
            e.preventDefault()
            saveCode()
            break
          case 'Enter':
            e.preventDefault()
            executeCode()
            break
        }
      }
    }
    
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [saveCode, executeCode])

  // Update code when initialCode changes
  useEffect(() => {
    if (initialCode && initialCode !== code) {
      setCode(initialCode)
    }
  }, [initialCode])

  return (
    <div className={`editable-code-playground ${className}`}>
      {/* Toolbar */}
      <div className="toolbar bg-slate-100 dark:bg-slate-800 p-3 border-b flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <button
            onClick={executeCode}
            disabled={isRunning}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            <Play className="w-4 h-4" />
            <span>{isRunning ? 'Running...' : 'Run'}</span>
          </button>
          
          <button
            onClick={saveCode}
            className="flex items-center space-x-2 px-3 py-2 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            <Save className="w-4 h-4" />
            <span>Save</span>
          </button>
          
          {enableFileOperations && (
            <div className="flex items-center space-x-1">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center space-x-2 px-3 py-2 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
              >
                <Upload className="w-4 h-4" />
                <span>Load</span>
              </button>
              
              <button
                onClick={downloadCode}
                className="flex items-center space-x-2 px-3 py-2 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>Download</span>
              </button>
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {enableMultipleLanguages && (
            <select
              value={currentLanguage}
              onChange={(e) => setCurrentLanguage(e.target.value)}
              className="px-3 py-1 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="java">Java</option>
              <option value="cpp">C++</option>
              <option value="html">HTML</option>
              <option value="css">CSS</option>
            </select>
          )}
          
          <button
            onClick={() => setSettings(prev => ({ ...prev, showOutput: !prev.showOutput }))}
            className="flex items-center space-x-2 px-3 py-2 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            {settings.showOutput ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            <span>Output</span>
          </button>
          
          <button 
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center space-x-2 px-3 py-2 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            <Settings className="w-4 h-4" />
            <span>Settings</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content flex flex-col lg:flex-row" style={{ height: '500px' }}>
        {/* Code Editor */}
        <div className="editor-section flex-1 min-h-0">
          <CodeMirror
            value={code}
            onChange={setCode}
            extensions={extensions}
            theme={isDark ? 'dark' : 'light'}
            basicSetup={{
              lineNumbers: settings.showLineNumbers,
              foldGutter: true,
              dropCursor: false,
              allowMultipleSelections: false,
              indentOnInput: true,
              bracketMatching: true,
              closeBrackets: true,
              autocompletion: true,
              highlightSelectionMatches: false,
              searchKeymap: true
            }}
            className="h-full"
          />
        </div>
        
        {/* Output Panel */}
        {settings.showOutput && (
          <div className="output-section lg:w-1/3 border-t lg:border-t-0 lg:border-l border-slate-300 dark:border-slate-600">
            <div className="output-header bg-slate-50 dark:bg-slate-900 p-2 border-b border-slate-300 dark:border-slate-600 flex items-center">
              <Terminal className="w-4 h-4 mr-2 text-slate-600 dark:text-slate-400" />
              <span className="text-sm font-medium text-slate-900 dark:text-slate-100">Output</span>
            </div>
            <div className="output-content p-4 h-full overflow-auto bg-slate-900 text-green-400 font-mono text-sm">
              <pre className="whitespace-pre-wrap">{output || 'No output yet. Run your code to see results.'}</pre>
            </div>
          </div>
        )}
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="settings-panel bg-slate-50 dark:bg-slate-900 p-4 border-t">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Settings</h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Font Size
              </label>
              <input
                type="range"
                min="10"
                max="24"
                value={settings.fontSize}
                onChange={(e) => setSettings(prev => ({ ...prev, fontSize: parseInt(e.target.value) }))}
                className="w-full"
              />
              <span className="text-xs text-slate-500">{settings.fontSize}px</span>
            </div>
            
            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.wordWrap}
                  onChange={(e) => setSettings(prev => ({ ...prev, wordWrap: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm text-slate-700 dark:text-slate-300">Word Wrap</span>
              </label>
            </div>
            
            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.showLineNumbers}
                  onChange={(e) => setSettings(prev => ({ ...prev, showLineNumbers: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm text-slate-700 dark:text-slate-300">Line Numbers</span>
              </label>
            </div>
            
            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.autoSave}
                  onChange={(e) => setSettings(prev => ({ ...prev, autoSave: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm text-slate-700 dark:text-slate-300">Auto Save</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Hidden file input */}
      {enableFileOperations && (
        <input
          ref={fileInputRef}
          type="file"
          accept=".json,.py,.js,.java,.cpp,.html,.css,.txt"
          onChange={loadCode}
          className="hidden"
        />
      )}
    </div>
  )
}

export default EditableCodePlayground