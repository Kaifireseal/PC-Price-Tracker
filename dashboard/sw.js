// Service worker for the AU PC Part Price Tracker PWA.
//
// Strategy:
//   - App shell (this HTML/CSS/JS) is cached so the site opens instantly
//     and works offline, even with no signal.
//   - Data files (prices.json, history.json, tiers.json) use
//     "network-first, fall back to cache" — so you always see fresh
//     prices when online, but still see the last-known prices if offline.
//
// Bump CACHE_VERSION whenever you change dashboard/index.html so old
// visitors pick up the new version instead of a stale cached copy.

const CACHE_VERSION = 'v1';
const APP_SHELL_CACHE = `pc-tracker-shell-${CACHE_VERSION}`;
const DATA_CACHE = `pc-tracker-data-${CACHE_VERSION}`;

const APP_SHELL_FILES = [
  './',
  './index.html',
  './manifest.json',
];

const DATA_FILE_PATTERNS = ['prices.json', 'history.json', 'tiers.json'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(APP_SHELL_CACHE).then((cache) => cache.addAll(APP_SHELL_FILES))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== APP_SHELL_CACHE && key !== DATA_CACHE)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const isDataFile = DATA_FILE_PATTERNS.some((name) => request.url.includes(name));

  if (isDataFile) {
    // Network-first: try to get fresh prices, fall back to last cached copy if offline.
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone();
          caches.open(DATA_CACHE).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  // App shell: cache-first, so the UI loads instantly.
  event.respondWith(
    caches.match(request).then((cached) => cached || fetch(request))
  );
});
