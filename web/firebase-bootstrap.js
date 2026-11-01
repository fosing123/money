/* Firebase app, opt-in Analytics, and explicit FCM push subscription for TIANA. */
(async function () {
  "use strict";
  const config = window.TIANA_FIREBASE_CONFIG;
  if (!config) return;

  const sdkBase = "https://www.gstatic.com/firebasejs/13.0.0";
  let analyticsSdk = null;
  let analyticsInstance = null;
  let messagingSdk = null;
  let messagingInstance = null;
  let foregroundListenerAttached = false;

  async function getMessagingRuntime() {
    if (!messagingSdk) messagingSdk = await import(sdkBase + "/firebase-messaging.js");
    if (!(await messagingSdk.isSupported())) throw new Error("Push notifications are not supported by this browser.");
    if (!messagingInstance) messagingInstance = messagingSdk.getMessaging(app);
    return { sdk: messagingSdk, messaging: messagingInstance };
  }

  function installationId() {
    if (window.TianaTelemetry && typeof window.TianaTelemetry.deviceId === "function") return window.TianaTelemetry.deviceId();
    let id = localStorage.getItem("TIANA_INSTALL_ID_V1");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("TIANA_INSTALL_ID_V1", id);
    }
    return id;
  }

  async function setAnalyticsConsent(enabled) {
    if (!enabled) {
      if (analyticsSdk && analyticsInstance) analyticsSdk.setAnalyticsCollectionEnabled(analyticsInstance, false);
      return null;
    }
    if (localStorage.getItem("TIANA_ANALYTICS_CONSENT") !== "yes") return null;
    if (!analyticsSdk) analyticsSdk = await import(sdkBase + "/firebase-analytics.js");
    if (!(await analyticsSdk.isSupported())) return null;
    if (!analyticsInstance) analyticsInstance = analyticsSdk.getAnalytics(app);
    analyticsSdk.setAnalyticsCollectionEnabled(analyticsInstance, true);
    return analyticsInstance;
  }

  async function enablePushNotifications() {
    if (!("Notification" in window)) throw new Error("This browser does not support web notifications.");
    if (!("serviceWorker" in navigator)) throw new Error("This browser does not support service workers.");
    if (!config.vapidPublicKey) throw new Error("The TIANA VAPID public key is not configured.");

    // Called from the explicit user click so the browser can display permission UI.
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      throw new Error(permission === "denied" ? "Notifications are blocked in browser settings." : "Notification permission was not granted.");
    }

    const registration = await navigator.serviceWorker.ready;
    const runtime = await getMessagingRuntime();
    const fcmToken = await runtime.sdk.getToken(runtime.messaging, {
      vapidKey: config.vapidPublicKey,
      serviceWorkerRegistration: registration
    });
    if (!fcmToken) throw new Error("Firebase did not return a device token.");

    const response = await fetch("/api/push/register", {
      method: "POST",
      credentials: "omit",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ deviceId: installationId(), token: fcmToken })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || "TIANA could not register this device.");

    localStorage.setItem("TIANA_PUSH_ENABLED", "yes");
    if (!foregroundListenerAttached) {
      runtime.sdk.onMessage(runtime.messaging, (message) => {
        window.dispatchEvent(new CustomEvent("tiana:push-message", { detail: message }));
      });
      foregroundListenerAttached = true;
    }
    return { enabled: true };
  }

  async function disablePushNotifications() {
    const deviceId = installationId();
    let runtime = null;
    try { runtime = await getMessagingRuntime(); } catch (_) {}

    const response = await fetch("/api/push/register?deviceId=" + encodeURIComponent(deviceId), {
      method: "DELETE",
      credentials: "omit",
      cache: "no-store"
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || "Could not remove the server-side notification registration.");
    }
    if (runtime) {
      try { await runtime.sdk.deleteToken(runtime.messaging); } catch (_) {}
    }
    localStorage.removeItem("TIANA_PUSH_ENABLED");
    return { enabled: false };
  }

  try {
    const appSdk = await import(sdkBase + "/firebase-app.js");
    const app = appSdk.getApps().find((item) => item.name === "[DEFAULT]") || appSdk.initializeApp(config);
    window.TianaFirebase = Object.freeze({
      app,
      projectId: config.projectId,
      setAnalyticsConsent,
      enablePushNotifications,
      disablePushNotifications
    });
    if (localStorage.getItem("TIANA_ANALYTICS_CONSENT") === "yes") await setAnalyticsConsent(true);
  } catch (error) {
    // Firebase is optional; local bookkeeping remains available if online integrations fail.
    console.warn("TIANA Firebase could not initialize. Core offline features remain available.", error);
  }
})();
