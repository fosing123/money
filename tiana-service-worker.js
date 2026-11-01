const CACHE_PREFIX = "tiana-pwa-";
const SHELL_CACHE = "tiana-pwa-shell-v1";
const OFFLINE_PAGE = "/static/nkem/offline.html";
const SHELL = [
  OFFLINE_PAGE,
  "/static/nkem/offline.css",
  "/static/nkem/offline-core.js",
  "/static/nkem/offline.js",
  "/static/nkem/app.css",
  "/static/nkem/theme.css",
  "/static/nkem/brand.css",
  "/static/nkem/ui-polish.css",
  "/static/manifest.webmanifest",
  "/static/money-mark.svg",
  "/static/assets/tiana-logo-transparent.png",
  "/static/assets/tiana-campus-hero.webp"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then(cache => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys
        .filter(key => key.startsWith(CACHE_PREFIX) && key !== SHELL_CACHE)
        .map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(async () => {
        const cache = await caches.open(SHELL_CACHE);
        return (await cache.match(OFFLINE_PAGE)) || new Response(
          "TIANA is offline. Reconnect to load this page.",
          { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } }
        );
      })
    );
    return;
  }

  // Cache only same-origin static assets. Never cache /api/, /media/, or HTML
  // pages containing account-specific financial information.
  if (!url.pathname.startsWith("/static/")) return;

  event.respondWith((async () => {
    const cache = await caches.open(SHELL_CACHE);
    const cached = await cache.match(request, { ignoreSearch: true });
    if (cached) return cached;
    try {
      const response = await fetch(request);
      if (response.ok && response.type === "basic") {
        await cache.put(request, response.clone());
      }
      return response;
    } catch (error) {
      return new Response("This resource is not available offline.", {
        status: 503,
        statusText: "Offline",
        headers: { "Content-Type": "text/plain; charset=utf-8" }
      });
    }
  })());
});
