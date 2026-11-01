(function () {
  "use strict";
  const $ = selector => document.querySelector(selector);
  const status = $("#offline-status");
  const account = $("#offline-account");
  const form = $("#offline-entry-form");
  const list = $("#offline-recent");
  const pending = $("#offline-pending");
  const submit = $("#offline-submit");

  function setStatus(message, online) {
    if (!status) return;
    status.textContent = message;
    status.dataset.online = online ? "true" : "false";
  }

  async function render() {
    if (!window.TianaOffline) return;
    const [saved, queue] = await Promise.all([
      window.TianaOffline.readSnapshot(),
      window.TianaOffline.listPending()
    ]);
    const snapshot = saved && saved.value;
    if (account) {
      account.innerHTML = '<option value="">Choose an account</option>' + (snapshot?.accounts || []).map(item =>
        '<option value="' + item.id + '" data-currency="' + window.TianaOffline.escapeHTML(item.currency) + '">' +
        window.TianaOffline.escapeHTML(item.name) + ' · ' + window.TianaOffline.formatMoney(item.balance, item.currency) + '</option>'
      ).join("");
    }
    $("#offline-balance").textContent = snapshot
      ? window.TianaOffline.formatMoney((snapshot.accounts || []).reduce((sum, item) => sum + Number(item.balance || 0), 0), snapshot.currency)
      : "Open TIANA online once";
    $("#offline-saved-at").textContent = saved ? "Last saved " + new Date(saved.savedAt).toLocaleString() : "No offline snapshot yet";
    $("#offline-budget-list").innerHTML = (snapshot?.budgets || []).slice(0, 5).map(item =>
      '<div class="offline-row"><span>' + window.TianaOffline.escapeHTML(item.name) + '</span><strong>' +
      window.TianaOffline.formatMoney(item.spent, item.currency) + ' / ' +
      window.TianaOffline.formatMoney(item.amount, item.currency) + '</strong></div>'
    ).join("") || '<p class="offline-muted">Your budget snapshot will appear after your next online visit.</p>';
    $("#offline-goal-list").innerHTML = (snapshot?.goals || []).slice(0, 4).map(item =>
      '<div class="offline-goal"><div><strong>' + window.TianaOffline.escapeHTML(item.name) + '</strong><span>' +
      window.TianaOffline.formatMoney(item.saved, item.currency) + ' of ' +
      window.TianaOffline.formatMoney(item.target, item.currency) + '</span></div><b>' + item.progress + '%</b></div>'
    ).join("") || '<p class="offline-muted">Your savings goals will appear here after an online visit.</p>';
    const rows = [
      ...(snapshot?.recent_transactions || []).map(item => ({ ...item, local: false })),
      ...queue.map(item => ({ ...item, local: true, transaction_date: item.transaction_date }))
    ].sort((a, b) => String(b.transaction_date || b.created_at).localeCompare(String(a.transaction_date || a.created_at))).slice(0, 10);
    list.innerHTML = rows.map(item => {
      const sign = item.kind === "income" ? "+" : "−";
      const title = item.description || item.category || (item.kind === "income" ? "Income" : "Expense");
      const syncLabel = item.local ? (item.status === "needs_review" ? "Needs review" : "Waiting to sync") : (item.account || "");
      return '<div class="offline-row"><span><b>' + window.TianaOffline.escapeHTML(title) + '</b><small>' +
        window.TianaOffline.escapeHTML(item.transaction_date || "") + ' · ' + window.TianaOffline.escapeHTML(syncLabel) +
        '</small></span><strong class="' + (item.kind === "income" ? "is-income" : "is-expense") + '">' +
        sign + window.TianaOffline.formatMoney(item.amount, item.currency) + '</strong></div>';
    }).join("") || '<p class="offline-muted">No activity saved on this device yet.</p>';
    pending.textContent = queue.length + " waiting";
    const hasAccounts = !!(snapshot && snapshot.accounts && snapshot.accounts.length);
    if (account) account.disabled = !hasAccounts;
    if (submit) submit.disabled = !hasAccounts;
  }

  if (form) {
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const data = new FormData(form);
      const accountOption = account.options[account.selectedIndex];
      const values = Object.fromEntries(data.entries());
      values.currency = accountOption?.dataset.currency || "XAF";
      try {
        await window.TianaOffline.queueTransaction(values);
        form.reset();
        await render();
        setStatus(navigator.onLine ? "Saved on this phone. Syncing now…" : "Saved safely on this phone. It will sync when you're online.", navigator.onLine);
        if (navigator.onLine) {
          await window.TianaOffline.syncPending();
          await render();
          setStatus("Your saved entries are up to date.", true);
        }
      } catch (error) {
        setStatus(error.message || "Could not save this entry.", false);
      }
    });
  }

  $("#offline-sync")?.addEventListener("click", async () => {
    if (!navigator.onLine) {
      setStatus("You're offline. Your entries are still saved on this phone.", false);
      return;
    }
    try {
      const result = await window.TianaOffline.syncPending();
      await render();
      setStatus(result.pending ? result.pending + " entries need your attention." : "Everything is synced.", true);
    } catch (error) {
      setStatus(error.message || "Sync failed. Your entries are still on this phone.", false);
    }
  });

  $("#offline-refresh")?.addEventListener("click", async () => {
    if (!navigator.onLine) return setStatus("Connect to the internet to refresh your snapshot.", false);
    try {
      await window.TianaOffline.refreshSnapshot();
      await render();
      setStatus("Your dashboard snapshot is refreshed.", true);
    } catch (error) {
      setStatus(error.message || "Could not refresh. Sign in to TIANA first.", false);
    }
  });

  window.addEventListener("online", async () => {
    try {
      await window.TianaOffline.syncPending();
      await render();
      setStatus("Connection restored. Your entries are synced.", true);
    } catch (_) {
      setStatus("Connection restored. TIANA will retry syncing your entries.", true);
    }
  });
  window.addEventListener("offline", () => setStatus("You're offline. Your saved records are available on this phone.", false));

  (async () => {
    await render();
    if (navigator.onLine) {
      try {
        await window.TianaOffline.syncPending();
        await render();
        setStatus("Online · your saved data is ready.", true);
      } catch (_) {
        setStatus("Online · using the last saved snapshot.", true);
      }
    } else {
      setStatus("Offline · using the last saved snapshot.", false);
    }
  })().catch(error => setStatus(error.message || "Offline workspace could not start.", false));
})();
