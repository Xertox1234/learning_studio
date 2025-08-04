/**
 * Virtual Scrolling Implementation
 * Efficiently renders large lists by only showing visible items
 */

class VirtualScroll {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' 
            ? document.querySelector(container) 
            : container;
            
        if (!this.container) {
            throw new Error('Virtual scroll container not found');
        }
        
        this.options = {
            // Item settings
            itemHeight: options.itemHeight || 80,
            estimatedItemHeight: options.estimatedItemHeight || 80,
            variableHeight: options.variableHeight || false,
            
            // Rendering settings
            overscan: options.overscan || 5, // Extra items to render outside viewport
            renderBatchSize: options.renderBatchSize || 10,
            
            // Data settings
            totalItems: options.totalItems || 0,
            getItem: options.getItem || (() => ({})),
            renderItem: options.renderItem || this.defaultRenderItem.bind(this),
            
            // Performance settings
            throttleScrollDelay: options.throttleScrollDelay || 16, // ~60fps
            usePlaceholders: options.usePlaceholders !== false,
            
            // Accessibility
            enableKeyboardNavigation: options.enableKeyboardNavigation !== false,
            announceChanges: options.announceChanges !== false,
            
            ...options
        };
        
        // State management
        this.scrollTop = 0;
        this.containerHeight = 0;
        this.viewportStartIndex = 0;
        this.viewportEndIndex = 0;
        this.renderedItems = new Map();
        this.itemHeights = new Map();
        this.totalHeight = 0;
        
        // Performance tracking
        this.metrics = {
            renderTime: 0,
            scrollEvents: 0,
            renderedItems: 0,
            recycledItems: 0
        };
        
        // Element caching
        this.scrollElement = null;
        this.contentElement = null;
        this.spacerTop = null;
        this.spacerBottom = null;
        
