# CodeMirror 6 Implementation

This document details the CodeMirror 6 implementation used in the Python Learning Studio platform for code editing, syntax highlighting, and interactive coding exercises. The platform now supports both traditional JavaScript integration and modern React components.

## Overview

Python Learning Studio uses CodeMirror 6 with custom extensions to provide:

1. Syntax highlighting for multiple programming languages
2. Fill-in-the-blank interactive code exercises with React widgets
3. Custom themes that adapt to the platform's light/dark mode
4. Code execution integration with the Docker executor
5. Auto-completion and linting capabilities
6. Advanced code playground with widget decorations

## Implementation Structure

### React Frontend (Primary)
```
/frontend/src/components/code-editor/
├── InteractiveCodeEditor.jsx    # React wrapper with widget support
├── FillInBlankExercise.jsx      # Fill-in-blank exercise component
├── AdvancedCodePlayground.jsx   # Advanced playground with features
└── index.js                     # Component exports
```

### Legacy JavaScript (Deprecated)
```
/static/js/
├── codemirror-loader.js      # Dynamic CodeMirror loading handler
├── codemirror-setup.js       # Base configuration and setup
├── codemirror-themes.js      # Theme definitions (light/dark)
├── codemirror6-enhanced.js   # Enhanced features implementation
├── codemirror6-init.js       # Initialization and editor setup
└── dist/                     # Compiled bundles
    ├── codemirror-enhanced.bundle.js
    ├── codemirror-themes.bundle.js
    └── ...
```

## Key Features

### 1. Fill-in-the-Blank Exercises (React Implementation)

The platform now uses React components with CodeMirror 6 widgets for creating interactive fill-in-the-blank code exercises:

```jsx
import FillInBlankExercise from './components/code-editor/FillInBlankExercise'

// Example usage
const exerciseData = {
  title: "Complete the Python Function",
  description: "Fill in the missing parts to create a working function",
  template: `def calculate_sum(a, b):
    return ___var1___ + ___var2___`,
  expectedAnswers: {
    "var1": "a",
    "var2": "b"
  },
  hints: ["Use the parameter names", "Both blanks should be variables"]
}

<FillInBlankExercise 
  exerciseData={exerciseData}
  onSubmit={(code, result, answers) => console.log('Submitted:', answers)}
  onValidate={(results, answers) => console.log('Validation:', results)}
/>
```

The React implementation uses CodeMirror 6's `WidgetType` and `Decoration` system internally:

```javascript
class FillInBlankWidget extends WidgetType {
  constructor(id, placeholder, value, onChange) {
    super()
    this.id = id
    this.placeholder = placeholder
    this.value = value
    this.onChange = onChange
  }

  toDOM() {
    const input = document.createElement('input')
    input.type = 'text'
    input.className = 'fill-blank-input'
    input.placeholder = this.placeholder
    input.value = this.value
    
    // React-style event handling
    input.addEventListener('input', (e) => {
      this.onChange(this.id, e.target.value)
    })
    
    return input
  }

  ignoreEvent() { return true }
}
```

### 1.1. Widget Implementation Details

The React implementation uses several key CodeMirror 6 concepts for widget management:

#### StateField for Widget Management
```javascript
import { StateField, StateEffect } from '@codemirror/state'
import { Decoration } from '@codemirror/view'

// Effect for updating fill-in-blank widgets
const updateFillBlanksEffect = StateEffect.define()

// State field to manage fill-in-blank decorations
const fillBlanksField = StateField.define({
  create() {
    return Decoration.set([])
  },
  update(decorations, tr) {
    decorations = decorations.map(tr.changes)
    
    for (let effect of tr.effects) {
      if (effect.is(updateFillBlanksEffect)) {
        decorations = Decoration.set(effect.value)
      }
    }
    
    return decorations
  },
  provide: f => EditorView.decorations.from(f)
})
```

#### ViewPlugin Integration
```javascript
import { ViewPlugin } from '@codemirror/view'

const fillBlanksPlugin = ViewPlugin.fromClass(class {
  constructor(view) {
    this.decorations = view.state.field(fillBlanksField)
  }

  update(update) {
    this.decorations = update.state.field(fillBlanksField)
  }
}, {
  decorations: v => v.decorations
})
```

#### Dynamic Widget Creation
The React components create widgets dynamically based on fill-blank configuration:

```javascript
const createFillBlankDecorations = useCallback(() => {
  if (!fillBlanks.length) return []

  const doc = editorRef.current?.view?.state.doc
  if (!doc) return []

  const decorations = []
  
  fillBlanks.forEach(blank => {
    const { id, position, placeholder } = blank
    const value = fillBlankValues[id] || ''
    
    if (position >= 0 && position <= doc.length) {
      const widget = new FillInBlankWidget(
        id, 
        placeholder, 
        value, 
        handleFillBlankChange
      )
      
      decorations.push(
        Decoration.widget({
          widget,
          side: 1  // Place widget after the position
        }).range(position)
      )
    }
  })

  return decorations
}, [fillBlanks, fillBlankValues, handleFillBlankChange])
```

#### Widget Lifecycle Management
The React implementation properly manages widget lifecycles:

