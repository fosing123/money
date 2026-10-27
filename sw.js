const CACHE = "student-money-shell-v5";
const SHELL = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./money-mark.svg",
  "./assets/student-hero.svg",
  "./assets/student-hero-3d.webp",
  "./assets/money-coach.svg",
  "./assets/marketplace.svg",
  "./assets/invest.svg"
];
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});
self.addEventListener("fetch", event => {
  if (event.request.method !== "GET" || new URL(event.request.url).origin !== self.location.origin) return;
  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
      if (response.ok) caches.open(CACHE).then(cache => cache.put(event.request, response.clone()));
      return response;
    }).catch(() => caches.match("./index.html")))
  );
});