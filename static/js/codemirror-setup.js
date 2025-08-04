// Enhanced CodeMirror 6 Setup - Python Learning Studio
// Modern code editor with AI integration and advanced features

class CodeMirrorSetup {
    constructor() {
        this.editors = new Map();
        this.currentTheme = 'dark';
        this.initialized = false;
        this.aiSuggestionsEnabled = true;
        this.errorHighlightingEnabled = true;
        this.modules = null;
    }

    async initialize() {
        if (this.initialized) return true;
        
        try {
            // Wait for CodeMirror modules to be available from CDN
            await this.waitForModules();
            this.initialized = true;
            return true;
        } catch (error) {
            console.error('Failed to initialize CodeMirror:', error);
            return false;
        }
    }

    async waitForModules() {
        try {
            // Use the dedicated loader
            if (window.codeMirrorLoader) {
                await window.codeMirrorLoader.loadModules();
                this.modules = window.CodeMirror;
                return;
            }
            
            // Fallback to direct checking
            return new Promise((resolve, reject) => {
                let attempts = 0;
                const maxAttempts = 150; // Increased timeout for CDN loading
                
                const checkModules = () => {
                    // Check for all required CodeMirror 6 modules
                    if (window.CodeMirror && 
                        window.CodeMirror.EditorView && 
                        window.CodeMirror.EditorState &&
                        window.CodeMirror.basicSetup) {
                        this.modules = window.CodeMirror;
                        resolve();
                    } else if (attempts < maxAttempts) {
                        attempts++;
                        setTimeout(checkModules, 200);
                    } else {
                        reject(new Error('CodeMirror 6 modules not fully loaded'));
                    }
                };
                
                checkModules();
            });
        } catch (error) {
            console.error('Module loading failed:', error);
            throw error;
        }
    }

    // Get editor configuration based on type and language
    getEditorConfig(type = 'basic', language = 'python', options = {}) {
        if (!this.modules) {
            throw new Error('CodeMirror modules not loaded');
        }

        const { EditorView, EditorState, basicSetup } = this.modules;
        
        // Base configuration
        const baseConfig = {
            extensions: [
                basicSetup,
                EditorView.theme({
                    '&': {
                        fontSize: '14px',
                        fontFamily: '"Fira Code", "JetBrains Mono", "Consolas", monospace'
                    },
                    '.cm-editor': {
                        height: '100%'
                    },
                    '.cm-focused': {
                        outline: 'none'
                    },
                    '.cm-content': {
                        padding: '16px',
                        lineHeight: '1.6',
                        minHeight: '100%'
                    },
                    '.cm-line': {
                        paddingLeft: '4px'
                    }
                }),
                EditorView.lineWrapping
            ]
        };

        // Add language-specific extensions
        if (language === 'python' && this.modules.python) {
            baseConfig.extensions.push(this.modules.python());
        } else if (language === 'javascript' && this.modules.javascript) {
            baseConfig.extensions.push(this.modules.javascript());
        }

        // Add theme
        if (this.currentTheme === 'dark' && this.modules.oneDark) {
            baseConfig.extensions.push(this.modules.oneDark);
        }

        // Add advanced features based on type
        if (type === 'advanced') {
            this.addAdvancedFeatures(baseConfig);
        } else if (type === 'ai-enhanced') {
            this.addAIFeatures(baseConfig);
        }

        // Merge with custom options
        if (options.doc) {
            baseConfig.doc = options.doc;
        }

        return baseConfig;
    }

