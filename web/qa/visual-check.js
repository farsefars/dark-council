const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const puppeteer = require("puppeteer-core");

const edge = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const pageFile = path.resolve(__dirname, "..", "dist", "index.html");
const outputDir = path.resolve(__dirname, "screenshots");
const viewports = [
  { name: "desktop", width: 1440, height: 1000 },
  { name: "tablet", width: 900, height: 900 },
  { name: "mobile", width: 390, height: 844 },
];

async function inspect(page, language, viewport) {
  await page.emulateMediaType("screen");
  await page.setViewport(viewport);
  const url = `${pathToFileURL(pageFile).href}?lang=${language}`;
  await page.goto(url, { waitUntil: "load" });
  await page.waitForFunction(
    (lang) => document.documentElement.dataset.lang === lang,
    {},
    language
  );

  const state = await page.evaluate((lang) => {
    const visible = (element) => {
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return !element.hidden && style.display !== "none" && style.visibility !== "hidden"
        && rect.width > 0 && rect.height > 0;
    };
    const shell = document.querySelector(".page-shell");
    const activeToc = document.querySelector(`.toc[data-lang="${lang}"]`);
    const main = document.querySelector(".main-column");
    const firstPathButton = document.querySelector(".path-button");
    const gameArc = document.querySelector(`.diagrams[data-lang="${lang}"] .game-arc`);
    const setupSummary = document.querySelector(".setup-summary");
    const visibleShellChildren = [...shell.children].filter(visible);
    return {
      language: document.documentElement.dataset.lang,
      visibleH1: [...document.querySelectorAll("h1")].filter(visible).length,
      visibleToc: [...document.querySelectorAll(".toc")].filter(visible).length,
      activePanels: [...document.querySelectorAll(`[data-lang-panel][data-lang="${lang}"]`)]
        .filter(visible).length,
      foreignPanels: [...document.querySelectorAll(`[data-lang-panel]:not([data-lang="${lang}"])`)]
        .filter(visible).length,
      shellChildren: visibleShellChildren.length,
      tocWidth: activeToc.getBoundingClientRect().width,
      mainWidth: main.getBoundingClientRect().width,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      rulesBeforeDiagrams:
        document.querySelector(`#${lang}-section-0`).compareDocumentPosition(
          document.querySelector(`#diagrams-${lang}`)
        ) & Node.DOCUMENT_POSITION_FOLLOWING,
      pathButtonHeight: firstPathButton.getBoundingClientRect().height,
      gameArcColumns: getComputedStyle(gameArc).gridTemplateColumns.split(" ").length,
      setupColumns: getComputedStyle(setupSummary).gridTemplateColumns.split(" ").length,
    };
  }, language);

  assert.equal(state.language, language);
  assert.equal(state.visibleH1, 1, `${viewport.name}/${language}: one visible h1`);
  assert.equal(state.visibleToc, 1, `${viewport.name}/${language}: one visible TOC`);
  assert.equal(state.activePanels, 5, `${viewport.name}/${language}: five active language panels`);
  assert.equal(state.foreignPanels, 0, `${viewport.name}/${language}: no foreign panels`);
  assert.equal(state.shellChildren, 2, `${viewport.name}/${language}: TOC + main only`);
  assert.ok(state.rulesBeforeDiagrams, `${viewport.name}/${language}: rules must precede diagrams`);
  assert.ok(state.overflow <= 0, `${viewport.name}/${language}: horizontal overflow ${state.overflow}px`);
  if (viewport.width >= 1088) {
    assert.ok(state.mainWidth > state.tocWidth * 3, `${viewport.name}/${language}: main is not wider`);
  }
  if (viewport.width <= 390) {
    assert.ok(state.pathButtonHeight >= 44, `${viewport.name}/${language}: touch target too small`);
    assert.equal(state.gameArcColumns, 1, `${viewport.name}/${language}: game arc must be one column`);
    assert.equal(state.setupColumns, 2, `${viewport.name}/${language}: setup summary must be two columns`);
  }

  const tocLinks = await page.$$eval(
    `.toc[data-lang="${language}"] a[data-section-link]`,
    (links) => links.map((link) => ({ href: link.getAttribute("href"), section: link.dataset.sectionLink }))
  );
  assert.equal(tocLinks.length, 13);

  for (const { href, section } of tocLinks) {
    await page.click(`.toc[data-lang="${language}"] a[href="${href}"]`);
    await page.waitForFunction(
      (targetSelector) => {
        const target = document.querySelector(targetSelector);
        const topbar = document.querySelector(".topbar").getBoundingClientRect().height;
        const top = target.getBoundingClientRect().top;
        return top >= topbar - 8 && top < topbar + 110;
      },
      { timeout: 12000 },
      href
    );
    const landing = await page.evaluate(
      ({ targetSelector, sectionNumber }) => {
        const target = document.querySelector(targetSelector);
        const topbar = document.querySelector(".topbar").getBoundingClientRect().height;
        return {
          top: target.getBoundingClientRect().top,
          open: target.matches("details") ? target.open : true,
          hash: location.hash,
          expected: targetSelector,
          topbar,
          section: sectionNumber,
        };
      },
      { targetSelector: href, sectionNumber: section }
    );
    assert.ok(landing.open, `${viewport.name}/${language}: §${section} did not open`);
    assert.equal(landing.hash, landing.expected, `${viewport.name}/${language}: §${section} hash`);
    assert.ok(
      landing.top >= landing.topbar - 8 && landing.top < landing.topbar + 110,
      `${viewport.name}/${language}: §${section} landed at ${landing.top}px`
    );
  }

  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: path.join(outputDir, `${viewport.name}-${language}.png`),
    fullPage: true,
  });
}

