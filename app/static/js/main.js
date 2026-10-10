const header = document.querySelector(".header");
const progress = document.querySelector(".scroll-progress");
const menuToggle = document.querySelector(".menu-toggle");
const nav = document.querySelector(".nav");

function updateScrollUI() {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const percent = scrollable > 0 ? (window.scrollY / scrollable) * 100 : 0;
  if (progress) progress.style.width = `${percent}%`;
  if (header) header.classList.toggle("scrolled", window.scrollY > 24);
}
window.addEventListener("scroll", updateScrollUI, { passive: true });
updateScrollUI();

if (menuToggle && nav) {
  menuToggle.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    menuToggle.setAttribute("aria-expanded", String(open));
    menuToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  });
  nav.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => {
    nav.classList.remove("open");
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", "Open menu");
  }));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && nav.classList.contains("open")) {
      nav.classList.remove("open");
      menuToggle.setAttribute("aria-expanded", "false");
      menuToggle.setAttribute("aria-label", "Open menu");
      menuToggle.focus();
    }
  });
}

// Reveal sections as they enter view; falls back to visible content without IntersectionObserver.
const revealItems = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window) {
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -35px 0px" });
  revealItems.forEach((item, index) => {
    item.style.setProperty("--reveal-delay", `${(index % 3) * 85}ms`);
    revealObserver.observe(item);
  });
} else {
  revealItems.forEach((item) => item.classList.add("is-visible"));
}

// Type-and-delete hero words. Motion is disabled for reduced-motion preferences.
const typed = document.getElementById("typed-word");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (typed && !reducedMotion) {
  const words = ["insight", "momentum", "solutions", "growth"];
  let wordIndex = 0;
  let charIndex = words[0].length;
  let deleting = false;
  function typeLoop() {
    const word = words[wordIndex];
    typed.textContent = word.slice(0, charIndex);
    let delay = deleting ? 48 : 90;
    if (!deleting && charIndex === word.length) {
      deleting = true;
      delay = 1350;
    } else if (deleting && charIndex === 0) {
      deleting = false;
      wordIndex = (wordIndex + 1) % words.length;
      delay = 280;
    } else {
      charIndex += deleting ? -1 : 1;
    }
    window.setTimeout(typeLoop, delay);
  }
  window.setTimeout(typeLoop, 1100);
}

// Gentle pointer tilt on desktop only.
const canHover = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
if (canHover && !reducedMotion) {
  const hero = document.querySelector(".hero");
  const heroAmbience = document.querySelector(".hero-ambience");
  if (hero && heroAmbience) {
    let pointerFrame = 0;
    let pointerEvent;
    hero.addEventListener("pointermove", (event) => {
      pointerEvent = event;
      if (pointerFrame) return;
      pointerFrame = window.requestAnimationFrame(() => {
        const rect = hero.getBoundingClientRect();
        heroAmbience.style.setProperty("--pointer-x", `${pointerEvent.clientX - rect.left}px`);
        heroAmbience.style.setProperty("--pointer-y", `${pointerEvent.clientY - rect.top}px`);
        pointerFrame = 0;
      });
    });
    hero.addEventListener("pointerleave", () => {
      heroAmbience.style.removeProperty("--pointer-x");
      heroAmbience.style.removeProperty("--pointer-y");
    });
  }

  document.querySelectorAll(".project-card").forEach((card) => {
    card.addEventListener("pointermove", (event) => {
      const rect = card.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;
      card.style.setProperty("--tilt-x", `${-y * 2.5}deg`);
      card.style.setProperty("--tilt-y", `${x * 2.5}deg`);
      card.style.setProperty("--pointer-x", `${event.clientX - rect.left}px`);
      card.style.setProperty("--pointer-y", `${event.clientY - rect.top}px`);
    });
    card.addEventListener("pointerleave", () => {
      card.style.setProperty("--tilt-x", "0deg");
      card.style.setProperty("--tilt-y", "0deg");
      card.style.removeProperty("--pointer-x");
      card.style.removeProperty("--pointer-y");
    });
  });
}