    // Add advanced IDE features
    addAdvancedFeatures(config) {
        const { EditorView, keymap } = this.modules;
        
        // Enhanced autocompletion with IntelliSense
        if (this.modules.autocompletion) {
            config.extensions.push(
                this.modules.autocompletion({
                    activateOnTyping: true,
                    maxRenderedOptions: 20,
                    defaultKeymap: true,
                    closeOnBlur: true,
                    override: [this.createCustomCompletionSource()]
                })
            );
        }

        // Add bracket matching and auto-closing
        if (this.modules.bracketMatching) {
            config.extensions.push(this.modules.bracketMatching());
        }
        
        if (this.modules.closeBrackets) {
            config.extensions.push(this.modules.closeBrackets());
        }

        // Add search functionality with regex support
        if (this.modules.search) {
            config.extensions.push(this.modules.search({
                top: true
            }));
        }

        // Add code folding
        if (this.modules.foldGutter) {
            config.extensions.push(this.modules.foldGutter());
        }

        // Enhanced key bindings
        config.extensions.push(keymap.of([
            { key: 'Ctrl-Enter', run: () => this.executeCodeAction() },
            { key: 'Cmd-Enter', run: () => this.executeCodeAction() },
            { key: 'Ctrl-/', run: () => this.toggleComment() },
            { key: 'Cmd-/', run: () => this.toggleComment() },
            { key: 'Ctrl-Space', run: () => this.triggerCompletion() },
            { key: 'Cmd-Space', run: () => this.triggerCompletion() },
            { key: 'F12', run: () => this.goToDefinition() },
            { key: 'Alt-F12', run: () => this.peekDefinition() },
            { key: 'Shift-F12', run: () => this.findReferences() }
        ]));

        // Add hover tooltips
        config.extensions.push(this.createHoverTooltips());
    }

    // Create custom completion source for Python/JavaScript
    createCustomCompletionSource() {
        return (context) => {
            const word = context.matchBefore(/\w*/);
            if (!word || (word.from === word.to && !context.explicit)) {
                return null;
            }

            // Get Python/JavaScript completions
            const completions = this.getPredefinedCompletions(context);
            
            return {
                from: word.from,
                options: completions
            };
        };
    }

    // Get predefined completions for Python
    getPredefinedCompletions(context) {
        const pythonBuiltins = [
            // Built-in functions
            { label: 'print', type: 'function', info: 'Print objects to the console' },
            { label: 'len', type: 'function', info: 'Return the length of an object' },
            { label: 'range', type: 'function', info: 'Generate a sequence of numbers' },
            { label: 'str', type: 'function', info: 'Convert to string' },
            { label: 'int', type: 'function', info: 'Convert to integer' },
            { label: 'float', type: 'function', info: 'Convert to float' },
            { label: 'bool', type: 'function', info: 'Convert to boolean' },
            { label: 'list', type: 'function', info: 'Create a list' },
            { label: 'dict', type: 'function', info: 'Create a dictionary' },
            { label: 'tuple', type: 'function', info: 'Create a tuple' },
            { label: 'set', type: 'function', info: 'Create a set' },
            { label: 'sum', type: 'function', info: 'Sum all items in an iterable' },
            { label: 'max', type: 'function', info: 'Return the largest item' },
            { label: 'min', type: 'function', info: 'Return the smallest item' },
            { label: 'abs', type: 'function', info: 'Return absolute value' },
            { label: 'round', type: 'function', info: 'Round a number' },
            { label: 'sorted', type: 'function', info: 'Return a sorted list' },
            { label: 'reversed', type: 'function', info: 'Return a reversed iterator' },
            { label: 'enumerate', type: 'function', info: 'Add counter to an iterable' },
            { label: 'zip', type: 'function', info: 'Combine iterables' },
            { label: 'map', type: 'function', info: 'Apply function to every item' },
            { label: 'filter', type: 'function', info: 'Filter items from iterable' },
            
            // Keywords
            { label: 'def', type: 'keyword', info: 'Define a function' },
            { label: 'class', type: 'keyword', info: 'Define a class' },
            { label: 'if', type: 'keyword', info: 'Conditional statement' },
            { label: 'elif', type: 'keyword', info: 'Else if condition' },
            { label: 'else', type: 'keyword', info: 'Else condition' },
            { label: 'for', type: 'keyword', info: 'For loop' },
            { label: 'while', type: 'keyword', info: 'While loop' },
            { label: 'try', type: 'keyword', info: 'Try exception handling' },
            { label: 'except', type: 'keyword', info: 'Catch exceptions' },
            { label: 'finally', type: 'keyword', info: 'Finally block' },
            { label: 'return', type: 'keyword', info: 'Return from function' },
            { label: 'yield', type: 'keyword', info: 'Generator yield' },
            { label: 'import', type: 'keyword', info: 'Import module' },
            { label: 'from', type: 'keyword', info: 'Import from module' },
            { label: 'as', type: 'keyword', info: 'Alias import' },
            { label: 'with', type: 'keyword', info: 'Context manager' },
            { label: 'lambda', type: 'keyword', info: 'Anonymous function' },
            { label: 'and', type: 'keyword', info: 'Logical AND' },
            { label: 'or', type: 'keyword', info: 'Logical OR' },
            { label: 'not', type: 'keyword', info: 'Logical NOT' },
            { label: 'in', type: 'keyword', info: 'Membership test' },
            { label: 'is', type: 'keyword', info: 'Identity test' },
            
            // Common methods
            { label: 'append', type: 'method', info: 'Add item to list' },
            { label: 'extend', type: 'method', info: 'Extend list with items' },
            { label: 'insert', type: 'method', info: 'Insert item at position' },
            { label: 'remove', type: 'method', info: 'Remove first occurrence' },
            { label: 'pop', type: 'method', info: 'Remove and return item' },
            { label: 'index', type: 'method', info: 'Find index of item' },
            { label: 'count', type: 'method', info: 'Count occurrences' },
            { label: 'sort', type: 'method', info: 'Sort list in place' },
            { label: 'reverse', type: 'method', info: 'Reverse list in place' },
            { label: 'split', type: 'method', info: 'Split string into list' },
            { label: 'join', type: 'method', info: 'Join list into string' },
            { label: 'replace', type: 'method', info: 'Replace substring' },
            { label: 'strip', type: 'method', info: 'Remove whitespace' },
            { label: 'lower', type: 'method', info: 'Convert to lowercase' },
            { label: 'upper', type: 'method', info: 'Convert to uppercase' },
            { label: 'title', type: 'method', info: 'Convert to title case' },
            { label: 'startswith', type: 'method', info: 'Check if starts with' },
            { label: 'endswith', type: 'method', info: 'Check if ends with' },
            { label: 'keys', type: 'method', info: 'Get dictionary keys' },
            { label: 'values', type: 'method', info: 'Get dictionary values' },
            { label: 'items', type: 'method', info: 'Get dictionary items' },
            { label: 'get', type: 'method', info: 'Get dictionary value safely' }
        ];

        return pythonBuiltins;
    }

