document.addEventListener('DOMContentLoaded', () => {
  const slides = document.querySelectorAll('.slide');
  if (!slides.length) return;

  let current = 0;
  const nextButton = document.getElementById('nextSlide');
  const prevButton = document.getElementById('prevSlide');

  const showSlide = (index) => {
    slides.forEach((slide, i) => {
      slide.classList.toggle('active', i === index);
    });
  };

  nextButton?.addEventListener('click', () => {
    current = (current + 1) % slides.length;
    showSlide(current);
  });

  prevButton?.addEventListener('click', () => {
    current = (current - 1 + slides.length) % slides.length;
    showSlide(current);
  });
});
