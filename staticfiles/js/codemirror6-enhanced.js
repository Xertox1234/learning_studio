/**
 * Enhanced CodeMirror 6 Implementation
 * Supports both fill-in-blanks and regular code highlighting
 * With VS Code Dark theme
 */

import { EditorView, basicSetup } from "codemirror"
import { python } from "@codemirror/lang-python"
import { javascript } from "@codemirror/lang-javascript"
import { EditorState, StateField, StateEffect } from "@codemirror/state"
import { Decoration, WidgetType, ViewPlugin, MatchDecorator } from "@codemirror/view"
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language"
import { tags as t } from "@lezer/highlight"

// VS Code Dark theme (inline)
const vscodeTheme = [
  EditorView.theme({
    "&": {
      color: "#abb2bf",
      backgroundColor: "#282c34"
    },
    ".cm-content": {
      caretColor: "#528bff",
      padding: "16px",
      minHeight: "200px",
      fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'SF Mono', Consolas, monospace",
      fontSize: "14px",
      lineHeight: "1.5"
    },
    ".cm-cursor, .cm-dropCursor": { borderLeftColor: "#0d6efd" },
    ".cm-selectionBackground, ::selection": { backgroundColor: "#3e4451" },
    ".cm-activeLine": { backgroundColor: "#2c313c" },
    ".cm-gutters": {
      backgroundColor: "#282c34",
      color: "#7d8799",
      border: "none"
    },
    ".cm-activeLineGutter": {
      backgroundColor: "#2c313a"
    },
    ".cm-foldPlaceholder": {
      backgroundColor: "transparent",
      border: "none",
      color: "#ddd"
    }
  }, { dark: true }),
  syntaxHighlighting(HighlightStyle.define([
    { tag: t.keyword, color: "#c678dd" },
    { tag: [t.name, t.deleted, t.character, t.propertyName, t.macroName], color: "#e06c75" },
    { tag: [t.function(t.variableName), t.labelName], color: "#61afef" },
    { tag: [t.color, t.constant(t.name), t.standard(t.name)], color: "#d19a66" },
    { tag: [t.definition(t.name), t.separator], color: "#abb2bf" },
    { tag: [t.typeName, t.className, t.number, t.changed, t.annotation, t.modifier, t.self, t.namespace], color: "#e5c07b" },
    { tag: [t.operator, t.operatorKeyword, t.url, t.escape, t.regexp, t.link, t.special(t.string)], color: "#56b6c2" },
    { tag: [t.meta, t.comment], color: "#7d8799" },
    { tag: t.strong, fontWeight: "bold" },
    { tag: t.emphasis, fontStyle: "italic" },
    { tag: t.link, color: "#7d8799", textDecoration: "underline" },
    { tag: t.heading, fontWeight: "bold", color: "#e06c75" },
    { tag: [t.atom, t.bool, t.special(t.variableName)], color: "#d19a66" },
    { tag: [t.processingInstruction, t.string, t.inserted], color: "#98c379" },
    { tag: t.invalid, color: "#ffffff" },
  ]))
]

// State effect for updating blank values in fill-in-blanks
const updateBlankEffect = StateEffect.define({
    map: (val, mapping) => val
})

// State field to track blank values
const blankValuesField = StateField.define({
    create() {
        return new Map()
    },
    update(value, tr) {
        for (let effect of tr.effects) {
            if (effect.is(updateBlankEffect)) {
                const newMap = new Map(value)
                newMap.set(effect.value.blankId, effect.value.newValue)
                return newMap
            }
        }
        return value
    }
})

// Widget for rendering input fields inline in fill-in-blanks
class BlankInputWidget extends WidgetType {
    constructor(blankInfo, currentValue = '') {
        super()
        this.blankInfo = blankInfo
        this.currentValue = currentValue
    }

    eq(other) {
        return other.blankInfo.id === this.blankInfo.id && 
               other.currentValue === this.currentValue
    }

