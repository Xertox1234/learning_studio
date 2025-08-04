/**
 * Service Worker for Python Learning Studio PWA
 * Provides offline functionality and caching strategies
 */

const CACHE_NAME = 'python-learning-studio-v1';
const OFFLINE_PAGE = '/offline/';

// Cache strategies
const CACHE_FIRST = [
  // Static assets
  '/static/css/',
  '/static/js/',
  '/static/images/',
  '/static/fonts/',
  // Icons and manifest
  '/static/manifest.json'
];

const NETWORK_FIRST = [
  // API endpoints
  '/api/',
  '/forum-features/api/',
  // User-specific content
  '/dashboard/',
  '/trust-level/',
  '/profile/'
];

const STALE_WHILE_REVALIDATE = [
  // Forum content
  '/forum/',
  '/courses/',
  '/lessons/',
  // Static pages
  '/',
  '/about/',
  '/help/'
];

// Install event - cache essential resources
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Caching essential resources');
        return cache.addAll([
          '/',
          '/static/css/main.css',
          '/static/js/main.js',
          '/static/manifest.json',
          OFFLINE_PAGE
        ]);
      })
      .then(() => {
        console.log('Service Worker installed successfully');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Service Worker installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== CACHE_NAME) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome-extension and other non-http requests
  if (!url.protocol.startsWith('http')) {
    return;
  }
  
  event.respondWith(handleFetch(request));
});

async function handleFetch(request) {
  const url = new URL(request.url);
  const pathname = url.pathname;
  
  try {
    // Cache First Strategy - for static assets
    if (shouldUseCacheFirst(pathname)) {
      return await cacheFirst(request);
    }
    
    // Network First Strategy - for API and dynamic content
    if (shouldUseNetworkFirst(pathname)) {
      return await networkFirst(request);
    }
    
    // Stale While Revalidate - for regular pages
    return await staleWhileRevalidate(request);
    
  } catch (error) {
    console.error('Fetch failed:', error);
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const cache = await caches.open(CACHE_NAME);
      return await cache.match(OFFLINE_PAGE) || new Response('Offline', { status: 503 });
    }
    
    // Return cached version if available, otherwise error
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);
    return cached || new Response('Network Error', { status: 503 });
  }
}

function shouldUseCacheFirst(pathname) {
  return CACHE_FIRST.some(pattern => pathname.startsWith(pattern));
}

function shouldUseNetworkFirst(pathname) {
  return NETWORK_FIRST.some(pattern => pathname.startsWith(pattern));
}

async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  
  if (cached) {
    return cached;
  }
  
  const response = await fetch(request);
  if (response.status === 200) {
    cache.put(request, response.clone());
  }
  
  return response;
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    
    if (response.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);
    
    if (cached) {
      return cached;
    }
    
    throw error;
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  
  // Always try to fetch fresh content in background
  const fetchPromise = fetch(request).then(response => {
    if (response.status === 200) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(() => {
    // Network failed, but that's ok for this strategy
  });
  
  // Return cached version immediately if available, otherwise wait for network
  return cached || fetchPromise;
}

// Background sync for offline actions
self.addEventListener('sync', event => {
  if (event.tag === 'reading-time-sync') {
    event.waitUntil(syncReadingTime());
  }
  
  if (event.tag === 'forum-post-sync') {
    event.waitUntil(syncForumPosts());
  }
});

async function syncReadingTime() {
  console.log('Syncing reading time data...');
  
  try {
    // Get pending reading time data from IndexedDB
    const pendingData = await getPendingReadingData();
    
    for (const data of pendingData) {
      const response = await fetch('/forum-features/api/track-reading-time/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });
      
      if (response.ok) {
        await removePendingReadingData(data.id);
      }
    }
    
    console.log('Reading time sync completed');
  } catch (error) {
    console.error('Reading time sync failed:', error);
  }
}

async function syncForumPosts() {
  console.log('Syncing forum posts...');
  // Implementation for syncing offline forum posts
}

// Helper functions for IndexedDB operations
async function getPendingReadingData() {
  // This would typically use IndexedDB to store offline data
  // For now, return empty array
  return [];
}

async function removePendingReadingData(id) {
  // Remove synced data from IndexedDB
}

// Push notification handling
self.addEventListener('push', event => {
  if (!event.data) {
    return;
  }
  
  const data = event.data.json();
  const options = {
    body: data.body,
    icon: '/static/images/icon-192x192.png',
    badge: '/static/images/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: data.url,
    actions: [
      {
        action: 'view',
        title: 'View',
        icon: '/static/images/action-view.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/static/images/action-dismiss.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'view' && event.notification.data) {
    event.waitUntil(
      clients.openWindow(event.notification.data)
    );
  } else if (event.action === 'dismiss') {
    // Just close the notification
  }
});

// Message handling from main thread
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME });
  }
});

console.log('Service Worker loaded');