async function inspectPrint(page, language) {
  await page.setViewport({ width: 1440, height: 1000 });
  await page.goto(`${pathToFileURL(pageFile).href}?lang=${language}`, { waitUntil: "load" });
  await page.evaluate(() => window.dispatchEvent(new Event("beforeprint")));
  await page.emulateMediaType("print");
  const state = await page.evaluate((lang) => {
    const visible = (element) => {
      const style = getComputedStyle(element);
      return !element.hidden && style.display !== "none" && style.visibility !== "hidden";
    };
    return {
      activeRulebook: visible(document.querySelector(`.rulebook[data-lang="${lang}"]`)),
      foreignRulebooks: [...document.querySelectorAll(`.rulebook:not([data-lang="${lang}"])`)]
        .filter(visible).length,
      publicBodies: [...document.querySelectorAll(
        `.rulebook[data-lang="${lang}"] .section-collapse > .collapsed-rule-body`
      )].filter(visible).length,
      openDetails: [...document.querySelectorAll(
        `[data-lang-panel][data-lang="${lang}"] details`
      )].filter((details) => details.open).length,
      quickReferences: [...document.querySelectorAll(".quick-reference")].filter(visible).length,
      tooltipVisible: visible(document.querySelector("#term-tip")),
    };
  }, language);
  assert.equal(state.activeRulebook, true, `print/${language}: active rulebook`);
  assert.equal(state.foreignRulebooks, 0, `print/${language}: no foreign rulebook`);
  assert.equal(state.publicBodies, 2, `print/${language}: public collapsed bodies print`);
  assert.equal(state.openDetails, 4, `print/${language}: every rules detail opens`);
  assert.equal(state.quickReferences, 0, `print/${language}: normal print excludes quick reference`);
  assert.equal(state.tooltipVisible, false, `print/${language}: tooltip chrome is hidden`);
  await page.screenshot({
    path: path.join(outputDir, `print-${language}.png`),
    fullPage: true,
  });
  await page.evaluate(() => window.dispatchEvent(new Event("afterprint")));
  await page.emulateMediaType("screen");
}

