// Service Worker for PWA offline support and caching

const CACHE_NAME = 'trading-bot-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/src/styles/mobile.css',
  '/src/styles/dark-mode.css',
  '/src/App.js',
  '/manifest.json'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Caching files');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: Clearing old cache');
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
  // API requests - network first, fallback to cache
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Clone the response
          const responseClone = response.clone();
          
          // Cache the response
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseClone);
          });
          
          return response;
        })
        .catch(() => {
          // If network fails, try cache
          return caches.match(event.request);
        })
    );
  } 
  // Static assets - cache first, fallback to network
  else {
    event.respondWith(
      caches.match(event.request)
        .then(response => {
          return response || fetch(event.request).then(fetchResponse => {
            return caches.open(CACHE_NAME).then(cache => {
              cache.put(event.request, fetchResponse.clone());
              return fetchResponse;
            });
          });
        })
        .catch(() => {
          // Return offline page if available
          if (event.request.destination === 'document') {
            return caches.match('/offline.html');
          }
        })
    );
  }
});

// Push notification handler
self.addEventListener('push', async event => {
  const text = event.data ? await event.data.text() : 'New notification from Trading Bot';
  
  const options = {
    body: text,
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    tag: 'trading-notification',
    requireInteraction: false
  };

  event.waitUntil(
    self.registration.showNotification('Trading Bot', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow('/')
  );
});

// Background sync handler (for failed requests)
self.addEventListener('sync', event => {
  if (event.tag === 'sync-trades') {
    event.waitUntil(syncTrades());
  }
});

async function syncTrades() {
  // Sync failed trades when back online
  console.log('Service Worker: Syncing trades');
  // Implementation would retrieve and retry failed requests
}
