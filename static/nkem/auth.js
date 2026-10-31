document.addEventListener("click", (event) => {
  const toggle = event.target.closest("[data-password-toggle]");
  if (!toggle) return;
  const wrap = toggle.closest(".tiana-password-wrap");
  const input = wrap && wrap.querySelector("input");
  if (!input) return;
  const reveal = input.type === "password";
  input.type = reveal ? "text" : "password";
  toggle.textContent = reveal ? "Hide" : "Show";
  toggle.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
  toggle.setAttribute("aria-pressed", reveal ? "true" : "false");
});
