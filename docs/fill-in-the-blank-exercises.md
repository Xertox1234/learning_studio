# Fill-in-the-Blank Code Exercises

This document provides detailed technical documentation for the fill-in-the-blank code exercise system implemented using CodeMirror 6 with React in the Python Learning Studio platform.

## Overview

The fill-in-the-blank system uses CodeMirror 6's decorations and widgets integrated with React components to transform special syntax markers into interactive input fields, allowing students to complete code exercises by filling in missing parts.

## React Implementation Details

### Core Components

1. **React CodeMirror Integration**: Using `@uiw/react-codemirror` for React-specific implementation
2. **Widget System**: Custom `WidgetType` implementation for interactive input fields
3. **Decoration Engine**: Pattern matching and decoration application with theme awareness
4. **Validation System**: React-based validation using DOM queries and state management

### Technical Implementation

#### 1. Widget Definition

The core of the implementation is the `BlankWidget` class that extends CodeMirror's `WidgetType` with theme awareness:

```javascript
import { WidgetType } from '@codemirror/view'

class BlankWidget extends WidgetType {
  constructor(placeholder, isDark = true) {
    super()
    this.placeholder = placeholder
    this.isDark = isDark
  }

  eq(other) {
    return other.placeholder === this.placeholder && other.isDark === this.isDark
  }

  toDOM() {
    const input = document.createElement("input")
    input.type = "text"
    input.placeholder = this.placeholder
    input.classList.add("cm-blank-input")
    input.dataset.blankId = this.placeholder.replace("BLANK_", "")
    
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
    
    // Prevent event bubbling to CodeMirror
    input.addEventListener('keydown', (e) => e.stopPropagation())
    input.addEventListener('keyup', (e) => e.stopPropagation())
    input.addEventListener('keypress', (e) => e.stopPropagation())
    input.addEventListener('input', (e) => e.stopPropagation())
    input.addEventListener('mousedown', (e) => e.stopPropagation())
    input.addEventListener('click', (e) => e.stopPropagation())
    
    return input
  }

  ignoreEvent() {
    return false // Allow input events to be handled by the DOM
  }
}
```

#### 2. Pattern Matching and Decoration

The system uses a theme-aware `MatchDecorator` to find special syntax patterns and replace them with widget decorations:

```javascript
import { MatchDecorator, Decoration } from '@codemirror/view'

const createBlankMatcher = (isDark) => new MatchDecorator({
  // Match pattern like {{BLANK_1}} where 1 is any number
  regexp: /\{\{BLANK_(\d+)\}\}/g,
  decoration: match => Decoration.replace({
    widget: new BlankWidget(`BLANK_${match[1]}`, isDark),
    inclusive: false
  })
})
```

#### 3. ViewPlugin Integration

A theme-responsive ViewPlugin combines everything to apply decorations to the editor:

```javascript
import { ViewPlugin, EditorView } from '@codemirror/view'

const createBlankPlugin = (isDark) => {
  const matcher = createBlankMatcher(isDark)
  
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
```

#### 4. Exercise Definition

Exercise definitions use a special syntax in the code to denote blank areas:

```python
def calculate_sum(a, b):
    """Calculate the sum of two numbers"""
    result = {{BLANK_1}} + {{BLANK_2}}
    return result
```

The expected solutions are defined separately in the exercise configuration:

```javascript
const exerciseConfig = {
  solutions: {
    "1": "a", // Solution for BLANK_1
    "2": "b"  // Solution for BLANK_2
  },
  // Optionally allow alternative solutions
  alternativeSolutions: {
    "1": ["a", "first", "num1"],
    "2": ["b", "second", "num2"]
  },
  // For more complex validation
  customValidators: {
    "3": (input) => {
      // Custom logic to validate input
      return input.includes("for") && input.includes("range");
    }
  }
};
```

#### 5. React Component Integration

The React component integrates CodeMirror with the widget system:

```javascript
import React, { useMemo } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { EditorView } from '@codemirror/view'
import { useTheme } from '../../contexts/ThemeContext'

const InteractiveCodeEditor = ({ value, onChange, language, className }) => {
  const { theme: contextTheme } = useTheme()
  const isDark = contextTheme === 'dark'
  
  const extensions = useMemo(() => {
    const blankPlugin = createBlankPlugin(isDark)
    
    return [
      python(),
      isDark ? oneDark : [],
      blankPlugin,
      EditorView.editable.of(false), // Template is read-only
      EditorView.theme({
        "&": {
          backgroundColor: isDark ? "#1e1e1e" : "#ffffff",
          color: isDark ? "#d4d4d4" : "#24292e"
        }
      })
    ]
  }, [isDark])
  
  return (
    <CodeMirror
      value={value}
      onChange={onChange}
      extensions={extensions}
      theme={isDark ? 'dark' : 'light'}
    />
  )
}
```

