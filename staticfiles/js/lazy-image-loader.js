/**
 * Lazy Image Loader with Blur-Up Technique
 * Provides progressive image loading with smooth transitions
 */

class LazyImageLoader {
    constructor(options = {}) {
        this.options = {
            // Selectors
            imageSelector: options.imageSelector || 'img[data-src]',
            blurImageSelector: options.blurImageSelector || 'img[data-blur-src]',
            backgroundImageSelector: options.backgroundImageSelector || '[data-bg-src]',
            
            // Loading settings
            rootMargin: options.rootMargin || '50px',
            threshold: options.threshold || 0.1,
            
            // Blur-up settings
            enableBlurUp: options.enableBlurUp !== false,
            blurAmount: options.blurAmount || 20,
            transitionDuration: options.transitionDuration || 300,
            
            // Performance settings
            maxConcurrentLoads: options.maxConcurrentLoads || 4,
            retryAttempts: options.retryAttempts || 3,
            retryDelay: options.retryDelay || 1000,
            
            // Placeholder settings
            placeholderColor: options.placeholderColor || '#f8f9fa',
            useColorPlaceholder: options.useColorPlaceholder || true,
            
            // Progressive enhancement
            webpSupport: null,
            avifSupport: null,
            
            ...options
        };
        
        // State tracking
        this.loadingImages = new Set();
        this.loadedImages = new Set();
        this.failedImages = new Set();
        this.retryCount = new Map();
        
        // Performance metrics
        this.metrics = {
            totalImages: 0,
            loadedImages: 0,
            failedImages: 0,
            averageLoadTime: 0,
            totalLoadTime: 0,
            cacheHits: 0
        };
        
        this.init();
    }
    
    async init() {
        await this.detectFormatSupport();
        this.setupIntersectionObserver();
        this.processExistingImages();
        this.bindEvents();
        
        console.log('LazyImageLoader initialized', {
            webpSupport: this.options.webpSupport,
            avifSupport: this.options.avifSupport
        });
    }
    
    async detectFormatSupport() {
        // Detect WebP support
        this.options.webpSupport = await this.supportsFormat('webp');
        
        // Detect AVIF support
        this.options.avifSupport = await this.supportsFormat('avif');
    }
    
    supportsFormat(format) {
        return new Promise(resolve => {
            const img = new Image();
            img.onload = () => resolve(true);
            img.onerror = () => resolve(false);
            
            const testSrc = {
                webp: 'data:image/webp;base64,UklGRiIAAABXRUJQVlA4IBYAAAAwAQCdASoBAAEADsD+JaQAA3AAAAAA',
                avif: 'data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAAB0AAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAEAAAABAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQ0MAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAACVtZGF0EgAKCBgABogQEAwgMg8f8D///8WfhwB8+ErK42A='
            };
            
            img.src = testSrc[format];
        });
    }
    
    setupIntersectionObserver() {
        this.observer = new IntersectionObserver(
            this.handleIntersection.bind(this),
            {
                rootMargin: this.options.rootMargin,
                threshold: this.options.threshold
            }
        );
    }
    
    processExistingImages() {
        // Process images already in the DOM
        this.observeImages(document);
    }
    
    observeImages(container = document) {
        // Regular images with data-src
        const images = container.querySelectorAll(this.options.imageSelector);
        images.forEach(img => {
            this.observer.observe(img);
            this.metrics.totalImages++;
        });
        
        // Background images
        const bgImages = container.querySelectorAll(this.options.backgroundImageSelector);
        bgImages.forEach(el => {
            this.observer.observe(el);
            this.metrics.totalImages++;
        });
        
        // Images with blur placeholders
        const blurImages = container.querySelectorAll(this.options.blurImageSelector);
        blurImages.forEach(img => {
            this.setupBlurImage(img);
            this.observer.observe(img);
            this.metrics.totalImages++;
        });
    }
    
