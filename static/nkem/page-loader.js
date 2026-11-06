(function () {
  "use strict";

  const overlay = document.querySelector("[data-tiana-page-loader]");
  if (!overlay) return;

  const messageNode = overlay.querySelector("[data-page-loader-message]");
  const messages = [
    "Getting everything ready for you",
    "Bringing your money details together",
    "Preparing your next screen"
  ];
  const SHOW_DELAY = 220;
  let showTimer = null;
  let hideTimer = null;
  let messageTimer = null;
  let messageIndex = 0;
  let visible = false;

  function paintMessage(message) {
    if (messageNode) messageNode.textContent = message || messages[0];
  }

  function showNow(message) {
    window.clearTimeout(hideTimer);
    overlay.hidden = false;
    overlay.setAttribute("aria-hidden", "false");
    paintMessage(message);
    document.body.classList.add("tiana-page-loading");
    window.requestAnimationFrame(() => overlay.classList.add("is-visible"));
    visible = true;

    if (!message) {
      window.clearInterval(messageTimer);
      messageIndex = 0;
      messageTimer = window.setInterval(() => {
        messageIndex = (messageIndex + 1) % messages.length;
        paintMessage(messages[messageIndex]);
      }, 3200);
    }
  }

  function show(message) {
    window.clearTimeout(showTimer);
    showTimer = window.setTimeout(() => showNow(message), SHOW_DELAY);
  }

  function hide(immediate) {
    window.clearTimeout(showTimer);
    window.clearTimeout(hideTimer);
    window.clearInterval(messageTimer);
    if (!visible && overlay.hidden) return;

    overlay.classList.remove("is-visible");
    overlay.setAttribute("aria-hidden", "true");
    document.body.classList.remove("tiana-page-loading");
    visible = false;

    if (immediate) {
      overlay.hidden = true;
    } else {
      hideTimer = window.setTimeout(() => {
        overlay.hidden = true;
      }, 260);
    }
  }

  function isPlainInternalNavigation(event, anchor) {
    if (!anchor || event.defaultPrevented || event.button !== 0) return false;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
    if (anchor.hasAttribute("download") || anchor.target && anchor.target !== "_self") return false;
    if (anchor.hasAttribute("data-no-page-loader")) return false;
    if (anchor.closest("[data-no-page-loader]")) return false;

    let destination;
    try {
      destination = new URL(anchor.href, window.location.href);
    } catch (_) {
      return false;
    }

    if (destination.origin !== window.location.origin) return false;
    if (destination.pathname === window.location.pathname &&
        destination.search === window.location.search &&
        destination.hash) return false;
    if (destination.href === window.location.href) return false;
    return true;
  }

  document.addEventListener("click", (event) => {
    const anchor = event.target.closest && event.target.closest("a[href]");
    if (!isPlainInternalNavigation(event, anchor)) return;

    const message = anchor.getAttribute("data-loader-message") || "Opening your page…";
    window.setTimeout(() => {
      if (!event.defaultPrevented) show(message);
    }, 0);
  }, true);

  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (form.hasAttribute("data-no-page-loader") || form.closest("[data-no-page-loader]")) return;
    if (form.target && form.target !== "_self") return;
    if ((form.getAttribute("method") || "get").toLowerCase() === "dialog") return;

    const message = form.getAttribute("data-loader-message") || "Saving your changes…";
    window.setTimeout(() => {
      // AJAX forms that call preventDefault() keep their own local feedback.
      if (!event.defaultPrevented) show(message);
    }, 0);
  }, true);

  window.addEventListener("beforeunload", () => showNow("Taking you to the next page…"));
  window.addEventListener("pageshow", () => hide(true));
  window.addEventListener("pagehide", () => {
    window.clearTimeout(showTimer);
    window.clearInterval(messageTimer);
  });

  // Expose a small opt-in API for long-running actions that are not navigation
  // or native form submissions. Call hide() when that action has completed.
  window.TianaPageLoader = {
    show: (message) => showNow(message || "Working on your request…"),
    hide: () => hide(false)
  };
})();