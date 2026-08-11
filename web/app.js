(() => {
  "use strict";

  const root = document.documentElement;
  const params = new URLSearchParams(location.search);
  const langButtons = [...document.querySelectorAll("[data-set-lang]")];
  const pathButtons = [...document.querySelectorAll("[data-reading-path]")];
  const countSelect = document.querySelector("#player-count");
  const thresholds = JSON.parse(document.querySelector("#threshold-data").textContent);
  const strings = JSON.parse(document.querySelector("#ui-data").textContent);
  const glossary = JSON.parse(document.querySelector("#glossary-data").textContent);
  const termTip = document.querySelector("#term-tip");
  let sectionObserver = null;
  let printDetailState = [];
  let activeTerm = null;
  let pinnedTerm = false;
  let hoverTimer = null;
  let suppressNextTermFocus = false;

  function currentLanguage() {
    return root.dataset.lang || "ua";
  }

  function updateChrome(language) {
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      const value = strings[language][node.dataset.i18n];
      if (value) node.textContent = value;
    });
    document.querySelectorAll("[data-i18n-label]").forEach((node) => {
      const value = strings[language][node.dataset.i18nLabel];
      if (!value) return;
      node.setAttribute("aria-label", value);
      node.setAttribute("title", value);
    });
  }

  function positionTooltip(trigger) {
    const margin = 12;
    const gap = 9;
    const triggerRect = trigger.getBoundingClientRect();
    const tipRect = termTip.getBoundingClientRect();
    let left = triggerRect.left + triggerRect.width / 2 - tipRect.width / 2;
    left = Math.max(margin, Math.min(left, window.innerWidth - tipRect.width - margin));
    let top = triggerRect.bottom + gap;
    let placement = "below";
    if (top + tipRect.height > window.innerHeight - margin) {
      top = triggerRect.top - tipRect.height - gap;
      placement = "above";
    }
    top = Math.max(margin, Math.min(top, window.innerHeight - tipRect.height - margin));
    termTip.style.left = `${Math.round(left)}px`;
    termTip.style.top = `${Math.round(top)}px`;
    termTip.dataset.placement = placement;
  }

  function showTerm(trigger, pin = false) {
    clearTimeout(hoverTimer);
    if (activeTerm && activeTerm !== trigger) {
      activeTerm.setAttribute("aria-expanded", "false");
      activeTerm.removeAttribute("aria-describedby");
    }
    const entry = glossary[currentLanguage()][trigger.dataset.term];
    if (!entry) return;
    activeTerm = trigger;
    pinnedTerm = pin;
    termTip.replaceChildren();
    const title = document.createElement("strong");
    title.textContent = entry.term;
    const copy = document.createElement("span");
    copy.textContent = entry.definition;
    termTip.append(title, copy);
    termTip.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
    trigger.setAttribute("aria-describedby", "term-tip");
    requestAnimationFrame(() => positionTooltip(trigger));
  }

  function hideTerm(force = false) {
    clearTimeout(hoverTimer);
    if (pinnedTerm && !force) return;
    activeTerm?.setAttribute("aria-expanded", "false");
    activeTerm?.removeAttribute("aria-describedby");
    activeTerm = null;
    pinnedTerm = false;
    termTip.hidden = true;
  }

  function bindScrollSpy(language) {
    sectionObserver?.disconnect();
    if (!("IntersectionObserver" in window)) return;
    const sections = [
      ...document.querySelectorAll(`[data-lang-panel][data-lang="${language}"] .rule-section`),
    ];
    const links = [
      ...document.querySelectorAll(
        `.toc[data-lang="${language}"] a[data-section-link]`
      ),
    ];
    sectionObserver = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((entry) => entry.isIntersecting).at(-1);
        if (!visible) return;
        links.forEach((link) => {
          link.classList.toggle(
            "is-current",
            link.dataset.sectionLink === visible.target.dataset.section
          );
        });
      },
      { rootMargin: "-20% 0px -70% 0px" }
    );
    sections.forEach((section) => sectionObserver.observe(section));
  }

  function setLanguage(language) {
    const lang = language === "en" ? "en" : "ua";
    root.dataset.lang = lang;
    root.lang = lang === "ua" ? "uk" : "en";
    localStorage.setItem("dark-council-language", lang);
    document.querySelectorAll("[data-lang-panel]").forEach((panel) => {
      panel.hidden = panel.dataset.lang !== lang;
    });
    updateChrome(lang);
    langButtons.forEach((button) => {
      const selected = button.dataset.setLang === lang;
      button.classList.toggle("is-active", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
    document.title = lang === "ua" ? "Темна Рада — правила" : "The Dark Council — Rules";
    hideTerm(true);
    bindScrollSpy(lang);
    updateThresholds();
  }

  function updateThresholds() {
    const count = String(countSelect.value);
    const data = thresholds[count];
    if (!data) return;
    root.dataset.playerCount = count;
    document.querySelectorAll("[data-selected-player-count]").forEach((node) => {
      node.textContent = count;
    });
    document.querySelectorAll("[data-threshold]").forEach((node) => {
      node.textContent = data[node.dataset.threshold];
    });
    document
      .querySelectorAll('.rule-section[data-section="12"] table:first-of-type tbody tr')
      .forEach((row) => {
        row.classList.toggle(
          "is-selected-count",
          row.cells[0]?.textContent.trim() === count
        );
      });
    localStorage.setItem("dark-council-player-count", count);
  }

  function openAndScroll(target, behavior = "smooth") {
    if (!target) return;
    const collapsible = target.matches("details") ? target : target.closest("details");
    if (collapsible) collapsible.open = true;
    target.scrollIntoView({ behavior, block: "start" });
  }

  function setReadingPath(path) {
    root.dataset.path = path;
    pathButtons.forEach((button) => {
      const selected = button.dataset.readingPath === path;
      button.classList.toggle("is-active", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
    const number = path === "syndicate" ? 11 : path === "gm" ? 12 : 0;
    openAndScroll(document.querySelector(`#${currentLanguage()}-section-${number}`));
  }

  document.addEventListener("click", (event) => {
    const term = event.target.closest(".term-ref");
    if (term) {
      event.preventDefault();
      if (activeTerm === term && pinnedTerm) {
        hideTerm(true);
      } else {
        showTerm(term, true);
      }
      return;
    }
    if (activeTerm) hideTerm(true);

    const language = event.target.closest("[data-set-lang]");
    if (language) {
      setLanguage(language.dataset.setLang);
      return;
    }

    const path = event.target.closest("[data-reading-path]");
    if (path) {
      setReadingPath(path.dataset.readingPath);
      return;
    }

    const tocLink = event.target.closest(".toc a[data-section-link]");
    if (tocLink) {
      event.preventDefault();
      openAndScroll(document.querySelector(tocLink.getAttribute("href")));
      history.replaceState(null, "", tocLink.getAttribute("href"));
      return;
    }

    if (event.target.closest("#theme-toggle")) {
      const next = root.dataset.theme === "light" ? "dark" : "light";
      root.dataset.theme = next;
      localStorage.setItem("dark-council-theme", next);
    }

    const print = event.target.closest("[data-print]");
    if (print) {
      root.dataset.print = print.dataset.print;
      window.print();
    }
  });

  document.addEventListener("pointerover", (event) => {
    const trigger = event.target.closest(".term-ref");
    if (!trigger || pinnedTerm || event.pointerType === "touch") return;
    clearTimeout(hoverTimer);
    hoverTimer = setTimeout(() => showTerm(trigger), 120);
  });
  document.addEventListener("pointerout", (event) => {
    const trigger = event.target.closest(".term-ref");
    if (!trigger || pinnedTerm || trigger.contains(event.relatedTarget)) return;
    clearTimeout(hoverTimer);
    hoverTimer = setTimeout(() => hideTerm(), 90);
  });
  document.addEventListener("focusin", (event) => {
    const trigger = event.target.closest(".term-ref");
    if (trigger && suppressNextTermFocus) {
      suppressNextTermFocus = false;
      return;
    }
    if (trigger) showTerm(trigger);
  });
  document.addEventListener("focusout", (event) => {
    if (event.target.closest(".term-ref") && !pinnedTerm) hideTerm();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && activeTerm) {
      const trigger = activeTerm;
      hideTerm(true);
      if (document.activeElement !== trigger) {
        suppressNextTermFocus = true;
        trigger.focus();
      }
    }
  });
  window.addEventListener(
    "scroll",
    () => {
      if (activeTerm && activeTerm === document.activeElement && !pinnedTerm) {
        requestAnimationFrame(() => positionTooltip(activeTerm));
      } else {
        hideTerm(true);
      }
    },
    { passive: true }
  );
  window.addEventListener("resize", () => {
    if (activeTerm) positionTooltip(activeTerm);
  });

  countSelect.addEventListener("change", updateThresholds);
  window.addEventListener("beforeprint", () => {
    printDetailState = [
      ...document.querySelectorAll(
        `[data-lang-panel][data-lang="${currentLanguage()}"] details`
      ),
    ].map((details) => [details, details.open]);
    printDetailState.forEach(([details]) => {
      details.open = true;
    });
  });
  window.addEventListener("afterprint", () => {
    printDetailState.forEach(([details, wasOpen]) => {
      details.open = wasOpen;
    });
    printDetailState = [];
    delete root.dataset.print;
  });

  const initialLanguage =
    params.get("lang") || localStorage.getItem("dark-council-language") || "ua";
  const savedCount = localStorage.getItem("dark-council-player-count");
  if (savedCount && thresholds[savedCount]) countSelect.value = savedCount;
  root.dataset.theme = localStorage.getItem("dark-council-theme") || "dark";
  setLanguage(initialLanguage);

  const initialHash = location.hash && document.querySelector(location.hash);
  if (initialHash) openAndScroll(initialHash, "auto");
})();