```javascript
// Update decorations when fill blanks change
useEffect(() => {
  if (editorRef.current?.view) {
    const decorations = createFillBlankDecorations()
    editorRef.current.view.dispatch({
      effects: updateFillBlanksEffect.of(decorations)
    })
  }
}, [createFillBlankDecorations])
```

### 1.2. Advanced Code Playground

The `AdvancedCodePlayground` component demonstrates more complex widget usage:

```jsx
import AdvancedCodePlayground from './components/code-editor/AdvancedCodePlayground'

<AdvancedCodePlayground
  initialCode="print('Hello, World!')"
  language="python"
  onSave={(codeData) => console.log('Saved:', codeData)}
  onExecute={(code, result) => console.log('Executed:', result)}
/>
```

This component includes:
- Real-time code execution
- File loading/saving capabilities
- Theme switching
- Auto-save functionality
- Keyboard shortcuts (Ctrl+S to save, Ctrl+Enter to run)

### 2. Theme Integration

The CodeMirror implementation includes custom themes that integrate with the platform-wide theming system:

- VS Code Dark theme for dark mode
- GitHub Light theme for light mode
- Automatic theme switching based on user preference

The theme integration uses CSS variables from the main theme system to ensure consistency across the platform.

### 3. Language Support

CodeMirror is configured with support for multiple programming languages, with special emphasis on Python:

- Python (primary language)
- JavaScript
- HTML/CSS
- SQL
- Java
- C/C++

Language modes are loaded dynamically based on the context to optimize performance.

### 4. Docker Executor Integration

The editor integrates with the Docker-based code execution system:

```javascript
// Example of code execution integration
document.querySelector('.run-code-btn').addEventListener('click', async () => {
  const code = editor.state.doc.toString();
  
  try {
    const response = await fetch('/api/v1/execute/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, language: 'python' })
    });
    
    const result = await response.json();
    outputElement.textContent = result.output;
  } catch (error) {
    console.error('Code execution failed:', error);
  }
});
```

### 5. Accessibility Features

The CodeMirror implementation includes several accessibility enhancements:

- Keyboard navigation improvements
- Screen reader compatibility
- High contrast theme options
- Customizable font size and family

## Usage in Templates

To implement the CodeMirror editor in templates:

```html
<div class="code-editor" data-language="python" data-theme="auto">
  <div id="editor-container"></div>
  <div class="editor-toolbar">
    <button class="run-code-btn">Run Code</button>
    <button class="reset-code-btn">Reset</button>
  </div>
  <div id="output-container"></div>
</div>

{% block extra_js %}
<script src="{% static 'js/dist/codemirror-enhanced.bundle.js' %}"></script>
<script>
  document.addEventListener('DOMContentLoaded', () => {
    initCodeMirror('editor-container', {
      language: 'python',
      theme: getUserThemePreference(),
      readOnly: false,
      autocompletion: true
    });
  });
</script>
{% endblock %}
```

## Integration with Exercise System

The CodeMirror editor is tightly integrated with the platform's exercise system:

1. **Code Submission**: Student code is captured from the editor for evaluation
2. **Test Case Execution**: Test cases run against the submitted code in Docker containers
3. **Feedback Display**: Execution results, errors, and hints are displayed in the UI
4. **Progress Tracking**: Successful submissions update the student's progress

## Extending the Editor

### Adding Custom Extensions

```javascript
import { EditorView } from "codemirror";
import { customExtension } from "./custom-extension";

// Add custom extension to editor
const editor = new EditorView({
  extensions: [
    basicSetup,
    pythonLanguage,
    customExtension(),
    // Other extensions
  ],
  parent: document.getElementById("editor-container")
});
```

### Creating Custom Themes

```javascript
import { EditorView } from "codemirror";
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { tags } from "@lezer/highlight";

// Define custom theme
const customTheme = EditorView.theme({
  // Theme configuration
});

const customHighlightStyle = HighlightStyle.define([
  // Syntax highlighting rules
]);

// Use in editor
const theme = [customTheme, syntaxHighlighting(customHighlightStyle)];
```

## Performance Considerations

1. The CodeMirror bundles are loaded asynchronously to improve page load performance
2. Language packages are loaded on-demand to reduce initial bundle size
3. Editor instances are properly disposed when no longer needed to prevent memory leaks

## Browser Compatibility

The CodeMirror 6 implementation has been tested and works in:

- Chrome 80+
- Firefox 72+
- Safari 13.1+
- Edge 80+

## Troubleshooting

### Common Issues

1. **Editor not loading**: Check console for script loading errors
2. **Theme not applying**: Verify the theme system integration is working correctly
3. **Performance issues**: Large files may need additional optimization settings

### Debug Steps

1. Check browser console for errors
2. Verify that all required dependencies are loaded
3. Inspect the DOM to ensure editor elements are properly rendered
4. Test with a minimal configuration to isolate issues

## Future Enhancements

1. **Collaborative editing**: Integration with operational transforms for real-time collaboration
2. **Enhanced debugging**: In-editor debugging capabilities for Python code
3. **Mobile optimization**: Improved touch controls and responsiveness
4. **Additional language support**: More programming languages and language-specific features
