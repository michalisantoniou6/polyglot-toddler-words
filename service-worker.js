const CACHE_VERSION = 'toddler-arcade-v7';
const APP_SHELL = [
    './',
    './index.html',
    './manifest.webmanifest',
    './icons/icon-180.png',
    './icons/icon-192.png',
    './icons/icon-512.png',
    './icons/icon-maskable-512.png',
    './assets/santa-ho-ho-ho.mp3?v=2',
    './assets/santa-sleigh.png'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_VERSION)
            .then(cache => cache.addAll(APP_SHELL))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(
                keys
                    .filter(key => key.startsWith('toddler-arcade-') && key !== CACHE_VERSION)
                    .map(key => caches.delete(key))
            ))
            .then(() => self.clients.claim())
    );
});

async function networkFirstNavigation(request) {
    const cache = await caches.open(CACHE_VERSION);
    const canonicalPage = new Request(new URL('./index.html', self.registration.scope));

    try {
        const response = await fetch(request);
        if (response.ok) await cache.put(canonicalPage, response.clone());
        return response;
    } catch (error) {
        return (await cache.match(canonicalPage)) || (await cache.match('./'));
    }
}

async function cacheFirstAsset(request) {
    const cache = await caches.open(CACHE_VERSION);
    const cached = await cache.match(request, { ignoreSearch: false });
    if (cached) return cached;

    const response = await fetch(request);
    if (response.ok) await cache.put(request, response.clone());
    return response;
}

self.addEventListener('fetch', event => {
    const request = event.request;
    if (request.method !== 'GET') return;

    const url = new URL(request.url);
    if (url.origin !== self.location.origin) return;

    if (request.mode === 'navigate') {
        event.respondWith(networkFirstNavigation(request));
        return;
    }

    event.respondWith(cacheFirstAsset(request));
});
