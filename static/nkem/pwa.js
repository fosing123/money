(function () {
  "use strict";
  const installButton = document.getElementById("tiana-install-button");
  let installPrompt = null;

  if ("serviceWorker" in navigator && window.isSecureContext) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/service-worker.js", { scope: "/" }).catch(error => {
        console.warn("TIANA offline support could not be registered.", error);
      });
    }, { once: true });
  }

  window.addEventListener("beforeinstallprompt", event => {
    event.preventDefault();
    installPrompt = event;
    if (installButton) {
      installButton.hidden = false;
      installButton.textContent = "Install TIANA";
    }
  });

  if (installButton) {
    const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
    if (isIOS && !window.matchMedia("(display-mode: standalone)").matches) {
      installButton.hidden = false;
      installButton.textContent = "How to install";
    }
    installButton.addEventListener("click", async () => {
      if (!installPrompt) {
        if (isIOS) alert("Open the Share menu in Safari, then choose “Add to Home Screen”.");
        else alert("Open your browser menu and choose “Install app” or “Add to Home screen” when available.");
        return;
      }
      installPrompt.prompt();
      await installPrompt.userChoice;
      installPrompt = null;
      installButton.hidden = true;
    });
  }

  window.addEventListener("appinstalled", () => {
    if (installButton) installButton.hidden = true;
  });

  const authenticated = document.body.dataset.userAuthenticated === "true";
  if (!authenticated || !window.TianaOffline) return;

  let refreshInProgress = false;
  async function maintainOfflineData() {
    if (!navigator.onLine || refreshInProgress) return;
    refreshInProgress = true;
    try {
      await window.TianaOffline.syncPending();
    } catch (error) {
      console.info("TIANA will retry offline sync when the connection is available.", error);
    } finally {
      refreshInProgress = false;
    }
  }

  window.addEventListener("online", maintainOfflineData);
  window.addEventListener("focus", maintainOfflineData);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") maintainOfflineData();
  });
  maintainOfflineData();
})();