// Expand the gallery on demand to keep the first view focused.
const showProjectsButton = document.getElementById("show-all-projects");
if (showProjectsButton) {
  showProjectsButton.addEventListener("click", () => {
    const expanded = showProjectsButton.getAttribute("aria-expanded") === "true";
    const nextExpanded = !expanded;
    showProjectsButton.setAttribute("aria-expanded", String(nextExpanded));
    showProjectsButton.innerHTML = nextExpanded
      ? 'Show fewer projects <span>−</span>'
      : 'Show all projects <span>＋</span>';
    document.querySelectorAll(".extra-project").forEach((card) => {
      card.classList.toggle("project-expanded", nextExpanded);
      if (nextExpanded) card.classList.add("is-visible");
    });
  });
}


// Accessible client-side project filters. No third-party scripts or tracking required.
const filterButtons = document.querySelectorAll("[data-filter]");
const projectCards = document.querySelectorAll("#project-grid .project-card");
const filterStatus = document.getElementById("project-filter-status");
if (filterButtons.length && projectCards.length) {
  filterButtons.forEach((button) => button.addEventListener("click", () => {
    const filter = button.dataset.filter;
    let visible = 0;
    filterButtons.forEach((item) => {
      const active = item === button;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-pressed", String(active));
    });
    projectCards.forEach((card) => {
      const matches = filter === "all" || (card.dataset.categories || "").split(/\s+/).includes(filter);
      card.classList.toggle("filter-hidden", !matches);
      card.classList.toggle("project-expanded", matches);
      if (matches) {
        visible += 1;
        card.classList.add("is-visible");
      }
    });
    if (filterStatus) filterStatus.textContent = `Showing ${visible} project${visible === 1 ? "" : "s"}${filter === "all" ? " across all categories" : ` in ${button.textContent.trim().replace(/\s+\d+$/, "")}`}.`;
    if (showProjectsButton) {
      const allVisible = filter === "all";
      showProjectsButton.setAttribute("aria-expanded", String(allVisible));
      showProjectsButton.innerHTML = allVisible ? 'Show fewer projects <span>−</span>' : 'Show all projects <span>＋</span>';
      document.querySelectorAll(".extra-project").forEach((card) => card.classList.toggle("project-expanded", allVisible));
    }
  }));
}

// Curated, profile-grounded answers; intentionally offline and not represented as a generative AI model.
const quickAnswers = {
  focus: { title: "Roles I'm targeting", text: "I'm targeting SEO and search strategy roles, marketing/SEO analyst roles, and junior data analyst or entry-level data science opportunities where I can combine business context with analytical problem-solving." },
  projects: { title: "Projects worth reviewing", text: "Start with SEO AI Intelligence for search and applied AI, Repo Doctor AI for developer tooling, Bank Customer Churn for supervised learning, and Mega Market Sales Dashboard for business analytics. Each project links to its public repository." },
  services: { title: "Ways I can help", text: "Potential project areas include technical/local SEO reviews, marketing performance reporting, data cleaning and dashboards, SQL analysis, and scoped Python prototypes. We should agree on deliverables and success criteria before work begins." },
  approach: { title: "My project approach", text: "Clarify the business question, inspect the available data or code, establish a baseline, document assumptions, validate results, and communicate limitations with practical next steps. I distinguish learning projects from verified client outcomes." }
};
const quickQuestionButtons = document.querySelectorAll("[data-answer]");
const answerTitle = document.getElementById("quick-answer-title");
const answerText = document.getElementById("quick-answer-text");
const answerKicker = document.querySelector(".answer-kicker");
quickQuestionButtons.forEach((button, index) => button.addEventListener("click", () => {
  const answer = quickAnswers[button.dataset.answer];
  if (!answer || !answerTitle || !answerText) return;
  quickQuestionButtons.forEach((item) => {
    const active = item === button;
    item.classList.toggle("is-active", active);
    item.setAttribute("aria-pressed", String(active));
  });
  answerTitle.textContent = answer.title;
  answerText.textContent = answer.text;
  if (answerKicker) answerKicker.textContent = `PORTFOLIO GUIDE / ${String(index + 1).padStart(2, "0")}`;
}));
