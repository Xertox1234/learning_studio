/**
 * Simple CodeMirror 6 with fill-in-the-blank functionality
 */

import {EditorView, basicSetup} from "codemirror"
import {python} from "@codemirror/lang-python"
import {Decoration, WidgetType, ViewPlugin, MatchDecorator} from "@codemirror/view"

class BlankWidget extends WidgetType {
  constructor(placeholder) {
    super()
    this.placeholder = placeholder
  }

  eq(other) {
    return other.placeholder === this.placeholder
  }

  toDOM() {
    const input = document.createElement("input")
    input.type = "text"
    input.placeholder = this.placeholder
    input.style.cssText = `
      background: #374151;
      border: 1px solid #4b5563;
      border-radius: 4px;
      color: #e5e7eb;
      font-family: inherit;
      font-size: inherit;
      padding: 4px 8px;
      min-width: 120px;
      outline: none;
      margin: 0 2px;
    `
    return input
  }

  ignoreEvent() {
    return false
  }
}

const blankMatcher = new MatchDecorator({
  regexp: /\{\{BLANK_(\d+)\}\}/g,
  decoration: match => Decoration.replace({
    widget: new BlankWidget(`BLANK_${match[1]}`)
  })
})

const blankPlugin = ViewPlugin.fromClass(class {
  decorations

  constructor(view) {
    this.decorations = blankMatcher.createDeco(view)
  }

  update(update) {
    this.decorations = blankMatcher.updateDeco(update, this.decorations)
  }
}, {
  decorations: v => v.decorations
})

// Initialize editors
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.interactive-code-editor').forEach(textarea => {
    const view = new EditorView({
      doc: textarea.value,
      extensions: [
        basicSetup,
        python(),
        blankPlugin,
        EditorView.theme({
          "&": { fontSize: "14px" },
          ".cm-content": { padding: "16px" },
          ".cm-editor": { backgroundColor: "#1e1e1e" }
        })
      ],
      parent: textarea.parentElement
    })
    
    textarea.style.display = 'none'
  })
})