#### 6. Solution Validation in React

The validation system uses DOM queries within React components:

```javascript
const validateAnswers = useCallback(async () => {
  const inputs = document.querySelectorAll('.cm-blank-input')
  const results = {}
  const values = {}
  const solutions = exerciseData?.solutions || {}
  const alternativeSolutions = exerciseData?.alternativeSolutions || {}
  
  inputs.forEach(input => {
    const blankId = input.dataset.blankId
    const userInput = input.value.trim()
    const expectedSolution = solutions[blankId]
    const alternatives = alternativeSolutions[blankId] || []
    
    values[blankId] = userInput
    
    let isCorrect = false
    
    // Check if input matches solution or alternatives
    if (userInput === expectedSolution || alternatives.includes(userInput)) {
      isCorrect = true
    }
    
    results[blankId] = isCorrect
    
    // Add visual feedback
    input.classList.remove('correct', 'incorrect')
    input.classList.add(isCorrect ? 'correct' : 'incorrect')
  })
  
  setValidationResults(results)
  setFillBlankValues(values)
  onValidate(results, values)
  
  return results
}, [exerciseData, onValidate])
```


## Creating New Fill-in-the-Blank Exercises in React

To create a new fill-in-the-blank exercise:

### 1. Define the Exercise Data

```javascript
const exerciseData = {
  id: "1",
  title: "Complete the Python Function",
  description: "Fill in the missing parts to create a function that checks if a number is even.",
  type: "fill-in-blank",
  template: `def is_even(number):
    """Check if a number is even."""
    return {{BLANK_1}} % {{BLANK_2}} == {{BLANK_3}}`,
  solutions: {
    "1": "number",
    "2": "2",
    "3": "0"
  },
  alternativeSolutions: {
    "1": ["number", "num", "n"],
    "2": ["2"],
    "3": ["0", "False"]
  },
  hints: [
    "Use the modulo operator to check divisibility",
    "Even numbers have no remainder when divided by 2"
  ],
  language: "python"
}
```

### 2. Use the FillInBlankExercise Component

```javascript
import { FillInBlankExercise } from '../components/code-editor'

export default function ExercisePage() {
  const handleSubmit = (code, executionResult, answers) => {
    // Handle submission to backend
    console.log('Submitted:', { code, executionResult, answers })
  }
  
  const handleValidate = (validationResults, answers) => {
    // Handle validation results
    console.log('Validation:', { validationResults, answers })
  }
  
  return (
    <FillInBlankExercise
      exerciseData={exerciseData}
      onSubmit={handleSubmit}
      onValidate={handleValidate}
      className="min-h-[400px]"
    />
  )
}
```

### 3. Component Features

The `FillInBlankExercise` component provides:
- Theme-aware code editor with read-only template
- Interactive input widgets for blanks
- Progress tracking
- Validation with visual feedback
- Code execution capability
- Reset functionality

## Advanced Customizations

### Custom Styling for Widgets

The input styling can be customized by modifying the CSS in the `toDOM()` method or by providing additional theme extensions:

```javascript
// In your theme file
EditorView.baseTheme({
  ".cm-blank-input": {
    // Custom styles for all blank inputs
    background: "var(--input-bg-color)",
    color: "var(--input-text-color)",
    border: "2px dashed var(--input-border-color)"
  },
  ".cm-blank-input:focus": {
    // Focus styles
    boxShadow: "0 0 0 3px rgba(66, 153, 225, 0.5)",
    borderColor: "var(--primary-color)"
  }
})
```

### Different Types of Blanks

You can extend the system to support different types of blanks by modifying the pattern and widget creation:

```javascript
// Match different types of blanks
const multiTypeMatcher = new MatchDecorator({
  regexp: /\{\{(STRING|NUMBER|BOOLEAN)_(\d+)\}\}/g,
  decoration: match => {
    const type = match[1].toLowerCase(); // string, number, boolean
    const id = match[2];
    return Decoration.replace({
      widget: new TypedBlankWidget(type, id)
    });
  }
});

// TypedBlankWidget implementation
class TypedBlankWidget extends WidgetType {
  constructor(type, id) {
    super();
    this.type = type;
    this.id = id;
  }
  
  toDOM() {
    const input = document.createElement("input");
    input.type = this.type === "boolean" ? "checkbox" : "text";
    input.dataset.blankId = this.id;
    input.dataset.blankType = this.type;
    
    // Add type-specific styling
    input.classList.add("cm-blank-input", `cm-blank-${this.type}`);
    
    return input;
  }
}
```

