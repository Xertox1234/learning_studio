/**
 * PWA Initialization and Install Prompt
 * Handles service worker registration and install prompts
 */

class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.installButton = null;
        
        this.init();
    }
    
    async init() {
        await this.checkInstallation();
        this.registerServiceWorker();
        this.setupInstallPrompt();
        this.addInstallButton();
        this.handleAppInstalled();
    }
    
    async checkInstallation() {
        // Check if app is installed
        if (window.navigator.standalone === true) {
            this.isInstalled = true;
            document.body.classList.add('pwa-installed');
        }
        
        // Check for display mode
        if (window.matchMedia('(display-mode: standalone)').matches) {
            this.isInstalled = true;
            document.body.classList.add('pwa-installed');
        }
    }
    
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/static/sw.js');
                console.log('Service Worker registered:', registration);
                
                // Handle service worker updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateNotification();
                        }
                    });
                });
                
                // Listen for messages from service worker
                navigator.serviceWorker.addEventListener('message', event => {
                    if (event.data.type === 'version') {
                        console.log('Service Worker version:', event.data.version);
                    }
                });
                
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }
    
    setupInstallPrompt() {
        window.addEventListener('beforeinstallprompt', event => {
            console.log('PWA install prompt available');
            
            // Prevent default install prompt
            event.preventDefault();
            
            // Store the event for later use
            this.deferredPrompt = event;
            
            // Show custom install button
            this.showInstallButton();
        });
    }
    
    addInstallButton() {
        // Create install button if it doesn't exist
        if (!document.querySelector('.pwa-install-btn')) {
            const installBtn = document.createElement('button');
            installBtn.className = 'btn btn-primary pwa-install-btn d-none';
            installBtn.innerHTML = '<i class="bi bi-download me-2"></i>Install App';
            installBtn.addEventListener('click', () => this.promptInstall());
            
            // Add to navbar or floating position
            const navbar = document.querySelector('.navbar-nav');
            if (navbar) {
                const listItem = document.createElement('li');
                listItem.className = 'nav-item';
                listItem.appendChild(installBtn);
                navbar.appendChild(listItem);
            } else {
                // Floating install button
                installBtn.style.position = 'fixed';
                installBtn.style.bottom = '20px';
                installBtn.style.right = '20px';
                installBtn.style.zIndex = '1050';
                installBtn.style.borderRadius = '50px';
                document.body.appendChild(installBtn);
            }
            
            this.installButton = installBtn;
        }
    }
    
    showInstallButton() {
        if (this.installButton && !this.isInstalled) {
            this.installButton.classList.remove('d-none');
            
            // Show install banner after delay
            setTimeout(() => {
                this.showInstallBanner();
            }, 5000);
        }
    }
    
    async promptInstall() {
        if (!this.deferredPrompt) {
            return;
        }
        
        // Show the install prompt
        this.deferredPrompt.prompt();
        
        // Wait for user response
        const { outcome } = await this.deferredPrompt.userChoice;
        console.log('Install prompt outcome:', outcome);
        
        if (outcome === 'accepted') {
            this.hideInstallButton();
            this.trackInstallEvent('accepted');
        } else {
            this.trackInstallEvent('dismissed');
        }
        
        // Clear the deferred prompt
        this.deferredPrompt = null;
    }
    
    showInstallBanner() {
        if (this.isInstalled || document.querySelector('.install-banner')) {
            return;
        }
        
        const banner = document.createElement('div');
        banner.className = 'install-banner alert alert-info alert-dismissible fade show position-fixed';
        banner.style.bottom = '20px';
        banner.style.left = '20px';
        banner.style.right = '20px';
        banner.style.zIndex = '1055';
        banner.style.maxWidth = '400px';
        banner.style.margin = '0 auto';
        
        banner.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="me-3">
                    <i class="bi bi-phone text-primary" style="font-size: 1.5rem;"></i>
                </div>
                <div class="flex-grow-1">
                    <strong>Install Python Learning Studio</strong>
                    <div class="small">Get the full app experience on your device</div>
                </div>
                <div class="ms-2">
                    <button class="btn btn-primary btn-sm me-2" onclick="window.pwaManager.promptInstall()">
                        Install
                    </button>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" onclick="window.pwaManager.dismissInstallBanner()"></button>
                </div>
            </div>
        `;
        
        document.body.appendChild(banner);
        
        // Auto-dismiss after 10 seconds
        setTimeout(() => {
            if (banner.parentNode) {
                banner.remove();
            }
        }, 10000);
    }
    
    dismissInstallBanner() {
        const banner = document.querySelector('.install-banner');
        if (banner) {
            banner.remove();
        }
        
        // Remember dismissal for this session
        sessionStorage.setItem('installBannerDismissed', 'true');
    }
    
    hideInstallButton() {
        if (this.installButton) {
            this.installButton.classList.add('d-none');
        }
    }
    
    handleAppInstalled() {
        window.addEventListener('appinstalled', () => {
            console.log('PWA was installed');
            this.isInstalled = true;
            this.hideInstallButton();
            this.showInstalledNotification();
            this.trackInstallEvent('completed');
        });
    }
    
    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show position-fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '1055';
        notification.style.maxWidth = '300px';
        
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi bi-arrow-clockwise me-2"></i>
                <div class="flex-grow-1">
                    <strong>Update Available</strong>
                    <div class="small">Refresh to get the latest version</div>
                </div>
                <button class="btn btn-sm btn-outline-primary ms-2" onclick="window.location.reload()">
                    Refresh
                </button>
                <button type="button" class="btn-close ms-2" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(notification);
    }
    
    showInstalledNotification() {
        const notification = document.createElement('div');
        notification.className = 'alert alert-success alert-dismissible fade show position-fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '1055';
        notification.style.maxWidth = '300px';
        
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi bi-check-circle-fill me-2"></i>
                <div class="flex-grow-1">
                    <strong>App Installed!</strong>
                    <div class="small">Python Learning Studio is now on your device</div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    trackInstallEvent(action) {
        // Track install events for analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'pwa_install', {
                event_category: 'PWA',
                event_label: action
            });
        }
        
        console.log('PWA Install Event:', action);
    }
    
    // Public API methods
    isAppInstalled() {
        return this.isInstalled;
    }
    
    canPromptInstall() {
        return this.deferredPrompt !== null;
    }
    
    async requestPersistentStorage() {
        if ('storage' in navigator && 'persist' in navigator.storage) {
            const granted = await navigator.storage.persist();
            console.log('Persistent storage granted:', granted);
            return granted;
        }
        return false;
    }
    
    async getStorageEstimate() {
        if ('storage' in navigator && 'estimate' in navigator.storage) {
            const estimate = await navigator.storage.estimate();
            console.log('Storage estimate:', estimate);
            return estimate;
        }
        return null;
    }
}

// Initialize PWA manager
document.addEventListener('DOMContentLoaded', () => {
    window.pwaManager = new PWAManager();
});

// Handle online/offline status
window.addEventListener('online', () => {
    document.body.classList.remove('offline');
    console.log('App is online');
});

window.addEventListener('offline', () => {
    document.body.classList.add('offline');
    console.log('App is offline');
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PWAManager;
}