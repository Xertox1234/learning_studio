/**
 * Real-time WebSocket client for forum functionality
 * Handles connections to different WebSocket endpoints and manages real-time updates
 */

class ForumWebSocketClient {
    constructor(options = {}) {
        this.options = {
            autoReconnect: true,
            reconnectInterval: 3000,
            maxReconnectAttempts: 5,
            heartbeatInterval: 30000,
            debug: false,
            ...options
        };

        this.connections = new Map();
        this.reconnectAttempts = new Map();
        this.heartbeatIntervals = new Map();
        this.eventHandlers = new Map();
        this.isOnline = navigator.onLine;

        this.bindEvents();
    }

    bindEvents() {
        // Handle online/offline status
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.reconnectAll();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.closeAll();
        });

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseHeartbeats();
            } else {
                this.resumeHeartbeats();
            }
        });

        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            this.closeAll();
        });
    }

    /**
     * Connect to a WebSocket endpoint
     */
    connect(endpoint, handlers = {}) {
        if (!this.isOnline) {
            this.log('Cannot connect - offline');
            return null;
        }

        if (this.connections.has(endpoint)) {
            this.log(`Already connected to ${endpoint}`);
            return this.connections.get(endpoint);
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}${endpoint}`;

        try {
            const ws = new WebSocket(wsUrl);
            
            ws.onopen = (event) => this.handleOpen(endpoint, event);
            ws.onmessage = (event) => this.handleMessage(endpoint, event);
            ws.onclose = (event) => this.handleClose(endpoint, event);
            ws.onerror = (event) => this.handleError(endpoint, event);

            this.connections.set(endpoint, ws);
            this.eventHandlers.set(endpoint, handlers);
            this.reconnectAttempts.set(endpoint, 0);

            this.log(`Connecting to ${endpoint}...`);
            return ws;

        } catch (error) {
            this.log(`Failed to create WebSocket connection to ${endpoint}:`, error);
            return null;
        }
    }

    /**
     * Disconnect from a specific endpoint
     */
    disconnect(endpoint) {
        const ws = this.connections.get(endpoint);
        if (ws) {
            ws.close(1000, 'Manual disconnect');
            this.connections.delete(endpoint);
            this.eventHandlers.delete(endpoint);
            this.stopHeartbeat(endpoint);
            this.log(`Disconnected from ${endpoint}`);
        }
    }

    /**
     * Close all connections
     */
    closeAll() {
        for (const endpoint of this.connections.keys()) {
            this.disconnect(endpoint);
        }
    }

    /**
     * Send message to a specific endpoint
     */
    send(endpoint, data) {
        const ws = this.connections.get(endpoint);
        if (ws && ws.readyState === WebSocket.OPEN) {
            const message = typeof data === 'string' ? data : JSON.stringify(data);
            ws.send(message);
            this.log(`Sent to ${endpoint}:`, data);
            return true;
        }
        this.log(`Cannot send to ${endpoint} - connection not open`);
        return false;
    }

    /**
     * Handle WebSocket open event
     */
    handleOpen(endpoint, event) {
        this.log(`Connected to ${endpoint}`);
        this.reconnectAttempts.set(endpoint, 0);
        this.startHeartbeat(endpoint);

        const handlers = this.eventHandlers.get(endpoint);
        if (handlers.onOpen) {
            handlers.onOpen(event);
        }

        this.dispatchEvent('connected', { endpoint, event });
    }

    /**
     * Handle WebSocket message event
     */
    handleMessage(endpoint, event) {
        try {
            const data = JSON.parse(event.data);
            this.log(`Received from ${endpoint}:`, data);

            // Handle built-in message types
            if (data.type === 'heartbeat_ack') {
                this.log(`Heartbeat acknowledged from ${endpoint}`);
                return;
            }

            const handlers = this.eventHandlers.get(endpoint);
            
            // Call specific handler for message type
            if (handlers[data.type]) {
                handlers[data.type](data);
            }

            // Call general message handler
            if (handlers.onMessage) {
                handlers.onMessage(data, event);
            }

            this.dispatchEvent('message', { endpoint, data, event });

        } catch (error) {
            this.log(`Error parsing message from ${endpoint}:`, error);
        }
    }

    /**
     * Handle WebSocket close event
     */
    handleClose(endpoint, event) {
        this.log(`Connection to ${endpoint} closed:`, event.code, event.reason);
        
        this.connections.delete(endpoint);
        this.stopHeartbeat(endpoint);

        const handlers = this.eventHandlers.get(endpoint);
        if (handlers.onClose) {
            handlers.onClose(event);
        }

        this.dispatchEvent('disconnected', { endpoint, event });

        // Attempt reconnection if enabled and not a manual close
        if (this.options.autoReconnect && event.code !== 1000 && this.isOnline) {
            this.attemptReconnect(endpoint);
        }
    }

    /**
     * Handle WebSocket error event
     */
    handleError(endpoint, event) {
        this.log(`WebSocket error on ${endpoint}:`, event);

        const handlers = this.eventHandlers.get(endpoint);
        if (handlers.onError) {
            handlers.onError(event);
        }

        this.dispatchEvent('error', { endpoint, event });
    }

    /**
     * Attempt to reconnect to an endpoint
     */
    attemptReconnect(endpoint) {
        const attempts = this.reconnectAttempts.get(endpoint) || 0;
        
        if (attempts >= this.options.maxReconnectAttempts) {
            this.log(`Max reconnection attempts reached for ${endpoint}`);
            return;
        }

        this.reconnectAttempts.set(endpoint, attempts + 1);
        
        setTimeout(() => {
            if (!this.connections.has(endpoint) && this.isOnline) {
                this.log(`Attempting to reconnect to ${endpoint} (attempt ${attempts + 1})`);
                const handlers = this.eventHandlers.get(endpoint);
                this.connect(endpoint, handlers);
            }
        }, this.options.reconnectInterval * Math.pow(2, attempts)); // Exponential backoff
    }

    /**
     * Reconnect all endpoints
     */
    reconnectAll() {
        for (const [endpoint, handlers] of this.eventHandlers.entries()) {
            if (!this.connections.has(endpoint)) {
                this.connect(endpoint, handlers);
            }
        }
    }

    /**
     * Start heartbeat for an endpoint
     */
    startHeartbeat(endpoint) {
        this.stopHeartbeat(endpoint); // Clear any existing interval
        
        const interval = setInterval(() => {
            this.send(endpoint, { type: 'heartbeat', timestamp: new Date().toISOString() });
        }, this.options.heartbeatInterval);
        
        this.heartbeatIntervals.set(endpoint, interval);
    }

    /**
     * Stop heartbeat for an endpoint
     */
    stopHeartbeat(endpoint) {
        const interval = this.heartbeatIntervals.get(endpoint);
        if (interval) {
            clearInterval(interval);
            this.heartbeatIntervals.delete(endpoint);
        }
    }

    /**
     * Pause all heartbeats
     */
    pauseHeartbeats() {
        for (const endpoint of this.heartbeatIntervals.keys()) {
            this.stopHeartbeat(endpoint);
        }
    }

    /**
     * Resume all heartbeats
     */
    resumeHeartbeats() {
        for (const endpoint of this.connections.keys()) {
            this.startHeartbeat(endpoint);
        }
    }

    /**
     * Send typing notification
     */
    sendTyping(endpoint, isTyping = true) {
        this.send(endpoint, {
            type: isTyping ? 'typing_start' : 'typing_stop',
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Send user activity update
     */
    sendActivity(endpoint, action, page = null) {
        this.send(endpoint, {
            type: 'user_activity',
            action: action,
            page: page || window.location.pathname,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Get connection status
     */
    getStatus(endpoint) {
        const ws = this.connections.get(endpoint);
        if (!ws) return 'disconnected';
        
        switch (ws.readyState) {
            case WebSocket.CONNECTING: return 'connecting';
            case WebSocket.OPEN: return 'connected';
            case WebSocket.CLOSING: return 'closing';
            case WebSocket.CLOSED: return 'closed';
            default: return 'unknown';
        }
    }

    /**
     * Get all connection statuses
     */
    getAllStatuses() {
        const statuses = {};
        for (const endpoint of this.eventHandlers.keys()) {
            statuses[endpoint] = this.getStatus(endpoint);
        }
        return statuses;
    }

    /**
     * Dispatch custom events
     */
    dispatchEvent(type, detail) {
        const event = new CustomEvent(`forum-ws-${type}`, { detail });
        document.dispatchEvent(event);
    }

    /**
     * Log messages if debug is enabled
     */
    log(...args) {
        if (this.options.debug) {
            console.log('[ForumWebSocket]', ...args);
        }
    }
}


/**
 * Topic-specific WebSocket manager
 */
class TopicWebSocket {
    constructor(topicId, options = {}) {
        this.topicId = topicId;
        this.client = new ForumWebSocketClient(options);
        this.endpoint = `/ws/forum/topic/${topicId}/`;
        
        this.handlers = {
            onOpen: () => this.onConnected(),
            onClose: () => this.onDisconnected(),
            new_post: (data) => this.handleNewPost(data),
            post_updated: (data) => this.handlePostUpdated(data),
            post_deleted: (data) => this.handlePostDeleted(data),
            like_updated: (data) => this.handleLikeUpdated(data),
            typing: (data) => this.handleTyping(data),
            user_joined: (data) => this.handleUserJoined(data),
            user_left: (data) => this.handleUserLeft(data),
            initial_data: (data) => this.handleInitialData(data)
        };

        this.typingUsers = new Set();
        this.onlineUsers = new Map();
    }

    connect() {
        return this.client.connect(this.endpoint, this.handlers);
    }

    disconnect() {
        this.client.disconnect(this.endpoint);
    }

    sendTyping(isTyping = true) {
        this.client.sendTyping(this.endpoint, isTyping);
    }

    onConnected() {
        this.updateConnectionStatus(true);
        console.log(`Connected to topic ${this.topicId}`);
    }

    onDisconnected() {
        this.updateConnectionStatus(false);
        console.log(`Disconnected from topic ${this.topicId}`);
    }

    handleNewPost(data) {
        this.addPostToPage(data.post);
        this.showNotification(`New post by ${data.post.poster.username}`);
    }

    handlePostUpdated(data) {
        this.updatePostOnPage(data.post);
    }

    handlePostDeleted(data) {
        this.removePostFromPage(data.post_id);
    }

    handleLikeUpdated(data) {
        this.updateLikeCount(data.post_id, data.likes_count, data.user_liked);
    }

    handleTyping(data) {
        if (data.is_typing) {
            this.typingUsers.add(data.username);
        } else {
            this.typingUsers.delete(data.username);
        }
        this.updateTypingIndicator();
    }

    handleUserJoined(data) {
        this.onlineUsers.set(data.user.id, data.user);
        this.updateOnlineUsers();
    }

    handleUserLeft(data) {
        this.onlineUsers.delete(data.user_id);
        this.updateOnlineUsers();
    }

    handleInitialData(data) {
        if (data.online_users) {
            data.online_users.forEach(user => {
                this.onlineUsers.set(user.id, user);
            });
            this.updateOnlineUsers();
        }
    }

    // UI update methods
    updateConnectionStatus(isConnected) {
        const indicator = document.querySelector('.connection-status');
        if (indicator) {
            indicator.className = `connection-status ${isConnected ? 'connected' : 'disconnected'}`;
            indicator.textContent = isConnected ? 'Live' : 'Offline';
        }
    }

    addPostToPage(post) {
        const postsContainer = document.querySelector('.posts-container, .forum-posts');
        if (postsContainer) {
            const postElement = this.createPostElement(post);
            postsContainer.appendChild(postElement);
            postElement.scrollIntoView({ behavior: 'smooth' });
        }
    }

    updatePostOnPage(post) {
        const postElement = document.querySelector(`[data-post-id="${post.id}"]`);
        if (postElement) {
            const contentElement = postElement.querySelector('.post-content');
            if (contentElement) {
                contentElement.innerHTML = post.content;
                postElement.classList.add('updated');
            }
        }
    }

    removePostFromPage(postId) {
        const postElement = document.querySelector(`[data-post-id="${postId}"]`);
        if (postElement) {
            postElement.style.opacity = '0.5';
            postElement.innerHTML = '<div class="text-muted">This post has been deleted.</div>';
        }
    }

    updateLikeCount(postId, likesCount, userLiked) {
        const likeButton = document.querySelector(`[data-post-id="${postId}"] .like-button`);
        const likeCount = document.querySelector(`[data-post-id="${postId}"] .like-count`);
        
        if (likeCount) {
            likeCount.textContent = likesCount;
        }
        
        if (likeButton) {
            likeButton.classList.toggle('liked', userLiked);
        }
    }

    updateTypingIndicator() {
        const indicator = document.querySelector('.typing-indicator');
        if (!indicator) return;

        if (this.typingUsers.size === 0) {
            indicator.style.display = 'none';
        } else {
            const users = Array.from(this.typingUsers);
            let text = '';
            
            if (users.length === 1) {
                text = `${users[0]} is typing...`;
            } else if (users.length === 2) {
                text = `${users[0]} and ${users[1]} are typing...`;
            } else {
                text = `${users[0]} and ${users.length - 1} others are typing...`;
            }
            
            indicator.textContent = text;
            indicator.style.display = 'block';
        }
    }

    updateOnlineUsers() {
        const container = document.querySelector('.online-users');
        if (!container) return;

        const usersList = Array.from(this.onlineUsers.values());
        container.innerHTML = `
            <h6>Online Users (${usersList.length})</h6>
            <ul class="list-unstyled">
                ${usersList.map(user => `
                    <li><i class="fas fa-circle text-success"></i> ${user.username}</li>
                `).join('')}
            </ul>
        `;
    }

    createPostElement(post) {
        const div = document.createElement('div');
        div.className = 'post-item';
        div.setAttribute('data-post-id', post.id);
        div.innerHTML = `
            <div class="post-header">
                <strong>${post.poster.username}</strong>
                <small class="text-muted">${new Date(post.created).toLocaleString()}</small>
            </div>
            <div class="post-content">${post.content}</div>
            <div class="post-actions">
                <button class="btn btn-sm btn-outline-primary like-button">
                    <i class="fas fa-heart"></i> <span class="like-count">0</span>
                </button>
            </div>
        `;
        return div;
    }

    showNotification(message) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Forum Update', { body: message });
        }
    }
}

// Export for use in other scripts
window.ForumWebSocketClient = ForumWebSocketClient;
window.TopicWebSocket = TopicWebSocket;