## Key Implementation Details

### Event Handling
The widget implementation must properly handle events to prevent CodeMirror from intercepting input:

```javascript
// Critical: Stop propagation of all keyboard events
input.addEventListener('keydown', (e) => e.stopPropagation())
input.addEventListener('keyup', (e) => e.stopPropagation())
input.addEventListener('keypress', (e) => e.stopPropagation())
```

### Theme Responsiveness
The system adapts to theme changes by:
1. Using `useMemo` with theme dependency
2. Passing theme state to widget constructors
3. Applying conditional styles based on theme

### Read-Only Template
The template code is made read-only while keeping widgets editable:

```javascript
EditorView.editable.of(false) // Template is READ-ONLY
```

## Exercise Storage and Retrieval

Exercises are stored in the database with:

1. **Template code** containing `{{BLANK_X}}` markers
2. **Solution map** with correct answers
3. **Alternative solutions** for flexibility
4. **Hints** for student assistance

Example Django model:

```python
class Exercise(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPE_CHOICES)
    content = models.JSONField(default=dict)  # Stores template, solutions, etc.
    
    def get_template(self):
        return self.content.get('template', '')
    
    def get_solutions(self):
        return self.content.get('solutions', {})
```

## Accessibility Considerations

The fill-in-the-blank system is built with accessibility in mind:

1. Input fields are keyboard navigable
2. ARIA attributes are added to improve screen reader experience
3. High-contrast mode support
4. Color is not the only indicator of correct/incorrect answers

Additional ARIA attributes are added to improve accessibility:

```javascript
// In the toDOM method of BlankWidget
input.setAttribute('aria-label', `Fill in blank ${this.placeholder}`);
input.setAttribute('aria-required', 'true');

// After validation
input.setAttribute('aria-invalid', isCorrect ? 'false' : 'true');
if (!isCorrect) {
  input.setAttribute('aria-describedby', `hint-${input.dataset.blankId}`);
}
```

## Troubleshooting

### Common Issues

1. **Blanks not rendering**: Check that the regexp pattern matches your template markers
2. **Validation not working**: Verify solution mappings match blank IDs
3. **Styling inconsistencies**: Ensure CSS variables are properly defined in your theme

### Debug Process

1. Check console for errors
2. Inspect the DOM to verify input fields are correctly created
3. Add data attributes to identify specific blanks for debugging
4. Test with simplified examples first

## Complete React Integration Example

Here's a complete example showing how to integrate the fill-in-the-blank system:

```javascript
// ExerciseView.jsx
import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { FillInBlankExercise } from '../components/code-editor'
import { exerciseService } from '../services/api'

export default function ExerciseView() {
  const { id } = useParams()
  const [exercise, setExercise] = useState(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    async function loadExercise() {
      try {
        const data = await exerciseService.getExercise(id)
        setExercise(data)
      } catch (error) {
        console.error('Failed to load exercise:', error)
      } finally {
        setLoading(false)
      }
    }
    loadExercise()
  }, [id])
  
  const handleSubmit = async (code, executionResult, answers) => {
    try {
      const result = await exerciseService.submitExercise(id, {
        code,
        answers,
        executionResult
      })
      // Handle submission result
    } catch (error) {
      console.error('Submission failed:', error)
    }
  }
  
  if (loading) return <div>Loading...</div>
  if (!exercise) return <div>Exercise not found</div>
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">{exercise.title}</h1>
      <FillInBlankExercise
        exerciseData={exercise}
        onSubmit={handleSubmit}
        onValidate={(results, answers) => {
          console.log('Validation:', results, answers)
        }}
      />
    </div>
  )
}
```

## Creating a Multiple Choice Fill-in-the-Blank Editor

### Concept Overview

A multiple choice fill-in-the-blank editor would extend the current implementation by keeping the same input field appearance but changing the interaction model. Instead of typing, users click buttons from an answer bank to fill the inputs. The blanks look identical to the regular fill-in-the-blank exercise.

### Theoretical Implementation

#### 1. Reuse Existing Widget with Read-Only Inputs

