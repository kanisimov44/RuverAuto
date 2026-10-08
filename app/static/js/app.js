// Интерактивность сайта: меню, тема, галерея. Без зависимостей.
// Сайт работает и без JavaScript: меню на компьютере видно всегда,
// а фото в галерее открывается обычной ссылкой.

function initNav() {
  const toggle = document.querySelector("[data-nav-toggle]");
  const nav = document.querySelector("[data-nav]");
  if (!toggle || !nav) return;

  const setOpen = (open) => {
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Закрыть меню" : "Открыть меню");
    nav.toggleAttribute("data-open", open);
  };

  toggle.addEventListener("click", () => setOpen(!nav.hasAttribute("data-open")));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && nav.hasAttribute("data-open")) {
      setOpen(false);
      toggle.focus();
    }
  });
  // При переходе на широкий экран мобильное меню закрывается
  window.matchMedia("(min-width: 960px)").addEventListener("change", () => setOpen(false));
}

function initTheme() {
  const toggle = document.querySelector("[data-theme-toggle]");
  if (!toggle) return;
  const root = document.documentElement;
  const systemDark = window.matchMedia("(prefers-color-scheme: dark)");

  const currentTheme = () => root.dataset.theme || (systemDark.matches ? "dark" : "light");

  toggle.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    try {
      localStorage.setItem("theme", next);
    } catch (e) {
      // Хранилище может быть недоступно (приватный режим): тема просто не запомнится
    }
  });
}

function initGallery(gallery) {
  const mainLink = gallery.querySelector("[data-gallery-open]");
  const mainImage = gallery.querySelector("[data-gallery-main]");
  const thumbs = [...gallery.querySelectorAll("[data-gallery-thumb]")];
  const dialog = gallery.querySelector("[data-lightbox]");
  const dialogImage = gallery.querySelector("[data-lightbox-image]");
  const counter = gallery.querySelector("[data-lightbox-counter]");
  if (!mainLink || !mainImage) return;

  const sources = thumbs.length ? thumbs.map((thumb) => thumb.dataset.src) : [mainLink.href];
  let index = 0;

  const show = (newIndex) => {
    index = (newIndex + sources.length) % sources.length;
    mainImage.src = sources[index];
    mainLink.href = sources[index];
    thumbs.forEach((thumb, i) => thumb.setAttribute("aria-current", String(i === index)));
    if (dialogImage) dialogImage.src = sources[index];
    if (counter) counter.textContent = `${index + 1} / ${sources.length}`;
  };

  thumbs.forEach((thumb, i) => thumb.addEventListener("click", () => show(i)));

  if (!dialog || typeof dialog.showModal !== "function") return;

  mainLink.addEventListener("click", (event) => {
    event.preventDefault();
    show(index);
    dialog.showModal();
    document.body.toggleAttribute("data-scroll-locked", true);
  });

  dialog.addEventListener("close", () => document.body.removeAttribute("data-scroll-locked"));
  gallery.querySelector("[data-lightbox-close]")?.addEventListener("click", () => dialog.close());
  gallery.querySelector("[data-lightbox-prev]")?.addEventListener("click", () => show(index - 1));
  gallery.querySelector("[data-lightbox-next]")?.addEventListener("click", () => show(index + 1));

  // Клик по затемнённому фону закрывает просмотр (но не завершение свайпа)
  let swiped = false;
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog && !swiped) dialog.close();
    swiped = false;
  });

  dialog.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") show(index - 1);
    if (event.key === "ArrowRight") show(index + 1);
  });

  // Свайп на телефоне
  let startX = null;
  dialog.addEventListener("pointerdown", (event) => {
    startX = event.clientX;
  });
  dialog.addEventListener("pointerup", (event) => {
    if (startX === null) return;
    const delta = event.clientX - startX;
    startX = null;
    if (Math.abs(delta) > 50 && sources.length > 1) {
      swiped = true;
      show(delta < 0 ? index + 1 : index - 1);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initNav();
  initTheme();
  document.querySelectorAll("[data-gallery]").forEach(initGallery);
});
