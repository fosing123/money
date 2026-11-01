/* Firebase Cloud Messaging background support.
 * Reuses TIANA's existing root-scope service worker.
 */
try {
  importScripts("/firebase-config.js");
  importScripts("https://www.gstatic.com/firebasejs/13.0.0/firebase-app-compat.js");
  importScripts("https://www.gstatic.com/firebasejs/13.0.0/firebase-messaging-compat.js");
  if (self.TIANA_FIREBASE_CONFIG && self.firebase && self.firebase.messaging) {
    self.firebase.initializeApp(self.TIANA_FIREBASE_CONFIG);
    const tianaMessaging = self.firebase.messaging();
    tianaMessaging.onBackgroundMessage((payload) => {
      // FCM renders notification payloads automatically; only render data-only messages here.
      if (payload && payload.notification) return;
      const data = (payload && payload.data) || {};
      self.registration.showNotification(data.title || "TIANA", {
        body: data.body || "You have a new update.",
        icon: "/money-mark.svg",
        badge: "/money-mark.svg",
        data: { link: data.link || "/" }
      });
    });
  }
} catch (_) {
  // Do not prevent the offline shell from starting when Firebase's CDN is unavailable.
}

const CACHE="tiana-local-shell-v1",SHELL=["/","/index.html","/app.css","/app.js","/vault.js","/install-gate.js","/privacy-telemetry.js","/firebase-config.js","/firebase-bootstrap.js","/google-drive-backup.js","/manifest.webmanifest","/money-mark.svg","/icons/tiana-icon.svg","/icons/tiana-180.png","/assets/invest.svg","/assets/marketplace.svg","/assets/money-coach.svg","/assets/onboarding-account.svg","/assets/onboarding-ai.svg","/assets/onboarding-control.svg","/assets/onboarding-goals.svg","/assets/onboarding-welcome.svg","/assets/student-hero-3d.webp","/assets/student-hero.svg","/assets/student-onboarding-photo.webp"];
self.addEventListener("install",e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener("activate",e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith("tiana-")&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener("fetch",e=>{const r=e.request;if(r.method!=="GET")return;const u=new URL(r.url);if(u.origin!==self.location.origin||u.pathname.startsWith("/api/"))return;if(r.mode==="navigate"){e.respondWith(fetch(r).catch(async()=>await caches.match("/index.html")||new Response("Open TIANA from your home screen while offline.",{status:503,headers:{"Content-Type":"text/plain"}})));return;}e.respondWith(caches.match(r).then(c=>c||fetch(r).then(res=>{if(res.ok&&res.type==="basic")caches.open(CACHE).then(cache=>cache.put(r,res.clone())).catch(()=>{});return res;}).catch(()=>new Response("This resource is not available offline.",{status:503}))));});
