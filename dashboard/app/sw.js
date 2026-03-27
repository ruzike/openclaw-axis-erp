// AXIS PWA Service Worker v1.0
const CACHE_NAME = 'axis-pwa-v1';
const STATIC_ASSETS = [
  '/app/',
  '/app/index.html',
  '/app/style.css',
  '/app/manifest.json',
  '/app/icon-192.svg',
  '/app/icon-512.svg'
];

// Install: cache static assets
self.addEventListener('install', event => {
  console.log('[SW] Installing AXIS PWA...');
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_ASSETS).catch(err => {
        console.warn('[SW] Some assets failed to cache:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate: clean old caches
self.addEventListener('activate', event => {
  console.log('[SW] Activating AXIS PWA...');
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch: cache-first for static, network-first for API
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Skip non-GET and WebSocket
  if (event.request.method !== 'GET') return;
  if (url.protocol === 'ws:' || url.protocol === 'wss:') return;

  // API calls: network-first
  if (url.pathname.startsWith('/api/') || url.pathname === '/health') {
    event.respondWith(
      fetch(event.request)
        .then(response => response)
        .catch(() => new Response(JSON.stringify({ status: 'offline', error: 'No network' }), {
          headers: { 'Content-Type': 'application/json' }
        }))
    );
    return;
  }

  // Static: cache-first
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => {
        // Offline fallback for HTML
        if (event.request.headers.get('accept')?.includes('text/html')) {
          return caches.match('/app/index.html');
        }
      });
    })
  );
});
