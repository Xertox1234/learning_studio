/**
 * Reading Tracker - Advanced reading metrics and engagement tracking
 * Tracks reading time, scroll depth, and engagement patterns
 */

class ReadingTracker {
    constructor(options = {}) {
        this.options = {
            // Tracking settings
            minReadTime: 3000, // Minimum time to consider as reading (ms)
            scrollThreshold: 0.05, // Minimum scroll to track progress
            heartbeatInterval: 5000, // How often to send data (ms)
            inactivityTimeout: 30000, // Time before considering user inactive (ms)
            
            // UI settings
            showProgressBar: true,
            showReadingTime: true,
            showCompletionBadge: true,
            
            // API endpoints
            trackingEndpoint: '/forum-features/api/track-reading-time/',
            
            // Selectors
            contentSelector: '.post-content, .lesson-content, .course-content',
            progressBarSelector: '.reading-progress-bar',
            
            ...options
        };
        
        // State tracking
        this.startTime = Date.now();
        this.lastActivityTime = Date.now();
        this.totalReadingTime = 0;
        this.isActive = true;
        this.isVisible = true;
        this.maxScrollDepth = 0;
        this.currentScrollDepth = 0;
        
        // Content information
        this.contentType = this.detectContentType();
        this.contentId = this.getContentId();
        this.contentHeight = 0;
        this.viewportHeight = 0;
        
        // Event tracking
        this.events = [];
        this.lastHeartbeat = Date.now();
        
        this.init();
    }
    
    init() {
        if (!this.contentId || !this.contentType) {
            console.log('ReadingTracker: No trackable content found');
            return;
        }
        
        this.setupElements();
        this.bindEvents();
        this.startTracking();
        
        console.log(`ReadingTracker: Initialized for ${this.contentType} #${this.contentId}`);
    }
    
    setupElements() {
        // Calculate content dimensions
        const content = document.querySelector(this.options.contentSelector);
        if (content) {
            this.contentHeight = content.scrollHeight;
        }
        this.viewportHeight = window.innerHeight;
        
        // Create or find progress bar
        if (this.options.showProgressBar) {
            this.createProgressBar();
        }
        
        // Create reading time display
        if (this.options.showReadingTime) {
            this.createReadingTimeDisplay();
        }
    }
    