    // Create hover tooltips for documentation
    createHoverTooltips() {
        const { EditorView } = this.modules;
        
        return EditorView.domEventHandlers({
            mouseover(event, view) {
                // Implementation for hover tooltips would go here
                // This would show documentation for functions/methods
            }
        });
    }

    // Trigger completion manually
    triggerCompletion() {
        if (this.modules.autocompletion) {
            return this.modules.autocompletion.startCompletion;
        }
        return false;
    }

    // Go to definition (placeholder)
    goToDefinition() {
        console.log('Go to definition triggered');
        return true;
    }

    // Peek definition (placeholder)
    peekDefinition() {
        console.log('Peek definition triggered');
        return true;
    }

    // Find references (placeholder)
    findReferences() {
        console.log('Find references triggered');
        return true;
    }

    // Add AI-powered features
    addAIFeatures(config) {
        this.addAdvancedFeatures(config);
        
        // Add AI suggestion decorations
        config.extensions.push(this.createAISuggestionExtension());
        
        // Add error highlighting
        config.extensions.push(this.createErrorHighlightExtension());
    }

    // Create AI suggestion extension
    createAISuggestionExtension() {
        const { EditorView, Decoration } = this.modules;
        
        return EditorView.decorations.of((view) => {
            // This would integrate with your AI service
            // For now, return empty decorations
            return Decoration.none;
        });
    }

