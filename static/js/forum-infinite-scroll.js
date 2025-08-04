/**
 * Forum Infinite Scroll Implementation
 * Extends InfiniteScroll for forum-specific content loading
 */

class ForumInfiniteScroll extends InfiniteScroll {
    constructor(options = {}) {
        const forumDefaults = {
            contentSelector: '.topic-row, .post-item',
            contentContainer: '.forum-content-container',
            batchSize: 20,
            
            // Forum-specific API endpoints
            topicsEndpoint: '/forum-features/api/topics/',
            postsEndpoint: '/forum-features/api/posts/',
            
            // Forum content types
            contentType: 'topics', // 'topics' or 'posts'
            forumId: null,
            topicId: null,
            
            // Forum-specific UI
            showUserAvatars: true,
            showTrustLevels: true,
            showPostPreviews: true,
            
            ...options
        };
        
        super(forumDefaults);
        this.setupForumSpecifics();
    }
    
    setupForumSpecifics() {
        // Set API endpoint based on content type
        if (this.options.contentType === 'posts' && this.options.topicId) {
            this.options.apiEndpoint = `${this.options.postsEndpoint}?topic=${this.options.topicId}`;
        } else if (this.options.contentType === 'topics' && this.options.forumId) {
            this.options.apiEndpoint = `${this.options.topicsEndpoint}?forum=${this.options.forumId}`;
        } else {
            this.options.apiEndpoint = this.options.topicsEndpoint;
        }
    }
    
    async createContentElement(item) {
        const element = document.createElement('div');
        
        if (this.options.contentType === 'topics') {
            return this.createTopicElement(item);
        } else if (this.options.contentType === 'posts') {
            return this.createPostElement(item);
        }
        
        return element;
    }
    
