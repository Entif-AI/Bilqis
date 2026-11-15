"use strict";

const fs = require("node:fs");
const playwright = require(process.env.BILQIS_PLAYWRIGHT_MODULE || "playwright");
const chrome = process.env.BILQIS_CHROME_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const { production, fixtureSemantic } = require("./atlas-browser-data.cjs");
const { server } = require("./atlas-browser-server.cjs");

function check(condition, message) {
  if (!condition) throw new Error(message);
}

async function setDisplay(page, theme, density) {
  await page.evaluate(({ theme, density }) => {
    localStorage.setItem("bilqis.mc.theme", theme);
    localStorage.setItem("bilqis.mc.density", density);
  }, { theme, density });
  await page.reload({ waitUntil: "domcontentloaded" });
}

async function navigateAtlas(page) {
  const nav = page.locator('[data-test-id="nav-destination-atlas"]');
  await nav.waitFor();
  await nav.click();
  await page.locator('[data-test-id="atlas-tab-lookup"]').waitFor();
}

async function selectSemantic(page, semanticId) {
  await page.locator('[data-test-id="atlas-tab-lookup"]').click();
  const input = page.locator('[data-test-id="atlas-search-input"]');
  await input.fill(semanticId);
  await page.locator('[data-test-id="atlas-tab-abi"]').click();
  check(await page.evaluate(() => document.activeElement?.dataset?.testId) === "atlas-tab-abi",
    "Atlas tab activation lost keyboard focus");
  await page.locator('[data-test-id="atlas-abi-bank-input"]').fill("0");
  await page.locator('[data-test-id="atlas-abi-row-input"]').fill("1");
  await page.locator('[data-test-id="atlas-tab-lookup"]').click();
  check(await page.evaluate(() => document.activeElement?.dataset?.testId) === "atlas-tab-lookup",
    "Atlas tab return lost keyboard focus");
  check(await input.inputValue() === semanticId, "Atlas semantic query state was lost across tabs");
  await page.locator('[data-test-id="atlas-tab-abi"]').click();
  check(await page.locator('[data-test-id="atlas-abi-row-input"]').inputValue() === "1",
    "Atlas ABI row state was lost across tabs");
  await page.locator('[data-test-id="atlas-tab-lookup"]').click();
  await page.locator('[data-test-id="atlas-search-submit"]').click();
  await page.locator('[data-test-id="atlas-panel-dossier"]:not([hidden])').waitFor();
  await page.locator('[data-test-id="atlas-semantic-dossier"]').getByText(semanticId, { exact: false }).first().waitFor();
}

