/**
 * Simple Fill-in-the-Blanks Implementation
 * Works without external dependencies and matches current theme
 */

class FillInBlanksEditor {
    constructor(textareaElement) {
        this.textarea = textareaElement;
        this.container = textareaElement.closest('.interactive-code-block');
        this.blankValues = new Map();
        this.initializeEditor();
    }

    initializeEditor() {
        if (!this.container || this.container.dataset.exerciseType !== 'fill_blank') {
            return;
        }

        // Create the editor wrapper
        this.createEditorWrapper();
        
        // Parse blanks data
        this.parseBlanksData();
        
        // Replace textarea with interactive editor
        this.replaceTextarea();
        
        // Setup event listeners
        this.setupEventListeners();
    }

    createEditorWrapper() {
        this.wrapper = document.createElement('div');
        this.wrapper.className = 'fill-blank-editor-wrapper';
        
        // Create header
        this.header = document.createElement('div');
        this.header.className = 'fill-blank-header';
        this.header.innerHTML = `
            <span><i class="bi bi-lightning-charge"></i> Fill in the Blanks</span>
            <div class="fill-blank-actions">
                <button class="btn btn-outline-primary check-answers-btn">
                    <i class="bi bi-check-circle"></i> Check Answers
                </button>
                <button class="btn btn-primary run-code-btn" disabled>
                    <i class="bi bi-play-fill"></i> Run Code
                </button>
            </div>
        `;
        
        // Create editor container
        this.editorContainer = document.createElement('div');
        this.editorContainer.className = 'fill-blank-editor';
        
        // Create results panel
        this.resultsPanel = document.createElement('div');
        this.resultsPanel.className = 'fill-blank-results';
        this.resultsPanel.style.display = 'none';
        
        // Assemble wrapper
        this.wrapper.appendChild(this.header);
        this.wrapper.appendChild(this.editorContainer);
        this.wrapper.appendChild(this.resultsPanel);
    }

    parseBlanksData() {
        try {
            this.blanksData = this.container.dataset.blanks ? 
                JSON.parse(this.container.dataset.blanks) : [];
        } catch (e) {
            console.warn('Could not parse blanks data:', e);
            this.blanksData = [];
        }
    }

    replaceTextarea() {
        // Get the original code content
        const originalCode = this.textarea.value;
        
        // Replace {{BLANK_X}} with input elements
        let html = this.escapeHtml(originalCode);
        
        // Replace blanks with input fields
        html = html.replace(/\{\{(BLANK_\d+)\}\}/g, (match, blankId) => {
            const blankInfo = this.blanksData.find(b => b.id === blankId) || 
                            { id: blankId, placeholder: blankId };
            
            return `<input type="text" 
                        class="blank-input" 
                        data-blank-id="${blankId}"
                        placeholder="${blankInfo.placeholder || blankId}"
                        autocomplete="off"
                        spellcheck="false">`;
        });
        
        // Create code display with syntax highlighting
        this.editorContainer.innerHTML = `
            <div class="code-display">
                <pre><code class="language-python">${html}</code></pre>
            </div>
        `;
        
        // Replace the original textarea
        this.textarea.parentNode.insertBefore(this.wrapper, this.textarea);
        this.textarea.style.display = 'none';
        
        // Store references to input fields
        this.inputFields = this.editorContainer.querySelectorAll('.blank-input');
    }