    createTopicElement(topic) {
        const element = document.createElement('div');
        element.className = 'topic-row card mb-3';
        element.dataset.itemId = topic.id;
        element.dataset.itemType = 'topic';
        
        const lastPost = topic.last_post || {};
        const author = topic.poster || {};
        
        element.innerHTML = `
            <div class="card-body">
                <div class="row align-items-center">
                    <!-- Topic Info -->
                    <div class="col-md-6">
                        <div class="d-flex align-items-start">
                            ${this.options.showUserAvatars ? `
                                <img src="${this.getAvatarUrl(author)}" 
                                     class="rounded-circle me-3 lazy-avatar" 
                                     width="40" height="40" 
                                     alt="${this.escapeHtml(author.username || 'User')}"
                                     data-src="${this.getAvatarUrl(author)}"
                                     style="background: var(--bs-secondary);">
                            ` : ''}
                            <div class="flex-grow-1">
                                <h6 class="mb-1">
                                    <a href="${this.escapeHtml(topic.url)}" class="text-decoration-none">
                                        ${this.getTopicIcon(topic)}
                                        ${this.escapeHtml(topic.subject)}
                                    </a>
                                </h6>
                                <div class="small text-muted">
                                    <span>by <strong>${this.escapeHtml(author.username || 'Unknown')}</strong></span>
                                    ${this.options.showTrustLevels && author.trust_level !== undefined ? `
                                        <span class="badge trust-level-${author.trust_level} ms-1">TL${author.trust_level}</span>
                                    ` : ''}
                                    <span class="ms-2">${this.formatDate(topic.created)}</span>
                                </div>
                                ${this.options.showPostPreviews && topic.preview ? `
                                    <p class="small text-muted mt-2 mb-0">${this.escapeHtml(topic.preview)}</p>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Topic Stats -->
                    <div class="col-md-3 text-center d-none d-md-block">
                        <div class="row">
                            <div class="col-6">
                                <div class="text-primary fw-bold">${topic.posts_count || 0}</div>
                                <div class="small text-muted">Posts</div>
                            </div>
                            <div class="col-6">
                                <div class="text-info fw-bold">${topic.views_count || 0}</div>
                                <div class="small text-muted">Views</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Last Activity -->
                    <div class="col-md-3">
                        ${lastPost.id ? `
                            <div class="d-flex align-items-center">
                                ${this.options.showUserAvatars ? `
                                    <img src="${this.getAvatarUrl(lastPost.poster)}" 
                                         class="rounded-circle me-2 lazy-avatar" 
                                         width="24" height="24" 
                                         alt="${this.escapeHtml(lastPost.poster?.username || 'User')}"
                                         data-src="${this.getAvatarUrl(lastPost.poster)}"
                                         style="background: var(--bs-secondary);">
                                ` : ''}
                                <div class="flex-grow-1">
                                    <div class="small">
                                        <strong>${this.escapeHtml(lastPost.poster?.username || 'Unknown')}</strong>
                                    </div>
                                    <div class="small text-muted">${this.formatDate(lastPost.created)}</div>
                                </div>
                                <a href="${this.escapeHtml(lastPost.url || topic.url)}" 
                                   class="btn btn-sm btn-outline-primary">
                                    <i class="bi bi-arrow-right"></i>
                                </a>
                            </div>
                        ` : `
                            <div class="text-center text-muted small">
                                No recent activity
                            </div>
                        `}
                    </div>
                </div>
            </div>
        `;
        
        return element;
    }
    
    createPostElement(post) {
        const element = document.createElement('div');
        element.className = 'post-item card mb-3';
        element.dataset.itemId = post.id;
        element.dataset.itemType = 'post';
        element.id = `post-${post.id}`;
        
        const author = post.poster || {};
        
        element.innerHTML = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center">
                    ${this.options.showUserAvatars ? `
                        <img src="${this.getAvatarUrl(author)}" 
                             class="rounded-circle me-3 lazy-avatar" 
                             width="40" height="40" 
                             alt="${this.escapeHtml(author.username || 'User')}"
                             data-src="${this.getAvatarUrl(author)}"
                             style="background: var(--bs-secondary);">
                    ` : ''}
                    <div>
                        <strong>${this.escapeHtml(author.username || 'Unknown')}</strong>
                        ${this.options.showTrustLevels && author.trust_level !== undefined ? `
                            <span class="badge trust-level-${author.trust_level} ms-1">TL${author.trust_level}</span>
                        ` : ''}
                        <div class="small text-muted">${this.formatDate(post.created)}</div>
                    </div>
                </div>
                <div class="post-actions">
                    <a href="#post-${post.id}" class="btn btn-sm btn-outline-secondary">
                        #${post.position || ''}
                    </a>
                </div>
            </div>
            
            <div class="card-body">
                <div class="row">
                    <!-- User Sidebar -->
                    <div class="col-md-2 text-center border-end d-none d-md-block">
                        <div class="user-info">
                            ${author.is_staff ? '<span class="badge bg-danger mb-2">Staff</span>' : '<span class="badge bg-secondary mb-2">Member</span>'}
                            <div class="small text-muted">
                                <div>Posts: <strong>${author.posts_count || 0}</strong></div>
                                <div>Joined: ${this.formatDate(author.date_joined, 'short')}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Post Content -->
                    <div class="col-md-10">
                        <div class="post-content">
                            ${post.content || ''}
                        </div>
                        
                        ${post.updated && post.updated !== post.created ? `
                            <div class="mt-3 small text-muted">
                                <i class="bi bi-pencil me-1"></i>
                                Last edited: ${this.formatDate(post.updated)}
                            </div>
                        ` : ''}
                        
                        <div class="post-actions mt-3">
                            <button class="btn btn-sm btn-outline-primary me-2" data-action="quote" data-post-id="${post.id}">
                                <i class="bi bi-reply me-1"></i>Quote
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" data-action="like" data-post-id="${post.id}">
                                <i class="bi bi-heart me-1"></i>Like
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return element;
    }
    
    getTopicIcon(topic) {
        if (topic.is_sticky) {
            return '<i class="bi bi-pin-angle-fill text-danger me-1"></i>';
        } else if (topic.is_announce) {
            return '<i class="bi bi-megaphone-fill text-warning me-1"></i>';
        } else if (topic.is_locked) {
            return '<i class="bi bi-lock-fill text-secondary me-1"></i>';
        } else if (topic.has_poll) {
            return '<i class="bi bi-bar-chart-fill text-info me-1"></i>';
        }
        return '<i class="bi bi-chat-dots me-1"></i>';
    }
    
    getAvatarUrl(user) {
        if (!user) return '/static/images/default-avatar.png';
        
        // Use Gravatar or default avatar
        if (user.avatar) {
            return user.avatar;
        } else if (user.email) {
            const email = user.email.toLowerCase().trim();
            const hash = this.md5(email);
            return `https://www.gravatar.com/avatar/${hash}?d=identicon&s=80`;
        }
        
