import React from 'react'
import { Code, Play, Target, Award } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { ReadOnlyCodeBlock } from '../components/code-editor'
import RunButtonCodeEditor from '../components/code-editor/RunButtonCodeEditor'
import MinimalFillBlankEditor from '../components/code-editor/MinimalFillBlankEditor'
import MinimalMultipleChoiceBlanks from '../components/code-editor/MinimalMultipleChoiceBlanks'

export default function MinimalInteractiveDemo() {
  const { theme } = useTheme()

  // Sample data for components
  const runButtonExample = {
    title: "Your First Python Program",
    code: `print("Welcome to Python Learning Studio!")
print("Let's start learning Python together!")`,
    language: "python",
    mockOutput: `Welcome to Python Learning Studio!
Let's start learning Python together!`,
    aiExplanation: "This code demonstrates the print() function, which displays text on the screen. It's the foundation of all Python output!"
  }

  const fillBlankExample = {
    template: `def add_numbers(a, b):
    result = {{BLANK_1}} + {{BLANK_2}}
    return {{BLANK_3}}

# Test the function  
sum_result = add_numbers(5, 3)
print(f"The sum is: {sum_result}")`,
    solutions: {
      '1': 'a',
      '2': 'b', 
      '3': 'result'
    },
    alternativeSolutions: {
      '1': ['a', 'first_param'],
      '2': ['b', 'second_param'],
      '3': ['result', 'sum', 'total']
    },
    aiHints: {
      '1': 'This should be the first parameter of the function',
      '2': 'This should be the second parameter of the function',
      '3': 'This should be the variable that stores the calculation result'
    }
  }

  const multipleChoiceExample = {
    template: `def calculate_area(radius):
    pi = {{CHOICE_1}}
    area = pi * radius {{CHOICE_2}} radius
    return {{CHOICE_3}}

# Calculate area of a circle
circle_area = calculate_area(5)
print(f"Area: {circle_area}")`,
    choices: {
      '1': ['3.14159', '2.71828', '1.41421'],
      '2': ['*', '+', '/'],
      '3': ['area', 'radius', 'pi']
    },
    solutions: {
      '1': '3.14159',
      '2': '*',
      '3': 'area'
    },
    aiExplanations: {
      '1': 'Pi (π ≈ 3.14159) is the mathematical constant used in circle calculations',
      '2': 'To calculate area, we multiply pi by radius squared (radius * radius)',
      '3': 'The function should return the calculated area value'
    }
  }

  return (
    <div className="container-custom py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Minimal Interactive Code Editors</h1>
          <p className="text-xl text-muted-foreground mb-6">
            Ultra-minimal CodeMirror components designed for Wagtail lesson integration
          </p>
          <div className="text-sm text-muted-foreground">
            These components look identical to ReadOnlyCodeBlock but add subtle interactivity
          </div>
        </div>

        {/* Component Showcase */}
        <div className="space-y-16">
          
          {/* 1. ReadOnlyCodeBlock (Baseline) */}
          <section>
            <div className="mb-8">
              <div className="flex items-center space-x-2 mb-4">
                <Code className="h-6 w-6 text-primary" />
                <h2 className="text-2xl font-bold">1. ReadOnlyCodeBlock (Baseline)</h2>
              </div>
              <p className="text-muted-foreground">
                Current read-only code display - the visual standard our interactive components match
              </p>
            </div>
            
            <div className="bg-card border rounded-lg p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Code className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold">{runButtonExample.title}</h3>
              </div>
              
              <ReadOnlyCodeBlock
                code={runButtonExample.code}
                language={runButtonExample.language}
                showLineNumbers={true}
              />
              
              <div className="mt-4 text-sm text-muted-foreground">
                ↑ Pure read-only display - no interactivity
              </div>
            </div>
          </section>

          {/* 2. RunButtonCodeEditor */}
          <section>
            <div className="mb-8">
              <div className="flex items-center space-x-2 mb-4">
                <Play className="h-6 w-6 text-primary" />
                <h2 className="text-2xl font-bold">2. RunButtonCodeEditor</h2>
              </div>
              <p className="text-muted-foreground">
                Identical visual appearance with a subtle floating Run button and expandable mock output
              </p>
            </div>
            
            <div className="bg-card border rounded-lg p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Play className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold">Interactive Code Example</h3>
              </div>
              
              <RunButtonCodeEditor
                code={runButtonExample.code}
                language={runButtonExample.language}
                title={runButtonExample.title}
                mockOutput={runButtonExample.mockOutput}
                aiExplanation={runButtonExample.aiExplanation}
                showLineNumbers={true}
              />
              
              <div className="mt-4 text-sm text-muted-foreground">
                ↑ Click "Run" button to see mock output and optional AI explanation
              </div>
            </div>
          </section>

          {/* 3. MinimalFillBlankEditor */}
          <section>
            <div className="mb-8">
              <div className="flex items-center space-x-2 mb-4">
                <Target className="h-6 w-6 text-primary" />
                <h2 className="text-2xl font-bold">3. MinimalFillBlankEditor</h2>
              </div>
              <p className="text-muted-foreground">
                Fill-in-the-blanks with inline text inputs that blend seamlessly with the code
              </p>
            </div>
            
            <div className="bg-card border rounded-lg p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Target className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold">Complete the Function</h3>
              </div>
              
              <div className="mb-4">
                <div className="prose dark:prose-invert text-sm">
                  Fill in the blanks to complete this function that adds two numbers together.
                </div>
              </div>
              
              <MinimalFillBlankEditor
                template={fillBlankExample.template}
                solutions={fillBlankExample.solutions}
                alternativeSolutions={fillBlankExample.alternativeSolutions}
                aiHints={fillBlankExample.aiHints}
                language="python"
                showLineNumbers={true}
              />
              
              <div className="mt-4 text-sm text-muted-foreground">
                ↑ Fill in the blanks with: <code>a</code>, <code>b</code>, <code>result</code> - then click "Check Answers"
              </div>
            </div>
          </section>

          {/* 4. MinimalMultipleChoiceBlanks */}
          <section>
            <div className="mb-8">
              <div className="flex items-center space-x-2 mb-4">
                <Award className="h-6 w-6 text-primary" />
                <h2 className="text-2xl font-bold">4. MinimalMultipleChoiceBlanks</h2>
              </div>
              <p className="text-muted-foreground">
                Multiple choice fill-in-blanks with subtle dropdown menus for guided learning
              </p>
            </div>
            
            <div className="bg-card border rounded-lg p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Award className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold">Choose the Correct Options</h3>
              </div>
              
              <div className="mb-4">
                <div className="prose dark:prose-invert text-sm">
                  Select the correct options from the dropdowns to complete the circle area calculation.
                </div>
              </div>
              
              <MinimalMultipleChoiceBlanks
                template={multipleChoiceExample.template}
                choices={multipleChoiceExample.choices}
                solutions={multipleChoiceExample.solutions}
                aiExplanations={multipleChoiceExample.aiExplanations}
                language="python"
                showLineNumbers={true}
              />
              
              <div className="mt-4 text-sm text-muted-foreground">
                ↑ Select options from the dropdowns, then click "Check Choices"
              </div>
            </div>
          </section>

          {/* Visual Comparison */}
          <section className="border-t pt-12">
            <div className="mb-8">
              <h2 className="text-2xl font-bold mb-4">Visual Comparison</h2>
              <p className="text-muted-foreground">
                All components maintain the same visual baseline with minimal additional UI elements
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold mb-3">Before Interaction</h3>
                <div className="text-sm text-muted-foreground mb-4">
                  Components look identical to ReadOnlyCodeBlock
                </div>
                <ReadOnlyCodeBlock
                  code="print('Hello, World!')"
                  language="python"
                  showLineNumbers={true}
                />
              </div>
              
              <div>
                <h3 className="text-lg font-semibold mb-3">After Interaction</h3>
                <div className="text-sm text-muted-foreground mb-4">
                  Subtle interactive elements appear only when needed
                </div>
                <RunButtonCodeEditor
                  code="print('Hello, World!')"
                  language="python"
                  showLineNumbers={true}
                  mockOutput="Hello, World!"
                />
              </div>
            </div>
          </section>

          {/* Integration Notes */}
          <section className="bg-muted/30 rounded-lg p-8">
            <h2 className="text-2xl font-bold mb-4">Integration with Wagtail Lessons</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
              <div>
                <h3 className="font-semibold mb-2">New Content Block Types</h3>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• <code>runnable_code_example</code> → RunButtonCodeEditor</li>
                  <li>• <code>fill_blank_code</code> → MinimalFillBlankEditor</li>
                  <li>• <code>multiple_choice_code</code> → MinimalMultipleChoiceBlanks</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Design Principles</h3>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• Ultra-minimal visual footprint</li>
                  <li>• Identical styling to ReadOnlyCodeBlock</li>
                  <li>• Progressive disclosure of functionality</li>
                  <li>• AI assistance integration ready</li>
                </ul>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}