// Simple Code Editor for Python Learning Studio
// Fallback implementation that works without external dependencies

class SimpleCodeEditor {
    constructor() {
        this.editors = new Map();
    }

    // Create exercise interface with textarea-based editor
    createExerciseInterface(containerId, exerciseData = {}) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Set default values if not provided
        const data = {
            title: exerciseData.title || 'Find Maximum',
            difficulty: exerciseData.difficulty_level || 'intermediate',
            duration: exerciseData.estimated_time || 29,
            points: exerciseData.points || 10,
            language: exerciseData.programming_language?.name || 'Python',
            description: exerciseData.description || 'Find the maximum number in a list',
            instructions: exerciseData.instructions || 'Follow these steps to complete the Find Maximum exercise:',
            starterCode: exerciseData.starter_code || 'def TODO(numbers):\n    # Find max number\n    pass',
            ...exerciseData
        };

        // Create the interface HTML
        container.innerHTML = `
            <div class="exercise-interface">
                <!-- Left Panel: Problem Description -->
                <div class="exercise-left-panel">
                    <div class="exercise-header">
                        <h2 class="exercise-title">${data.title}</h2>
                        <div class="exercise-meta">
                            <span class="difficulty ${data.difficulty}">${data.difficulty.toUpperCase()}</span>
                            <span class="duration"><i class="bi bi-clock"></i> ${data.duration} min</span>
                            <span class="points"><i class="bi bi-award"></i> ${data.points} points</span>
                            <span class="language"><i class="bi bi-code"></i> ${data.language}</span>
                        </div>
                    </div>

                    <div class="problem-section">
                        <h3><i class="bi bi-file-text"></i> Problem Description</h3>
                        <div class="problem-content">
                            ${data.description}
                        </div>
                    </div>

                    <div class="instructions-section">
                        <h3><i class="bi bi-list-task"></i> Instructions</h3>
                        <div class="instructions-content">
                            ${data.instructions}
                        </div>
                    </div>

                    <div class="test-cases-section">
                        <h3><i class="bi bi-check-circle"></i> Sample Test Cases</h3>
                        <div class="test-cases-list">
                            <div class="test-case">
                                <h4>Basic Test</h4>
                                <div class="test-input">
                                    <strong>Expected Output:</strong>
                                    <code>9</code>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="action-buttons">
                        <button class="btn btn-outline-primary" onclick="showHint()">
                            <i class="bi bi-lightbulb"></i> Hint
                        </button>
                        <button class="btn btn-outline-info" onclick="showSolution()">
                            <i class="bi bi-eye"></i> Solution
                        </button>
                    </div>
                </div>

                <!-- Right Panel: Code Editor -->
                <div class="exercise-right-panel">
                    <div class="editor-header">
                        <div class="editor-title">
                            <i class="bi bi-code-slash"></i> Code Editor
                        </div>
                        <div class="editor-controls">
                            <div class="file-tabs">
                                <div class="file-tab active">
                                    <i class="bi bi-file-earmark-code"></i>
                                    solution.py
                                </div>
                            </div>
                            <div class="editor-actions">
                                <button class="btn btn-sm btn-outline-secondary" id="resetCode">
                                    Reset
                                </button>
                                <button class="btn btn-sm btn-primary" id="runCode">
                                    <i class="bi bi-play-fill"></i> Run Code
                                </button>
                                <button class="btn btn-sm btn-primary" id="submitCode">
                                    Submit
                                </button>
                            </div>
                        </div>
                    </div>

                    <div class="editor-container" id="exerciseEditor"></div>

                    <div class="output-section">
                        <div class="output-tabs">
                            <button class="output-tab active" data-tab="output">
                                <i class="bi bi-terminal"></i> Output
                            </button>
                            <button class="output-tab" data-tab="tests">
                                <i class="bi bi-check-circle"></i> Test Results
                            </button>
                            <button class="output-tab" data-tab="console">
                                <i class="bi bi-console"></i> Console
                            </button>
                        </div>
                        
                        <div class="output-content">
                            <div class="output-panel active" id="outputPanel">
                                <div class="output-placeholder">
                                    Run your code to see the output here...
                                </div>
                            </div>
                            <div class="output-panel" id="testsPanel">
                                <div class="tests-placeholder">
                                    Submit your solution to see test results...
                                </div>
                            </div>
                            <div class="output-panel" id="consolePanel">
                                <div class="console-placeholder">
                                    Console logs will appear here...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Create the editor immediately after creating the HTML
        setTimeout(() => {
            const editor = this.createEditor('exerciseEditor', {
                initialValue: data.starterCode,
                language: 'python'
            });

            // Set up event listeners
            this.setupExerciseEventListeners(editor, data);
            
            console.log('Editor created and attached:', editor);
        }, 100);

        return true;
    }

    // Create playground interface
    createPlaygroundInterface(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="playground-interface">
                <div class="playground-header">
                    <div class="playground-title">
                        <i class="bi bi-code-square"></i> Python Code Playground
                    </div>
                    <div class="playground-controls">
                        <select class="form-select language-selector" id="languageSelector">
                            <option value="python">Python</option>
                            <option value="javascript">JavaScript</option>
                            <option value="java">Java</option>
                            <option value="cpp">C++</option>
                        </select>
                        <button class="btn btn-primary" id="runPlaygroundCode">
                            <i class="bi bi-play-fill"></i> Run
                        </button>
                    </div>
                </div>

                <div class="playground-content">
                    <div class="playground-editor" id="playgroundEditor"></div>
                    <div class="playground-output">
                        <div class="output-header">
                            <span><i class="bi bi-terminal"></i> Output</span>
                            <button class="btn btn-sm btn-outline-secondary" id="clearOutput">
                                <i class="bi bi-x-lg"></i> Clear
                            </button>
                        </div>
                        <div class="output-content" id="playgroundOutput">
                            <div class="output-placeholder">
                                Write some code and click Run to see the output...
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const editor = this.createEditor('playgroundEditor', {
            initialValue: '# Welcome to Python Learning Studio Playground!\n# Write your Python code here and click Run to execute\n\nprint("Hello, World!")',
            language: 'python'
        });

        this.setupPlaygroundEventListeners(editor);
        return editor;
    }

    // Create a simple textarea-based editor
    createEditor(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) return null;

        const {
            initialValue = '',
            language = 'python',
            readOnly = false
        } = options;

        // Create styled textarea that looks like the screenshot
        const textarea = document.createElement('textarea');
        textarea.className = 'form-control code-editor';
        textarea.style.cssText = `
            width: 100%;
            height: 100%;
            background: #1a1a1a;
            color: #e2e8f0;
            border: none;
            resize: none;
            padding: 20px;
            font-family: 'Fira Code', 'JetBrains Mono', 'SF Mono', Consolas, monospace;
            font-size: 14px;
            line-height: 1.6;
            tab-size: 4;
            border-radius: 0;
            outline: none;
        `;
        textarea.value = initialValue;
        textarea.readOnly = readOnly;
        textarea.spellcheck = false;

        // Add syntax highlighting classes for display
        container.appendChild(textarea);

        // Auto-resize and handle tab key
        this.enhanceTextarea(textarea);

        const editorObj = {
            container: container,
            textarea: textarea,
            getValue: () => textarea.value,
            setValue: (value) => { textarea.value = value; },
            state: { doc: { toString: () => textarea.value } }
        };

        this.editors.set(containerId, editorObj);
        return editorObj;
    }

    // Enhance textarea with better coding experience
    enhanceTextarea(textarea) {
        // Handle tab key for indentation
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                e.preventDefault();
                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                
                // Insert 4 spaces
                textarea.value = textarea.value.substring(0, start) + '    ' + textarea.value.substring(end);
                textarea.selectionStart = textarea.selectionEnd = start + 4;
            }
        });

        // Auto-save
        textarea.addEventListener('input', () => {
            // Auto-save functionality could be added here
        });
    }

    // Set up event listeners for exercise interface
    setupExerciseEventListeners(editor, exerciseData) {
        // Output tab switching
        document.querySelectorAll('.output-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.output-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.output-panel').forEach(p => p.classList.remove('active'));
                
                tab.classList.add('active');
                document.getElementById(tab.dataset.tab + 'Panel').classList.add('active');
            });
        });

        // Run code button
        document.getElementById('runCode')?.addEventListener('click', () => {
            this.runCode(editor, 'output');
        });

        // Submit code button
        document.getElementById('submitCode')?.addEventListener('click', () => {
            this.submitCode(editor, exerciseData);
        });

        // Reset code button
        document.getElementById('resetCode')?.addEventListener('click', () => {
            if (confirm('Reset your code? This will delete all your current work.')) {
                editor.setValue(exerciseData.starterCode || 'def TODO(numbers):\n    # Find max number\n    pass');
            }
        });
    }

    // Set up event listeners for playground interface
    setupPlaygroundEventListeners(editor) {
        document.getElementById('runPlaygroundCode')?.addEventListener('click', () => {
            this.runCode(editor, 'playground');
        });

        document.getElementById('clearOutput')?.addEventListener('click', () => {
            document.getElementById('playgroundOutput').innerHTML = '<div class="output-placeholder">Output cleared...</div>';
        });
    }

    // Run code function
    async runCode(editor, outputType = 'output') {
        const code = editor.getValue();
        const outputElement = outputType === 'playground' 
            ? document.getElementById('playgroundOutput')
            : document.getElementById('outputPanel');

        if (!code.trim()) {
            this.showOutput(outputElement, 'Please write some code first!', 'error');
            return;
        }

        // Show loading
        outputElement.innerHTML = `
            <div class="output-loading">
                <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                Running code...
            </div>
        `;

        try {
            const response = await fetch('/api/v1/execute/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ code })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.showOutput(outputElement, result.output, 'success');
            } else {
                this.showOutput(outputElement, result.error, 'error');
            }
        } catch (error) {
            this.showOutput(outputElement, `Error: ${error.message}`, 'error');
        }
    }

    // Submit code for grading
    async submitCode(editor, exerciseData) {
        const code = editor.getValue();
        
        if (!code.trim()) {
            alert('Please write some code before submitting!');
            return;
        }

        // Mock successful submission for demo
        this.showTestResults({
            score: 100,
            passedTests: 1,
            totalTests: 1,
            testResults: [{
                passed: true,
                input: '[1,5,3,9,2]',
                expected: '9',
                actual: '9'
            }]
        });
    }

    // Show output in element
    showOutput(element, content, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info-circle';
        const className = type === 'success' ? 'text-success' : type === 'error' ? 'text-danger' : 'text-info';

        element.innerHTML = `
            <div class="output-result">
                <div class="output-header">
                    <i class="bi bi-${icon} ${className}"></i>
                    <span class="output-timestamp">${timestamp}</span>
                </div>
                <pre class="output-content">${content}</pre>
            </div>
        `;
    }

    // Show test results
    showTestResults(results) {
        const testsPanel = document.getElementById('testsPanel');
        const testsTab = document.querySelector('[data-tab="tests"]');
        
        // Switch to tests tab
        document.querySelectorAll('.output-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.output-panel').forEach(p => p.classList.remove('active'));
        testsTab.classList.add('active');
        testsPanel.classList.add('active');

        testsPanel.innerHTML = `
            <div class="test-results">
                <div class="test-summary">
                    <div class="score ${results.score === 100 ? 'success' : 'partial'}">
                        Score: ${results.score || 0}%
                    </div>
                    <div class="tests-passed">
                        ${results.passedTests || 0}/${results.totalTests || 1} tests passed
                    </div>
                </div>
                <div class="test-cases">
                    ${(results.testResults || []).map((test, index) => `
                        <div class="test-case ${test.passed ? 'passed' : 'failed'}">
                            <div class="test-header">
                                <i class="bi bi-${test.passed ? 'check-circle' : 'x-circle'}"></i>
                                Test ${index + 1}
                            </div>
                            <div class="test-details">
                                <div class="test-input">Input: <code>${test.input}</code></div>
                                <div class="test-expected">Expected: <code>${test.expected}</code></div>
                                <div class="test-actual">Got: <code>${test.actual}</code></div>
                                ${!test.passed ? `<div class="test-error">${test.error || ''}</div>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Get CSRF token
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    // Utility functions
    getContent(editorId) {
        const editor = this.editors.get(editorId);
        return editor ? editor.getValue() : '';
    }

    setContent(editorId, content) {
        const editor = this.editors.get(editorId);
        if (editor) {
            editor.setValue(content);
        }
    }
}

// Global setup for compatibility
window.SimpleCodeEditor = SimpleCodeEditor;
window.codeMirrorSetup = new SimpleCodeEditor();

// Global hint and solution functions
window.showHint = function() {
    alert('Hint: Try using the max() function or iterate through the list to find the largest number.');
};

window.showSolution = function() {
    if (confirm('Are you sure you want to see the solution? This will end your attempt.')) {
        alert('Solution:\\n\\ndef TODO(numbers):\\n    return max(numbers)');
    }
};