async function inspectControls(page) {
  await page.emulateMediaType("screen");
  await page.setViewport({ width: 1440, height: 1000 });
  await page.goto(`${pathToFileURL(pageFile).href}?lang=ua`, { waitUntil: "load" });

  await page.click('[data-set-lang="en"]');
  await page.waitForFunction(() => document.documentElement.dataset.lang === "en");
  let state = await page.evaluate(() => ({
    heading: document.querySelector('.hero:not([hidden]) h1')?.textContent.trim(),
    uaVisible: [...document.querySelectorAll('[data-lang-panel][data-lang="ua"]')]
      .filter((node) => !node.hidden).length,
    enVisible: [...document.querySelectorAll('[data-lang-panel][data-lang="en"]')]
      .filter((node) => !node.hidden).length,
  }));
  assert.equal(state.heading, "The Dark Council");
  assert.equal(state.uaVisible, 0);
  assert.equal(state.enVisible, 5);

  for (const [pathName, section] of [["syndicate", 11], ["gm", 12]]) {
    await page.click(`[data-reading-path="${pathName}"]`);
    await page.waitForFunction(
      (selector) => {
        const target = document.querySelector(selector);
        const topbar = document.querySelector(".topbar").getBoundingClientRect().height;
        const top = target.getBoundingClientRect().top;
        return target.open && top >= topbar - 8 && top < topbar + 110;
      },
      { timeout: 12000 },
      `#en-section-${section}`
    );
  }

  await page.click('[data-set-lang="ua"]');
  await page.waitForFunction(() => document.documentElement.dataset.lang === "ua");
  state = await page.evaluate(() => ({
    heading: document.querySelector('.hero:not([hidden]) h1')?.textContent.trim(),
    uaVisible: [...document.querySelectorAll('[data-lang-panel][data-lang="ua"]')]
      .filter((node) => !node.hidden).length,
    enVisible: [...document.querySelectorAll('[data-lang-panel][data-lang="en"]')]
      .filter((node) => !node.hidden).length,
  }));
  assert.equal(state.heading, "Темна Рада");
  assert.equal(state.uaVisible, 5);
  assert.equal(state.enVisible, 0);
}

async function inspectPlayerCount(page) {
  await page.emulateMediaType("screen");
  await page.setViewport({ width: 1440, height: 1000 });
  await page.goto(`${pathToFileURL(pageFile).href}?lang=ua`, { waitUntil: "load" });

  async function selectAndRead(count) {
    await page.select("#player-count", String(count));
    await page.waitForFunction(
      (expected) => document.documentElement.dataset.playerCount === expected,
      {},
      String(count)
    );
    return page.evaluate(() => {
      const selected = document.querySelector(
        '.rulebook[data-lang="ua"] .rule-section[data-section="12"] tr.is-selected-count'
      );
      return {
        count: document.querySelector("[data-selected-player-count]").textContent.trim(),
        factions: document.querySelector('.setup-summary [data-threshold="factions"]').textContent.trim(),
        magnates: document.querySelector('.setup-summary [data-threshold="magnates"]').textContent.trim(),
        magnateThreshold: document.querySelector(
          '.setup-summary [data-threshold="magnateThreshold"]'
        ).textContent.trim(),
        syndicateThreshold: document.querySelector(
          '.setup-summary [data-threshold="syndicateThreshold"]'
        ).textContent.trim(),
        selectedRow: selected?.cells[0]?.textContent.trim(),
      };
    });
  }

  assert.deepEqual(await selectAndRead(10), {
    count: "10",
    factions: "4 / 4",
    magnates: "2",
    magnateThreshold: "16",
    syndicateThreshold: "42",
    selectedRow: "10",
  });
  assert.deepEqual(await selectAndRead(15), {
    count: "15",
    factions: "6 / 6",
    magnates: "3",
    magnateThreshold: "24",
    syndicateThreshold: "39",
    selectedRow: "15",
  });
}