    setupBlurImage(img) {
        if (this.options.enableBlurUp && img.dataset.blurSrc) {
            // Create low-res placeholder
            const placeholder = new Image();
            placeholder.onload = () => {
                img.src = img.dataset.blurSrc;
                img.style.filter = `blur(${this.options.blurAmount}px)`;
                img.style.transform = 'scale(1.1)'; // Slight scale to hide blur edges
                img.style.transition = `filter ${this.options.transitionDuration}ms ease, transform ${this.options.transitionDuration}ms ease`;
            };
            placeholder.src = img.dataset.blurSrc;
        }
    }
    
    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                this.loadImage(entry.target);
                this.observer.unobserve(entry.target);
            }
        });
    }
    
    async loadImage(element) {
        if (this.loadingImages.has(element) || this.loadedImages.has(element)) {
            return;
        }
        
        // Check concurrent load limit
        if (this.loadingImages.size >= this.options.maxConcurrentLoads) {
            setTimeout(() => this.loadImage(element), 100);
            return;
        }
        
        this.loadingImages.add(element);
        element.classList.add('lazy-loading');
        
        const startTime = performance.now();
        
        try {
            if (element.tagName === 'IMG') {
                await this.loadRegularImage(element);
            } else {
                await this.loadBackgroundImage(element);
            }
            
            const loadTime = performance.now() - startTime;
            this.updateMetrics(loadTime, true);
            
            this.loadedImages.add(element);
            element.classList.remove('lazy-loading');
            element.classList.add('lazy-loaded');
            
        } catch (error) {
            console.error('Failed to load image:', error);
            this.handleImageError(element);
        } finally {
            this.loadingImages.delete(element);
        }
    }
    
    async loadRegularImage(img) {
        const originalSrc = this.getOptimizedSrc(img.dataset.src || img.dataset.lazySrc);
        
        return new Promise((resolve, reject) => {
            const newImg = new Image();
            
            newImg.onload = () => {
                // Apply the image with transition
                if (this.options.enableBlurUp && img.style.filter) {
                    // Remove blur effect
                    img.style.filter = 'none';
                    img.style.transform = 'scale(1)';
                }
                
                // Set the high-res source
                img.src = originalSrc;
                img.removeAttribute('data-src');
                img.removeAttribute('data-lazy-src');
                
                // Add loaded class after transition
                setTimeout(() => {
                    img.classList.add('image-loaded');
                }, this.options.transitionDuration);
                
                resolve();
            };
            
            newImg.onerror = () => {
                reject(new Error(`Failed to load image: ${originalSrc}`));
            };
            
            // Start loading
            newImg.src = originalSrc;
        });
    }
    
    async loadBackgroundImage(element) {
        const originalSrc = this.getOptimizedSrc(element.dataset.bgSrc);
        
        return new Promise((resolve, reject) => {
            const img = new Image();
            
            img.onload = () => {
                // Apply background image with transition
                element.style.backgroundImage = `url(${originalSrc})`;
                element.removeAttribute('data-bg-src');
                element.classList.add('bg-loaded');
                resolve();
            };
            
            img.onerror = () => {
                reject(new Error(`Failed to load background image: ${originalSrc}`));
            };
            
            img.src = originalSrc;
        });
    }
    
    getOptimizedSrc(src) {
        if (!src) return src;
        
        // Try to serve modern formats if supported
        const url = new URL(src, window.location.origin);
        
        // Check if we can optimize the format
        if (this.options.avifSupport && !src.includes('.avif')) {
            // Try AVIF version
            const avifSrc = src.replace(/\.(jpg|jpeg|png)$/, '.avif');
            return avifSrc;
        } else if (this.options.webpSupport && !src.includes('.webp')) {
            // Try WebP version
            const webpSrc = src.replace(/\.(jpg|jpeg|png)$/, '.webp');
            return webpSrc;
        }
        
        return src;
    }
    
    handleImageError(element) {
        this.failedImages.add(element);
        element.classList.remove('lazy-loading');
        element.classList.add('lazy-error');
        
        // Try retry if attempts remaining
        const retryCount = this.retryCount.get(element) || 0;
        
        if (retryCount < this.options.retryAttempts) {
            this.retryCount.set(element, retryCount + 1);
            
            setTimeout(() => {
                this.failedImages.delete(element);
                element.classList.remove('lazy-error');
                this.loadImage(element);
            }, this.options.retryDelay * (retryCount + 1)); // Exponential backoff
        } else {
            // Show fallback/placeholder
            this.showErrorPlaceholder(element);
            this.updateMetrics(0, false);
        }
    }
    
    showErrorPlaceholder(element) {
        if (element.tagName === 'IMG') {
            // Generate a placeholder image
            element.src = this.generatePlaceholder(
                element.width || 300, 
                element.height || 200
            );
            element.alt = 'Image not available';
        } else {
            // Set placeholder background
            element.style.backgroundColor = this.options.placeholderColor;
            element.style.backgroundImage = 'none';
        }
    }
    
    generatePlaceholder(width, height) {
        // Create a simple SVG placeholder
        const svg = `
            <svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="${this.options.placeholderColor}"/>
                <text x="50%" y="50%" text-anchor="middle" dy="0.3em" 
                      font-family="Arial, sans-serif" font-size="14" fill="#6c757d">
                    Image not available
                </text>
            </svg>
        `;
        
        return `data:image/svg+xml;base64,${btoa(svg)}`;
    }
    
    updateMetrics(loadTime, success) {
        if (success) {
            this.metrics.loadedImages++;
            this.metrics.totalLoadTime += loadTime;
            this.metrics.averageLoadTime = this.metrics.totalLoadTime / this.metrics.loadedImages;
        } else {
            this.metrics.failedImages++;
        }
    }
    
    bindEvents() {
        // Handle dynamic content
        this.setupMutationObserver();
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.resumeLoading();
            }
        });
        
        // Handle online/offline
        window.addEventListener('online', () => {
            this.retryFailedImages();
        });
    }
    
    setupMutationObserver() {
        this.mutationObserver = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        this.observeImages(node);
                    }
                });
            });
        });
        
        this.mutationObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    resumeLoading() {
        // Resume loading images that might have been paused
        const pausedImages = document.querySelectorAll('.lazy-loading');
        pausedImages.forEach(img => {
            if (!this.loadingImages.has(img)) {
                this.loadImage(img);
            }
        });
    }
    
    retryFailedImages() {
        // Retry failed images when back online
        this.failedImages.forEach(element => {
            element.classList.remove('lazy-error');
            this.retryCount.delete(element);
            this.failedImages.delete(element);
            this.loadImage(element);
        });
    }
    
    // Public API methods
    loadAll() {
        // Force load all images immediately
        const allImages = document.querySelectorAll(
            `${this.options.imageSelector}, ${this.options.backgroundImageSelector}, ${this.options.blurImageSelector}`
        );
        
        allImages.forEach(element => {
            if (!this.loadedImages.has(element)) {
                this.loadImage(element);
            }
        });
    }
    
    refresh() {
        // Re-scan for new images
        this.processExistingImages();
    }
    
    getMetrics() {
        return {
            ...this.metrics,
            loadingImages: this.loadingImages.size,
            successRate: this.metrics.totalImages > 0 
                ? (this.metrics.loadedImages / this.metrics.totalImages) * 100 
                : 0
        };
    }
    
    destroy() {
        this.observer?.disconnect();
        this.mutationObserver?.disconnect();
        
        document.removeEventListener('visibilitychange', this.resumeLoading);
        window.removeEventListener('online', this.retryFailedImages);
        
        this.loadingImages.clear();
        this.loadedImages.clear();
        this.failedImages.clear();
        this.retryCount.clear();
    }
}

// Auto-initialize lazy loading
document.addEventListener('DOMContentLoaded', function() {
    window.lazyImageLoader = new LazyImageLoader({
        enableBlurUp: true,
        maxConcurrentLoads: 4,
        retryAttempts: 2
    });
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LazyImageLoader;
}