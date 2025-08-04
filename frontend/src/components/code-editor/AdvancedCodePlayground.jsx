import React, { useState, useCallback, useEffect, useRef } from 'react'
import InteractiveCodeEditor from './InteractiveCodeEditor'
import { Play, Save, Download, Upload, Settings, Terminal, Eye, EyeOff } from 'lucide-react'

const AdvancedCodePlayground = ({
  initialCode = '',
  language = 'python',
  onSave = () => {},
  onExecute = () => {},
  className = ''
}) => {
  const [code, setCode] = useState(initialCode)
  const [output, setOutput] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [settings, setSettings] = useState({
    theme: 'dark',
    fontSize: 14,
    wordWrap: false,
    showLineNumbers: true,
    showOutput: true,
    autoSave: false
  })
  const [widgets, setWidgets] = useState([])
  const fileInputRef = useRef(null)

  // Widget types for advanced playground
  const widgetTypes = {
    comment: {
      name: 'Comment Widget',
      create: (id, position, config = {}) => ({
        id,
        type: 'comment',
        position,
        content: config.content || 'Add your comment here...',
        color: config.color || '#3b82f6'
      })
    },
    note: {
      name: 'Sticky Note',
      create: (id, position, config = {}) => ({
        id,
        type: 'note',
        position,
        content: config.content || 'Note',
        color: config.color || '#f59e0b'
      })
    },
    breakpoint: {
      name: 'Breakpoint',
      create: (id, position, config = {}) => ({
        id,
        type: 'breakpoint',
        position,
        active: config.active || true
      })
    }
  }

  // Execute code
  const executeCode = useCallback(async () => {
    setIsRunning(true)
    setOutput('Running...')
    
    try {
      const response = await fetch('/api/v1/execute/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}` // Add auth if needed
        },
        body: JSON.stringify({
          code,
          language
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
      setOutput(`Network Error: ${error.message}`)
    } finally {
      setIsRunning(false)
    }
  }, [code, language, onExecute])

  // Save code
  const saveCode = useCallback(() => {
    const codeData = {
      code,
      language,
      widgets,
      settings,
      timestamp: new Date().toISOString()
    }
    
    onSave(codeData)
    
    // Also save to localStorage as backup
    localStorage.setItem('playground_backup', JSON.stringify(codeData))
  }, [code, language, widgets, settings, onSave])

  // Load code from file
  const loadCode = useCallback((event) => {
    const file = event.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result)
          setCode(data.code || e.target.result)
          setWidgets(data.widgets || [])
          setSettings(prev => ({ ...prev, ...data.settings }))
        } catch {
          // If not JSON, treat as plain text
          setCode(e.target.result)
        }
      }
      reader.readAsText(file)
    }
  }, [])

  // Download code
  const downloadCode = useCallback(() => {
    const codeData = {
      code,
      language,
      widgets,
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
  }, [code, language, widgets, settings])

  // Auto-save functionality
  useEffect(() => {
    if (settings.autoSave) {
      const timer = setTimeout(saveCode, 2000) // Auto-save after 2 seconds of inactivity
      return () => clearTimeout(timer)
    }
  }, [code, settings.autoSave, saveCode])

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

  return (
    <div className={`advanced-code-playground ${className}`}>
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
        </div>
        
        <div className="flex items-center space-x-2">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="px-3 py-1 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
          >
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
          </select>
          
          <button
            onClick={() => setSettings(prev => ({ ...prev, showOutput: !prev.showOutput }))}
            className="flex items-center space-x-2 px-3 py-2 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            {settings.showOutput ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            <span>Output</span>
          </button>
          
          <button className="flex items-center space-x-2 px-3 py-2 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors">
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content flex flex-col lg:flex-row h-96">
        {/* Code Editor */}
        <div className="editor-section flex-1 min-h-0">
          <InteractiveCodeEditor
            value={code}
            onChange={setCode}
            language={language}
            theme={settings.theme}
            className="h-full"
            basicSetup={{
              lineNumbers: settings.showLineNumbers,
              wordWrap: settings.wordWrap,
              fontSize: settings.fontSize
            }}
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

      {/* Settings Panel (Hidden by default, can be toggled) */}
      <div className="settings-panel bg-slate-50 dark:bg-slate-900 p-4 border-t hidden">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Settings</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Theme
            </label>
            <select
              value={settings.theme}
              onChange={(e) => setSettings(prev => ({ ...prev, theme: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </div>
          
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
                checked={settings.autoSave}
                onChange={(e) => setSettings(prev => ({ ...prev, autoSave: e.target.checked }))}
                className="rounded"
              />
              <span className="text-sm text-slate-700 dark:text-slate-300">Auto Save</span>
            </label>
          </div>
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json,.py,.js,.txt"
        onChange={loadCode}
        className="hidden"
      />
    </div>
  )
}

export default AdvancedCodePlayground