```javascript
class MultipleChoiceBlankWidget extends BlankWidget {
  constructor(placeholder, isDark = true, currentValue = '') {
    super(placeholder, isDark)
    this.currentValue = currentValue
  }
  
  toDOM() {
    const input = super.toDOM() // Get standard input from parent
    
    // Make it read-only but keep same appearance
    input.readOnly = true
    input.value = this.currentValue
    input.style.cursor = 'pointer'
    
    // Add click handler to focus this blank
    input.addEventListener('click', (e) => {
      e.stopPropagation()
      // Dispatch custom event to notify which blank was clicked
      window.dispatchEvent(new CustomEvent('blankClicked', {
        detail: { blankId: this.placeholder.replace('BLANK_', '') }
      }))
    })
    
    // Keep all the same styling and appearance
    return input
  }
}
```

#### 2. Answer Bank Component

```javascript
const AnswerBank = ({ options, usedOptions, onOptionClick }) => {
  return (
    <div className="answer-bank">
      <h4>Available Options:</h4>
      <div className="answer-options">
        {options.map((option, index) => (
          <button
            key={index}
            className={`answer-option ${usedOptions.includes(option) ? 'used' : ''}`}
            disabled={usedOptions.includes(option)}
            onClick={() => onOptionClick(option)}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  )
}
```

#### 3. State Management with Focused Blank

```javascript
const MultipleChoiceFillInBlank = ({ exerciseData }) => {
  const [selections, setSelections] = useState({})
  const [focusedBlank, setFocusedBlank] = useState(null)
  const [availableOptions] = useState(exerciseData.options)
  
  useEffect(() => {
    // Listen for blank clicks
    const handleBlankClick = (event) => {
      const { blankId } = event.detail
      setFocusedBlank(blankId)
    }
    
    window.addEventListener('blankClicked', handleBlankClick)
    return () => window.removeEventListener('blankClicked', handleBlankClick)
  }, [])
  
  const handleOptionClick = (option) => {
    if (!focusedBlank) {
      // If no blank is focused, fill the first empty one
      const emptyBlanks = Object.keys(exerciseData.solutions)
        .filter(id => !selections[id])
      
      if (emptyBlanks.length > 0) {
        setFocusedBlank(emptyBlanks[0])
      }
    }
    
    if (focusedBlank) {
      // Remove the option from its current blank if already used
      const previouslyUsedBlank = Object.keys(selections)
        .find(key => selections[key] === option)
      
      let newSelections = { ...selections }
      if (previouslyUsedBlank) {
        delete newSelections[previouslyUsedBlank]
      }
      
      // Assign to focused blank
      newSelections[focusedBlank] = option
      setSelections(newSelections)
      
      // Update CodeMirror widgets
      updateAllWidgets(newSelections)
      setFocusedBlank(null)
    }
  }
  
  return (
    <>
      <InteractiveCodeEditor
        value={exerciseData.template}
        extensions={[createMultipleChoicePlugin(selections)]}
      />
      <AnswerBank
        options={availableOptions}
        usedOptions={Object.values(selections)}
        focusedBlank={focusedBlank}
        onOptionClick={handleOptionClick}
      />
    </>
  )
}
```

#### 4. Exercise Data Structure

```javascript
const multipleChoiceExercise = {
  type: "multiple-choice-fill-blank",
  template: `def {{BLANK_1}}(x, y):
    return x {{BLANK_2}} y`,
  options: ["add", "+", "subtract", "-", "multiply", "*"],
  solutions: {
    "1": "add",
    "2": "+"
  },
  // Each option can only be used once
  singleUse: true
}
```

### Key Implementation Considerations

1. **Identical Appearance**: Blanks look exactly like regular fill-in-the-blank inputs but are read-only
2. **Click-to-Focus**: Clicking a blank highlights it as the target for the next answer selection
3. **Visual Feedback**: 
   - Focused blank gets a highlight border
   - Used options are disabled/dimmed in the answer bank
   - Input fields show the selected values
4. **Single-Use Logic**: Each answer can only be used once, automatically moving from previous blank if reused
5. **Fallback Behavior**: If no blank is focused, clicking an answer fills the first empty blank
6. **Validation**: Same validation system as regular fill-in-the-blank, checking `input.value` against solutions

### User Experience Flow

1. **Initial State**: All blanks appear empty, answer bank shows all options available
2. **Select Target**: User clicks on a blank input field to focus it
3. **Choose Answer**: User clicks an answer button, which fills the focused blank
4. **Visual Update**: The input shows the selected value, answer button becomes disabled
5. **Reassignment**: If user clicks a used answer, it moves from its current blank to the newly focused one
6. **Validation**: Same "Validate" button checks all input values against expected solutions

This approach maintains the familiar look and feel of the existing fill-in-the-blank system while adding the guided selection mechanism of multiple choice, creating an intuitive hybrid experience.
