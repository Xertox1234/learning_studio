/**
 * Enhanced Fill-in-the-Blanks Implementation
 * Based on CodeMirror 6 and matching the screenshot design
 */

import { EditorView, basicSetup } from "https://cdn.skypack.dev/codemirror@6.0.1"
import { python } from "https://cdn.skypack.dev/@codemirror/lang-python@6.1.3"
import { EditorState, StateField, StateEffect } from "https://cdn.skypack.dev/@codemirror/state@6.4.1"
import { Decoration, WidgetType, ViewPlugin, MatchDecorator } from "https://cdn.skypack.dev/@codemirror/view@6.26.3"

// State effect for updating blank values
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

// Widget for rendering input fields inline
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
        
        const input = document.createElement("input")
        input.type = "text"
        input.className = "blank-input"
        input.placeholder = this.blankInfo.placeholder || `Enter ${this.blankInfo.id}`
        input.value = this.currentValue
        input.dataset.blankId = this.blankInfo.id
        
        // Styling to match the screenshot
        // Apply individual styles to avoid conflicts
        input.style.background = '#000000'
        input.style.border = '2px solid #375a7f'
        input.style.borderRadius = '6px'
        input.style.color = '#ffffff'
        input.style.fontFamily = "'Cascadia Code', 'Fira Code', monospace"
        input.style.fontSize = '14px'
        input.style.padding = '8px 12px'
        input.style.outline = 'none'
        input.style.margin = '0 4px'
        input.style.transition = 'all 0.2s ease'
        // Don't set width here - let CSS and size attribute handle it
        
        // Focus/blur effects
        input.addEventListener('focus', () => {
            input.style.borderColor = '#375a7f'
            input.style.boxShadow = '0 0 0 2px rgba(55, 90, 127, 0.2)'
        })
        
        input.addEventListener('blur', () => {
            input.style.borderColor = '#375a7f'
            input.style.boxShadow = 'none'
        })
        
        // Function to auto-resize input based on content
        const autoResize = () => {
            const text = input.value || input.placeholder || ''
            // Use a more reliable approach: set size attribute based on character count
            const minSize = 4
            const size = Math.max(minSize, text.length + 2)
            input.setAttribute('size', size)
            
            // Also set style width as backup
            const charWidth = 8.5 // approximate character width in pixels for monospace
            const newWidth = Math.max(60, size * charWidth + 24) // 24px for padding and border
            input.style.width = newWidth + 'px'
        }
        
        // Auto-resize on input and initially
        input.addEventListener('input', (e) => {
            autoResize()
            view.dispatch({
                effects: updateBlankEffect.of({
                    blankId: this.blankInfo.id,
                    newValue: e.target.value
                })
            })
        })
        
        // Also resize on keyup for better responsiveness
        input.addEventListener('keyup', autoResize)
        
        // Initial resize
        setTimeout(autoResize, 0)
        
        container.appendChild(input)
        return container
    }

    ignoreEvent() {
        return false
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

// View plugin to manage decorations
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

// Main function to initialize fill-in-the-blanks editors
export function initializeFillInBlanks() {
    document.querySelectorAll('.interactive-code-editor').forEach(textarea => {
        const container = textarea.closest('.interactive-code-block')
        if (!container || container.dataset.exerciseType !== 'fill_blank') {
            return
        }

        // Create editor wrapper
        const wrapper = document.createElement('div')
        wrapper.className = 'fill-blank-editor-wrapper'
        wrapper.style.cssText = `
            background: #1e1e1e;
            border: 1px solid #374151;
            border-radius: 8px;
            overflow: hidden;
            margin: 16px 0;
        `

        // Create header
        const header = document.createElement('div')
        header.className = 'fill-blank-header'
        header.style.cssText = `
            background: #374151;
            padding: 12px 16px;
            border-bottom: 1px solid #4b5563;
            display: flex;
            justify-content: space-between;
            align-items: center;
        `
        
        const title = document.createElement('span')
        title.textContent = 'Fill in the Blanks'
        title.style.cssText = `
            color: #e5e7eb;
            font-weight: 600;
            font-size: 14px;
        `
        
        const actions = document.createElement('div')
        actions.className = 'fill-blank-actions'
        actions.style.cssText = `
            display: flex;
            gap: 8px;
        `
        
        // Check Answers button
        const checkBtn = document.createElement('button')
        checkBtn.className = 'btn btn-sm btn-outline-info'
        checkBtn.innerHTML = '<i class="bi bi-check-circle"></i> Check Answers'
        checkBtn.addEventListener('click', () => checkAnswers(view, container))
        
        // Run Code button  
        const runBtn = document.createElement('button')
        runBtn.className = 'btn btn-sm btn-primary'
        runBtn.innerHTML = '<i class="bi bi-play-fill"></i> Run Code'
        runBtn.addEventListener('click', () => runCode(view, container))
        
        actions.appendChild(checkBtn)
        actions.appendChild(runBtn)
        header.appendChild(title)
        header.appendChild(actions)
        
        // Create editor container
        const editorContainer = document.createElement('div')
        editorContainer.style.cssText = `
            min-height: 200px;
            font-family: 'Cascadia Code', 'Fira Code', monospace;
        `

        // Initialize CodeMirror 6
        const view = new EditorView({
            doc: textarea.value,
            extensions: [
                basicSetup,
                python(),
                blankValuesField,
                blankPlugin,
                EditorView.theme({
                    "&": { 
                        fontSize: "14px",
                        height: "100%"
                    },
                    ".cm-content": { 
                        padding: "16px",
                        minHeight: "200px"
                    },
                    ".cm-editor": { 
                        backgroundColor: "#1e1e1e",
                        color: "#e5e7eb"
                    },
                    ".cm-focused": {
                        outline: "none"
                    },
                    ".cm-cursor": {
                        borderLeftColor: "#375a7f"
                    },
                    ".cm-activeLine": {
                        backgroundColor: "rgba(255, 255, 255, 0.05)"
                    }
                }),
                EditorView.updateListener.of((update) => {
                    // Sync with original textarea
                    textarea.value = view.state.doc.toString()
                })
            ],
            parent: editorContainer
        })

        // Create result panel
        const resultPanel = document.createElement('div')
        resultPanel.className = 'fill-blank-results'
        resultPanel.style.cssText = `
            background: #374151;
            border-top: 1px solid #4b5563;
            padding: 16px;
            display: none;
        `

        // Assemble the editor
        wrapper.appendChild(header)
        wrapper.appendChild(editorContainer)
        wrapper.appendChild(resultPanel)
        
        // Replace textarea with new editor
        textarea.parentNode.insertBefore(wrapper, textarea)
        textarea.style.display = 'none'
        
        // Store references for later use
        container.fillBlankEditor = {
            view,
            wrapper,
            resultPanel,
            checkBtn,
            runBtn
        }
    })
}

// Function to check answers
function checkAnswers(view, container) {
    const blankValues = view.state.field(blankValuesField)
    const resultPanel = container.fillBlankEditor.resultPanel
    
    // Get expected answers (you can define these based on your requirements)
    const expectedAnswers = {
        'BLANK_1': ['"John"', '"Mary"', '"Sarah"', '"Mike"'], // Accept any quoted string
        'BLANK_2': Array.from({length: 48}, (_, i) => String(i + 18)), // 18-65
        'BLANK_3': ['True', 'False']
    }
    
    let results = []
    let allCorrect = true
    
    for (let [blankId, userAnswer] of blankValues) {
        const expected = expectedAnswers[blankId] || []
        const isCorrect = expected.some(exp => 
            userAnswer.trim().toLowerCase() === exp.toLowerCase() ||
            (blankId === 'BLANK_1' && /^["'][^"']+["']$/.test(userAnswer.trim())) // Any quoted string
        )
        
        results.push({
            blankId,
            userAnswer,
            isCorrect,
            expected: blankId === 'BLANK_1' ? 'Any quoted name (e.g., "John")' : expected.join(' or ')
        })
        
        if (!isCorrect) allCorrect = false
    }
    
    // Display results
    let resultHTML = `
        <div class="check-results">
            <h6 style="color: #e5e7eb; margin-bottom: 12px;">
                <i class="bi bi-clipboard-check"></i> Answer Check Results
            </h6>
    `
    
    results.forEach(result => {
        const icon = result.isCorrect ? 'bi-check-circle-fill text-success' : 'bi-x-circle-fill text-danger'
        const status = result.isCorrect ? 'Correct' : 'Incorrect'
        
        resultHTML += `
            <div style="margin-bottom: 8px; padding: 8px; background: #2d3748; border-radius: 4px;">
                <i class="bi ${icon}"></i>
                <strong>${result.blankId}:</strong> ${status}
                ${!result.isCorrect ? `<br><small style="color: #9ca3af;">Expected: ${result.expected}</small>` : ''}
            </div>
        `
    })
    
    const overallIcon = allCorrect ? 'bi-trophy-fill text-warning' : 'bi-exclamation-triangle-fill text-info'
    const overallMessage = allCorrect ? 
        'Excellent! All answers are correct. You can now run the code.' :
        'Some answers need attention. Please review and try again.'
    
    resultHTML += `
        <div style="margin-top: 12px; padding: 12px; background: #1e1e1e; border-radius: 6px; border-left: 4px solid ${allCorrect ? '#fbbf24' : '#375a7f'};">
            <i class="bi ${overallIcon}"></i> ${overallMessage}
        </div>
    </div>
    `
    
    resultPanel.innerHTML = resultHTML
    resultPanel.style.display = 'block'
    
    // Enable/disable run button based on results
    container.fillBlankEditor.runBtn.disabled = !allCorrect
    if (allCorrect) {
        container.fillBlankEditor.runBtn.classList.remove('btn-secondary')
        container.fillBlankEditor.runBtn.classList.add('btn-primary')
    } else {
        container.fillBlankEditor.runBtn.classList.remove('btn-primary')
        container.fillBlankEditor.runBtn.classList.add('btn-secondary')
    }
}

// Function to run code (placeholder for actual execution)
function runCode(view, container) {
    const blankValues = view.state.field(blankValuesField)
    const resultPanel = container.fillBlankEditor.resultPanel
    
    // Get the current code with blanks filled
    let code = view.state.doc.toString()
    
    // Replace blanks with actual values
    for (let [blankId, value] of blankValues) {
        const pattern = new RegExp(`\\{\\{${blankId}\\}\\}`, 'g')
        code = code.replace(pattern, value)
    }
    
    // Simulate code execution (in a real implementation, this would call your backend)
    const mockOutput = generateMockOutput(blankValues)
    
    let resultHTML = `
        <div class="run-results">
            <h6 style="color: #e5e7eb; margin-bottom: 12px;">
                <i class="bi bi-play-circle"></i> Code Output
            </h6>
            <div style="background: #1e1e1e; border: 1px solid #4b5563; border-radius: 6px; padding: 12px;">
                <pre style="color: #0d6efd; margin: 0; font-family: 'Cascadia Code', monospace; font-size: 13px;">${mockOutput}</pre>
            </div>
        </div>
    `
    
    resultPanel.innerHTML = resultHTML
    resultPanel.style.display = 'block'
}

// Generate mock output based on filled blanks
function generateMockOutput(blankValues) {
    const name = blankValues.get('BLANK_1') || 'YourName'
    const age = blankValues.get('BLANK_2') || 'YourAge'
    const isStudent = blankValues.get('BLANK_3') || 'True/False'
    
    return `Hello, my name is ${name}
I am ${age} years old
Am I a student? ${isStudent}`
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeFillInBlanks)