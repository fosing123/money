(() => {
  const search = document.querySelector("[data-learn-search]");
  const cards = Array.from(document.querySelectorAll("[data-learn-card]"));
  const filters = Array.from(document.querySelectorAll("[data-learn-filter]"));
  const empty = document.querySelector("[data-learn-empty]");
  if (!cards.length) return;

  let activeCategory = "all";
  const normalise = (value) => (value || "").toLocaleLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

  const applyFilters = () => {
    const query = normalise(search ? search.value.trim() : "");
    let visible = 0;
    cards.forEach((card) => {
      const matchesCategory = activeCategory === "all" || card.dataset.category === activeCategory;
      const matchesQuery = !query || normalise(card.dataset.search).includes(query);
      const show = matchesCategory && matchesQuery;
      card.hidden = !show;
      if (show) visible += 1;
    });
    if (empty) empty.hidden = visible !== 0;
  };

  filters.forEach((button) => {
    button.addEventListener("click", () => {
      activeCategory = button.dataset.learnFilter || "all";
      filters.forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
      applyFilters();
    });
  });
  if (search) search.addEventListener("input", applyFilters);
})();
