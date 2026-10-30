document.addEventListener("DOMContentLoaded", () => {
  const backButton = document.querySelector("[data-welcome-back]");
  if (!backButton) return;

  backButton.addEventListener("click", () => {
    const fallback = backButton.dataset.fallbackUrl || "/";
    window.location.assign(fallback);
  });
});