async function inspectTooltips(page) {
  await page.emulateMediaType("screen");
  await page.setViewport({ width: 1440, height: 1000 });
  await page.goto(`${pathToFileURL(pageFile).href}?lang=ua`, { waitUntil: "load" });

  const first = '.rulebook[data-lang="ua"] .term-ref';
  await page.$eval(first, (node) => node.scrollIntoView({ block: "center" }));
  await new Promise((resolve) => setTimeout(resolve, 700));
  await page.$eval(first, (node) => {
    node.dispatchEvent(new PointerEvent("pointerover", { bubbles: true, pointerType: "mouse" }));
  });
  await page.waitForFunction(() => !document.querySelector("#term-tip").hidden);
  let state = await page.evaluate((selector) => {
    const trigger = document.querySelector(selector);
    const tip = document.querySelector("#term-tip");
    const rect = tip.getBoundingClientRect();
    return {
      expanded: trigger.getAttribute("aria-expanded"),
      described: trigger.getAttribute("aria-describedby"),
      left: rect.left,
      right: rect.right,
      top: rect.top,
      bottom: rect.bottom,
      width: innerWidth,
      height: innerHeight,
      text: tip.textContent,
    };
  }, first);
  assert.equal(state.expanded, "true");
  assert.equal(state.described, "term-tip");
  assert.ok(state.text.length > 20);
  assert.ok(state.left >= 0 && state.right <= state.width);
  assert.ok(state.top >= 0 && state.bottom <= state.height);

  await page.keyboard.press("Escape");
  await page.waitForFunction(() => document.querySelector("#term-tip").hidden);
  await page.$$eval(
    '.rulebook[data-lang="ua"] .term-ref',
    (nodes) => nodes[1].focus({ preventScroll: true })
  );
  await new Promise((resolve) => setTimeout(resolve, 200));
  const focusState = await page.evaluate(() => ({
    hidden: document.querySelector("#term-tip").hidden,
    activeClass: document.activeElement?.className,
    expanded: document.activeElement?.getAttribute("aria-expanded"),
  }));
  assert.equal(focusState.hidden, false, `focus tooltip state: ${JSON.stringify(focusState)}`);
  await page.keyboard.press("Escape");
  await page.waitForFunction(() => document.querySelector("#term-tip").hidden);

  await page.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
  await page.goto(`${pathToFileURL(pageFile).href}?lang=ua`, { waitUntil: "load" });
  await page.$eval(first, (node) => node.scrollIntoView({ block: "center" }));
  await new Promise((resolve) => setTimeout(resolve, 700));
  await page.click(first);
  await page.waitForFunction(() => !document.querySelector("#term-tip").hidden);
  state = await page.evaluate(() => {
    const rect = document.querySelector("#term-tip").getBoundingClientRect();
    return { left: rect.left, right: rect.right, width: innerWidth };
  });
  assert.ok(state.left >= 0 && state.right <= state.width, "mobile tooltip must be clamped");
  await page.screenshot({
    path: path.join(outputDir, "tooltip-mobile-ua.png"),
    fullPage: false,
  });
  await page.mouse.click(4, 400);
  await page.waitForFunction(() => document.querySelector("#term-tip").hidden);
}

(async () => {
  assert.ok(fs.existsSync(edge), `Edge not found at ${edge}`);
  assert.ok(fs.existsSync(pageFile), `Generated page not found at ${pageFile}`);
  fs.mkdirSync(outputDir, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: edge,
    headless: true,
    args: ["--allow-file-access-from-files", "--disable-gpu", "--no-first-run"],
  });
  try {
    const page = await browser.newPage();
    const browserErrors = [];
    page.on("pageerror", (error) => browserErrors.push(String(error)));
    for (const viewport of viewports) {
      for (const language of ["ua", "en"]) {
        await inspect(page, language, viewport);
        console.log(`PASS ${viewport.name} ${language}`);
      }
    }
    for (const language of ["ua", "en"]) {
      await inspectPrint(page, language);
      console.log(`PASS print ${language}`);
    }
    await inspectControls(page);
    console.log("PASS language and reading-path controls");
    await inspectPlayerCount(page);
    console.log("PASS player-count setup summary and GM table selection");
    await inspectTooltips(page);
    console.log("PASS tooltip hover, focus, tap, Escape and viewport clamping");
    assert.deepEqual(browserErrors, [], `Browser errors: ${browserErrors.join("\n")}`);
  } finally {
    await browser.close();
  }
  console.log(`Screenshots: ${outputDir}`);
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
