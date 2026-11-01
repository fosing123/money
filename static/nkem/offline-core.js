(function () {
  "use strict";
  const DB_NAME = "tiana-offline-v1";
  const DB_VERSION = 1;
  let dbPromise;

  function openDB() {
    if (!("indexedDB" in window)) return Promise.reject(new Error("This browser does not support local offline storage."));
    if (dbPromise) return dbPromise;
    dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains("meta")) db.createObjectStore("meta", { keyPath: "key" });
        if (!db.objectStoreNames.contains("outbox")) db.createObjectStore("outbox", { keyPath: "id" });
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("Could not open offline storage."));
      request.onblocked = () => reject(new Error("Close another TIANA tab to finish preparing offline storage."));
    });
    return dbPromise;
  }

  async function storeRequest(storeName, mode, action) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, mode);
      const store = tx.objectStore(storeName);
      let result;
      try { result = action(store); } catch (error) { reject(error); return; }
      tx.oncomplete = () => resolve(result && "result" in result ? result.result : result);
      tx.onerror = () => reject(tx.error || new Error("Local save failed."));
      tx.onabort = () => reject(tx.error || new Error("Local save was cancelled."));
    });
  }

  const get = (store, key) => storeRequest(store, "readonly", s => s.get(key));
  const put = (store, value) => storeRequest(store, "readwrite", s => s.put(value));
  const remove = (store, key) => storeRequest(store, "readwrite", s => s.delete(key));
  const all = store => storeRequest(store, "readonly", s => s.getAll());

  function newId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") return window.crypto.randomUUID();
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0;
      return (c === "x" ? r : (r & 3 | 8)).toString(16);
    });
  }

  function csrfToken() {
    const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  async function refreshSnapshot() {
    if (!navigator.onLine) return null;
    const response = await fetch("/api/offline/bootstrap/", {
      credentials: "same-origin",
      cache: "no-store",
      headers: { "Accept": "application/json" }
    });
    if (!response.ok || !(response.headers.get("content-type") || "").includes("application/json")) {
      throw new Error(response.status === 403 ? "Sign in again to refresh your offline data." : "Could not refresh your offline data.");
    }
    const snapshot = await response.json();
    await put("meta", { key: "bootstrap", value: snapshot, savedAt: new Date().toISOString() });
    return snapshot;
  }

  async function queueTransaction(values) {
    const amount = Number(values.amount);
    if (!Number.isFinite(amount) || amount <= 0) throw new Error("Enter an amount greater than zero.");
    if (!values.account_id) throw new Error("Choose an account from your saved offline profile.");
    if (!["income", "expense"].includes(values.kind)) throw new Error("Only income and expense entries can be queued offline.");
    const row = {
      id: newId(),
      type: "transaction",
      account_id: Number(values.account_id),
      kind: values.kind,
      amount: amount.toFixed(2),
      currency: String(values.currency || "XAF").toUpperCase(),
      category: String(values.category || "Other").trim().slice(0, 50) || "Other",
      description: String(values.description || "").trim().slice(0, 255),
      merchant: String(values.merchant || "").trim().slice(0, 120),
      transaction_date: values.transaction_date || new Date().toISOString().slice(0, 10),
      status: "pending",
      created_at: new Date().toISOString()
    };
    await put("outbox", row);
    return row;
  }

  let syncing = false;
  async function syncPending() {
    if (!navigator.onLine || syncing) return { synced: 0, pending: (await all("outbox")).length };
    syncing = true;
    try {
      const queue = await all("outbox");
      const pending = queue.filter(item => item.status === "pending");
      let synced = 0;
      for (let offset = 0; offset < pending.length; offset += 25) {
        const batch = pending.slice(offset, offset + 25);
        const response = await fetch("/api/offline/sync/", {
          method: "POST",
          credentials: "same-origin",
          cache: "no-store",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-CSRFToken": csrfToken()
          },
          body: JSON.stringify({ items: batch })
        });
        if (!response.ok || !(response.headers.get("content-type") || "").includes("application/json")) {
          throw new Error(response.status === 403 ? "Sign in again before syncing your saved entries." : "Sync could not complete. Your entries are still saved on this phone.");
        }
        const payload = await response.json();
        for (const result of (payload.results || [])) {
          if (result.status === "synced") {
            await remove("outbox", result.id);
            synced += 1;
          } else {
            const failed = batch.find(item => item.id === result.id);
            if (failed) await put("outbox", { ...failed, status: "needs_review", message: result.message || "Review this entry online." });
          }
        }
      }
      try { await refreshSnapshot(); } catch (_) { /* The queued entries are already safely acknowledged. */ }
      return { synced, pending: (await all("outbox")).length };
    } finally {
      syncing = false;
    }
  }

  async function listPending() { return all("outbox"); }
  async function readSnapshot() { return get("meta", "bootstrap"); }

  function formatMoney(value, currency) {
    const amount = Number(value) || 0;
    return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 }).format(amount) + " " + (currency || "XAF");
  }
  function escapeHTML(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, char => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[char]);
  }

  window.TianaOffline = {
    refreshSnapshot, queueTransaction, syncPending, listPending, readSnapshot, removePending: id => remove("outbox", id),
    formatMoney, escapeHTML
  };
})();