    // Create error highlighting extension
    createErrorHighlightExtension() {
        const { EditorView, Decoration, StateField, StateEffect } = this.modules;
        
        // Define effect for updating error decorations
        const addErrors = StateEffect.define();
        const clearErrors = StateEffect.define();
        
        // Error decoration mark
        const errorMark = Decoration.mark({
            class: 'cm-error-highlight',
            attributes: { 
                title: 'Syntax error detected'
            }
        });
        
        const errorLineMark = Decoration.line({
            class: 'cm-error-line'
        });
        
        // State field to track errors
        const errorState = StateField.define({
            create() {
                return Decoration.none;
            },
            update(errors, tr) {
                errors = errors.map(tr.changes);
                for (let effect of tr.effects) {
                    if (effect.is(addErrors)) {
                        errors = errors.update({
                            add: effect.value.map(error => {
                                const from = Math.min(error.from, tr.newDoc.length);
                                const to = Math.min(error.to || from + 1, tr.newDoc.length);
                                return error.line 
                                    ? errorLineMark.range(tr.newDoc.line(error.line).from)
                                    : errorMark.range(from, to);
                            })
                        });
                    } else if (effect.is(clearErrors)) {
                        errors = Decoration.none;
                    }
                }
                return errors;
            },
            provide: f => EditorView.decorations.from(f)
        });
        
        // Add CSS for error highlighting
        const errorTheme = EditorView.theme({
            '.cm-error-highlight': {
                textDecoration: 'underline',
                textDecorationColor: '#ff6b6b',
                textDecorationStyle: 'wavy',
                textDecorationThickness: '2px'
            },
            '.cm-error-line': {
                backgroundColor: 'rgba(255, 107, 107, 0.1)',
                borderLeft: '3px solid #ff6b6b',
                paddingLeft: '8px'
            },
            '.cm-error-tooltip': {
                background: '#2d1b1b',
                border: '1px solid #ff6b6b',
                borderRadius: '4px',
                padding: '8px 12px',
                color: '#ff6b6b',
                fontSize: '13px',
                fontFamily: 'monospace',
                maxWidth: '300px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
                zIndex: 1000
            }
        });
        
        return [errorState, errorTheme, this.createErrorTooltips(addErrors, clearErrors)];
    }
    
    // Create error tooltips
    createErrorTooltips(addErrors, clearErrors) {
        const { EditorView } = this.modules;
        
        return EditorView.domEventHandlers({
            mouseover: (event, view) => {
                const pos = view.posAtCoords({ x: event.clientX, y: event.clientY });
                if (pos !== null) {
                    this.showErrorTooltip(view, pos, event);
                }
            },
            mouseout: () => {
                this.hideErrorTooltip();
            }
        });
    }
    
    // Show error tooltip
    showErrorTooltip(view, pos, event) {
        // Check if position has error decoration
        const decorations = view.state.field(this.errorStateField, false);
        if (decorations) {
            const iter = decorations.iter();
            while (!iter.next().done) {
                if (iter.from <= pos && pos <= iter.to) {
                    const tooltip = document.createElement('div');
                    tooltip.className = 'cm-error-tooltip';
                    tooltip.textContent = 'Syntax error detected at this location';
                    tooltip.style.position = 'absolute';
                    tooltip.style.left = event.clientX + 'px';
                    tooltip.style.top = (event.clientY - 40) + 'px';
                    
                    document.body.appendChild(tooltip);
                    this.currentTooltip = tooltip;
                    break;
                }
            }
        }
    }
    
    // Hide error tooltip
    hideErrorTooltip() {
        if (this.currentTooltip) {
            this.currentTooltip.remove();
            this.currentTooltip = null;
        }
    }

    // Execute code action for keybindings
    executeCodeAction() {
        // Find the active editor and execute its code
        const activeEditor = this.getActiveEditor();
        if (activeEditor && activeEditor.runCode) {
            activeEditor.runCode();
        }
        return true;
    }

    // Toggle comment functionality
    toggleComment() {
        // Implementation for comment toggling
        return true;
    }

    // Get currently active editor
    getActiveEditor() {
        // Return the most recently focused editor
        for (const [id, editor] of this.editors) {
            if (editor.view && editor.view.hasFocus) {
                return editor;
            }
        }
        return null;
    }

