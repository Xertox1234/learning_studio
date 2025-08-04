import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiRequest } from '../utils/api'
import { EditableCodePlayground } from '../components/code-editor'
import { Loader2, AlertCircle, Code } from 'lucide-react'

export default function WagtailPlaygroundPage() {
  const [playgroundData, setPlaygroundData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [savedCode, setSavedCode] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    loadPlaygroundData()
  }, [])

  const loadPlaygroundData = async () => {
    try {
      setLoading(true)
      const response = await apiRequest('/api/v1/wagtail/playground/')
      if (response.ok) {
        const data = await response.json()
        setPlaygroundData(data)
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (err) {
      console.error('Failed to load playground data:', err)
      setError('Failed to load playground. Please try again later.')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = (codeData) => {
    setSavedCode(codeData.code)
    // Here you could save to the backend API
    console.log('Code saved:', codeData)
  }

  const handleExecute = (code, result) => {
    console.log('Code executed:', { code, result })
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col items-center justify-center min-h-96">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-4" />
          <p className="text-muted-foreground">Loading playground...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col items-center justify-center min-h-96">
          <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
          <h2 className="text-xl font-semibold text-foreground mb-2">Failed to Load Playground</h2>
          <p className="text-muted-foreground mb-4 text-center max-w-md">
            {error}
          </p>
          <button
            onClick={loadPlaygroundData}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (!playgroundData) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col items-center justify-center min-h-96">
          <Code className="w-12 h-12 text-gray-400 mb-4" />
          <h2 className="text-xl font-semibold text-foreground mb-2">Playground Not Available</h2>
          <p className="text-muted-foreground mb-4 text-center max-w-md">
            The code playground is not currently available. Please check back later.
          </p>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    )
  }

  // Default features if none configured in Wagtail
  const defaultFeatures = [
    {
      title: 'Real-time Code Execution',
      description: 'Run your code instantly and see results',
      icon: 'play-circle'
    },
    {
      title: 'Syntax Highlighting',
      description: 'Beautiful code highlighting for better readability',
      icon: 'code'
    },
    {
      title: 'Auto-save Functionality',
      description: 'Your code is automatically saved as you type',
      icon: 'save'
    },
    {
      title: 'Multiple Languages',
      description: 'Support for Python, JavaScript, HTML, CSS, and more',
      icon: 'layers'
    }
  ]

  // Default shortcuts if none configured in Wagtail
  const defaultShortcuts = [
    { keys: 'Ctrl+S', description: 'Save code' },
    { keys: 'Ctrl+Enter', description: 'Run code' },
    { keys: 'Tab', description: 'Indent' },
    { keys: 'Shift+Tab', description: 'Unindent' }
  ]

  const features = playgroundData.features.length > 0 ? playgroundData.features : defaultFeatures
  const shortcuts = playgroundData.shortcuts.length > 0 ? playgroundData.shortcuts : defaultShortcuts

  return (
    <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground mb-2">{playgroundData.title}</h1>
          {playgroundData.description && (
            <div 
              className="text-muted-foreground prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: playgroundData.description }}
            />
          )}
          {!playgroundData.description && (
            <p className="text-muted-foreground">
              Write, test, and experiment with code in our interactive playground.
            </p>
          )}
        </div>

        {/* Main Playground */}
        <div className="bg-card rounded-lg shadow-lg overflow-hidden mb-8">
          <EditableCodePlayground
            initialCode={playgroundData.default_code}
            language={playgroundData.programming_language}
            onSave={handleSave}
            onExecute={handleExecute}
            className="min-h-[600px]"
            enableFileOperations={playgroundData.settings.enable_file_operations}
            enableAutoSave={playgroundData.settings.enable_auto_save}
            enableMultipleLanguages={playgroundData.settings.enable_multiple_languages}
          />
        </div>

        {/* Features and Information */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Features */}
          <div className="bg-card p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <span className="mr-2 text-yellow-500">⭐</span>
              Features
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {features.map((feature, index) => (
                <div key={index} className="p-3 border border-border rounded-lg hover:shadow-md transition-shadow">
                  <div className="flex items-center mb-2">
                    <span className="mr-2 text-primary">📋</span>
                    <h6 className="font-medium text-sm">{feature.title}</h6>
                  </div>
                  <p className="text-muted-foreground text-xs">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Keyboard Shortcuts */}
          <div className="bg-card p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <span className="mr-2 text-blue-500">⌨️</span>
              Keyboard Shortcuts
            </h3>
            <div className="space-y-3">
              {shortcuts.map((shortcut, index) => (
                <div key={index} className="flex justify-between items-center">
                  <kbd className="bg-muted px-2 py-1 rounded text-sm font-mono">
                    {shortcut.keys}
                  </kbd>
                  <span className="text-muted-foreground text-sm">{shortcut.description}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Code Examples (if configured) */}
        {playgroundData.code_examples.length > 0 && (
          <div className="mb-8">
            <h3 className="text-xl font-semibold mb-4 flex items-center">
              <span className="mr-2 text-green-500">💻</span>
              Code Examples
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {playgroundData.code_examples.map((example, index) => (
                <div key={index} className="bg-card border border-border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-2">
                    <h6 className="font-medium text-sm">{example.title}</h6>
                    <span className={`px-2 py-1 rounded text-xs text-white ${
                      example.category === 'basic' ? 'bg-green-500' :
                      example.category === 'intermediate' ? 'bg-yellow-500' : 'bg-red-500'
                    }`}>
                      {example.category}
                    </span>
                  </div>
                  <p className="text-muted-foreground text-xs mb-3">{example.description}</p>
                  <div className="relative">
                    <pre className="bg-muted p-3 rounded text-xs overflow-auto max-h-48">
                      <code>{example.code}</code>
                    </pre>
                    <span className="absolute top-2 right-2 bg-secondary text-secondary-foreground px-2 py-1 rounded text-xs">
                      {example.language}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
    </div>
  )
}