    bindEvents() {
        // Scroll tracking
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            this.updateActivity();
            this.updateScrollDepth();
            
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                this.updateProgressBar();
            }, 100);
        }, { passive: true });
        
        // Activity tracking
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'].forEach(event => {
            document.addEventListener(event, () => this.updateActivity(), { passive: true });
        });
        
        // Visibility tracking
        document.addEventListener('visibilitychange', () => {
            this.isVisible = !document.hidden;
            if (this.isVisible) {
                this.updateActivity();
            }
        });
        
        // Page unload tracking
        window.addEventListener('beforeunload', () => {
            this.sendTrackingData(true);
        });
        
        // Resize handling
        window.addEventListener('resize', () => {
            this.viewportHeight = window.innerHeight;
            this.updateScrollDepth();
        }, { passive: true });
    }
    
    startTracking() {
        // Start heartbeat for periodic data sending
        this.heartbeatInterval = setInterval(() => {
            this.checkActivity();
            this.updateReadingTime();
            this.sendHeartbeat();
        }, this.options.heartbeatInterval);
        
        // Initial scroll depth
        this.updateScrollDepth();
        this.updateProgressBar();
    }
    
    updateActivity() {
        const now = Date.now();
        this.lastActivityTime = now;
        
        if (!this.isActive) {
            this.isActive = true;
            this.addEvent('activity_resumed');
        }
    }
    
    checkActivity() {
        const now = Date.now();
        const timeSinceActivity = now - this.lastActivityTime;
        
        if (timeSinceActivity > this.options.inactivityTimeout && this.isActive) {
            this.isActive = false;
            this.addEvent('activity_paused');
        }
    }
    
    updateReadingTime() {
        if (this.isActive && this.isVisible) {
            const now = Date.now();
            const interval = now - this.lastHeartbeat;
            this.totalReadingTime += interval;
            this.lastHeartbeat = now;
            
            if (this.options.showReadingTime) {
                this.updateReadingTimeDisplay();
            }
        }
    }
    
    updateScrollDepth() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollableHeight = Math.max(
            document.body.scrollHeight,
            document.documentElement.scrollHeight
        ) - this.viewportHeight;
        
        if (scrollableHeight > 0) {
            this.currentScrollDepth = Math.min(scrollTop / scrollableHeight, 1);
            this.maxScrollDepth = Math.max(this.maxScrollDepth, this.currentScrollDepth);
            
            // Track milestone scrolling
            const milestones = [0.25, 0.5, 0.75, 0.9, 1.0];
            milestones.forEach(milestone => {
                if (this.currentScrollDepth >= milestone && !this.hasReachedMilestone(milestone)) {
                    this.addEvent('scroll_milestone', { milestone });
                }
            });
        }
    }
    
    updateProgressBar() {
        const progressBar = document.querySelector(this.options.progressBarSelector);
        if (progressBar) {
            const percentage = Math.round(this.currentScrollDepth * 100);
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', percentage);
            
            // Add completion class
            if (percentage >= 95) {
                progressBar.classList.add('reading-complete');
                if (this.options.showCompletionBadge) {
                    this.showCompletionBadge();
                }
            }
        }
    }
    
    createProgressBar() {
        // Check if progress bar already exists
        if (document.querySelector(this.options.progressBarSelector)) {
            return;
        }
        
        const progressContainer = document.createElement('div');
        progressContainer.className = 'reading-progress-container';
        progressContainer.innerHTML = `
            <div class="reading-progress-wrapper">
                <div class="reading-progress-bar" 
                     role="progressbar" 
                     aria-valuenow="0" 
                     aria-valuemin="0" 
                     aria-valuemax="100"
                     aria-label="Reading progress">
                </div>
            </div>
        `;
        
        // Insert at top of page
        document.body.insertBefore(progressContainer, document.body.firstChild);
    }
    
    createReadingTimeDisplay() {
        const timeDisplay = document.createElement('div');
        timeDisplay.className = 'reading-time-display';
        timeDisplay.innerHTML = `
            <div class="reading-time-wrapper">
                <i class="bi bi-clock"></i>
                <span class="reading-time-text">0m</span>
            </div>
        `;
        
        // Position fixed on screen
        document.body.appendChild(timeDisplay);
    }
    
    updateReadingTimeDisplay() {
        const display = document.querySelector('.reading-time-text');
        if (display) {
            const minutes = Math.floor(this.totalReadingTime / 60000);
            const seconds = Math.floor((this.totalReadingTime % 60000) / 1000);
            
            if (minutes > 0) {
                display.textContent = `${minutes}m`;
            } else if (seconds > 0) {
                display.textContent = `${seconds}s`;
            } else {
                display.textContent = '0s';
            }
        }
    }
    
    showCompletionBadge() {
        // Avoid showing multiple badges
        if (document.querySelector('.reading-completion-badge')) {
            return;
        }
        
        const badge = document.createElement('div');
        badge.className = 'reading-completion-badge';
        badge.innerHTML = `
            <div class="badge-content">
                <i class="bi bi-check-circle-fill"></i>
                <span>Reading Complete!</span>
            </div>
        `;
        
        document.body.appendChild(badge);
        
        // Animate in
        setTimeout(() => badge.classList.add('show'), 100);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            badge.classList.remove('show');
            setTimeout(() => badge.remove(), 300);
        }, 3000);
    }
    
    addEvent(type, data = {}) {
        this.events.push({
            type,
            timestamp: Date.now(),
            scrollDepth: this.currentScrollDepth,
            ...data
        });
    }
    
    hasReachedMilestone(milestone) {
        return this.events.some(event => 
            event.type === 'scroll_milestone' && 
            event.milestone === milestone
        );
    }
    
    sendHeartbeat() {
        if (this.totalReadingTime >= this.options.minReadTime) {
            this.sendTrackingData();
        }
    }
    
    sendTrackingData(isPageUnload = false) {
        if (!this.contentId || this.totalReadingTime < 1000) {
            return;
        }
        
        const data = {
            content_type: this.contentType,
            content_id: this.contentId,
            time_spent: Math.round(this.totalReadingTime / 1000), // Convert to seconds
            scroll_depth: this.maxScrollDepth,
            events: this.events,
            session_data: {
                start_time: this.startTime,
                is_active: this.isActive,
                is_visible: this.isVisible,
                viewport_height: this.viewportHeight,
                content_height: this.contentHeight
            }
        };
        
        // Use sendBeacon for page unload to ensure delivery
        if (isPageUnload && navigator.sendBeacon) {
            const formData = new FormData();
            formData.append('data', JSON.stringify(data));
            navigator.sendBeacon(this.options.trackingEndpoint, formData);
        } else {
            // Regular AJAX for normal tracking
            fetch(this.options.trackingEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(data)
            }).catch(error => {
                console.error('ReadingTracker: Failed to send data', error);
            });
        }
        
        // Reset events after sending
        this.events = [];
    }
    
    detectContentType() {
        const path = window.location.pathname;
        
        if (path.includes('/forum/')) {
            if (path.includes('/topic/')) {
                return 'topic';
            }
            return 'forum';
        }
        
        if (path.includes('/courses/')) {
            if (path.includes('/lessons/')) {
                return 'lesson';
            }
            return 'course';
        }
        
        if (path.includes('/exercises/')) {
            return 'exercise';
        }
        
        return null;
    }
    
    getContentId() {
        // Extract ID from URL or data attributes
        const path = window.location.pathname;
        
        // Try to get from data attribute first
        const content = document.querySelector(this.options.contentSelector);
        if (content && content.dataset.contentId) {
            return content.dataset.contentId;
        }
        
        // Extract from URL patterns
        const topicMatch = path.match(/\/topic\/[^\/]+\/(\d+)/);
        if (topicMatch) {
            return topicMatch[1];
        }
        
        const courseMatch = path.match(/\/courses\/[^\/]+\/(\d+)/);
        if (courseMatch) {
            return courseMatch[1];
        }
        
        const lessonMatch = path.match(/\/lessons\/[^\/]+\/(\d+)/);
        if (lessonMatch) {
            return lessonMatch[1];
        }
        
        const exerciseMatch = path.match(/\/exercises\/(\d+)/);
        if (exerciseMatch) {
            return exerciseMatch[1];
        }
        
        return null;
    }
    
    getCSRFToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenElement) {
            return tokenElement.value;
        }
        
        const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
        return cookieMatch ? cookieMatch[1] : '';
    }
    
    // Public API
    getStats() {
        return {
            readingTime: this.totalReadingTime,
            scrollDepth: this.maxScrollDepth,
            isActive: this.isActive,
            events: this.events.length,
            contentType: this.contentType,
            contentId: this.contentId
        };
    }
    
    pause() {
        this.isActive = false;
        clearInterval(this.heartbeatInterval);
    }
    
    resume() {
        this.isActive = true;
        this.updateActivity();
        this.startTracking();
    }
    
    destroy() {
        clearInterval(this.heartbeatInterval);
        this.sendTrackingData(true);
        
        // Remove created elements
        const progressContainer = document.querySelector('.reading-progress-container');
        if (progressContainer) {
            progressContainer.remove();
        }
        
        const timeDisplay = document.querySelector('.reading-time-display');
        if (timeDisplay) {
            timeDisplay.remove();
        }
    }
}

// Auto-initialize on supported pages
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on content pages
    const contentSelectors = [
        '.post-content',
        '.lesson-content', 
        '.course-content',
        '.topic-detail',
        '.exercise-content'
    ];
    
    const hasContent = contentSelectors.some(selector => 
        document.querySelector(selector)
    );
    
    if (hasContent && typeof window !== 'undefined') {
        window.readingTracker = new ReadingTracker();
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ReadingTracker;
}