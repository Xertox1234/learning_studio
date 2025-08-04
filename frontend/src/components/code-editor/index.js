// CodeMirror 6 React Components Export
export { default as InteractiveCodeEditor } from './InteractiveCodeEditor.jsx'
export { default as FillInBlankExercise } from './FillInBlankExercise.jsx'
export { default as AdvancedCodePlayground } from './AdvancedCodePlayground.jsx'
export { default as EditableCodePlayground } from './EditableCodePlayground.jsx'
export { default as ProgressiveHintPanel } from './ProgressiveHintPanel.jsx'
export { default as ReadOnlyCodeBlock } from './ReadOnlyCodeBlock.jsx'

// Test and development components
export { default as CodeBlockTest } from './CodeBlockTest.jsx'

// Re-export useful CodeMirror types and utilities for custom implementations
export {
  WidgetType,
  Decoration,
  ViewPlugin
} from '@codemirror/view'

export {
  EditorState,
  StateField,
  StateEffect
} from '@codemirror/state'