async function audit(page, launchMode, viewport, theme, density) {
  await page.setViewportSize(viewport);
  await setDisplay(page, theme, density);
  await navigateAtlas(page);
  await page.addScriptTag({ url: "/axe.min.js" });
  const semanticId = launchMode === "fixtures" ? fixtureSemantic : production.semantic;
  await selectSemantic(page, semanticId);
  const canonicalRows = await page.locator('[data-test-id="atlas-semantic-relation-table"] tr[data-edge-kind="canonical"]').count();
  check(canonicalRows === (launchMode === "production" ? 14 : 1),
    `${launchMode} Atlas canonical relationship volume was not rendered`);
  await page.locator('[data-test-id="atlas-lens-learned"]').click();
  await page.locator('[data-test-id="atlas-semantic-relation-table"]').waitFor();

  const result = await page.locator('[data-test-id="atlas-view"]').evaluate(async node => {
    const axeResult = await axe.run(node, {
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
    });
    const ids = [...node.querySelectorAll("[data-test-id]")].map(item => item.dataset.testId);
    return {
      violations: axeResult.violations.map(item => item.id),
      documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      tablists: node.querySelectorAll('[role="tablist"]').length,
      tabs: node.querySelectorAll('[role="tab"]').length,
      duplicateIds: ids.filter((id, index) => ids.indexOf(id) !== index),
      helpTriggers: node.querySelectorAll('[data-test-id^="atlas-help-"][data-test-id$="-trigger"]').length,
      sourceLabels: node.querySelectorAll('[data-authority="source"]').length,
      derivedLabels: node.querySelectorAll('[data-authority="derived"]').length,
      timedFacts: node.querySelectorAll("[data-source-unix-seconds]").length,
      sourceTimes: [...node.querySelectorAll("[data-source-unix-seconds]")]
        .map(item => item.getAttribute("data-source-unix-seconds")),
      text: node.innerText,
    };
  });
  check(result.violations.length === 0, `${launchMode} Atlas axe: ${JSON.stringify(result.violations)}`);
  check(!result.documentOverflow, `${launchMode} Atlas created document overflow`);
  check(result.tablists === 1 && result.tabs === 3, `${launchMode} Atlas tab hierarchy is not one three-tab set`);
  check(result.duplicateIds.length === 0, `${launchMode} Atlas duplicated test hooks: ${result.duplicateIds}`);
  check(result.helpTriggers >= 6, `${launchMode} Atlas omitted contextual help`);
  check(result.sourceLabels > 0 && result.derivedLabels > 0 && result.timedFacts > 0,
    `${launchMode} Atlas source, derived, and temporal evidence layers are not distinct`);
  check(!/\bnever\b|does not prove|does not mean|does not imply/i.test(result.text),
    `${launchMode} Atlas retained unsolicited negative-capability copy`);

  if (launchMode === "production") {
    check(result.text.includes(production.semantic), "production Atlas omitted production semantic identity");
    check(!/atlas-fixture|REFERENCE_FIXTURES|Reference fixture/i.test(result.text),
      "production Atlas rendered fixture material");
    check(result.sourceTimes.includes(String(production.materialized)),
      "production Atlas omitted authoritative materialization time");
    check(result.sourceTimes.includes(String(production.observed)),
      "production Atlas omitted authoritative observation time");
    check(result.sourceTimes.includes(String(production.sourceMaterialized)),
      "production Atlas substituted generation time for source materialization time");
    check(result.sourceTimes.includes(String(production.summaryMaterialized)),
      "production Atlas substituted dossier time for overview materialization time");
  } else {
    const badge = page.locator('[data-test-id="shell-mode-badge"]');
    check(await badge.innerText() === "REFERENCE FIXTURES", "fixture Atlas omitted persistent fixture posture");
    check(result.text.includes(fixtureSemantic), "fixture Atlas omitted intended fixture semantic surface");
    check(result.text.includes("REFERENCE FIXTURES"), "fixture Atlas omitted route-local launch posture");
  }

  if (viewport.width >= 1200) {
    await page.locator('[data-test-id="shell-rail-toggle"]').click();
    await page.locator('[data-test-id="atlas-semantic-inspect"]').click();
    const inspector = page.locator('[data-test-id="investigation-inspector"]');
    await inspector.waitFor();
    check((await inspector.innerText()).includes(semanticId), `${launchMode} Atlas inspector lost semantic identity`);
    const splitter = page.locator("#inspector-splitter");
    const before = Number(await splitter.getAttribute("aria-valuenow"));
    await splitter.focus();
    await page.keyboard.press("End");
    const after = Number(await splitter.getAttribute("aria-valuenow"));
    check(after >= before, `${launchMode} Atlas inspector resize did not use shared splitter geometry`);
    await page.locator('[data-test-id="atlas-lens-canonical"]').click();
    const overflow = await page.locator('[data-test-id="atlas-semantic-relation-table-wrap"]').evaluate(node => {
      const dossier = node.closest('[data-test-id="atlas-semantic-dossier"]');
      const wrapRect = node.getBoundingClientRect();
      const dossierRect = dossier.getBoundingClientRect();
      return {
        documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
        rowCount: node.querySelectorAll('tr[data-edge-kind="canonical"]').length,
        boundedByDossier: wrapRect.left >= dossierRect.left - 1 && wrapRect.right <= dossierRect.right + 1,
      };
    });
    check(!overflow.documentOverflow, `${launchMode} Atlas inspector resize created document overflow`);
    check(overflow.rowCount === (launchMode === "production" ? 14 : 1),
      `${launchMode} Atlas canonical relationships disappeared after inspector resize`);
    check(overflow.boundedByDossier, `${launchMode} Atlas relation table escaped the dossier after inspector resize`);
    if (launchMode === "production") {
      await page.locator('[data-test-id="atlas-tab-lookup"]').click();
      await page.locator('[data-test-id="atlas-search-input"]').fill(production.secondary);
      await page.locator('[data-test-id="atlas-search-submit"]').click();
      await page.locator('[data-test-id="atlas-panel-dossier"]:not([hidden])').waitFor();
      check((await page.locator("#inspector-title").innerText()).includes(production.secondary),
        "production Atlas inspector stayed bound to the stale semantic selection");
    }
    await page.locator("#inspector-close").click();
  }
  return result;
}

(async () => {
  const app = server();
  await new Promise(resolve => app.listen(0, "127.0.0.1", resolve));
  const port = app.address().port;
  const browser = await playwright.chromium.launch({ executablePath: chrome, headless: true });
  const results = [];
  fs.mkdirSync("output/playwright/1186", { recursive: true });
  try {
    for (const launchMode of ["production", "fixtures"]) {
      const page = await browser.newPage();
      await page.goto(`http://127.0.0.1:${port}/apps/mission-control/renderer/?launchMode=${launchMode}`, {
        waitUntil: "domcontentloaded",
      });
      for (const variant of [
        [{ width: 1440, height: 960 }, "dark", "comfortable"],
        [{ width: 1440, height: 960 }, "light", "compact"],
        [{ width: 390, height: 844 }, "light", "compact"],
      ]) {
        const audited = await audit(page, launchMode, ...variant);
        results.push({
          launchMode,
          viewport: variant[0], theme: variant[1], density: variant[2],
          ...audited,
        });
        await page.screenshot({
          path: `output/playwright/1186/after-${launchMode}-${variant[1]}-${variant[2]}-${variant[0].width}.png`,
          fullPage: true,
        });
      }
      await page.close();
    }
    fs.writeFileSync("output/playwright/1186/browser-result.json", `${JSON.stringify({ ok: true, results }, null, 2)}\n`);
    console.log(JSON.stringify({ ok: true, results }, null, 2));
  } finally {
    await browser.close();
    await new Promise(resolve => app.close(resolve));
  }
})().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
