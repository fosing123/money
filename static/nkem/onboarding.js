document.addEventListener("DOMContentLoaded", () => {
  const slides = Array.from(document.querySelectorAll("[data-onboarding-slide]"));
  if (!slides.length) return;

  const dots = Array.from(document.querySelectorAll("[data-onboarding-dot]"));
  const back = document.querySelector("[data-onboarding-back]");
  const next = document.querySelector("[data-onboarding-next]");
  const nextLabel = document.querySelector("[data-onboarding-next-label]");
  const skip = document.querySelector(".onboarding-skip");
  const stage = document.querySelector("[data-onboarding-stage]");
  const finishUrl = skip ? skip.href : "/register/";

  let index = 0;
  let startX = 0;
  let startY = 0;

  const render = target => {
    index = Math.max(0, Math.min(slides.length - 1, target));

    slides.forEach((slide, i) => {
      const active = i === index;
      slide.classList.toggle("is-active", active);
      slide.setAttribute("aria-hidden", active ? "false" : "true");
    });

    dots.forEach((dot, i) => {
      const active = i === index;
      dot.classList.toggle("is-active", active);
      dot.setAttribute("aria-pressed", active ? "true" : "false");
    });

    if (back) {
      back.hidden = index === 0;
      back.disabled = index === 0;
    }

    const isLast = index === slides.length - 1;
    if (nextLabel) nextLabel.textContent = isLast ? "Get started" : "Next";
    if (next) {
      next.setAttribute(
        "aria-label",
        isLast ? "Create your TIANA account" : "Go to the next onboarding slide"
      );
    }
  };

  next?.addEventListener("click", () => {
    if (index === slides.length - 1) {
      window.location.assign(finishUrl);
      return;
    }
    render(index + 1);
  });

  back?.addEventListener("click", () => {
    if (index > 0) render(index - 1);
  });

  dots.forEach((dot, i) => {
    dot.addEventListener("click", () => render(i));
  });

  stage?.addEventListener("touchstart", event => {
    const touch = event.changedTouches[0];
    startX = touch.clientX;
    startY = touch.clientY;
  }, { passive: true });

  stage?.addEventListener("touchend", event => {
    const touch = event.changedTouches[0];
    const deltaX = touch.clientX - startX;
    const deltaY = touch.clientY - startY;

    if (Math.abs(deltaX) > 44 && Math.abs(deltaX) > Math.abs(deltaY) * 1.25) {
      render(index + (deltaX < 0 ? 1 : -1));
    }
  }, { passive: true });

  stage?.addEventListener("keydown", event => {
    if (event.key === "ArrowRight") render(index + 1);
    if (event.key === "ArrowLeft") render(index - 1);
  });

  render(0);
});
