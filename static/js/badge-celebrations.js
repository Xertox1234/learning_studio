/**
 * Badge celebration system with various animation effects.
 */

class BadgeCelebrations {
    constructor() {
        this.isConnected = false;
        this.websocket = null;
        this.notificationContainer = null;
        this.pendingNotifications = [];
        this.soundEnabled = localStorage.getItem('celebration_sounds') !== 'false';
        
        this.init();
    }
    
    init() {
        this.createNotificationContainer();
        this.connectWebSocket();
        this.loadPendingNotifications();
        this.setupEventListeners();
        
        // Create audio elements for sound effects
        this.createAudioElements();
    }
    
    createNotificationContainer() {
        this.notificationContainer = document.createElement('div');
        this.notificationContainer.id = 'badge-notifications';
        this.notificationContainer.className = 'position-fixed top-0 end-0 p-3';
        this.notificationContainer.style.zIndex = '9999';
        document.body.appendChild(this.notificationContainer);
    }
    
    createAudioElements() {
        this.sounds = {
            badge_earned: this.createAudio('/static/sounds/badge-earned.mp3'),
            achievement: this.createAudio('/static/sounds/achievement.mp3'),
            milestone: this.createAudio('/static/sounds/milestone.mp3'),
            level_up: this.createAudio('/static/sounds/level-up.mp3')
        };
    }
    
    createAudio(src) {
        const audio = new Audio();
        audio.src = src;
        audio.preload = 'auto';
        audio.volume = 0.6;
        return audio;
    }
    
