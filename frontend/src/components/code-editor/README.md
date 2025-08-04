# CodeMirror 6 Components

This directory contains CodeMirror 6 React components for the Python Learning Studio frontend.

## Components

### ReadOnlyCodeBlock

A read-only CodeMirror 6 component for displaying syntax-highlighted code blocks in lessons and documentation.

**Features:**
- Syntax highlighting for Python, JavaScript, Java, C++, HTML, CSS
- Automatic theme switching (light/dark mode)
- Read-only display with line numbers
- Clean, bordered appearance matching the design system
- Performance optimized for multiple code blocks

**Usage:**
```jsx
import { ReadOnlyCodeBlock } from '../components/code-editor'

// Basic usage
<ReadOnlyCodeBlock 
  code="print('Hello, World!')" 
  language="python" 
/>

// With custom options
<ReadOnlyCodeBlock 
  code={codeString}
  language="javascript"
  showLineNumbers={true}
  className="my-custom-class"
/>
```

**Supported Languages:**
- `python` - Python syntax highlighting
- `javascript` / `js` - JavaScript syntax highlighting
- `java` - Java syntax highlighting
- `cpp` / `c++` - C++ syntax highlighting
- `html` - HTML syntax highlighting
- `css` - CSS syntax highlighting
- `text` - Plain text (no highlighting)

**Integration with LessonContent:**

The component is automatically used by the `LessonContent` component in `LessonPage.jsx` to render markdown-style code blocks:

```markdown
## Python Example

Here's a simple Python function:

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Generate first 10 numbers
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
```

This will be rendered with proper Python syntax highlighting.
```

**Theme Integration:**

The component automatically adapts to the current theme using the `useTheme()` hook:
- **Light mode**: Clean white background with subtle borders
- **Dark mode**: Dark background using CodeMirror's oneDark theme
- **Colors**: Consistent with the application's design system

### InteractiveCodeEditor

Interactive CodeMirror 6 component for fill-in-the-blank exercises with widget support.

### FillInBlankExercise

Complete exercise interface combining the interactive editor with validation and hint systems.

### AdvancedCodePlayground

Full-featured code editor with execution capabilities.

## Dependencies

- `@uiw/react-codemirror` - React wrapper for CodeMirror 6
- `@codemirror/lang-*` - Language support packages
- `@codemirror/theme-one-dark` - Dark theme
- `@codemirror/view` - Editor view components
- `@codemirror/state` - Editor state management