    // Create the exercise interface matching the screenshot exactly
    async createExerciseInterface(containerId, exerciseData) {
        await this.initialize();
        const container = document.getElementById(containerId);
        if (!container) return;

        // Create the exact layout from the screenshot
        container.innerHTML = `
            <div class="exercise-interface">
                <!-- Left Panel: Problem Description -->
                <div class="exercise-left-panel">
                    <div class="exercise-header">
                        <h2 class="exercise-title">Find Maximum</h2>
                        <div class="exercise-meta">
                            <span class="difficulty intermediate">INTERMEDIATE</span>
                            <span class="duration"><i class="bi bi-clock"></i> 29 min</span>
                            <span class="points"><i class="bi bi-award"></i> 10 points</span>
                            <span class="language"><i class="bi bi-code"></i> Python</span>
                        </div>
                    </div>

                    <div class="problem-section">
                        <h3><i class="bi bi-file-text"></i> Problem Description</h3>
                        <div class="problem-content">
                            Find the maximum number in a list
                        </div>
                    </div>

                    <div class="instructions-section">
                        <h3><i class="bi bi-list-task"></i> Instructions</h3>
                        <div class="instructions-content">
                            Follow these steps to complete the Find Maximum exercise:
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
                        <button class="btn btn-outline-primary" onclick="window.showHint && window.showHint()">
                            <i class="bi bi-lightbulb"></i> Hint
                        </button>
                        <button class="btn btn-outline-info" onclick="window.showSolution && window.showSolution()">
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
                                <button class="btn btn-sm btn-success" id="runCode">
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

        // Create the editor with advanced features for exercises
        const editor = await this.createEditor('exerciseEditor', {
            initialValue: `def TODO(numbers):
    # Find max number
    pass`,
            language: 'python',
            type: 'ai-enhanced', // Use AI-enhanced mode for exercises
            outputType: 'exercise'
        });

        // Set up event listeners
        this.setupExerciseEventListeners(editor, exerciseData);

        return editor;
    }

    // Create playground interface
    async createPlaygroundInterface(containerId) {
        await this.initialize();
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
                        <button class="btn btn-success" id="runPlaygroundCode">
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

        const editor = await this.createEditor('playgroundEditor', {
            initialValue: '# Welcome to Python Learning Studio Playground!\n# Write your Python code here and click Run to execute\n\nprint("Hello, World!")',
            language: 'python',
            type: 'advanced', // Use advanced mode for playground
            outputType: 'playground'
        });

        this.setupPlaygroundEventListeners(editor);
        return editor;
    }

    // Create a modern CodeMirror 6 editor with advanced features
    async createEditor(containerId, options = {}) {
        await this.initialize();
        const container = document.getElementById(containerId);
        if (!container) return null;

        const {
            initialValue = '',
            language = 'python',
            readOnly = false,
            type = 'basic', // 'basic', 'advanced', 'ai-enhanced'
            placeholder = 'Write your code here...'
        } = options;

        try {
            // Get configuration for this editor type
            const config = this.getEditorConfig(type, language, { doc: initialValue });
            
            // Create CodeMirror 6 editor
            const { EditorView, EditorState } = this.modules;
            
            const state = EditorState.create(config);
            const view = new EditorView({
                state,
                parent: container
            });

            // Create editor object with enhanced API
            const editorObj = {
                container: container,
                view: view,
                getValue: () => view.state.doc.toString(),
                setValue: (value) => {
                    view.dispatch({
                        changes: {
                            from: 0,
                            to: view.state.doc.length,
                            insert: value
                        }
                    });
                },
                focus: () => view.focus(),
                getSelection: () => view.state.selection.main,
                replaceSelection: (text) => {
                    view.dispatch(view.state.replaceSelection(text));
                },
                // Add execution capability
                runCode: () => this.runCode(editorObj, options.outputType || 'output'),
                // Add AI features
                getSuggestions: () => this.getAISuggestions(editorObj),
                highlightErrors: (errors) => this.highlightErrors(editorObj, errors)
            };

            this.editors.set(containerId, editorObj);
            return editorObj;

        } catch (error) {
            console.error('Failed to create CodeMirror editor:', error);
            return this.createFallbackEditor(containerId, options);
        }
    }

    // Fallback to simple textarea if CodeMirror fails
    createFallbackEditor(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) return null;

        const {
            initialValue = '',
            language = 'python',
            readOnly = false,
            placeholder = 'Write your code here...'
        } = options;

        const textarea = document.createElement('textarea');
        textarea.className = 'form-control code-editor fallback-editor';
        textarea.style.cssText = `
            width: 100%;
            height: 100%;
            background: #1a1a1a;
            color: #e2e8f0;
            border: none;
            resize: none;
            padding: 20px;
            font-family: 'Fira Code', 'JetBrains Mono', 'Consolas', monospace;
            font-size: 14px;
            line-height: 1.6;
            tab-size: 4;
        `;
        textarea.value = initialValue;
        textarea.readOnly = readOnly;
        textarea.placeholder = placeholder;

        container.appendChild(textarea);

        const editorObj = {
            container: container,
            textarea: textarea,
            getValue: () => textarea.value,
            setValue: (value) => { textarea.value = value; },
            focus: () => textarea.focus(),
            runCode: () => this.runCode(editorObj, options.outputType || 'output'),
            getSuggestions: () => Promise.resolve([]),
            highlightErrors: () => {}
        };

        this.editors.set(containerId, editorObj);
        return editorObj;
    }

    // Legacy method for backwards compatibility
    async createSimpleEditor(containerId, options = {}) {
        return this.createEditor(containerId, { ...options, type: 'basic' });
    }

    // Try to enhance textarea with CodeMirror
    async enhanceWithCodeMirror(container, textarea, options) {
        try {
            // This will be enhanced when CodeMirror modules are fully loaded
            setTimeout(async () => {
                if (window.CodeMirror && window.CodeMirror.EditorView) {
                    // Replace textarea with CodeMirror when ready
                    this.replaceWithCodeMirror(container, textarea, options);
                }
            }, 1000);
        } catch (error) {
            console.log('CodeMirror enhancement not available, using textarea fallback');
        }
    }

    // Replace textarea with full CodeMirror editor
    replaceWithCodeMirror(container, textarea, options) {
        // This would replace the textarea with a full CodeMirror editor
        // For now, keep the working textarea implementation
        console.log('CodeMirror enhancement ready');
    }

    // Event listeners for exercise interface
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
            if (confirm('Reset your code?')) {
                editor.setValue('def TODO(numbers):\n    # Find max number\n    pass');
            }
        });
    }

    // Event listeners for playground
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

        try {
            const response = await fetch(`/api/v1/exercises/${exerciseData.id}/submit/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ code })
            });

            const result = await response.json();
            this.showTestResults(result);
        } catch (error) {
            console.error('Submission error:', error);
        }
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
            </div>
        `;
    }

    // AI Integration Methods
    async getAISuggestions(editor) {
        if (!this.aiSuggestionsEnabled) return [];
        
        const code = editor.getValue();
        const cursor = editor.getSelection ? editor.getSelection() : null;
        
        try {
            const response = await fetch('/api/v1/ai/suggestions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ 
                    code, 
                    cursor_position: cursor ? cursor.from : 0,
                    language: 'python'
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                return result.suggestions || [];
            }
        } catch (error) {
            console.error('AI suggestions error:', error);
        }
        
        return [];
    }

    async highlightErrors(editor, errors = null) {
        if (!this.errorHighlightingEnabled) return;
        
        // If no errors provided, analyze the code
        if (!errors) {
            const code = editor.getValue();
            errors = await this.analyzeCodeForErrors(code);
        }
        
        // Apply error decorations if editor supports it
        if (editor.view && this.modules) {
            this.applyErrorDecorations(editor.view, errors);
        }
    }

    async analyzeCodeForErrors(code) {
        // First try basic Python syntax validation
        const basicErrors = this.validatePythonSyntax(code);
        
        // Then try AI-powered analysis
        try {
            const response = await fetch('/api/v1/ai/analyze/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ code, language: 'python' })
            });
            
            if (response.ok) {
                const result = await response.json();
                const aiErrors = result.errors || [];
                return [...basicErrors, ...aiErrors];
            }
        } catch (error) {
            console.debug('AI error analysis not available:', error.message);
        }
        
        return basicErrors;
    }

    validatePythonSyntax(code) {
        const errors = [];
        const lines = code.split('\n');
        
        // Basic Python syntax checks
        let indentLevel = 0;
        let inString = false;
        let stringChar = '';
        let parenCount = 0;
        let bracketCount = 0;
        let braceCount = 0;
        
        lines.forEach((line, lineIndex) => {
            const trimmed = line.trim();
            
            // Skip empty lines and comments
            if (!trimmed || trimmed.startsWith('#')) return;
            
            // Check for unmatched brackets/parentheses
            for (let i = 0; i < line.length; i++) {
                const char = line[i];
                
                if (!inString) {
                    if (char === '"' || char === "'") {
                        inString = true;
                        stringChar = char;
                    } else if (char === '(') {
                        parenCount++;
                    } else if (char === ')') {
                        parenCount--;
                        if (parenCount < 0) {
                            errors.push({
                                line: lineIndex + 1,
                                from: i,
                                to: i + 1,
                                message: 'Unmatched closing parenthesis',
                                severity: 'error'
                            });
                        }
                    } else if (char === '[') {
                        bracketCount++;
                    } else if (char === ']') {
                        bracketCount--;
                        if (bracketCount < 0) {
                            errors.push({
                                line: lineIndex + 1,
                                from: i,
                                to: i + 1,
                                message: 'Unmatched closing bracket',
                                severity: 'error'
                            });
                        }
                    } else if (char === '{') {
                        braceCount++;
                    } else if (char === '}') {
                        braceCount--;
                        if (braceCount < 0) {
                            errors.push({
                                line: lineIndex + 1,
                                from: i,
                                to: i + 1,
                                message: 'Unmatched closing brace',
                                severity: 'error'
                            });
                        }
                    }
                } else if (char === stringChar && line[i-1] !== '\\') {
                    inString = false;
                    stringChar = '';
                }
            }
            
            // Check for missing colons after control structures
            if (trimmed.match(/^(if|elif|else|for|while|def|class|try|except|finally|with)\b/) && !trimmed.endsWith(':')) {
                errors.push({
                    line: lineIndex + 1,
                    from: line.length - 1,
                    to: line.length,
                    message: 'Missing colon after control structure',
                    severity: 'error'
                });
            }
            
            // Check for common Python mistakes
            if (trimmed.includes('=') && !trimmed.includes('==') && !trimmed.includes('!=') && !trimmed.includes('<=') && !trimmed.includes('>=')) {
                const ifMatch = trimmed.match(/if\s+.*=/);
                if (ifMatch) {
                    errors.push({
                        line: lineIndex + 1,
                        from: ifMatch.index,
                        to: ifMatch.index + ifMatch[0].length,
                        message: 'Did you mean "==" for comparison?',
                        severity: 'warning'
                    });
                }
            }
        });
        
        // Check for unmatched brackets at end
        if (parenCount > 0) {
            errors.push({
                line: lines.length,
                message: `${parenCount} unmatched opening parenthesis`,
                severity: 'error'
            });
        }
        if (bracketCount > 0) {
            errors.push({
                line: lines.length,
                message: `${bracketCount} unmatched opening bracket`,
                severity: 'error'
            });
        }
        if (braceCount > 0) {
            errors.push({
                line: lines.length,
                message: `${braceCount} unmatched opening brace`,
                severity: 'error'
            });
        }
        
        return errors;
    }

    applyErrorDecorations(view, errors) {
        if (!view || !errors.length) return;
        
        try {
            const { StateEffect } = this.modules;
            // This would dispatch error decorations to the editor
            // For now, just log the errors
            console.log('Applying error decorations:', errors);
        } catch (error) {
            console.error('Failed to apply error decorations:', error);
        }
    }

    async explainError(error, code) {
        try {
            const response = await fetch('/api/v1/ai/explain-error/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ error, code, language: 'python' })
            });
            
            if (response.ok) {
                const result = await response.json();
                return result.explanation || 'Could not explain this error.';
            }
        } catch (error) {
            console.error('Error explanation failed:', error);
        }
        
        return 'Error explanation service unavailable.';
    }

    // Format code using AI or built-in formatters
    async formatCode(editor, language = 'python') {
        const code = editor.getValue();
        
        try {
            const response = await fetch('/api/v1/ai/format/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ code, language })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.formatted_code) {
                    editor.setValue(result.formatted_code);
                    return true;
                }
            }
        } catch (error) {
            console.error('Code formatting failed:', error);
        }
        
        return false;
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

// Global setup
window.CodeMirrorSetup = CodeMirrorSetup;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.codeMirrorSetup = new CodeMirrorSetup();
});

// Global hint and solution functions
window.showHint = function(exerciseData) {
    alert('Hint: Try using the max() function or iterate through the list to find the largest number.');
};

window.showSolution = function(exerciseData) {
    if (confirm('Are you sure you want to see the solution?')) {
        alert('Solution:\n\ndef TODO(numbers):\n    return max(numbers)');
    }
};