    toDOM(view) {
        const container = document.createElement("span")
        container.className = "blank-input-container"
        container.style.cssText = `
            display: inline-block;
            position: relative;
            z-index: 10;
        `
        
        const input = document.createElement("input")
        input.type = "text"
        input.className = "blank-input"
        input.placeholder = this.blankInfo.placeholder || `Enter ${this.blankInfo.id}`
        input.value = this.currentValue
        input.dataset.blankId = this.blankInfo.id
        
        // Styling to match VS Code theme with Bootstrap blue accents
        input.style.cssText = `
            background: #3c4043;
            border: 2px solid #5f6368;
            border-radius: 6px;
            color: #e8eaed;
            font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace;
            font-size: 14px;
            font-weight: 500;
            padding: 6px 10px;
            min-width: 120px;
            max-width: 200px;
            outline: none;
            margin: 0 4px;
            transition: all 0.2s ease;
            box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3);
            position: relative;
            z-index: 11;
        `
        
        // Prevent CodeMirror from intercepting events
        input.addEventListener('mousedown', (e) => {
            e.stopPropagation()
        })
        
        input.addEventListener('click', (e) => {
            e.stopPropagation()
            input.focus()
        })
        
        input.addEventListener('keydown', (e) => {
            e.stopPropagation()
        })
        
        input.addEventListener('keyup', (e) => {
            e.stopPropagation()
        })
        
        input.addEventListener('keypress', (e) => {
            e.stopPropagation()
        })
        
        // Focus/blur effects
        input.addEventListener('focus', (e) => {
            e.stopPropagation()
            input.style.borderColor = '#0d6efd'
            input.style.boxShadow = '0 0 0 2px rgba(13, 110, 253, 0.3)'
        })
        
        input.addEventListener('blur', (e) => {
            e.stopPropagation()
            input.style.borderColor = '#5f6368'
            input.style.boxShadow = 'inset 0 1px 3px rgba(0, 0, 0, 0.3)'
        })
        
        // Update state when input changes
        input.addEventListener('input', (e) => {
            e.stopPropagation()
            view.dispatch({
                effects: updateBlankEffect.of({
                    blankId: this.blankInfo.id,
                    newValue: e.target.value
                })
            })
        })
        
        container.appendChild(input)
        return container
    }

    ignoreEvent(event) {
        // Allow all input-related events to be handled by the input field
        return true
    }
}

// Match decorator to find {{BLANK_X}} patterns
const blankMatcher = new MatchDecorator({
    regexp: /\{\{(BLANK_\d+)\}\}/g,
    decoration: (match, view, pos) => {
        const blankId = match[1]
        const blankValues = view.state.field(blankValuesField)
        const currentValue = blankValues.get(blankId) || ''
        
        // Get blank info from dataset
        const editorElement = view.dom.closest('.interactive-code-block')
        const blanksData = editorElement ? JSON.parse(editorElement.dataset.blanks || '[]') : []
        const blankInfo = blanksData.find(b => b.id === blankId) || { id: blankId, placeholder: blankId }
        
        return Decoration.replace({
            widget: new BlankInputWidget(blankInfo, currentValue)
        })
    }
})

// View plugin to manage decorations for fill-in-blanks
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

// Enhanced CodeMirror 6 Editor class
class CodeMirror6Editor {
    constructor(textarea, options = {}) {
        this.textarea = textarea
        this.options = {
            language: 'python',
            readonly: false,
            lineNumbers: true,
            fillBlanks: false,
            theme: 'vscode-dark',
            ...options
        }
        this.initializeEditor()
    }

    initializeEditor() {
        // Determine language
        const language = this.getLanguageExtension()
        
        // Base extensions
        const extensions = [
            basicSetup,
            language,
            vscodeTheme,
            EditorView.lineWrapping,
            EditorView.updateListener.of((update) => {
                if (update.docChanged) {
                    this.textarea.value = this.view.state.doc.toString()
                }
            })
        ]

        // Add fill-in-blanks support if needed
        if (this.options.fillBlanks) {
            extensions.push(blankValuesField, blankPlugin)
        }

        // Add readonly state if needed
        if (this.options.readonly) {
            extensions.push(EditorState.readOnly.of(true))
        }

        // Create editor view
        this.view = new EditorView({
            doc: this.textarea.value,
            extensions,
            parent: this.createEditorContainer()
        })

        // Hide original textarea
        this.textarea.style.display = 'none'
    }

    createEditorContainer() {
        const container = document.createElement('div')
        container.className = 'codemirror-container'
        container.style.cssText = `
            border: 1px solid #4a5568;
            border-radius: 8px;
            overflow: hidden;
            background: #282c34;
            margin: 16px 0;
        `

        // Insert after textarea
        this.textarea.parentNode.insertBefore(container, this.textarea.nextSibling)
        return container
    }

    getLanguageExtension() {
        const lang = this.options.language || this.textarea.dataset.language || 'python'
        switch (lang.toLowerCase()) {
            case 'python':
                return python()
            case 'javascript':
            case 'js':
                return javascript()
            default:
                return python() // Default to Python
        }
    }

