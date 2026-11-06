(() => {
  "use strict";
  const modal = document.querySelector("[data-tiana-analysis-modal]");
  if (!modal) return;
  const dialog = modal.querySelector(".tiana-analysis-dialog");
  const resultPanel = modal.querySelector("[data-analysis-result]");
  const loadingPanel = modal.querySelector("[data-analysis-loading]");
  const errorPanel = modal.querySelector("[data-analysis-error]");
  const personalizationPanel = modal.querySelector("[data-analysis-personalization]");
  const personalizationForm = modal.querySelector("[data-personalization-form]");
  const insightUrl = modal.dataset.insightUrl || "/analyzer/insight/";
  const previewUrl = modal.dataset.previewUrl || "/analyzer/transaction-preview/";
  const personalizationUrl = modal.dataset.personalizationUrl || "/analyzer/personalization/";
  let pendingAction = null;
  let lastFocusedElement = null;
  let requestController = null;

  const el = (tag, className, value) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined && value !== null) node.textContent = String(value);
    return node;
  };
  const csrfToken = () => {
    const input = document.querySelector("input[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  };
  const readJsonResponse = async (response) => {
    const body = await response.text();
    const contentType = response.headers.get("content-type") || "";
    const normalizedType = contentType.toLowerCase();
    const isJson = normalizedType.includes("application/json") || normalizedType.includes("+json");
    if (redirectedToLogin) {
      throw new Error("Your TIANA session has expired. Refresh the page, sign in again and retry.");
    }
    if (!isJson) {
      const ray = response.headers.get("cf-ray");
      const reference = ray ? " Reference: " + ray + "." : "";
      if (response.status === 401 || response.status === 403) {
        throw new Error("TIANA could not verify your session. Refresh the page and try again." + reference);
      }
      if (response.status >= 500) {
        throw new Error("TIANA's service ran into a server error (HTTP " + response.status + "). Your money records were not changed. Please refresh and retry." + reference);
      }
      throw new Error("TIANA received an unexpected response (HTTP " + response.status + "). Please refresh and try again." + reference);
    }
    try {
      const payload = body ? JSON.parse(body) : {};
      if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
        throw new Error("The response was not a valid data object.");
      }
      return payload;
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new Error("TIANA's reply was incomplete. Please retry in a moment.");
      }
      throw error;
    }
  };
  const setPanel = (panel) => {
    loadingPanel.hidden = panel !== "loading";
    resultPanel.hidden = panel !== "result";
    errorPanel.hidden = panel !== "error";
    personalizationPanel.hidden = panel !== "personalization";
  };
  const openModal = () => {
    lastFocusedElement = document.activeElement;
    modal.hidden = false;
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("tiana-analysis-open");
    window.requestAnimationFrame(() => {
      const close = modal.querySelector(".tiana-analysis-close");
      if (close) close.focus();
    });
  };
  const closeModal = () => {
    if (requestController) requestController.abort();
    requestController = null;
    modal.hidden = true;
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("tiana-analysis-open");
    pendingAction = null;
    if (lastFocusedElement && typeof lastFocusedElement.focus === "function") lastFocusedElement.focus();
  };
  const showError = (message) => {
    errorPanel.textContent = message || "Something went wrong. Please try again.";
    setPanel("error");
  };
  const appendList = (target, items) => {
    target.replaceChildren();
    (items || []).forEach((item) => {
      const text = typeof item === "string" ? item : item.text || item.title || "";
      if (text) target.appendChild(el("li", "", text));
    });
  };
  const toggleSection = (selector, show) => {
    const section = modal.querySelector(selector);
    if (section) section.hidden = !show;
    return section;
  };
  const renderMetrics = (metrics) => {
    const target = modal.querySelector("[data-result-metrics]");
    target.replaceChildren();
    (metrics || []).forEach((item) => {
      const card = el("article", "tiana-analysis-metric tiana-analysis-metric--" + (item.tone || "neutral"));
      card.append(el("small", "", item.label), el("strong", "", item.value), el("span", "", item.hint || ""));
      target.appendChild(card);
    });
  };
  const renderBreakdown = (items) => {
    const target = modal.querySelector("[data-result-breakdown]");
    target.replaceChildren();
    (items || []).forEach((item) => {
      const row = el("div", "tiana-analysis-breakdown-row");
      const label = el("div", "tiana-analysis-breakdown-label");
      label.append(el("span", "", item.label), el("strong", "", item.points + "/" + item.maximum));
      const track = el("i", "tiana-analysis-breakdown-track");
      const fill = el("b");
      fill.style.width = Math.max(0, Math.min(100, Number(item.percent) || 0)) + "%";
      track.appendChild(fill);
      row.append(label, track);
      target.appendChild(row);
    });
  };
  const renderCategories = (items) => {
    const target = modal.querySelector("[data-result-categories]");
    target.replaceChildren();
    (items || []).forEach((item) => {
      const row = el("div", "tiana-analysis-bar-row");
      const label = el("div", "tiana-analysis-bar-label");
      label.append(el("strong", "", item.name), el("span", "", item.value));
      const track = el("i", "tiana-analysis-bar-track");
      const fill = el("b");
      fill.style.width = Math.max(0, Math.min(100, Number(item.percent) || 0)) + "%";
      track.appendChild(fill);
      row.append(label, track, el("small", "", item.hint || ""));
      target.appendChild(row);
    });
  };
  const renderRecords = (items) => {
    const target = modal.querySelector("[data-result-rows]");
    target.replaceChildren();
    (items || []).forEach((item) => {
      const row = el("article", "tiana-analysis-record tiana-analysis-record--" + (item.status || item.kind || "neutral"));
      const copy = el("div", "tiana-analysis-record-copy");
      copy.append(el("strong", "", item.title), el("small", "", item.subtitle || ""));
      if (item.hint) copy.append(el("p", "", item.hint));
      const right = el("div", "tiana-analysis-record-value");
      right.append(el("strong", "", item.value || ""));
      if (item.percent !== undefined && item.percent !== null) right.append(el("span", "", Math.round(Number(item.percent) || 0) + "%"));
      row.append(copy, right);
      if (item.percent !== undefined && item.percent !== null) {
        const track = el("i", "tiana-analysis-record-track");
        const fill = el("b");
        fill.style.width = Math.max(0, Math.min(100, Number(item.percent) || 0)) + "%";
        track.appendChild(fill);
        row.appendChild(track);
      }
      target.appendChild(row);
    });
  };
  const renderInsights = (insights) => {
    const observations = insights.observations || insights.reasoning || [];
    const recommendations = insights.recommendations || [];
    const goalSuggestions = insights.goal_suggestions || [];
    const alternatives = insights.alternatives || [];
    appendList(modal.querySelector("[data-result-observations]"), observations);
    appendList(modal.querySelector("[data-result-recommendations]"), recommendations);
    appendList(modal.querySelector("[data-result-alternatives]"), alternatives);
    appendList(modal.querySelector("[data-result-goal-ideas]"), goalSuggestions);
    toggleSection("[data-result-observations-section]", observations.length > 0);
    toggleSection("[data-result-recommendations-section]", recommendations.length > 0);
    toggleSection("[data-result-goals-section]", goalSuggestions.length > 0);
    toggleSection("[data-result-alternatives-section]", alternatives.length > 0);
    const encouragement = modal.querySelector("[data-result-encouragement]");
    encouragement.textContent = insights.encouragement || "";
    encouragement.hidden = !insights.encouragement;
  };
  const renderResult = (payload) => {
    const result = payload.result || {};
    const insights = payload.insights || {};
    modal.querySelector("[data-result-heading]").textContent = result.title || "Your money review";
    modal.querySelector("[data-result-subtitle]").textContent = result.subtitle || "";
    modal.querySelector("[data-result-summary]").textContent = insights.summary || result.summary || "Here is what your recorded money is showing.";
    modal.querySelector("[data-result-summary-label]").textContent = payload.ai_enhanced ? "A NOTE FROM TIANA" : "YOUR MONEY REVIEW";
    modal.querySelector("[data-result-kicker]").textContent = result.scope === "preview" ? "BEFORE YOU SAVE" : "YOUR PERSONAL MONEY REVIEW";
    const verdict = modal.querySelector("[data-result-verdict]");
    verdict.textContent = result.verdict || "";
    verdict.hidden = !result.verdict;
    verdict.className = "tiana-analysis-verdict tiana-analysis-verdict--" + String(result.verdict || "").toLowerCase();
    renderMetrics(result.metrics);
    toggleSection("[data-result-score-section]", result.score !== null && result.score !== undefined);
    if (result.score !== null && result.score !== undefined) {
      modal.querySelector("[data-result-score]").textContent = result.score + "/100";
      modal.querySelector("[data-result-score-track]").style.width = Math.max(0, Math.min(100, Number(result.score) || 0)) + "%";
      renderBreakdown(result.breakdown || []);
    }
    toggleSection("[data-result-categories-section]", (result.categories || []).length > 0);
    renderCategories(result.categories || []);
    toggleSection("[data-result-rows-section]", (result.rows || []).length > 0);
    renderRecords(result.rows || []);
    modal.querySelector("[data-result-rows-heading]").textContent = result.scope === "budgets" || result.scope === "budget"
      ? "Here's how each limit is holding up"
      : result.scope === "goals" || result.scope === "goal" ? "Your progress so far" : "Your largest recorded expenses";
    renderInsights(insights);
    modal.querySelector("[data-result-ai-status]").textContent = payload.ai_enhanced
      ? "Personalised with TIANA's AI"
      : (payload.ai_error || "Showing a clear review from your saved numbers. The AI explanation is temporarily unavailable.");
    setPanel("result");
  };
  const getAction = (trigger) => {
    if (trigger.dataset.analysisMode === "preview") {
      const form = trigger.closest("form") || document.querySelector(".transaction-refresh-form");
      const values = form ? new FormData(form) : new FormData();
      const kind = form ? form.querySelector("[name=kind]") : null;
      return {
        type: "preview",
        endpoint: trigger.dataset.analysisEndpoint || previewUrl,
        payload: {
          kind: kind ? kind.value : (values.get("kind") || "expense"),
          amount: values.get("amount") || "",
          category: values.get("category") || "General",
          description: values.get("description") || "",
          is_essential: values.get("is_essential") || false,
        },
      };
    }
    return {
      type: "insight",
      endpoint: insightUrl,
      payload: {
        scope: trigger.dataset.analysisScope || "activity",
        object_id: trigger.dataset.analysisObjectId || null,
        period: trigger.dataset.analysisPeriod || "week",
        start_date: trigger.dataset.analysisStartDate || "",
        end_date: trigger.dataset.analysisEndDate || "",
      },
    };
  };
  const requestAnalysis = async (action) => {
    pendingAction = action;
    openModal();
    setPanel("loading");
    if (requestController) requestController.abort();
    const controller = new AbortController();
    requestController = controller;
    try {
      const response = await fetch(action.endpoint, {
        method: "POST",
        credentials: "same-origin",
        signal: controller.signal,
        headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken()},
        body: JSON.stringify(action.payload),
      });
      const payload = await readJsonResponse(response);
      if (response.status === 409 && payload.personalization_required) {
        await showPersonalization(false);
        return;
      }
      if (!response.ok) throw new Error(payload.error || "TIANA couldn't complete this review just now.");
      renderResult(payload);
    } catch (error) {
      if (error.name !== "AbortError") showError(error.message);
    } finally {
      if (requestController === controller) requestController = null;
    }
  };
  const fillPersonalization = (profile) => {
    if (!profile) return;
    const form = personalizationForm;
    const selector = 'input[name="voice_style"][value="' + (profile.voice_style || "friendly") + '"]';
    const voice = form.querySelector(selector);
    if (voice) voice.checked = true;
    ["ambition", "current_stage", "desired_career", "future_vision", "why_it_matters"].forEach((key) => {
      if (form.elements[key]) form.elements[key].value = profile[key] || "";
    });
  };
  const showPersonalization = async (editing) => {
    openModal();
    setPanel("personalization");
    const heading = modal.querySelector(".tiana-analysis-personalization-intro h2");
    const paragraph = modal.querySelector(".tiana-analysis-personalization-intro p");
    heading.textContent = editing ? "Let's tune how I guide you." : "How would you like me to guide you?";
    paragraph.textContent = editing
      ? "Your money advice should sound right to you. Adjust my voice and update the future you're working towards."
      : "Money advice feels different when it understands the person behind the numbers. Tell me a little about the voice you prefer and the future you're building.";
    const save = personalizationForm.querySelector("button[type=submit]");
    save.textContent = editing ? "Save preferences" : "Save and continue →";
    if (editing) {
      try {
        const response = await fetch(personalizationUrl, {credentials: "same-origin"});
        const data = await readJsonResponse(response);
        if (response.ok) fillPersonalization(data.persona);
        else throw new Error(data.error || "Your preferences could not be loaded.");
      } catch (_) {
        // Keep the usable blank form visible if existing preferences cannot be fetched.
      }
    }
  };
  personalizationForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const save = personalizationForm.querySelector("button[type=submit]");
    save.disabled = true;
    save.textContent = "Saving…";
    const payload = Object.fromEntries(new FormData(personalizationForm).entries());
    try {
      const response = await fetch(personalizationUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken()},
        body: JSON.stringify(payload),
      });
      const data = await readJsonResponse(response);
      if (!response.ok) throw new Error(data.error || "Your preferences couldn't be saved.");
      if (pendingAction) await requestAnalysis(pendingAction);
      else closeModal();
    } catch (error) {
      showError(error.message);
    } finally {
      save.disabled = false;
      save.textContent = "Save and continue →";
    }
  });
  document.addEventListener("click", (event) => {
    const dismiss = event.target.closest("[data-analysis-dismiss]");
    if (dismiss) {
      closeModal();
      return;
    }
    const personalize = event.target.closest("[data-analysis-personalize]");
    if (personalize) {
      showPersonalization(true);
      return;
    }
    const trigger = event.target.closest("[data-analysis-open]");
    if (trigger) {
      event.preventDefault();
      if (trigger.disabled) return;
      requestAnalysis(getAction(trigger));
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.hidden) closeModal();
    if (event.key === "Tab" && !modal.hidden) {
      const focusable = Array.from(dialog.querySelectorAll("button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled])"))
        .filter((node) => !node.closest("[hidden]"));
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  });
})();