        return `/static/images/avatar-placeholder.png?text=${encodeURIComponent(user.username?.charAt(0) || '?')}`;
    }
    
    md5(str) {
        // Simple MD5 implementation for Gravatar
        // In production, you might want to use a proper crypto library
        return str; // Placeholder - implement actual MD5 or use a library
    }
    
    formatDate(dateString, format = 'relative') {
        if (!dateString) return 'Unknown';
        
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        if (format === 'short') {
            return date.toLocaleDateString('en-US', { 
                month: 'short', 
                year: 'numeric' 
            });
        }
        
        // Relative formatting
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (seconds < 60) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
        });
    }
    
    async setupElementObservers(element) {
        await super.setupElementObservers(element);
        
        // Setup forum-specific interactions
        this.setupPostActions(element);
        this.setupLazyAvatars(element);
    }
    
    setupPostActions(element) {
        // Quote button
        const quoteBtn = element.querySelector('[data-action="quote"]');
        if (quoteBtn) {
            quoteBtn.addEventListener('click', (e) => {
                e.preventDefault();
                const postId = e.target.closest('[data-action="quote"]').dataset.postId;
                this.handleQuotePost(postId, element);
            });
        }
        
        // Like button
        const likeBtn = element.querySelector('[data-action="like"]');
        if (likeBtn) {
            likeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                const postId = e.target.closest('[data-action="like"]').dataset.postId;
                this.handleLikePost(postId, e.target.closest('[data-action="like"]'));
            });
        }
    }
    
    setupLazyAvatars(element) {
        const avatars = element.querySelectorAll('.lazy-avatar');
        avatars.forEach(avatar => {
            this.setupLazyImage(avatar);
        });
    }
    
    async handleQuotePost(postId, postElement) {
        try {
            const response = await fetch(`/forum-features/api/posts/${postId}/quote/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.insertQuoteInEditor(data.quote_text);
            }
        } catch (error) {
            console.error('Failed to quote post:', error);
        }
    }
    
    async handleLikePost(postId, button) {
        try {
            const response = await fetch(`/forum-features/api/posts/${postId}/like/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateLikeButton(button, data.liked, data.likes_count);
            }
        } catch (error) {
            console.error('Failed to like post:', error);
        }
    }
    
    insertQuoteInEditor(quoteText) {
        // Try to find reply editor
        const editor = document.querySelector('#id_content, .reply-editor textarea');
        if (editor) {
            const currentText = editor.value;
            const newText = currentText + (currentText ? '\n\n' : '') + quoteText + '\n\n';
            editor.value = newText;
            editor.focus();
            editor.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    updateLikeButton(button, liked, count) {
        const icon = button.querySelector('i');
        if (liked) {
            icon.className = 'bi bi-heart-fill me-1';
            button.classList.add('text-danger');
        } else {
            icon.className = 'bi bi-heart me-1';
            button.classList.remove('text-danger');
        }
        
        // Update count if displayed
        const countSpan = button.querySelector('.like-count');
        if (countSpan) {
            countSpan.textContent = count > 0 ? count : '';
        }
    }
    
    getCSRFToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenElement) {
            return tokenElement.value;
        }
        
        const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
        return cookieMatch ? cookieMatch[1] : '';
    }
    
    // Forum-specific refresh for live updates
    async refreshContent() {
        if (this.options.contentType === 'posts') {
            // For posts, check for new posts since last load
            await this.checkForNewPosts();
        } else {
            // For topics, do a regular refresh
            this.refresh();
        }
    }
    
    async checkForNewPosts() {
        try {
            const lastPostId = this.getLastPostId();
            const response = await fetch(`${this.options.apiEndpoint}&since=${lastPostId}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.results && data.results.length > 0) {
                    await this.prependNewPosts(data.results);
                }
            }
        } catch (error) {
            console.error('Failed to check for new posts:', error);
        }
    }
    
    getLastPostId() {
        const posts = this.contentContainer.querySelectorAll('[data-item-type="post"]');
        if (posts.length > 0) {
            return posts[posts.length - 1].dataset.itemId;
        }
        return 0;
    }
    
    async prependNewPosts(posts) {
        const fragment = document.createDocumentFragment();
        
        for (const post of posts.reverse()) { // Newest first
            const element = await this.createPostElement(post);
            if (element) {
                element.style.opacity = '0';
                element.style.transform = 'translateY(-20px)';
                fragment.appendChild(element);
                this.setupElementObservers(element);
            }
        }
        
        this.contentContainer.insertBefore(fragment, this.contentContainer.firstChild);
        
        // Animate in
        const newPosts = Array.from(fragment.children);
        newPosts.forEach((post, index) => {
            setTimeout(() => {
                post.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                post.style.opacity = '1';
                post.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }
}

// Auto-initialize on forum pages
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a forum page
    const forumContainer = document.querySelector('.forum-content-container');
    const topicsList = document.querySelector('.topics-list');
    const postsList = document.querySelector('.posts-list');
    
    if (forumContainer || topicsList || postsList) {
        // Determine content type and container
        let contentType = 'topics';
        let container = '.forum-content-container';
        let forumId = null;
        let topicId = null;
        
        if (postsList) {
            contentType = 'posts';
            container = '.posts-list';
            // Extract topic ID from URL or data attribute
            const topicMatch = window.location.pathname.match(/\/topic\/[^\/]+\/(\d+)/);
            if (topicMatch) {
                topicId = topicMatch[1];
            }
        } else if (topicsList) {
            container = '.topics-list';
            // Extract forum ID from URL or data attribute
            const forumMatch = window.location.pathname.match(/\/forum\/[^\/]+\/(\d+)/);
            if (forumMatch) {
                forumId = forumMatch[1];
            }
        }
        
        // Initialize infinite scroll
        window.forumInfiniteScroll = new ForumInfiniteScroll({
            contentType: contentType,
            contentContainer: container,
            forumId: forumId,
            topicId: topicId,
            batchSize: 20
        });
        
        console.log('Forum infinite scroll initialized:', contentType);
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ForumInfiniteScroll;
}