/**
 * Forum JavaScript functionality for Python Learning Studio
 */

class ForumManager {
    constructor() {
        this.init();
    }
    
    init() {
        // Initialize forum features
        this.initQuickReply();
        this.initPollOptions();
        this.initTopicActions();
        this.initSearchFeatures();
        this.bindEventListeners();
    }
    
    /**
     * Initialize quick reply functionality
     */
    initQuickReply() {
        const quickReplyForm = document.querySelector('.quick-reply form');
        if (quickReplyForm) {
            quickReplyForm.addEventListener('submit', (e) => {
                const textarea = quickReplyForm.querySelector('textarea[name="content"]');
                if (!textarea.value.trim()) {
                    e.preventDefault();
                    this.showError('Please enter your reply content.');
                    textarea.focus();
                }
            });
        }
    }
    
    /**
     * Initialize poll options management
     */
    initPollOptions() {
        const addOptionBtn = document.getElementById('add-option');
        if (addOptionBtn) {
            addOptionBtn.addEventListener('click', () => {
                this.addPollOption();
            });
        }
        
        // Handle remove option buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-option') || 
                e.target.closest('.remove-option')) {
                e.preventDefault();
                this.removePollOption(e.target.closest('.input-group'));
            }
        });
    }
    
    /**
     * Add new poll option field
     */
    addPollOption() {
        const pollOptions = document.getElementById('poll-options');
        const totalForms = document.querySelector('#id_poll_options-TOTAL_FORMS');
        
        if (!pollOptions || !totalForms) return;
        
        const currentFormCount = parseInt(totalForms.value);
        const maxForms = 10; // Limit poll options
        
        if (currentFormCount >= maxForms) {
            this.showError(`Maximum ${maxForms} poll options allowed.`);
            return;
        }
        
        const newOption = document.createElement('div');
        newOption.className = 'input-group mb-2';
        newOption.innerHTML = `
            <input type="text" name="poll_options-${currentFormCount}-text" 
                   class="form-control" placeholder="Enter poll option" maxlength="255">
            <button type="button" class="btn btn-outline-danger btn-sm remove-option">
                <i class="bi bi-trash"></i>
            </button>
        `;
        
        pollOptions.appendChild(newOption);
        totalForms.value = currentFormCount + 1;
        
        // Focus on new input
        newOption.querySelector('input').focus();
    }
    
    /**
     * Remove poll option field
     */
    removePollOption(optionElement) {
        const pollOptions = document.getElementById('poll-options');
        const totalForms = document.querySelector('#id_poll_options-TOTAL_FORMS');
        
        if (!pollOptions || !totalForms) return;
        
        const currentFormCount = parseInt(totalForms.value);
        
        if (currentFormCount <= 2) {
            this.showError('At least 2 poll options are required.');
            return;
        }
        
        optionElement.remove();
        totalForms.value = currentFormCount - 1;
    }
    
    /**
     * Initialize topic action buttons
     */
    initTopicActions() {
        // Quote button functionality
        document.addEventListener('click', (e) => {
            if (e.target.closest('.btn-quote')) {
                e.preventDefault();
                this.handleQuote(e.target.closest('.btn-quote'));
            }
        });
        
        // Topic moderation actions
        document.addEventListener('click', (e) => {
            if (e.target.closest('.topic-action')) {
                this.handleTopicAction(e.target.closest('.topic-action'));
            }
        });
    }
    
    /**
     * Handle quote functionality
     */
    handleQuote(quoteBtn) {
        const postElement = quoteBtn.closest('.card');
        const authorElement = postElement.querySelector('.card-header strong');
        const contentElement = postElement.querySelector('.post-content');
        
        if (!authorElement || !contentElement) return;
        
        const author = authorElement.textContent.trim();
        const content = contentElement.textContent.trim();
        const postUrl = quoteBtn.href;
        
        // Find quick reply textarea or redirect to reply page with quote
        const quickReplyTextarea = document.querySelector('.quick-reply textarea[name="content"]');
        
        if (quickReplyTextarea) {
            const quoteText = `[quote="${author}"]${content}[/quote]\n\n`;
            quickReplyTextarea.value = quoteText;
            quickReplyTextarea.focus();
            quickReplyTextarea.setSelectionRange(quoteText.length, quoteText.length);
            
            // Scroll to quick reply
            document.querySelector('.quick-reply').scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        } else {
            // Redirect to full reply page
            window.location.href = postUrl;
        }
    }
    
    /**
     * Handle topic moderation actions
     */
    handleTopicAction(actionBtn) {
        const action = actionBtn.dataset.action;
        const confirmMessage = actionBtn.dataset.confirm;
        
        if (confirmMessage && !confirm(confirmMessage)) {
            return false;
        }
        
        // Add loading state
        actionBtn.disabled = true;
        const originalText = actionBtn.innerHTML;
        actionBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Processing...';
        
        // Restore button state after a delay (in case of page redirect)
        setTimeout(() => {
            actionBtn.disabled = false;
            actionBtn.innerHTML = originalText;
        }, 3000);
    }
    
    /**
     * Initialize search features
     */
    initSearchFeatures() {
        const searchForm = document.querySelector('.forum-search form');
        if (searchForm) {
            const searchInput = searchForm.querySelector('input[type="search"]');
            
            // Add search suggestions (placeholder for future implementation)
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    // Debounce search suggestions
                    clearTimeout(this.searchTimeout);
                    this.searchTimeout = setTimeout(() => {
                        this.showSearchSuggestions(e.target.value);
                    }, 300);
                });
            }
        }
    }
    
    /**
     * Show search suggestions (placeholder)
     */
    showSearchSuggestions(query) {
        // Placeholder for search suggestions implementation
        if (query.length < 2) return;
        
        // This would typically make an AJAX request to get suggestions
        console.log('Search suggestions for:', query);
    }
    
    /**
     * Bind additional event listeners
     */
    bindEventListeners() {
        // Auto-expand textareas
        document.addEventListener('input', (e) => {
            if (e.target.tagName === 'TEXTAREA') {
                this.autoExpandTextarea(e.target);
            }
        });
        
        // Handle form validation
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('forum-form')) {
                this.validateForumForm(e);
            }
        });
        
        // Handle topic type changes
        const topicTypeSelect = document.querySelector('select[name="topic_type"]');
        if (topicTypeSelect) {
            topicTypeSelect.addEventListener('change', (e) => {
                this.handleTopicTypeChange(e.target.value);
            });
        }
    }
    
    /**
     * Auto-expand textarea as user types
     */
    autoExpandTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }
    
    /**
     * Validate forum forms
     */
    validateForumForm(event) {
        const form = event.target;
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.showFieldError(field, 'This field is required.');
                isValid = false;
            } else {
                this.clearFieldError(field);
            }
        });
        
        // Validate topic subject length
        const subjectField = form.querySelector('input[name="subject"]');
        if (subjectField && subjectField.value.length > 255) {
            this.showFieldError(subjectField, 'Subject is too long (maximum 255 characters).');
            isValid = false;
        }
        
        // Validate content length
        const contentField = form.querySelector('textarea[name="content"]');
        if (contentField && contentField.value.length < 10) {
            this.showFieldError(contentField, 'Content is too short (minimum 10 characters).');
            isValid = false;
        }
        
        if (!isValid) {
            event.preventDefault();
        }
    }
    
    /**
     * Handle topic type changes
     */
    handleTopicTypeChange(topicType) {
        // Show/hide relevant form sections based on topic type
        console.log('Topic type changed to:', topicType);
        
        // Example: Show poll section only for poll topics
        const pollSection = document.querySelector('.poll-section');
        if (pollSection) {
            pollSection.style.display = topicType === 'poll' ? 'block' : 'none';
        }
    }
    
    /**
     * Show field error
     */
    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
    }
    
    /**
     * Clear field error
     */
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const existingError = field.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }
    }
    
    /**
     * Show error message
     */
    showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(alert, container.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 5000);
        }
    }
    
    /**
     * Show success message
     */
    showSuccess(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(alert, container.firstChild);
            
            // Auto-dismiss after 3 seconds
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 3000);
        }
    }
}

// Initialize forum manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.body.classList.contains('forum-page')) {
        window.forumManager = new ForumManager();
    }
});

// Export for potential use by other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ForumManager;
}