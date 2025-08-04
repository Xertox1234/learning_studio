/**
 * Infinite Scroll and Just-in-Time Loading System
 * Provides smooth infinite scrolling with intelligent content loading
 */

class InfiniteScroll {
    constructor(options = {}) {
        this.options = {
            // Core settings
            container: options.container || window,
            contentSelector: options.contentSelector || '.content-item',
            loadingTrigger: options.loadingTrigger || 300, // px from bottom
            batchSize: options.batchSize || 20,
            
            // API settings
            apiEndpoint: options.apiEndpoint || '/api/infinite-scroll/',
            pageParam: options.pageParam || 'page',
            
            // UI settings
            loadingTemplate: options.loadingTemplate || this.defaultLoadingTemplate(),
            emptyTemplate: options.emptyTemplate || this.defaultEmptyTemplate(),
            errorTemplate: options.errorTemplate || this.defaultErrorTemplate(),
            
            // Performance settings
            throttleDelay: options.throttleDelay || 100,
            prefetchDistance: options.prefetchDistance || 1000,
            maxConcurrentRequests: options.maxConcurrentRequests || 2,
            
            // Content settings
            contentContainer: options.contentContainer || '.content-container',
            preserveScrollPosition: options.preserveScrollPosition || true,
            
            ...options
        };
        
        // State management
        this.currentPage = 1;
        this.loading = false;
        this.hasMore = true;
        this.error = null;
        this.totalItems = 0;
        this.loadedItems = 0;
        this.requestQueue = [];
        this.activeRequests = 0;
        
        // Performance tracking
        this.metrics = {
            loadTimes: [],
            cacheHits: 0,
            networkRequests: 0,
            bytesLoaded: 0
        };
        
        // Cache for prefetched content
        this.contentCache = new Map();
        this.prefetchedPages = new Set();
        
        this.init();
    }
    
    init() {
        this.container = typeof this.options.container === 'string' 
            ? document.querySelector(this.options.container)
            : this.options.container;
            
        this.contentContainer = document.querySelector(this.options.contentContainer);
        
        if (!this.contentContainer) {
            console.error('InfiniteScroll: Content container not found');
            return;
        }
        
        this.setupIntersectionObserver();
        this.bindEvents();
        this.createLoadingIndicator();
        this.setupErrorRecovery();
        
        // Initial load if container is empty
        if (this.contentContainer.children.length === 0) {
            this.loadNextBatch();
        }
        
        console.log('InfiniteScroll initialized');
    }
    
    setupIntersectionObserver() {
        // Observer for loading trigger
        this.loadingObserver = new IntersectionObserver(
            this.throttle(this.handleIntersection.bind(this), this.options.throttleDelay),
            {
                root: this.container === window ? null : this.container,
                rootMargin: `0px 0px ${this.options.loadingTrigger}px 0px`,
                threshold: 0
            }
        );
        
        // Observer for prefetching
        this.prefetchObserver = new IntersectionObserver(
            this.handlePrefetchIntersection.bind(this),
            {
                root: this.container === window ? null : this.container,
                rootMargin: `0px 0px ${this.options.prefetchDistance}px 0px`,
                threshold: 0
            }
        );
        
        // Observer for content visibility (for analytics)
        this.visibilityObserver = new IntersectionObserver(
            this.handleVisibilityIntersection.bind(this),
            {
                root: this.container === window ? null : this.container,
                rootMargin: '0px',
                threshold: [0.1, 0.5, 0.9]
            }
        );
    }
    
