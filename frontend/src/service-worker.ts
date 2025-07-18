/// <reference types="@sveltejs/kit" />
/// <reference lib="webworker" />

import { build, files, version } from '$service-worker';

// Create a unique cache name for this deployment
const CACHE_NAME = `tradesense-v${version}`;

// Assets to cache on install
const ASSETS = [
  ...build, // the app itself
  ...files  // static files
];

// Install event - cache all static assets
self.addEventListener('install', (event: ExtendableEvent) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(ASSETS))
      .then(() => {
        // @ts-ignore
        self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.keys().then(async (keys) => {
      // Delete old caches
      for (const key of keys) {
        if (key !== CACHE_NAME) {
          await caches.delete(key);
        }
      }
      // @ts-ignore
      self.clients.claim();
    })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event: FetchEvent) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Don't cache API requests
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  event.respondWith(
    (async () => {
      // Try cache first
      const cachedResponse = await caches.match(event.request);
      
      if (cachedResponse) {
        // Return cached response
        return cachedResponse;
      }

      try {
        // Fetch from network
        const response = await fetch(event.request);

        // Cache successful responses
        if (response.status === 200) {
          const cache = await caches.open(CACHE_NAME);
          cache.put(event.request, response.clone());
        }

        return response;
      } catch (err) {
        // Network failed, try to return a cached offline page
        const cache = await caches.open(CACHE_NAME);
        const offlinePage = await cache.match('/offline.html');
        
        if (offlinePage) {
          return offlinePage;
        }

        // If no offline page, return error
        return new Response('Network error', {
          status: 408,
          headers: { 'Content-Type': 'text/plain' }
        });
      }
    })()
  );
});

// Background sync for offline trade uploads
self.addEventListener('sync', (event: any) => {
  if (event.tag === 'sync-trades') {
    event.waitUntil(syncTrades());
  }
});

async function syncTrades() {
  // Get pending trades from IndexedDB
  const pendingTrades = await getPendingTrades();
  
  for (const trade of pendingTrades) {
    try {
      const response = await fetch('/api/v1/trades', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${trade.token}`
        },
        body: JSON.stringify(trade.data)
      });

      if (response.ok) {
        await removePendingTrade(trade.id);
      }
    } catch (error) {
      console.error('Failed to sync trade:', error);
    }
  }
}

// Placeholder functions for IndexedDB operations
async function getPendingTrades(): Promise<any[]> {
  // Implementation would use IndexedDB to get pending trades
  return [];
}

async function removePendingTrade(id: string): Promise<void> {
  // Implementation would remove synced trade from IndexedDB
}