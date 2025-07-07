/**
 * Python Learning Studio - Main JavaScript
 * Handles interactive functionality and API communications
 */

class PythonLearningStudio {
    constructor() {
        this.apiBase = '/api/v1/';
        this.codeEditors = new Map();
        this.notifications = [];
        this.init();
    }

    init() {
        this.setupCSRF();
        this.setupEventListeners();
        this.loadNotifications();
        this.initializeCodeEditors();
    }

    // CSRF Token Setup
    setupCSRF() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (csrfToken) {
            this.csrfToken = csrfToken;
        }
    }

    // Event Listeners
    setupEventListeners() {
        // Code execution buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.run-code-btn')) {
                this.executeCode(e.target);
            }
            if (e.target.matches('.submit-code-btn')) {
                this.submitCode(e.target);
            }
            if (e.target.matches('.get-hint-btn')) {
                this.getHint(e.target);
            }
            if (e.target.matches('.ai-help-btn')) {
                this.getAIHelp(e.target);
            }
        });

        // Search functionality
        const searchForm = document.querySelector('form[role="search"]');
        if (searchForm) {
            searchForm.addEventListener('submit', this.handleSearch.bind(this));
        }

        // Auto-save code
        document.addEventListener('input', (e) => {
            if (e.target.matches('.code-editor textarea')) {
                this.autoSaveCode(e.target);
            }
        });

        // Modal events
        document.addEventListener('show.bs.modal', this.handleModalShow.bind(this));
    }

    // Code Editor Management
    initializeCodeEditors() {
        document.querySelectorAll('.code-editor').forEach(element => {
            this.createCodeEditor(element);
        });
    }

    createCodeEditor(element) {
        const language = element.dataset.language || 'python';
        const readonly = element.dataset.readonly === 'true';
        
        const editor = CodeMirror.fromTextArea(element, {
            mode: language,
            theme: 'material-darker',
            lineNumbers: true,
            autoCloseBrackets: true,
            matchBrackets: true,
            indentUnit: 4,
            indentWithTabs: false,
            readOnly: readonly,
            extraKeys: {
                'Ctrl-Space': 'autocomplete',
                'Ctrl-Enter': () => this.executeCurrentCode(element),
                'F11': (cm) => {
                    cm.setOption('fullScreen', !cm.getOption('fullScreen'));
                },
                'Esc': (cm) => {
                    if (cm.getOption('fullScreen')) cm.setOption('fullScreen', false);
                }
            }
        });

        this.codeEditors.set(element.id || element.name, editor);
        return editor;
    }

    getCodeEditor(id) {
        return this.codeEditors.get(id);
    }

    // Code Execution
    async executeCode(button) {
        const editorId = button.dataset.editor;
        const editor = this.getCodeEditor(editorId);
        if (!editor) return;

        const code = editor.getValue();
        const language = button.dataset.language || 'python';
        const outputElement = document.querySelector(button.dataset.output);

        button.disabled = true;
        button.innerHTML = '<i class="bi bi-hourglass-split"></i> Running...';
        
        try {
            const response = await this.apiCall('code-execution/', {
                method: 'POST',
                body: JSON.stringify({
                    code: code,
                    language: language,
                    timeout: 10
                })
            });

            this.displayCodeOutput(outputElement, response, 'execution');
        } catch (error) {
            this.displayCodeOutput(outputElement, {
                success: false,
                error: error.message,
                output: ''
            }, 'execution');
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-play-fill"></i> Run Code';
        }
    }

    async submitCode(button) {
        const editorId = button.dataset.editor;
        const exerciseId = button.dataset.exercise;
        const editor = this.getCodeEditor(editorId);
        if (!editor || !exerciseId) return;

        const code = editor.getValue();
        const outputElement = document.querySelector(button.dataset.output);

        button.disabled = true;
        button.innerHTML = '<i class="bi bi-hourglass-split"></i> Submitting...';

        try {
            const response = await this.apiCall('exercise-evaluation/', {
                method: 'POST',
                body: JSON.stringify({
                    exercise_id: exerciseId,
                    code: code
                })
            });

            this.displayCodeOutput(outputElement, response, 'submission');
            this.updateProgress(response);
        } catch (error) {
            this.displayCodeOutput(outputElement, {
                success: false,
                error: error.message
            }, 'submission');
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-check-circle"></i> Submit';
        }
    }

    displayCodeOutput(element, result, type) {
        if (!element) return;

        let outputHtml = '';
        
        if (type === 'execution') {
            if (result.success) {
                outputHtml = `
                    <div class="code-output success">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="text-success"><i class="bi bi-check-circle"></i> Execution Successful</span>
                            <small>Time: ${(result.execution_time * 1000).toFixed(2)}ms</small>
                        </div>
                        <pre>${result.output || 'No output'}</pre>
                    </div>
                `;
            } else {
                outputHtml = `
                    <div class="code-output error">
                        <div class="text-danger mb-2"><i class="bi bi-x-circle"></i> Execution Error</div>
                        <pre>${result.error}</pre>
                    </div>
                `;
            }
        } else if (type === 'submission') {
            const scoreClass = result.score >= 80 ? 'success' : result.score >= 60 ? 'warning' : 'danger';
            
            outputHtml = `
                <div class="submission-results">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h6 class="mb-0">Submission Results</h6>
                        <span class="badge bg-${scoreClass} fs-6">${result.score}%</span>
                    </div>
                    
                    <div class="test-summary mb-3">
                        <div class="row text-center">
                            <div class="col">
                                <div class="fw-bold text-success">${result.passed_tests || 0}</div>
                                <small class="text-muted">Passed</small>
                            </div>
                            <div class="col">
                                <div class="fw-bold text-danger">${(result.total_tests || 0) - (result.passed_tests || 0)}</div>
                                <small class="text-muted">Failed</small>
                            </div>
                            <div class="col">
                                <div class="fw-bold">${result.total_tests || 0}</div>
                                <small class="text-muted">Total</small>
                            </div>
                        </div>
                    </div>
            `;

            if (result.test_results) {
                outputHtml += '<div class="test-results">';
                result.test_results.forEach(test => {
                    outputHtml += `
                        <div class="test-case ${test.passed ? 'passed' : 'failed'}">
                            <div class="d-flex justify-content-between align-items-center">
                                <span><i class="bi bi-${test.passed ? 'check' : 'x'}-circle"></i> ${test.name}</span>
                                <small>${(test.execution_time * 1000).toFixed(2)}ms</small>
                            </div>
                            ${!test.passed ? `
                                <div class="mt-2 small">
                                    <div><strong>Expected:</strong> <code>${test.expected}</code></div>
                                    <div><strong>Got:</strong> <code>${test.actual}</code></div>
                                </div>
                            ` : ''}
                        </div>
                    `;
                });
                outputHtml += '</div>';
            }

            outputHtml += '</div>';
        }

        element.innerHTML = outputHtml;
    }

    // AI Assistance
    async getHint(button) {
        const exerciseId = button.dataset.exercise;
        const editorId = button.dataset.editor;
        const editor = this.getCodeEditor(editorId);

        button.disabled = true;
        button.innerHTML = '<i class="bi bi-hourglass-split"></i> Getting hint...';

        try {
            const response = await this.apiCall('ai-assistance/', {
                method: 'POST',
                body: JSON.stringify({
                    assistance_type: 'hint_generation',
                    content: editor ? editor.getValue() : '',
                    context: `Exercise ID: ${exerciseId}`
                })
            });

            this.showHintModal(response.response);
        } catch (error) {
            this.showAlert('Error getting hint: ' + error.message, 'danger');
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-lightbulb"></i> Get Hint';
        }
    }

    async getAIHelp(button) {
        const type = button.dataset.type || 'code_explanation';
        const content = button.dataset.content || '';
        
        try {
            const response = await this.apiCall('ai-assistance/', {
                method: 'POST',
                body: JSON.stringify({
                    assistance_type: type,
                    content: content
                })
            });

            this.showAIResponse(response.response);
        } catch (error) {
            this.showAlert('AI assistance unavailable: ' + error.message, 'warning');
        }
    }

    // UI Helpers
    showHintModal(hint) {
        const modal = document.getElementById('hintModal') || this.createHintModal();
        modal.querySelector('.modal-body').innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-lightbulb me-2"></i>
                ${hint}
            </div>
        `;
        new bootstrap.Modal(modal).show();
    }

    showAIResponse(response) {
        const modal = document.getElementById('aiResponseModal') || this.createAIResponseModal();
        modal.querySelector('.modal-body').innerHTML = `
            <div class="ai-message">
                <div class="ai-avatar">
                    <i class="bi bi-robot"></i>
                </div>
                <div class="message-content">
                    ${response}
                </div>
            </div>
        `;
        new bootstrap.Modal(modal).show();
    }

    createHintModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'hintModal';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="bi bi-lightbulb me-2"></i>Hint</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body"></div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        return modal;
    }

    createAIResponseModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'aiResponseModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="bi bi-robot me-2"></i>AI Assistant</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body"></div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        return modal;
    }

    showAlert(message, type = 'info') {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container-fluid') || document.body;
        container.insertBefore(alert, container.firstChild);
        
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    // Notifications
    async loadNotifications() {
        try {
            const notifications = await this.apiCall('notifications/');
            this.updateNotificationUI(notifications);
        } catch (error) {
            console.warn('Could not load notifications:', error);
        }
    }

    updateNotificationUI(notifications) {
        const unreadCount = notifications.filter(n => !n.is_read).length;
        const countElement = document.getElementById('notification-count');
        if (countElement) {
            countElement.textContent = unreadCount || '';
            countElement.style.display = unreadCount ? 'block' : 'none';
        }
    }

    // Progress Updates
    updateProgress(submissionResult) {
        // Update progress bars and statistics
        const progressElements = document.querySelectorAll('[data-progress-type]');
        progressElements.forEach(element => {
            this.updateProgressElement(element, submissionResult);
        });
    }

    updateProgressElement(element, result) {
        const type = element.dataset.progressType;
        
        if (type === 'exercise' && result.score >= 80) {
            element.style.width = '100%';
            element.className = element.className.replace(/bg-\w+/, 'bg-success');
        }
    }

    // Search
    handleSearch(event) {
        event.preventDefault();
        const query = event.target.querySelector('input[type="search"]').value;
        this.performSearch(query);
    }

    async performSearch(query) {
        try {
            const results = await this.apiCall(`courses/?search=${encodeURIComponent(query)}`);
            this.displaySearchResults(results);
        } catch (error) {
            this.showAlert('Search failed: ' + error.message, 'danger');
        }
    }

    // Auto-save
    autoSaveCode(textarea) {
        const key = `code_draft_${textarea.name || textarea.id}`;
        localStorage.setItem(key, textarea.value);
    }

    loadCodeDraft(textareaId) {
        const key = `code_draft_${textareaId}`;
        return localStorage.getItem(key) || '';
    }

    // API Helper
    async apiCall(endpoint, options = {}) {
        const url = this.apiBase + endpoint;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            }
        };

        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`API call failed: ${response.status} ${response.statusText}`);
        }

        return response.json();
    }

    // Modal Handlers
    handleModalShow(event) {
        const modal = event.target;
        const modalType = modal.dataset.modalType;
        
        if (modalType === 'code-editor') {
            this.initializeModalCodeEditor(modal);
        }
    }

    initializeModalCodeEditor(modal) {
        const textarea = modal.querySelector('.code-editor');
        if (textarea && !this.getCodeEditor(textarea.id)) {
            this.createCodeEditor(textarea);
        }
    }
}

// Initialize the application
const app = new PythonLearningStudio();

// Expose app globally for debugging
window.PLS = app;