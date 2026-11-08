(() => {
  "use strict";

  const renderAdSlots = () => {
    document.querySelectorAll("[data-adsterra-slot]").forEach((slot) => {
      if (slot.dataset.rendered === "true") return;
      const code = slot.dataset.adsterraCode || "";
      const width = Math.max(1, Math.min(1200, Number(slot.dataset.adWidth) || 320));
      const height = Math.max(1, Math.min(1200, Number(slot.dataset.adHeight) || 50));
      if (!code || !code.toLowerCase().includes("<script")) {
        slot.closest(".tiana-ad-placement")?.remove();
        return;
      }

      const frame = document.createElement("iframe");
      frame.title = "Advertisement";
      frame.width = String(width);
      frame.height = String(height);
      frame.loading = "lazy";
      frame.referrerPolicy = "strict-origin-when-cross-origin";
      frame.setAttribute("sandbox", "allow-scripts allow-popups allow-popups-to-escape-sandbox");
      frame.style.width = width + "px";
      frame.style.height = height + "px";
      frame.style.maxWidth = "100%";
      frame.style.border = "0";
      const documentSource = "<!doctype html><html><head><meta charset=\"utf-8\">" +
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">" +
        "<style>html,body{margin:0;padding:0;width:" + width + "px;min-height:" + height +
        "px;overflow:hidden;background:transparent}</style></head><body>" + code + "</body></html>";
      frame.srcdoc = documentSource;
      slot.replaceChildren(frame);
      slot.style.setProperty("--ad-width", width + "px");
      slot.style.setProperty("--ad-height", height + "px");
      slot.dataset.rendered = "true";
    });
  };

  const gate = document.querySelector("[data-tiana-ai-ad-gate]");
  let activeResolve = null;
  let unlockTimer = null;
  let oldFocus = null;
  const continueButton = gate?.querySelector("[data-tiana-ai-ad-continue]");
  const status = gate?.querySelector("[data-tiana-ai-ad-status]");
  const closeGate = (continued) => {
    if (!gate || !activeResolve) return;
    if (unlockTimer) window.clearTimeout(unlockTimer);
    unlockTimer = null;
    const resolve = activeResolve;
    activeResolve = null;
    gate.hidden = true;
    gate.setAttribute("aria-hidden", "true");
    document.body.classList.remove("tiana-ai-ad-gate-open");
    if (oldFocus && typeof oldFocus.focus === "function") oldFocus.focus({preventScroll:true});
    oldFocus = null;
    resolve(Boolean(continued));
  };

  if (gate) {
    gate.querySelectorAll("[data-tiana-ai-ad-cancel]").forEach((button) =>
      button.addEventListener("click", () => closeGate(false))
    );
    continueButton?.addEventListener("click", () => {
      if (!continueButton.disabled) closeGate(true);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !gate.hidden) closeGate(false);
    });
  }

  window.TianaAdGate = {
    show() {
      if (!gate) return Promise.resolve(true);
      if (activeResolve) return Promise.resolve(false);
      renderAdSlots();
      oldFocus = document.activeElement;
      gate.hidden = false;
      document.body.classList.add("tiana-ai-ad-gate-open");
      if (continueButton) continueButton.disabled = true;
      if (status) status.textContent = "Loading the sponsored placement…";
      const adFrame = gate.querySelector("[data-adsterra-slot] iframe");
      if (adFrame) {
        adFrame.addEventListener("load", () => {
          if (status && !gate.hidden) status.textContent = "Thanks for supporting TIANA. You can continue when ready.";
        }, {once:true});
      }
      window.requestAnimationFrame(() => continueButton?.focus());
      return new Promise((resolve) => {
        activeResolve = resolve;
        // Standard banners have no trusted view-completion callback. This pause
        // never asks users to click the advert and still unlocks if it is blocked.
        unlockTimer = window.setTimeout(() => {
          if (continueButton) continueButton.disabled = false;
          if (status) status.textContent = "You do not need to click the advertisement. Continue when ready.";
        }, 5000);
      });
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderAdSlots, {once:true});
  } else {
    renderAdSlots();
  }
})();
