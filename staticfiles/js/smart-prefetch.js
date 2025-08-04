/**
 * Smart Prefetching System
 * Intelligently prefetches content based on user behavior and patterns
 */

class SmartPrefetch {
    constructor(options = {}) {
        this.options = {
            // Prefetch settings
            enablePrefetch: options.enablePrefetch !== false,
            prefetchOnHover: options.prefetchOnHover !== false,
            prefetchOnIdle: options.prefetchOnIdle !== false,
            prefetchTopics: options.prefetchTopics !== false,
            
            // Timing settings
            hoverDelay: options.hoverDelay || 300,
            idleDelay: options.idleDelay || 2000,
            maxConcurrentPrefetch: options.maxConcurrentPrefetch || 2,
            
            // Selectors
            linkSelector: options.linkSelector || 'a[href^="/forum/"], a[href^="/courses/"], a[href^="/lessons/"]',
            topicLinkSelector: options.topicLinkSelector || 'a[href*="/topic/"]',
            
            // Intelligent prefetch settings
            enableLearning: options.enableLearning !== false,
            maxPrefetchMB: options.maxPrefetchMB || 10,
            respectDataSaver: options.respectDataSaver !== false,
            
            // Cache settings
            maxCacheAge: options.maxCacheAge || 5 * 60 * 1000, // 5 minutes
            
            ...options
        };
        
        // State management
        this.prefetchedUrls = new Set();
        this.prefetchQueue = [];
        this.activePrefetches = 0;
        this.lastInteraction = Date.now();
        this.isIdle = false;
        
        // User behavior tracking
        this.userBehavior = {
            visitedPages: [],
            hoverPatterns: new Map(),
            clickPatterns: new Map(),
            timeOnPage: new Map(),
            scrollBehavior: new Map()
        };
        
        // Performance tracking
        this.metrics = {
            prefetchRequests: 0,
            prefetchHits: 0,
            prefetchBytes: 0,
            averageResponseTime: 0,
            cacheHitRate: 0
        };
        
        // Connection monitoring
        this.connectionInfo = {
            effectiveType: '4g',
            saveData: false,
            downlink: 10
        };
        
        this.init();
    }
    
    init() {
        if (!this.options.enablePrefetch) {
            console.log('Smart prefetch disabled');
            return;
        }
        
        this.detectConnection();
        this.bindEvents();
        this.startIdleTracking();
        this.loadUserBehavior();
        
        console.log('Smart prefetch initialized', {
            connection: this.connectionInfo.effectiveType,
            saveData: this.connectionInfo.saveData
        });
    }
    
    detectConnection() {
        if ('connection' in navigator) {
            const conn = navigator.connection;
            this.connectionInfo = {
                effectiveType: conn.effectiveType || '4g',
                saveData: conn.saveData || false,
                downlink: conn.downlink || 10
            };
            
            // Listen for connection changes
            conn.addEventListener('change', () => {
                this.connectionInfo = {
                    effectiveType: conn.effectiveType || '4g',
                    saveData: conn.saveData || false,
                    downlink: conn.downlink || 10
                };
                this.adjustPrefetchStrategy();
            });
        }
    }
    
    adjustPrefetchStrategy() {
        const { effectiveType, saveData, downlink } = this.connectionInfo;
        
        // Disable prefetch on slow connections or data saver mode
        if (this.options.respectDataSaver && saveData) {
            this.options.enablePrefetch = false;
            return;
        }
        
        // Adjust prefetch aggressiveness based on connection
        if (effectiveType === 'slow-2g' || effectiveType === '2g') {
            this.options.maxConcurrentPrefetch = 1;
            this.options.maxPrefetchMB = 2;
            this.options.prefetchOnHover = false;
        } else if (effectiveType === '3g') {
            this.options.maxConcurrentPrefetch = 1;
            this.options.maxPrefetchMB = 5;
        } else {
            // 4g or better
            this.options.maxConcurrentPrefetch = 2;
            this.options.maxPrefetchMB = 10;
        }
        
        console.log('Prefetch strategy adjusted:', {
            effectiveType,
            saveData,
            maxConcurrent: this.options.maxConcurrentPrefetch,
            maxMB: this.options.maxPrefetchMB
        });
    }
    
