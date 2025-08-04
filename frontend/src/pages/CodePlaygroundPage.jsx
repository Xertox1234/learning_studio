import { useState } from 'react'
import { AdvancedCodePlayground } from '../components/code-editor'

export default function CodePlaygroundPage() {
  const [savedCode, setSavedCode] = useState('')

  const handleSave = (codeData) => {
    setSavedCode(codeData.code)
    // Here you could save to your backend API
    console.log('Code saved:', codeData)
  }

  const handleExecute = (code, result) => {
    console.log('Code executed:', { code, result })
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-foreground mb-2">Code Playground</h1>
        <p className="text-muted-foreground">
          Write, test, and experiment with Python code in our interactive playground.
        </p>
      </div>

      <div className="bg-card rounded-lg shadow-lg overflow-hidden">
        <AdvancedCodePlayground
          initialCode={`# Welcome to Python Learning Studio Playground!
# Write your Python code here and click Run to execute it.

def greet(name):
    """A simple greeting function"""
    return f"Hello, {name}! Welcome to Python programming!"

# Try it out
message = greet("Programmer")
print(message)

# You can also do calculations
result = 42 * 2
print(f"The answer to everything times 2 is: {result}")
`}
          language="python"
          onSave={handleSave}
          onExecute={handleExecute}
          className="min-h-[600px]"
        />
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-card p-4 rounded-lg">
          <h3 className="font-semibold text-lg mb-2">Features</h3>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>• Real-time code execution</li>
            <li>• Syntax highlighting</li>
            <li>• Auto-save functionality</li>
            <li>• Load/save code files</li>
            <li>• Keyboard shortcuts (Ctrl+S, Ctrl+Enter)</li>
          </ul>
        </div>

        <div className="bg-card p-4 rounded-lg">
          <h3 className="font-semibold text-lg mb-2">Keyboard Shortcuts</h3>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>• <kbd className="bg-muted px-1 rounded">Ctrl+S</kbd> - Save code</li>
            <li>• <kbd className="bg-muted px-1 rounded">Ctrl+Enter</kbd> - Run code</li>
            <li>• <kbd className="bg-muted px-1 rounded">Tab</kbd> - Indent</li>
            <li>• <kbd className="bg-muted px-1 rounded">Shift+Tab</kbd> - Unindent</li>
          </ul>
        </div>
      </div>
    </div>
  )
}