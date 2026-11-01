/* Firebase app initialization for the TIANA PWA.
 * Firebase Analytics loads only after the user opts in through Settings.
 */
(async function () {
  "use strict";
  const config = window.TIANA_FIREBASE_CONFIG;
  if (!config) return;
  try {
    const sdkBase = "https://www.gstatic.com/firebasejs/13.0.0";
    const appSdk = await import(sdkBase + "/firebase-app.js");
    const app = appSdk.getApps().find((item) => item.name === "[DEFAULT]") || appSdk.initializeApp(config);
    let analyticsSdk = null;
    let analyticsInstance = null;

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

    window.TianaFirebase = Object.freeze({ app, projectId: config.projectId, setAnalyticsConsent });
    if (localStorage.getItem("TIANA_ANALYTICS_CONSENT") === "yes") await setAnalyticsConsent(true);
  } catch (error) {
    console.warn("TIANA Firebase could not initialize. Core offline features remain available.", error);
  }
})();