    bindEvents() {
        // Hover prefetching
        if (this.options.prefetchOnHover) {
            this.bindHoverEvents();
        }
        
        // Visibility prefetching
        this.bindVisibilityEvents();
        
        // User interaction tracking
        this.bindInteractionTracking();
        
        // Page navigation tracking
        this.bindNavigationTracking();
    }
    
    bindHoverEvents() {
        let hoverTimer;
        
        document.addEventListener('mouseover', (e) => {
            const link = e.target.closest(this.options.linkSelector);
            if (!link) return;
            
            clearTimeout(hoverTimer);
            hoverTimer = setTimeout(() => {
                this.handleHover(link);
            }, this.options.hoverDelay);
        });
        
        document.addEventListener('mouseout', (e) => {
            clearTimeout(hoverTimer);
        });
        
        // Touch events for mobile
        document.addEventListener('touchstart', (e) => {
            const link = e.target.closest(this.options.linkSelector);
            if (link) {
                this.handleHover(link);
            }
        }, { passive: true });
    }
    
    bindVisibilityEvents() {
        const observer = new IntersectionObserver(
            this.handleVisibilityChange.bind(this),
            {
                rootMargin: '50px',
                threshold: 0.1
            }
        );
        
        // Observe all prefetchable links
        document.querySelectorAll(this.options.linkSelector).forEach(link => {
            observer.observe(link);
        });
        
        // Observe new links added to DOM
        const mutationObserver = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const links = node.querySelectorAll ? 
                            node.querySelectorAll(this.options.linkSelector) : [];
                        links.forEach(link => observer.observe(link));
                    }
                });
            });
        });
        
        mutationObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    bindInteractionTracking() {
        // Track user activity for idle detection
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'].forEach(event => {
            document.addEventListener(event, () => {
                this.lastInteraction = Date.now();
                this.isIdle = false;
            }, { passive: true });
        });
        
        // Track click patterns
        document.addEventListener('click', (e) => {
            const link = e.target.closest(this.options.linkSelector);
            if (link) {
                this.trackClickPattern(link);
            }
        });
    }
    
    bindNavigationTracking() {
        // Track page visits
        this.userBehavior.visitedPages.push({
            url: window.location.pathname,
            timestamp: Date.now()
        });
        
        // Track time on page
        let startTime = Date.now();
        
        window.addEventListener('beforeunload', () => {
            const timeOnPage = Date.now() - startTime;
            this.userBehavior.timeOnPage.set(window.location.pathname, timeOnPage);
            this.saveUserBehavior();
        });
    }
    
    startIdleTracking() {
        setInterval(() => {
            const timeSinceLastInteraction = Date.now() - this.lastInteraction;
            
            if (timeSinceLastInteraction > this.options.idleDelay && !this.isIdle) {
                this.isIdle = true;
                this.handleIdle();
            }
        }, 1000);
    }
    
    handleHover(link) {
        const url = link.href;
        const priority = this.calculatePriority(link, 'hover');
        
        this.trackHoverPattern(link);
        this.queuePrefetch(url, priority, 'hover');
    }
    
    handleVisibilityChange(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const link = entry.target;
                const url = link.href;
                const priority = this.calculatePriority(link, 'visible');
                
                this.queuePrefetch(url, priority, 'visible');
            }
        });
    }
    
    handleIdle() {
        if (!this.options.prefetchOnIdle) return;
        
        // Prefetch likely next pages based on user behavior
        const predictedUrls = this.predictNextPages();
        
        predictedUrls.forEach((url, index) => {
            const priority = 'idle-' + index;
            this.queuePrefetch(url, priority, 'idle');
        });
    }
    
    calculatePriority(link, trigger) {
        let score = 0;
        
        // Base score by trigger type
        const triggerScores = {
            hover: 80,
            visible: 60,
            idle: 40
        };
        score += triggerScores[trigger] || 50;
        
        // Adjust based on user behavior
        const url = link.href;
        const path = new URL(url).pathname;
        
        // Higher score for previously visited patterns
        if (this.userBehavior.clickPatterns.has(path)) {
            score += this.userBehavior.clickPatterns.get(path) * 10;
        }
        
        // Higher score for frequently hovered links
        if (this.userBehavior.hoverPatterns.has(path)) {
            score += this.userBehavior.hoverPatterns.get(path) * 5;
        }
        
        // Boost forum topics if user frequently visits forum
        if (path.includes('/forum/') && this.isFrequentForumUser()) {
            score += 20;
        }
        
        // Boost courses if user is learning-focused
        if (path.includes('/courses/') && this.isFrequentLearner()) {
            score += 25;
        }
        
        return Math.min(100, score);
    }
    
    isFrequentForumUser() {
        const forumVisits = this.userBehavior.visitedPages.filter(
            page => page.url.includes('/forum/')
        ).length;
        return forumVisits > 3;
    }
    
    isFrequentLearner() {
        const courseVisits = this.userBehavior.visitedPages.filter(
            page => page.url.includes('/courses/') || page.url.includes('/lessons/')
        ).length;
        return courseVisits > 2;
    }
    
    queuePrefetch(url, priority, trigger) {
        if (this.prefetchedUrls.has(url) || !this.shouldPrefetch(url)) {
            return;
        }
        
        this.prefetchQueue.push({
            url,
            priority,
            trigger,
            timestamp: Date.now()
        });
        
        // Sort queue by priority
        this.prefetchQueue.sort((a, b) => b.priority - a.priority);
        
        this.processPrefetchQueue();
    }
    
    shouldPrefetch(url) {
        // Don't prefetch same origin
        if (new URL(url).origin !== window.location.origin) {
            return false;
        }
        
        // Don't prefetch if already cached
        if (this.prefetchedUrls.has(url)) {
            return false;
        }
        
        // Don't prefetch if bandwidth is limited
        if (this.connectionInfo.saveData) {
            return false;
        }
        
        // Don't prefetch on slow connections
        if (['slow-2g', '2g'].includes(this.connectionInfo.effectiveType)) {
            return false;
        }
        
        return true;
    }
    
    async processPrefetchQueue() {
        if (this.activePrefetches >= this.options.maxConcurrentPrefetch || 
            this.prefetchQueue.length === 0) {
            return;
        }
        
        const item = this.prefetchQueue.shift();
        if (!item) return;
        
        this.activePrefetches++;
        
        try {
            await this.prefetchUrl(item.url, item.trigger);
            this.prefetchedUrls.add(item.url);
            this.metrics.prefetchRequests++;
        } catch (error) {
            console.warn('Prefetch failed:', item.url, error);
        } finally {
            this.activePrefetches--;
            
            // Process next item
            setTimeout(() => this.processPrefetchQueue(), 100);
        }
    }
    
    async prefetchUrl(url, trigger) {
        const startTime = performance.now();
        
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Purpose': 'prefetch',
                    'X-Trigger': trigger
                },
                priority: 'low'
            });
            
            if (response.ok) {
                const responseTime = performance.now() - startTime;
                this.metrics.averageResponseTime = 
                    (this.metrics.averageResponseTime + responseTime) / 2;
                
                // Track prefetch size
                const contentLength = response.headers.get('content-length');
                if (contentLength) {
                    this.metrics.prefetchBytes += parseInt(contentLength);
                }
                
                console.log(`Prefetched: ${url} (${trigger}) in ${responseTime.toFixed(2)}ms`);
            }
        } catch (error) {
            throw new Error(`Prefetch failed for ${url}: ${error.message}`);
        }
    }
    
    predictNextPages() {
        const predictions = [];
        
        // Predict based on current page type
        const currentPath = window.location.pathname;
        
        if (currentPath.includes('/forum/')) {
            // In forum - predict popular topics
            predictions.push(...this.predictForumTopics());
        } else if (currentPath.includes('/courses/')) {
            // In courses - predict next lessons
            predictions.push(...this.predictNextLessons());
        } else if (currentPath.includes('/lessons/')) {
            // In lesson - predict exercises
            predictions.push(...this.predictRelatedExercises());
        }
        
        // Add frequently visited pages
        predictions.push(...this.getFrequentlyVisitedPages());
        
        // Remove duplicates and limit
        return [...new Set(predictions)].slice(0, 3);
    }
    
    predictForumTopics() {
        // This would typically query an API for trending topics
        // For now, return some educated guesses based on current forum
        const predictions = [];
        
        // Extract forum ID from current URL if available
        const forumMatch = window.location.pathname.match(/\/forum\/[^\/]+\/(\d+)/);
        if (forumMatch) {
            const forumId = forumMatch[1];
            predictions.push(`/forum-features/api/topics/?forum=${forumId}&limit=5`);
        }
        
        return predictions;
    }
    
    predictNextLessons() {
        // Predict next lessons in sequence
        const predictions = [];
        
        const lessonMatch = window.location.pathname.match(/\/courses\/([^\/]+)\/lessons\/([^\/]+)/);
        if (lessonMatch) {
            const [, courseSlug, lessonSlug] = lessonMatch;
            // This would typically query an API for next lessons
            predictions.push(`/courses/${courseSlug}/`);
        }
        
        return predictions;
    }
    
    predictRelatedExercises() {
        // Predict exercises related to current lesson
        return ['/exercises/'];
    }
    
    getFrequentlyVisitedPages() {
        const frequentPages = [];
        
        // Count page visits
        const pageCounts = new Map();
        this.userBehavior.visitedPages.forEach(page => {
            pageCounts.set(page.url, (pageCounts.get(page.url) || 0) + 1);
        });
        
        // Get top visited pages
        const sortedPages = Array.from(pageCounts.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 2)
            .map(([url]) => url);
        
        return sortedPages;
    }
    
    trackHoverPattern(link) {
        const path = new URL(link.href).pathname;
        const count = this.userBehavior.hoverPatterns.get(path) || 0;
        this.userBehavior.hoverPatterns.set(path, count + 1);
    }
    
    trackClickPattern(link) {
        const path = new URL(link.href).pathname;
        const count = this.userBehavior.clickPatterns.get(path) || 0;
        this.userBehavior.clickPatterns.set(path, count + 1);
        
        // Track as prefetch hit if it was prefetched
        if (this.prefetchedUrls.has(link.href)) {
            this.metrics.prefetchHits++;
            this.metrics.cacheHitRate = 
                (this.metrics.prefetchHits / this.metrics.prefetchRequests) * 100;
        }
    }
    
    loadUserBehavior() {
        try {
            const stored = localStorage.getItem('smartPrefetch_behavior');
            if (stored) {
                const data = JSON.parse(stored);
                this.userBehavior.visitedPages = data.visitedPages || [];
                this.userBehavior.hoverPatterns = new Map(data.hoverPatterns || []);
                this.userBehavior.clickPatterns = new Map(data.clickPatterns || []);
                this.userBehavior.timeOnPage = new Map(data.timeOnPage || []);
            }
        } catch (error) {
            console.warn('Failed to load user behavior data:', error);
        }
    }
    
    saveUserBehavior() {
        try {
            const data = {
                visitedPages: this.userBehavior.visitedPages.slice(-50), // Keep last 50
                hoverPatterns: Array.from(this.userBehavior.hoverPatterns.entries()),
                clickPatterns: Array.from(this.userBehavior.clickPatterns.entries()),
                timeOnPage: Array.from(this.userBehavior.timeOnPage.entries())
            };
            localStorage.setItem('smartPrefetch_behavior', JSON.stringify(data));
        } catch (error) {
            console.warn('Failed to save user behavior data:', error);
        }
    }
    
    // Public API
    getMetrics() {
        return {
            ...this.metrics,
            queueLength: this.prefetchQueue.length,
            activePrefetches: this.activePrefetches,
            prefetchedUrls: this.prefetchedUrls.size,
            connectionType: this.connectionInfo.effectiveType
        };
    }
    
    enablePrefetch() {
        this.options.enablePrefetch = true;
    }
    
    disablePrefetch() {
        this.options.enablePrefetch = false;
        this.prefetchQueue = [];
    }
    
    clearCache() {
        this.prefetchedUrls.clear();
        this.prefetchQueue = [];
    }
    
    destroy() {
        this.saveUserBehavior();
        this.clearCache();
        
        // Remove event listeners would go here
        // (In a real implementation, you'd store and clean up listeners)
    }
}

// Auto-initialize smart prefetch
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if user hasn't opted out
    const userOptOut = localStorage.getItem('smartPrefetch_disabled');
    
    if (!userOptOut) {
        window.smartPrefetch = new SmartPrefetch({
            enablePrefetch: true,
            prefetchOnHover: true,
            prefetchOnIdle: true,
            respectDataSaver: true
        });
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SmartPrefetch;
}