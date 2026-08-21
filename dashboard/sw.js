// Service worker for the AU PC Part Price Tracker PWA.
//
// Strategy: network-first for EVERYTHING (app shell AND data files).
// Always tries to fetch the latest version first; only falls back to the
// last cached copy if the network request fails (i.e. actually offline).
//
// Why this changed from the original cache-first app shell: cache-first
// meant returning visitors kept seeing whatever version of index.html was
// cached the very first time the app was installed on their device -
// updates never showed up on a normal reload, only after a hard refresh
// (which bypasses the service worker entirely). That's broken for a PWA
// people install to their phone home screen, since there's no easy
// "hard refresh" gesture there. Network-first fixes this permanently -
// no more needing to bump CACHE_VERSION and hope devices notice.
//
// Bumped to v2 specifically so browsers detect this file itself changed
// and actually install the new logic (byte-for-byte identical service
// worker files don't trigger an update check).

const CACHE_VERSION = 'v2';
const APP_SHELL_CACHE = `pc-tracker-shell-${CACHE_VERSION}`;
const DATA_CACHE = `pc-tracker-data-${CACHE_VERSION}`;

const APP_SHELL_FILES = [
  './',
  './index.html',
  './manifest.json',
];

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

  const isAppShell = APP_SHELL_FILES.some((f) => request.url.endsWith(f.replace('./', '')))
    || request.mode === 'navigate';
  const targetCache = isAppShell ? APP_SHELL_CACHE : DATA_CACHE;

  event.respondWith(
    fetch(request)
      .then((response) => {
        const clone = response.clone();
        caches.open(targetCache).then((cache) => cache.put(request, clone));
        return response;
      })
      .catch(() => caches.match(request))
  );
});