    bindEvents() {
        // Handle page refresh/navigation
        window.addEventListener('beforeunload', () => {
            this.saveScrollPosition();
        });
        
        // Handle back/forward navigation
        window.addEventListener('popstate', () => {
            this.restoreScrollPosition();
        });
        
        // Handle online/offline
        window.addEventListener('online', () => {
            this.handleOnline();
        });
        
        window.addEventListener('offline', () => {
            this.handleOffline();
        });
    }
    
    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting && this.hasMore && !this.loading) {
                this.loadNextBatch();
            }
        });
    }
    
    handlePrefetchIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting && this.hasMore) {
                const nextPage = this.currentPage + 1;
                if (!this.prefetchedPages.has(nextPage)) {
                    this.prefetchPage(nextPage);
                }
            }
        });
    }
    
    handleVisibilityIntersection(entries) {
        entries.forEach(entry => {
            const item = entry.target;
            const itemId = item.dataset.itemId;
            
            if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
                // Track item as viewed
                this.trackItemView(itemId, entry.intersectionRatio);
            }
        });
    }
    
    async loadNextBatch() {
        if (this.loading || !this.hasMore || this.activeRequests >= this.options.maxConcurrentRequests) {
            return;
        }
        
        this.loading = true;
        this.activeRequests++;
        this.showLoading();
        
        const startTime = performance.now();
        
        try {
            // Check cache first
            const cacheKey = `page_${this.currentPage}`;
            let data;
            
            if (this.contentCache.has(cacheKey)) {
                data = this.contentCache.get(cacheKey);
                this.metrics.cacheHits++;
                console.log(`Cache hit for page ${this.currentPage}`);
            } else {
                data = await this.fetchData(this.currentPage);
                this.contentCache.set(cacheKey, data);
                this.metrics.networkRequests++;
            }
            
            await this.processData(data);
            
            const loadTime = performance.now() - startTime;
            this.metrics.loadTimes.push(loadTime);
            
            this.currentPage++;
            this.error = null;
            
        } catch (error) {
            console.error('Failed to load content:', error);
            this.error = error;
            this.showError();
        } finally {
            this.loading = false;
            this.activeRequests--;
            this.hideLoading();
        }
    }
    
    async fetchData(page) {
        const url = new URL(this.options.apiEndpoint, window.location.origin);
        url.searchParams.set(this.options.pageParam, page);
        url.searchParams.set('limit', this.options.batchSize);
        
        const response = await fetch(url, {
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Track bytes loaded
        const contentLength = response.headers.get('content-length');
        if (contentLength) {
            this.metrics.bytesLoaded += parseInt(contentLength);
        }
        
        return data;
    }
    
    async processData(data) {
        if (!data.results || data.results.length === 0) {
            this.hasMore = false;
            this.showEmpty();
            return;
        }
        
        // Update pagination info
        this.hasMore = data.has_next || false;
        this.totalItems = data.count || this.totalItems;
        
        // Create content elements
        const fragment = document.createDocumentFragment();
        
        for (const item of data.results) {
            const element = await this.createContentElement(item);
            if (element) {
                fragment.appendChild(element);
                this.loadedItems++;
                
                // Setup observers for this element
                this.setupElementObservers(element);
            }
        }
        
        // Add to container with animation
        await this.appendContent(fragment);
        
        // Update loading trigger
        this.updateLoadingTrigger();
    }
    
    async createContentElement(item) {
        // This should be overridden by specific implementations
        // Default implementation creates a basic card
        const element = document.createElement('div');
        element.className = 'content-item card mb-3';
        element.dataset.itemId = item.id;
        element.dataset.itemType = item.type || 'unknown';
        
        element.innerHTML = `
            <div class="card-body">
                <h5 class="card-title">${this.escapeHtml(item.title || 'Untitled')}</h5>
                <p class="card-text">${this.escapeHtml(item.content || item.description || '')}</p>
                ${item.url ? `<a href="${this.escapeHtml(item.url)}" class="btn btn-primary">View</a>` : ''}
            </div>
        `;
        
        return element;
    }
    
    async appendContent(fragment) {
        // Preserve scroll position during content insertion
        const scrollTop = this.container === window 
            ? window.pageYOffset 
            : this.container.scrollTop;
            
        // Add with fade-in animation
        const children = Array.from(fragment.children);
        children.forEach((child, index) => {
            child.style.opacity = '0';
            child.style.transform = 'translateY(20px)';
        });
        
        this.contentContainer.appendChild(fragment);
        
        // Animate in
        children.forEach((child, index) => {
            setTimeout(() => {
                child.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                child.style.opacity = '1';
                child.style.transform = 'translateY(0)';
            }, index * 50); // Stagger animation
        });
        
        // Restore scroll position if needed
        if (this.options.preserveScrollPosition) {
            if (this.container === window) {
                window.scrollTo(0, scrollTop);
            } else {
                this.container.scrollTop = scrollTop;
            }
        }
    }
    
    setupElementObservers(element) {
        // Add to visibility observer for analytics
        this.visibilityObserver.observe(element);
        
        // Setup lazy loading for images within this element
        const images = element.querySelectorAll('img[data-src]');
        images.forEach(img => {
            this.setupLazyImage(img);
        });
    }
    
    setupLazyImage(img) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadImage(entry.target);
                    imageObserver.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '50px'
        });
        
        imageObserver.observe(img);
    }
    
    async loadImage(img) {
        const src = img.dataset.src;
        if (!src) return;
        
        try {
            // Create a new image to preload
            const newImg = new Image();
            newImg.onload = () => {
                // Fade transition
                img.style.transition = 'opacity 0.3s ease';
                img.style.opacity = '0';
                
                setTimeout(() => {
                    img.src = src;
                    img.style.opacity = '1';
                    img.classList.add('loaded');
                }, 150);
            };
            
            newImg.onerror = () => {
                img.classList.add('error');
                console.error('Failed to load image:', src);
            };
            
            newImg.src = src;
            
        } catch (error) {
            console.error('Error loading image:', error);
            img.classList.add('error');
        }
    }
    
    async prefetchPage(page) {
        if (this.prefetchedPages.has(page) || this.activeRequests >= this.options.maxConcurrentRequests) {
            return;
        }
        
        this.prefetchedPages.add(page);
        
        try {
            const data = await this.fetchData(page);
            const cacheKey = `page_${page}`;
            this.contentCache.set(cacheKey, data);
            console.log(`Prefetched page ${page}`);
        } catch (error) {
            console.warn(`Failed to prefetch page ${page}:`, error);
            this.prefetchedPages.delete(page);
        }
    }
    
    createLoadingIndicator() {
        this.loadingIndicator = document.createElement('div');
        this.loadingIndicator.className = 'loading-indicator d-none text-center p-4';
        this.loadingIndicator.innerHTML = this.options.loadingTemplate;
        this.contentContainer.appendChild(this.loadingIndicator);
        
        // Observe loading indicator for infinite scroll
        this.loadingObserver.observe(this.loadingIndicator);
    }
    
    updateLoadingTrigger() {
        // Move loading indicator to end of content
        this.contentContainer.appendChild(this.loadingIndicator);
    }
    
    showLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.classList.remove('d-none');
        }
    }
    
    hideLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.classList.add('d-none');
        }
    }
    
    showError() {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-indicator alert alert-danger text-center m-3';
        errorElement.innerHTML = this.options.errorTemplate;
        
        const retryBtn = errorElement.querySelector('.retry-btn');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => {
                errorElement.remove();
                this.loadNextBatch();
            });
        }
        
        this.contentContainer.appendChild(errorElement);
    }
    
    showEmpty() {
        if (this.loadedItems === 0) {
            const emptyElement = document.createElement('div');
            emptyElement.className = 'empty-indicator text-center p-5';
            emptyElement.innerHTML = this.options.emptyTemplate;
            this.contentContainer.appendChild(emptyElement);
        }
    }
    
    // Utility methods
    throttle(func, delay) {
        let timeoutId;
        let lastExecTime = 0;
        
        return function(...args) {
            const currentTime = Date.now();
            
            if (currentTime - lastExecTime > delay) {
                func.apply(this, args);
                lastExecTime = currentTime;
            } else {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    func.apply(this, args);
                    lastExecTime = Date.now();
                }, delay - (currentTime - lastExecTime));
            }
        };
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    saveScrollPosition() {
        const position = this.container === window 
            ? window.pageYOffset 
            : this.container.scrollTop;
        sessionStorage.setItem('infiniteScroll_position', position);
        sessionStorage.setItem('infiniteScroll_page', this.currentPage);
    }
    
    restoreScrollPosition() {
        const position = sessionStorage.getItem('infiniteScroll_position');
        const page = sessionStorage.getItem('infiniteScroll_page');
        
        if (position) {
            setTimeout(() => {
                if (this.container === window) {
                    window.scrollTo(0, parseInt(position));
                } else {
                    this.container.scrollTop = parseInt(position);
                }
            }, 100);
        }
        
        if (page) {
            this.currentPage = parseInt(page);
        }
    }
    
    trackItemView(itemId, ratio) {
        // Track item views for analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'content_view', {
                event_category: 'Engagement',
                event_label: itemId,
                custom_parameter_1: ratio
            });
        }
    }
    
    handleOnline() {
        console.log('Back online - resuming infinite scroll');
        if (this.hasMore && !this.loading) {
            this.loadNextBatch();
        }
    }
    
    handleOffline() {
        console.log('Gone offline - infinite scroll paused');
    }
    
    setupErrorRecovery() {
        // Exponential backoff for failed requests
        this.retryCount = 0;
        this.maxRetries = 3;
    }
    
    // Default templates
    defaultLoadingTemplate() {
        return `
            <div class="spinner-border text-primary me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span>Loading more content...</span>
        `;
    }
    
    defaultEmptyTemplate() {
        return `
            <div class="text-muted">
                <i class="bi bi-inbox fs-1 d-block mb-3"></i>
                <h5>No more content</h5>
                <p>You've reached the end of the list.</p>
            </div>
        `;
    }
    
    defaultErrorTemplate() {
        return `
            <div>
                <i class="bi bi-exclamation-triangle fs-4 text-warning me-2"></i>
                <span>Failed to load content.</span>
                <button class="btn btn-outline-primary btn-sm ms-2 retry-btn">Try Again</button>
            </div>
        `;
    }
    
    // Public API
    getMetrics() {
        return {
            ...this.metrics,
            currentPage: this.currentPage,
            loadedItems: this.loadedItems,
            totalItems: this.totalItems,
            cacheSize: this.contentCache.size,
            averageLoadTime: this.metrics.loadTimes.reduce((a, b) => a + b, 0) / this.metrics.loadTimes.length || 0
        };
    }
    
    refresh() {
        this.contentContainer.innerHTML = '';
        this.currentPage = 1;
        this.hasMore = true;
        this.loadedItems = 0;
        this.contentCache.clear();
        this.prefetchedPages.clear();
        this.createLoadingIndicator();
        this.loadNextBatch();
    }
    
    destroy() {
        this.loadingObserver?.disconnect();
        this.prefetchObserver?.disconnect();
        this.visibilityObserver?.disconnect();
        
        window.removeEventListener('beforeunload', this.saveScrollPosition);
        window.removeEventListener('popstate', this.restoreScrollPosition);
        window.removeEventListener('online', this.handleOnline);
        window.removeEventListener('offline', this.handleOffline);
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = InfiniteScroll;
}