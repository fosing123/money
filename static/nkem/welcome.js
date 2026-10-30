document.addEventListener("DOMContentLoaded", () => {
  const backButton = document.querySelector("[data-welcome-back]");
  if (!backButton) return;

  backButton.addEventListener("click", () => {
    const fallback = backButton.dataset.fallbackUrl || "/";
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.location.assign(fallback);
    }
  });
});