        this.init();
    }
    
    init() {
        this.setupDOM();
        this.bindEvents();
        this.calculateDimensions();
        this.render();
        
        console.log('Virtual scroll initialized', {
            totalItems: this.options.totalItems,
            containerHeight: this.containerHeight,
            itemHeight: this.options.itemHeight
        });
    }
    
    setupDOM() {
        // Create virtual scroll structure
        this.container.style.position = 'relative';
        this.container.style.overflow = 'auto';
        
        // Create scroll element
        this.scrollElement = document.createElement('div');
        this.scrollElement.className = 'virtual-scroll';
        this.scrollElement.style.position = 'relative';
        this.scrollElement.style.height = '100%';
        
        // Create content element
        this.contentElement = document.createElement('div');
        this.contentElement.className = 'virtual-scroll-content';
        this.contentElement.style.position = 'relative';
        
        // Create spacers for maintaining scroll height
        this.spacerTop = document.createElement('div');
        this.spacerTop.className = 'virtual-scroll-spacer-top';
        this.spacerTop.style.height = '0px';
        
        this.spacerBottom = document.createElement('div');
        this.spacerBottom.className = 'virtual-scroll-spacer-bottom';
        this.spacerBottom.style.height = '0px';
        
        // Assemble structure
        this.scrollElement.appendChild(this.spacerTop);
        this.scrollElement.appendChild(this.contentElement);
        this.scrollElement.appendChild(this.spacerBottom);
        this.container.appendChild(this.scrollElement);
        
        // Set up ARIA attributes for accessibility
        this.container.setAttribute('role', 'grid');
        this.container.setAttribute('aria-rowcount', this.options.totalItems);
        this.contentElement.setAttribute('role', 'rowgroup');
    }
    
    bindEvents() {
        // Throttled scroll handler
        let scrollTimeout;
        this.container.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                this.handleScroll();
            }, this.options.throttleScrollDelay);
        }, { passive: true });
        
        // Resize handler
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 100);
        });
        
        // Keyboard navigation
        if (this.options.enableKeyboardNavigation) {
            this.bindKeyboardEvents();
        }
        
        // Mutation observer for dynamic height calculation
        if (this.options.variableHeight) {
            this.setupMutationObserver();
        }
    }
    
    bindKeyboardEvents() {
        this.container.addEventListener('keydown', (e) => {
            const focusedIndex = this.getFocusedItemIndex();
            
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    this.focusItem(Math.min(focusedIndex + 1, this.options.totalItems - 1));
                    break;
                    
                case 'ArrowUp':
                    e.preventDefault();
                    this.focusItem(Math.max(focusedIndex - 1, 0));
                    break;
                    
                case 'PageDown':
                    e.preventDefault();
                    const pageSize = Math.floor(this.containerHeight / this.options.itemHeight);
                    this.focusItem(Math.min(focusedIndex + pageSize, this.options.totalItems - 1));
                    break;
                    
                case 'PageUp':
                    e.preventDefault();
                    const pageSizeUp = Math.floor(this.containerHeight / this.options.itemHeight);
                    this.focusItem(Math.max(focusedIndex - pageSizeUp, 0));
                    break;
                    
                case 'Home':
                    e.preventDefault();
                    this.focusItem(0);
                    break;
                    
                case 'End':
                    e.preventDefault();
                    this.focusItem(this.options.totalItems - 1);
                    break;
            }
        });
    }
    
    setupMutationObserver() {
        this.mutationObserver = new MutationObserver((mutations) => {
            let needsUpdate = false;
            
            mutations.forEach(mutation => {
                if (mutation.type === 'childList' || 
                    (mutation.type === 'attributes' && 
                     mutation.attributeName === 'style')) {
                    needsUpdate = true;
                }
            });
            
            if (needsUpdate) {
                this.updateVariableHeights();
            }
        });
        
        this.mutationObserver.observe(this.contentElement, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style']
        });
    }
    
    calculateDimensions() {
        this.containerHeight = this.container.clientHeight;
        
        if (this.options.variableHeight) {
            this.calculateVariableHeights();
        } else {
            this.totalHeight = this.options.totalItems * this.options.itemHeight;
        }
        
        this.updateScrollHeight();
    }
    
    calculateVariableHeights() {
        // For variable heights, we need to estimate or measure
        let totalHeight = 0;
        
        for (let i = 0; i < this.options.totalItems; i++) {
            let height = this.itemHeights.get(i);
            
            if (!height) {
                // Use estimated height for unmeasured items
                height = this.options.estimatedItemHeight;
                this.itemHeights.set(i, height);
            }
            
            totalHeight += height;
        }
        
        this.totalHeight = totalHeight;
    }
    
    updateScrollHeight() {
        this.scrollElement.style.height = `${this.totalHeight}px`;
    }
    
    handleScroll() {
        this.scrollTop = this.container.scrollTop;
        this.metrics.scrollEvents++;
        
        const oldStartIndex = this.viewportStartIndex;
        const oldEndIndex = this.viewportEndIndex;
        
        this.calculateVisibleRange();
        
        // Only re-render if the visible range changed significantly
        if (this.viewportStartIndex !== oldStartIndex || 
            this.viewportEndIndex !== oldEndIndex) {
            this.render();
        }
    }
    
    handleResize() {
        this.calculateDimensions();
        this.calculateVisibleRange();
        this.render();
    }
    
    calculateVisibleRange() {
        if (this.options.variableHeight) {
            this.calculateVariableVisibleRange();
        } else {
            this.calculateFixedVisibleRange();
        }
    }
    
    calculateFixedVisibleRange() {
        const itemHeight = this.options.itemHeight;
        const scrollTop = this.scrollTop;
        const containerHeight = this.containerHeight;
        
        // Calculate visible range
        this.viewportStartIndex = Math.floor(scrollTop / itemHeight);
        this.viewportEndIndex = Math.min(
            Math.ceil((scrollTop + containerHeight) / itemHeight),
            this.options.totalItems
        );
        
        // Add overscan
        this.viewportStartIndex = Math.max(0, this.viewportStartIndex - this.options.overscan);
        this.viewportEndIndex = Math.min(
            this.options.totalItems,
            this.viewportEndIndex + this.options.overscan
        );
    }
    
    calculateVariableVisibleRange() {
        let accumulatedHeight = 0;
        let startIndex = 0;
        let endIndex = this.options.totalItems;
        
        // Find start index
        for (let i = 0; i < this.options.totalItems; i++) {
            const itemHeight = this.itemHeights.get(i) || this.options.estimatedItemHeight;
            
            if (accumulatedHeight + itemHeight > this.scrollTop) {
                startIndex = i;
                break;
            }
            
            accumulatedHeight += itemHeight;
        }
        
        // Find end index
        const viewportBottom = this.scrollTop + this.containerHeight;
        
        for (let i = startIndex; i < this.options.totalItems; i++) {
            const itemHeight = this.itemHeights.get(i) || this.options.estimatedItemHeight;
            accumulatedHeight += itemHeight;
            
            if (accumulatedHeight > viewportBottom) {
                endIndex = i + 1;
                break;
            }
        }
        
        // Add overscan
        this.viewportStartIndex = Math.max(0, startIndex - this.options.overscan);
        this.viewportEndIndex = Math.min(this.options.totalItems, endIndex + this.options.overscan);
    }
    
    render() {
        const startTime = performance.now();
        
        // Clear content
        this.contentElement.innerHTML = '';
        
        // Calculate spacer heights
        const topSpacerHeight = this.getOffsetForIndex(this.viewportStartIndex);
        const bottomSpacerHeight = this.totalHeight - this.getOffsetForIndex(this.viewportEndIndex);
        
        this.spacerTop.style.height = `${topSpacerHeight}px`;
        this.spacerBottom.style.height = `${bottomSpacerHeight}px`;
        
        // Render visible items
        for (let i = this.viewportStartIndex; i < this.viewportEndIndex; i++) {
            this.renderItemAtIndex(i);
        }
        
        // Update ARIA attributes
        this.container.setAttribute('aria-rowcount', this.options.totalItems);
        
        // Track performance
        const renderTime = performance.now() - startTime;
        this.metrics.renderTime = renderTime;
        this.metrics.renderedItems = this.viewportEndIndex - this.viewportStartIndex;
        
        // Announce changes for screen readers
        if (this.options.announceChanges) {
            this.announceVisibleRange();
        }
        
        console.log(`Rendered ${this.metrics.renderedItems} items in ${renderTime.toFixed(2)}ms`);
    }
    
    renderItemAtIndex(index) {
        const item = this.options.getItem(index);
        if (!item) return;
        
        const element = this.createItemElement(item, index);
        
        // Set up accessibility attributes
        element.setAttribute('role', 'row');
        element.setAttribute('aria-rowindex', index + 1);
        element.setAttribute('tabindex', index === 0 ? 0 : -1);
        
        this.contentElement.appendChild(element);
        
        // Measure height for variable height mode
        if (this.options.variableHeight) {
            this.measureItemHeight(element, index);
        }
    }
    
    createItemElement(item, index) {
        let element = this.renderedItems.get(index);
        
        if (!element) {
            element = document.createElement('div');
            element.className = 'virtual-scroll-item';
            element.dataset.index = index;
            
            if (!this.options.variableHeight) {
                element.style.height = `${this.options.itemHeight}px`;
            }
            
            this.renderedItems.set(index, element);
        } else {
            this.metrics.recycledItems++;
        }
        
        // Render item content
        const content = this.options.renderItem(item, index);
        if (typeof content === 'string') {
            element.innerHTML = content;
        } else if (content instanceof Element) {
            element.innerHTML = '';
            element.appendChild(content);
        }
        
        return element;
    }
    
    measureItemHeight(element, index) {
        // Use ResizeObserver if available for accurate measurements
        if ('ResizeObserver' in window) {
            const resizeObserver = new ResizeObserver(entries => {
                entries.forEach(entry => {
                    const newHeight = entry.contentRect.height;
                    const oldHeight = this.itemHeights.get(index) || this.options.estimatedItemHeight;
                    
                    if (Math.abs(newHeight - oldHeight) > 1) {
                        this.itemHeights.set(index, newHeight);
                        this.updateTotalHeight();
                    }
                });
            });
            
            resizeObserver.observe(element);
        } else {
            // Fallback to manual measurement
            setTimeout(() => {
                const height = element.offsetHeight;
                this.itemHeights.set(index, height);
                this.updateTotalHeight();
            }, 0);
        }
    }
    
    updateTotalHeight() {
        if (this.options.variableHeight) {
            this.calculateVariableHeights();
            this.updateScrollHeight();
        }
    }
    
    getOffsetForIndex(index) {
        if (this.options.variableHeight) {
            let offset = 0;
            for (let i = 0; i < index; i++) {
                offset += this.itemHeights.get(i) || this.options.estimatedItemHeight;
            }
            return offset;
        } else {
            return index * this.options.itemHeight;
        }
    }
    
    defaultRenderItem(item, index) {
        return `
            <div class="virtual-item-content">
                <div class="virtual-item-index">#${index}</div>
                <div class="virtual-item-data">${JSON.stringify(item)}</div>
            </div>
        `;
    }
    
    getFocusedItemIndex() {
        const focused = this.container.querySelector('[tabindex="0"]');
        return focused ? parseInt(focused.dataset.index) : 0;
    }
    
    focusItem(index) {
        // Clamp index to valid range
        index = Math.max(0, Math.min(index, this.options.totalItems - 1));
        
        // Scroll item into view
        this.scrollToItem(index);
        
        // Update focus
        const currentFocused = this.container.querySelector('[tabindex="0"]');
        if (currentFocused) {
            currentFocused.setAttribute('tabindex', '-1');
        }
        
        // Focus new item (after render)
        setTimeout(() => {
            const newFocused = this.container.querySelector(`[data-index="${index}"]`);
            if (newFocused) {
                newFocused.setAttribute('tabindex', '0');
                newFocused.focus();
            }
        }, 50);
    }
    
    scrollToItem(index) {
        const offset = this.getOffsetForIndex(index);
        this.container.scrollTop = offset;
    }
    
    announceVisibleRange() {
        if (!this.options.announceChanges) return;
        
        const liveRegion = document.getElementById('virtual-scroll-live-region') || 
            this.createLiveRegion();
        
        const message = `Showing items ${this.viewportStartIndex + 1} to ${this.viewportEndIndex} of ${this.options.totalItems}`;
        liveRegion.textContent = message;
    }
    
    createLiveRegion() {
        const liveRegion = document.createElement('div');
        liveRegion.id = 'virtual-scroll-live-region';
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.style.position = 'absolute';
        liveRegion.style.left = '-10000px';
        liveRegion.style.width = '1px';
        liveRegion.style.height = '1px';
        liveRegion.style.overflow = 'hidden';
        
        document.body.appendChild(liveRegion);
        return liveRegion;
    }
    
    // Public API methods
    setTotalItems(count) {
        this.options.totalItems = count;
        this.calculateDimensions();
        this.render();
    }
    
    updateItem(index, newData) {
        this.renderedItems.delete(index);
        
        if (index >= this.viewportStartIndex && index < this.viewportEndIndex) {
            this.render();
        }
    }
    
    refresh() {
        this.renderedItems.clear();
        this.calculateDimensions();
        this.render();
    }
    
    getMetrics() {
        return {
            ...this.metrics,
            viewportStartIndex: this.viewportStartIndex,
            viewportEndIndex: this.viewportEndIndex,
            totalHeight: this.totalHeight,
            containerHeight: this.containerHeight
        };
    }
    
    destroy() {
        this.mutationObserver?.disconnect();
        
        // Clean up DOM
        if (this.container.contains(this.scrollElement)) {
            this.container.removeChild(this.scrollElement);
        }
        
        // Clean up live region
        const liveRegion = document.getElementById('virtual-scroll-live-region');
        if (liveRegion) {
            liveRegion.remove();
        }
        
        this.renderedItems.clear();
        this.itemHeights.clear();
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VirtualScroll;
}