    connectWebSocket() {
        if (typeof userId === 'undefined') {
            console.log('User not authenticated, skipping WebSocket connection');
            return;
        }
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/${userId}/`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('Badge notification WebSocket connected');
                this.isConnected = true;
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleNotification(data);
            };
            
            this.websocket.onclose = () => {
                console.log('Badge notification WebSocket disconnected');
                this.isConnected = false;
                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.connectWebSocket(), 5000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
        }
    }
    
    async loadPendingNotifications() {
        try {
            const response = await fetch('/forum/api/achievements/');
            if (response.ok) {
                const data = await response.json();
                if (data.recent_badges && data.recent_badges.length > 0) {
                    data.recent_badges.forEach(badge => {
                        this.showBadgeNotification(badge, false); // Don't play sound for pending
                    });
                }
            }
        } catch (error) {
            console.error('Failed to load pending notifications:', error);
        }
    }
    
    handleNotification(data) {
        switch (data.type) {
            case 'badge_earned':
                this.showBadgeNotification(data.badge, true);
                this.triggerCelebration(data.celebration_type || 'sparkle');
                break;
            case 'achievement_unlocked':
                this.showAchievementNotification(data.achievement);
                this.triggerCelebration('fireworks');
                break;
            case 'milestone_reached':
                this.showMilestoneNotification(data.milestone);
                this.triggerCelebration(data.celebration_type || 'confetti');
                break;
            case 'leaderboard_update':
                this.showLeaderboardNotification(data.leaderboard);
                break;
            case 'badge_progress':
                this.showProgressNotification(data.badge, data.message);
                break;
        }
    }
    
    showBadgeNotification(badge, playSound = true) {
        const notification = this.createNotificationElement({
            title: `🎉 Badge Earned!`,
            subtitle: badge.name,
            description: badge.description,
            icon: badge.icon,
            color: badge.color,
            rarity: badge.rarity_display || badge.rarity,
            points: badge.points_awarded,
            type: 'badge'
        });
        
        this.displayNotification(notification);
        
        if (playSound && this.soundEnabled) {
            this.playSound('badge_earned');
        }
        
        // Update user stats if displayed
        this.updateStatsDisplay();
    }
    
    showAchievementNotification(achievement) {
        const notification = this.createNotificationElement({
            title: `🏆 Achievement Unlocked!`,
            subtitle: achievement.name,
            description: achievement.description,
            icon: achievement.icon,
            color: achievement.color,
            points: achievement.points_reward,
            type: 'achievement'
        });
        
        this.displayNotification(notification);
        
        if (this.soundEnabled) {
            this.playSound('achievement');
        }
        
        this.updateStatsDisplay();
    }
    
    showMilestoneNotification(milestone) {
        const notification = this.createNotificationElement({
            title: `🎯 ${milestone.title}`,
            subtitle: `${milestone.value} ${milestone.type}!`,
            description: milestone.message,
            icon: milestone.icon,
            color: milestone.color,
            type: 'milestone'
        });
        
        this.displayNotification(notification);
        
        if (this.soundEnabled) {
            this.playSound('milestone');
        }
    }
    
    showLeaderboardNotification(leaderboard) {
        const notification = this.createNotificationElement({
            title: `📈 Leaderboard Update!`,
            subtitle: `Rank #${leaderboard.new_rank}`,
            description: leaderboard.message,
            icon: leaderboard.icon,
            color: leaderboard.color,
            type: 'leaderboard'
        });
        
        this.displayNotification(notification);
    }
    
    showProgressNotification(badge, message) {
        const notification = document.createElement('div');
        notification.className = 'toast fade show border-0 shadow-sm';
        notification.style.backgroundColor = '#f8f9fa';
        
        notification.innerHTML = `
            <div class="toast-header bg-info text-white">
                <i class="${badge.icon} me-2"></i>
                <strong class="me-auto">Badge Progress</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                <div class="d-flex align-items-center mb-2">
                    <strong>${badge.name}</strong>
                    <span class="ms-auto text-muted small">${badge.percentage}%</span>
                </div>
                <div class="progress mb-2" style="height: 6px;">
                    <div class="progress-bar bg-info" style="width: ${badge.percentage}%"></div>
                </div>
                <small class="text-muted">${message}</small>
            </div>
        `;
        
        this.displayNotification(notification, 3000);
    }
    
    createNotificationElement({title, subtitle, description, icon, color, rarity, points, type}) {
        const notification = document.createElement('div');
        notification.className = 'toast fade show border-0 shadow-lg';
        
        // Set background based on type and rarity
        let bgClass = 'bg-success';
        if (type === 'achievement') bgClass = 'bg-warning';
        else if (type === 'milestone') bgClass = 'bg-info';
        else if (rarity) {
            const rarityColors = {
                'Common': 'bg-secondary',
                'Uncommon': 'bg-success',
                'Rare': 'bg-primary',
                'Epic': 'bg-warning',
                'Legendary': 'bg-danger'
            };
            bgClass = rarityColors[rarity] || 'bg-success';
        }
        
        notification.innerHTML = `
            <div class="toast-header ${bgClass} text-white">
                <i class="${icon} me-2" style="font-size: 1.2rem;"></i>
                <strong class="me-auto">${title}</strong>
                ${rarity ? `<span class="badge bg-dark ms-2">${rarity}</span>` : ''}
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                <div class="d-flex align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1 fw-bold">${subtitle}</h6>
                        <p class="mb-1 small text-muted">${description}</p>
                        ${points ? `<small class="text-success fw-bold">+${points} points</small>` : ''}
                    </div>
                    <div class="celebration-icon ms-3" style="color: ${color}; font-size: 2rem;">
                        <i class="${icon}"></i>
                    </div>
                </div>
            </div>
        `;
        
        return notification;
    }
    
    displayNotification(notification, autoHideDelay = 8000) {
        this.notificationContainer.appendChild(notification);
        
        // Initialize Bootstrap toast
        const bsToast = new bootstrap.Toast(notification, {
            delay: autoHideDelay
        });
        
        // Add entrance animation
        notification.style.transform = 'translateX(100%)';
        notification.style.transition = 'transform 0.3s ease-out';
        
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        bsToast.show();
        
        // Clean up after hiding
        notification.addEventListener('hidden.bs.toast', () => {
            notification.remove();
        });
    }
    
    triggerCelebration(type) {
        switch (type) {
            case 'sparkle':
                this.createSparkleEffect();
                break;
            case 'bounce':
                this.createBounceEffect();
                break;
            case 'confetti':
                this.createConfettiEffect();
                break;
            case 'fireworks':
                this.createFireworksEffect();
                break;
            case 'epic_celebration':
                this.createEpicCelebration();
                break;
        }
    }
    
    createSparkleEffect() {
        for (let i = 0; i < 15; i++) {
            const sparkle = document.createElement('div');
            sparkle.className = 'celebration-sparkle';
            sparkle.innerHTML = '✨';
            sparkle.style.cssText = `
                position: fixed;
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
                font-size: ${Math.random() * 20 + 10}px;
                z-index: 10000;
                pointer-events: none;
                animation: sparkle 2s ease-out forwards;
            `;
            
            document.body.appendChild(sparkle);
            
            setTimeout(() => sparkle.remove(), 2000);
        }
    }
    
    createBounceEffect() {
        const elements = document.querySelectorAll('.badge, .btn-primary, h1, h2');
        elements.forEach(el => {
            el.style.animation = 'bounce 0.6s ease-in-out';
            setTimeout(() => {
                el.style.animation = '';
            }, 600);
        });
    }
    
    createConfettiEffect() {
        const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#f0932b', '#eb4d4b', '#6c5ce7'];
        
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.style.cssText = `
                position: fixed;
                top: -10px;
                left: ${Math.random() * 100}%;
                width: 10px;
                height: 10px;
                background: ${colors[Math.floor(Math.random() * colors.length)]};
                z-index: 10000;
                pointer-events: none;
                animation: confetti ${Math.random() * 3 + 2}s linear forwards;
            `;
            
            document.body.appendChild(confetti);
            
            setTimeout(() => confetti.remove(), 5000);
        }
    }
    
    createFireworksEffect() {
        for (let i = 0; i < 5; i++) {
            setTimeout(() => {
                const firework = document.createElement('div');
                firework.innerHTML = '🎆';
                firework.style.cssText = `
                    position: fixed;
                    top: ${Math.random() * 50 + 25}%;
                    left: ${Math.random() * 80 + 10}%;
                    font-size: 50px;
                    z-index: 10000;
                    pointer-events: none;
                    animation: firework 1.5s ease-out forwards;
                `;
                
                document.body.appendChild(firework);
                setTimeout(() => firework.remove(), 1500);
            }, i * 300);
        }
    }
    
    createEpicCelebration() {
        // Combine multiple effects for legendary badges
        this.createFireworksEffect();
        setTimeout(() => this.createConfettiEffect(), 500);
        setTimeout(() => this.createSparkleEffect(), 1000);
        
        // Screen flash effect
        const flash = document.createElement('div');
        flash.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 215, 0, 0.3);
            z-index: 9998;
            pointer-events: none;
            animation: flash 0.5s ease-out;
        `;
        
        document.body.appendChild(flash);
        setTimeout(() => flash.remove(), 500);
    }
    
    updateStatsDisplay() {
        // Update any visible stats displays
        const statsElements = document.querySelectorAll('[data-user-stat]');
        if (statsElements.length > 0) {
            fetch('/forum/api/achievements/')
                .then(response => response.json())
                .then(data => {
                    statsElements.forEach(el => {
                        const stat = el.getAttribute('data-user-stat');
                        if (data.stats && data.stats[stat] !== undefined) {
                            el.textContent = data.stats[stat];
                        }
                    });
                })
                .catch(error => console.error('Failed to update stats:', error));
        }
    }
    
    playSound(soundType) {
        if (this.sounds[soundType]) {
            this.sounds[soundType].play().catch(() => {
                // Ignore audio play failures (common on mobile/autoplay restrictions)
            });
        }
    }
    
    setupEventListeners() {
        // Sound toggle
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-toggle-sounds]')) {
                this.soundEnabled = !this.soundEnabled;
                localStorage.setItem('celebration_sounds', this.soundEnabled);
                e.target.innerHTML = this.soundEnabled ? 
                    '<i class="bi bi-volume-up"></i>' : 
                    '<i class="bi bi-volume-mute"></i>';
            }
        });
        
        // Manual celebration trigger (for testing)
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-trigger-celebration]')) {
                const type = e.target.getAttribute('data-trigger-celebration');
                this.triggerCelebration(type);
            }
        });
    }
}

// CSS animations
const celebrationStyles = `
<style>
@keyframes sparkle {
    0% { opacity: 0; transform: scale(0) rotate(0deg); }
    50% { opacity: 1; transform: scale(1) rotate(180deg); }
    100% { opacity: 0; transform: scale(0) rotate(360deg); }
}

@keyframes bounce {
    0%, 20%, 53%, 80%, 100% { transform: translate3d(0,0,0); }
    40%, 43% { transform: translate3d(0,-15px,0); }
    70% { transform: translate3d(0,-7px,0); }
    90% { transform: translate3d(0,-3px,0); }
}

@keyframes confetti {
    0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
    100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
}

@keyframes firework {
    0% { transform: scale(0); opacity: 1; }
    50% { transform: scale(1.2); opacity: 0.8; }
    100% { transform: scale(0); opacity: 0; }
}

@keyframes flash {
    0% { opacity: 0; }
    50% { opacity: 1; }
    100% { opacity: 0; }
}

.celebration-sparkle {
    user-select: none;
}
</style>
`;

// Add styles to document
document.head.insertAdjacentHTML('beforeend', celebrationStyles);

// Initialize celebrations when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.badgeCelebrations = new BadgeCelebrations();
});