    setupEventListeners() {
        // Input field event listeners
        this.inputFields.forEach(input => {
            input.addEventListener('input', (e) => {
                const blankId = e.target.dataset.blankId;
                this.blankValues.set(blankId, e.target.value);
                this.updateTextarea();
            });
            
            // Add enter key support to move to next input
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const inputs = Array.from(this.inputFields);
                    const currentIndex = inputs.indexOf(e.target);
                    const nextInput = inputs[currentIndex + 1];
                    if (nextInput) {
                        nextInput.focus();
                    }
                }
            });
        });
        
        // Button event listeners
        const checkBtn = this.header.querySelector('.check-answers-btn');
        const runBtn = this.header.querySelector('.run-code-btn');
        
        checkBtn.addEventListener('click', () => this.checkAnswers());
        runBtn.addEventListener('click', () => this.runCode());
    }

    updateTextarea() {
        // Update the original textarea with current values
        let code = this.textarea.value;
        for (let [blankId, value] of this.blankValues) {
            const pattern = new RegExp(`\\{\\{${blankId}\\}\\}`, 'g');
            code = code.replace(pattern, value);
        }
        this.textarea.value = code;
    }

    checkAnswers() {
        const expectedAnswers = {
            'BLANK_1': {
                type: 'string',
                description: 'Any quoted name (e.g., "John")',
                validate: (value) => /^["'][^"']+["']$/.test(value.trim())
            },
            'BLANK_2': {
                type: 'number',
                description: 'Any number between 18-65',
                validate: (value) => {
                    const num = parseInt(value.trim());
                    return !isNaN(num) && num >= 18 && num <= 65;
                }
            },
            'BLANK_3': {
                type: 'boolean',
                description: 'True or False (capital T/F)',
                validate: (value) => ['True', 'False'].includes(value.trim())
            }
        };
        
        let results = [];
        let allCorrect = true;
        
        // Check each blank
        for (let input of this.inputFields) {
            const blankId = input.dataset.blankId;
            const userAnswer = input.value;
            const expected = expectedAnswers[blankId];
            
            let isCorrect = false;
            if (expected && expected.validate) {
                isCorrect = expected.validate(userAnswer);
            }
            
            results.push({
                blankId,
                userAnswer,
                isCorrect,
                description: expected ? expected.description : 'Valid input required'
            });
            
            // Update input styling
            input.classList.remove('is-valid', 'is-invalid');
            input.classList.add(isCorrect ? 'is-valid' : 'is-invalid');
            
            if (!isCorrect) allCorrect = false;
        }
        
        // Display results
        this.displayResults(results, allCorrect);
        
        // Enable/disable run button
        const runBtn = this.header.querySelector('.run-code-btn');
        runBtn.disabled = !allCorrect;
        if (allCorrect) {
            runBtn.classList.remove('btn-secondary');
            runBtn.classList.add('btn-primary');
        } else {
            runBtn.classList.remove('btn-primary');
            runBtn.classList.add('btn-secondary');
        }
    }

    displayResults(results, allCorrect) {
        let html = `
            <div class="check-results">
                <h6><i class="bi bi-clipboard-check"></i> Answer Check Results</h6>
        `;
        
        results.forEach(result => {
            const icon = result.isCorrect ? 'bi-check-circle-fill text-success' : 'bi-x-circle-fill text-danger';
            const status = result.isCorrect ? 'Correct' : 'Incorrect';
            
            html += `
                <div class="result-item">
                    <i class="bi ${icon}"></i>
                    <strong>${result.blankId}:</strong> ${status}
                    ${!result.isCorrect ? `<br><small class="text-muted">Expected: ${result.description}</small>` : ''}
                </div>
            `;
        });
        
        const overallIcon = allCorrect ? 'bi-trophy-fill text-warning' : 'bi-exclamation-triangle-fill text-info';
        const overallMessage = allCorrect ? 
            'Excellent! All answers are correct. You can now run the code.' :
            'Some answers need attention. Please review and try again.';
        
        html += `
            <div class="overall-result ${allCorrect ? 'success' : 'warning'}">
                <i class="bi ${overallIcon}"></i> ${overallMessage}
            </div>
        </div>
        `;
        
        this.resultsPanel.innerHTML = html;
        this.resultsPanel.style.display = 'block';
    }

    runCode() {
        // Generate mock output based on current values
        const name = this.blankValues.get('BLANK_1') || '"YourName"';
        const age = this.blankValues.get('BLANK_2') || 'YourAge';
        const isStudent = this.blankValues.get('BLANK_3') || 'True/False';
        
        const output = `Hello, my name is ${name.replace(/['"]/g, '')}
I am ${age} years old
Am I a student? ${isStudent}`;
        
        const html = `
            <div class="run-results">
                <h6><i class="bi bi-play-circle"></i> Code Output</h6>
                <div class="output-display">
                    <pre>${output}</pre>
                </div>
            </div>
        `;
        
        this.resultsPanel.innerHTML = html;
        this.resultsPanel.style.display = 'block';
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, (m) => map[m]);
    }
}

// Initialize fill-in-blanks editors when DOM is loaded
function initializeFillInBlanks() {
    const textareas = document.querySelectorAll('.interactive-code-editor');
    textareas.forEach(textarea => {
        const container = textarea.closest('.interactive-code-block');
        if (container && container.dataset.exerciseType === 'fill_blank') {
            new FillInBlanksEditor(textarea);
        }
    });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeFillInBlanks);
} else {
    initializeFillInBlanks();
}

// Export for manual initialization if needed
window.FillInBlanksEditor = FillInBlanksEditor;
window.initializeFillInBlanks = initializeFillInBlanks;