    // Get blank values for fill-in-blanks exercises
    getBlankValues() {
        if (!this.options.fillBlanks) return new Map()
        return this.view.state.field(blankValuesField)
    }

    // Update editor content
    updateContent(newContent) {
        this.view.dispatch({
            changes: {
                from: 0,
                to: this.view.state.doc.length,
                insert: newContent
            }
        })
    }

    // Destroy editor
    destroy() {
        if (this.view) {
            this.view.destroy()
            this.textarea.style.display = ''
        }
    }
}

// Enhanced Fill-in-Blanks class using CodeMirror 6
class EnhancedFillInBlanks {
    constructor(textarea) {
        this.textarea = textarea
        this.container = textarea.closest('.interactive-code-block')
        if (!this.container || this.container.dataset.exerciseType !== 'fill_blank') {
            return
        }
        this.initializeEditor()
    }

    initializeEditor() {
        // Create editor wrapper
        this.createEditorWrapper()
        
        // Parse blanks data
        this.parseBlanksData()
        
        // Initialize CodeMirror with fill-blanks support
        this.editor = new CodeMirror6Editor(this.textarea, {
            fillBlanks: true,
            readonly: false,
            lineNumbers: true
        })
        
        // Setup event listeners
        this.setupEventListeners()
    }

    createEditorWrapper() {
        this.wrapper = document.createElement('div')
        this.wrapper.className = 'enhanced-fill-blank-wrapper'
        
        // Create header
        this.header = document.createElement('div')
        this.header.className = 'enhanced-fill-blank-header'
        this.header.style.cssText = `
            background: #2d3748;
            padding: 14px 20px;
            border-bottom: 1px solid #4a5568;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #e2e8f0;
        `
        
        this.header.innerHTML = `
            <span style="font-weight: 600; display: flex; align-items: center; gap: 8px;">
                <i class="bi bi-lightning-charge"></i> Interactive Code Exercise
            </span>
            <div style="display: flex; gap: 10px;">
                <button class="btn btn-sm btn-outline-primary check-answers-btn">
                    <i class="bi bi-check-circle"></i> Check Answers
                </button>
                <button class="btn btn-sm btn-primary run-code-btn" disabled>
                    <i class="bi bi-play-fill"></i> Run Code
                </button>
            </div>
        `
        
        // Create results panel
        this.resultsPanel = document.createElement('div')
        this.resultsPanel.className = 'enhanced-results-panel'
        this.resultsPanel.style.cssText = `
            background: #2d3748;
            border-top: 1px solid #4a5568;
            padding: 20px;
            display: none;
        `
        
        // Assemble wrapper
        this.wrapper.appendChild(this.header)
        this.wrapper.appendChild(this.resultsPanel)
        
        // Insert into DOM
        this.container.appendChild(this.wrapper)
    }

    parseBlanksData() {
        try {
            this.blanksData = this.container.dataset.blanks ? 
                JSON.parse(this.container.dataset.blanks) : []
        } catch (e) {
            console.warn('Could not parse blanks data:', e)
            this.blanksData = []
        }
    }

    setupEventListeners() {
        const checkBtn = this.header.querySelector('.check-answers-btn')
        const runBtn = this.header.querySelector('.run-code-btn')
        
        checkBtn.addEventListener('click', () => this.checkAnswers())
        runBtn.addEventListener('click', () => this.runCode())
    }

    checkAnswers() {
        const blankValues = this.editor.getBlankValues()
        
        const expectedAnswers = {
            'BLANK_1': {
                validate: (value) => /^["'][^"']+["']$/.test(value.trim()),
                description: 'Any quoted name (e.g., "John")'
            },
            'BLANK_2': {
                validate: (value) => {
                    const num = parseInt(value.trim())
                    return !isNaN(num) && num >= 18 && num <= 65
                },
                description: 'Any number between 18-65'
            },
            'BLANK_3': {
                validate: (value) => ['True', 'False'].includes(value.trim()),
                description: 'True or False (capital T/F)'
            }
        }
        
        let results = []
        let allCorrect = true
        
        for (let [blankId, userAnswer] of blankValues) {
            const expected = expectedAnswers[blankId]
            const isCorrect = expected ? expected.validate(userAnswer) : false
            
            results.push({
                blankId,
                userAnswer,
                isCorrect,
                description: expected ? expected.description : 'Valid input required'
            })
            
            if (!isCorrect) allCorrect = false
        }
        
        this.displayResults(results, allCorrect)
        
        // Enable/disable run button
        const runBtn = this.header.querySelector('.run-code-btn')
        runBtn.disabled = !allCorrect
    }

    displayResults(results, allCorrect) {
        let html = `
            <h6 style="color: #e2e8f0; margin-bottom: 16px;">
                <i class="bi bi-clipboard-check"></i> Answer Check Results
            </h6>
        `
        
        results.forEach(result => {
            const icon = result.isCorrect ? 'bi-check-circle-fill text-success' : 'bi-x-circle-fill text-danger'
            const status = result.isCorrect ? 'Correct' : 'Incorrect'
            
            html += `
                <div style="margin-bottom: 10px; padding: 12px; background: #374151; border-radius: 6px; border-left: 4px solid ${result.isCorrect ? '#0d6efd' : '#fc8181'};">
                    <i class="bi ${icon}"></i>
                    <strong>${result.blankId}:</strong> ${status}
                    ${!result.isCorrect ? `<br><small style="color: #a0aec0;">Expected: ${result.description}</small>` : ''}
                </div>
            `
        })
        
        const overallMessage = allCorrect ? 
            'Excellent! All answers are correct. You can now run the code.' :
            'Some answers need attention. Please review and try again.'
        
        html += `
            <div style="margin-top: 16px; padding: 16px; background: ${allCorrect ? '#1e40af' : '#1e3a8a'}; border-radius: 8px; color: #dbeafe;">
                <i class="bi ${allCorrect ? 'bi-trophy-fill' : 'bi-exclamation-triangle-fill'}"></i> ${overallMessage}
            </div>
        `
        
        this.resultsPanel.innerHTML = html
        this.resultsPanel.style.display = 'block'
    }

    runCode() {
        const blankValues = this.editor.getBlankValues()
        
        const name = blankValues.get('BLANK_1') || '"YourName"'
        const age = blankValues.get('BLANK_2') || 'YourAge'
        const isStudent = blankValues.get('BLANK_3') || 'True/False'
        
        const output = `Hello, my name is ${name.replace(/['"]/g, '')}
I am ${age} years old
Am I a student? ${isStudent}`
        
        const html = `
            <h6 style="color: #e2e8f0; margin-bottom: 16px;">
                <i class="bi bi-play-circle"></i> Code Output
            </h6>
            <div style="background: #1e1e1e; border: 1px solid #4b5563; border-radius: 8px; padding: 16px;">
                <pre style="color: #0d6efd; margin: 0; font-family: 'Cascadia Code', monospace;">${output}</pre>
            </div>
        `
        
        this.resultsPanel.innerHTML = html
        this.resultsPanel.style.display = 'block'
    }
}

// Regular code example highlighting
class CodeExampleHighlighter {
    constructor(textarea) {
        this.textarea = textarea
        if (textarea.classList.contains('code-editor') || textarea.classList.contains('interactive-code-editor')) {
            this.initializeEditor()
        }
    }

    initializeEditor() {
        const isInteractive = this.textarea.classList.contains('interactive-code-editor')
        const container = this.textarea.closest('.interactive-code-block')
        const isFillBlank = container && container.dataset.exerciseType === 'fill_blank'
        
        // Don't initialize if it's a fill-blank exercise (handled by EnhancedFillInBlanks)
        if (isFillBlank) return
        
        this.editor = new CodeMirror6Editor(this.textarea, {
            readonly: !isInteractive,
            lineNumbers: true,
            fillBlanks: false
        })
    }
}

// Auto-initialization
function initializeCodeMirror() {
    // Initialize fill-in-blanks exercises
    document.querySelectorAll('.interactive-code-editor').forEach(textarea => {
        const container = textarea.closest('.interactive-code-block')
        if (container && container.dataset.exerciseType === 'fill_blank') {
            new EnhancedFillInBlanks(textarea)
        }
    })
    
    // Initialize regular code editors
    document.querySelectorAll('.code-editor, .interactive-code-editor').forEach(textarea => {
        new CodeExampleHighlighter(textarea)
    })
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCodeMirror)
} else {
    initializeCodeMirror()
}

// Export classes for manual use
window.CodeMirror6Editor = CodeMirror6Editor
window.EnhancedFillInBlanks = EnhancedFillInBlanks
window.initializeCodeMirror = initializeCodeMirror