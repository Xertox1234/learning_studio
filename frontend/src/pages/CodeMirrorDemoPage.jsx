import React, { useState } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import {
  InteractiveCodeEditor,
  FillInBlankExercise,
  ReadOnlyCodeBlock,
  AdvancedCodePlayground
} from '../components/code-editor'
import CodeEditorErrorBoundary from '../components/code-editor/CodeEditorErrorBoundary'

export default function CodeMirrorDemoPage() {
  const { theme } = useTheme()
  const [editorValue, setEditorValue] = useState('# Welcome to CodeMirror Demo\nprint("Hello, World!")')
  const [fillInBlankAnswers, setFillInBlankAnswers] = useState({})

  // Sample data for fill-in-blank exercise
  const fillInBlankExerciseData = {
    id: 'demo-1',
    title: 'Python Function Demo',
    description: 'Complete the function to calculate the sum of two numbers',
    difficulty: 'beginner',
    programming_language: 'python',
    template: `def add_numbers(a, b):
    result = {{BLANK_1}} + {{BLANK_2}}
    return result

# Test the function
sum_result = add_numbers(5, 3)
print(f"The sum is: {sum_result}")`,
    solutions: {
      '1': 'a',
      '2': 'b'
    },
    alternativeSolutions: {
      '1': ['a', 'first_param'],
      '2': ['b', 'second_param']  
    },
    test_cases: [
      { input: '5, 3', expected_output: '8' },
      { input: '10, 20', expected_output: '30' }
    ]
  }

  const handleEditorChange = (value) => {
    setEditorValue(value)
    console.log('Editor value changed:', value)
  }

  const handleFillBlankSubmit = (answers) => {
    console.log('Fill-in-blank submitted:', answers)
    setFillInBlankAnswers(answers)
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-foreground mb-4">CodeMirror Component Demo</h1>
        <p className="text-lg text-muted-foreground">
          Explore different CodeMirror components and their features in the Python Learning Studio.
        </p>
      </div>

      {/* Interactive Code Editor Demo */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold text-foreground mb-4">Interactive Code Editor</h2>
        <p className="text-muted-foreground mb-4">
          A basic editable code editor with syntax highlighting and theme support.
        </p>
        <div className="bg-card rounded-lg shadow-lg p-6">
          <CodeEditorErrorBoundary>
            <InteractiveCodeEditor
              value={editorValue}
              onChange={handleEditorChange}
              language="python"
              height="100px"
              theme={theme}
            />
          </CodeEditorErrorBoundary>
          <div className="mt-4 p-4 bg-muted rounded">
            <p className="text-sm text-muted-foreground">
              Current value length: {editorValue.length} characters
            </p>
          </div>
        </div>
      </section>

      {/* Fill-in-Blank Exercise Demo */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold text-foreground mb-4">Fill-in-Blank Exercise</h2>
        <p className="text-muted-foreground mb-4">
          Interactive fill-in-blank exercises with validation and hint system.
        </p>
        <div className="bg-card rounded-lg shadow-lg">
          <CodeEditorErrorBoundary>
            <FillInBlankExercise
              exerciseData={fillInBlankExerciseData}
              onSubmit={handleFillBlankSubmit}
              showHints={true}
            />
          </CodeEditorErrorBoundary>
        </div>
        {Object.keys(fillInBlankAnswers).length > 0 && (
          <div className="mt-4 p-4 bg-muted rounded">
            <p className="text-sm text-muted-foreground">
              Submitted answers: {JSON.stringify(fillInBlankAnswers)}
            </p>
          </div>
        )}
      </section>

      {/* Read-Only Code Block Demo */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold text-foreground mb-4">Read-Only Code Block</h2>
        <p className="text-muted-foreground mb-4">
          Display code snippets with syntax highlighting (non-editable).
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium text-foreground mb-2">Python Example</h3>
            <CodeEditorErrorBoundary>
              <ReadOnlyCodeBlock
                code={`# Fibonacci sequence generator
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# Generate first 10 numbers
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")`}
                language="python"
              />
            </CodeEditorErrorBoundary>
          </div>
          <div>
            <h3 className="text-lg font-medium text-foreground mb-2">JavaScript Example</h3>
            <CodeEditorErrorBoundary>
              <ReadOnlyCodeBlock
                code={`// Array manipulation example
const numbers = [1, 2, 3, 4, 5];

const doubled = numbers.map(n => n * 2);
const filtered = doubled.filter(n => n > 5);
const sum = filtered.reduce((a, b) => a + b, 0);

console.log('Original:', numbers);
console.log('Doubled:', doubled);
console.log('Filtered:', filtered);
console.log('Sum:', sum);`}
                language="javascript"
              />
            </CodeEditorErrorBoundary>
          </div>
        </div>
      </section>

      {/* Advanced Code Playground Demo */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold text-foreground mb-4">Advanced Code Playground</h2>
        <p className="text-muted-foreground mb-4">
          Full-featured code editor with execution capabilities and output display.
        </p>
        <div className="bg-card rounded-lg shadow-lg overflow-hidden">
          <CodeEditorErrorBoundary>
            <AdvancedCodePlayground
              initialCode={`# Advanced playground with execution
import random

def generate_password(length=12):
    """Generate a random password"""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    password = ''.join(random.choice(chars) for _ in range(length))
    return password

# Generate 5 passwords
print("Generated passwords:")
for i in range(5):
    print(f"{i+1}. {generate_password()}")
`}
              language="python"
              className="min-h-[400px]"
            />
          </CodeEditorErrorBoundary>
        </div>
      </section>

      {/* Theme Comparison */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold text-foreground mb-4">Theme Comparison</h2>
        <p className="text-muted-foreground mb-4">
          See how code looks in different themes. Current theme: <span className="font-semibold">{theme}</span>
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium text-foreground mb-2">Force Light Theme</h3>
            <CodeEditorErrorBoundary>
              <InteractiveCodeEditor
                value={`# This editor always uses light theme
def hello_light():
    return "Hello from the light side!"`}
                language="python"
                height="80px"
                theme="light"
                readOnly={true}
              />
            </CodeEditorErrorBoundary>
          </div>
          <div>
            <h3 className="text-lg font-medium text-foreground mb-2">Force Dark Theme</h3>
            <CodeEditorErrorBoundary>
              <InteractiveCodeEditor
                value={`# This editor always uses dark theme
def hello_dark():
    return "Hello from the dark side!"`}
                language="python"
                height="80px"
                theme="dark"
                readOnly={true}
              />
            </CodeEditorErrorBoundary>
          </div>
        </div>
      </section>

      {/* Features Summary */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold text-foreground mb-4">Component Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-card p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-foreground mb-2">InteractiveCodeEditor</h3>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>✓ Syntax highlighting</li>
              <li>✓ Theme support</li>
              <li>✓ Customizable height</li>
              <li>✓ Change callbacks</li>
              <li>✓ Multiple languages</li>
            </ul>
          </div>
          <div className="bg-card p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-foreground mb-2">FillInBlankExercise</h3>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>✓ Interactive widgets</li>
              <li>✓ Validation system</li>
              <li>✓ Progressive hints</li>
              <li>✓ Test case support</li>
              <li>✓ Answer checking</li>
            </ul>
          </div>
          <div className="bg-card p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-foreground mb-2">AdvancedCodePlayground</h3>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>✓ Code execution</li>
              <li>✓ Output display</li>
              <li>✓ Error handling</li>
              <li>✓ Save functionality</li>
              <li>✓ Full editor features</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  )
}