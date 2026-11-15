"use strict";

const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const repo = path.resolve(__dirname, "../../../..");
const renderer = path.join(repo, "apps/mission-control/renderer");
const playwright = require(process.env.BILQIS_PLAYWRIGHT_MODULE || "playwright");
const axePath = process.env.BILQIS_AXE_MODULE || require.resolve("axe-core/axe.min.js");
const chrome = process.env.BILQIS_CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const operator = JSON.parse(fs.readFileSync(path.join(repo,
  "apps/mission-control/fixtures/operator-view-v1.json"), "utf8"));
const mime = { ".html": "text/html", ".mjs": "text/javascript", ".js": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };

function check(condition, message) { if (!condition) throw new Error(message); }
function datum(value, origin) { return { state: "PRESENT", origin, value, units: "ordinal" }; }

const salienceRecord = {
  schema_version: "bilqis.bamf.mission-control.salience-event/v1",
  meta: {
    record_id: "salience-record:browser:current",
    run: operator.meta.run,
    materialized_at: 1794700124,
    observed_at: 1794700120,
    as_of: operator.meta.as_of,
    authority: "MEASURED",
    coverage: "COMPLETE",
    source_refs: ["source:browser:salience"],
    evidence_refs: ["evidence:browser:salience"],
    receipt_refs: ["receipt:browser:salience"],
  },
  salience_id: "salience:browser:current",
  capability_id: "B.AND",
  impact: datum("HIGH", "SOURCE_AUTHORITATIVE"),
  exigency: datum("MODERATE", "DERIVED"),
  novelty: datum("LOW", "INFERRED"),
  action_kind: "TEACHING",
};

const bridge = 'const mode=new URL(location.href).searchParams.get("launchMode")==="fixtures"?"fixtures":"production";'+
  'window.bamfMissionControl={launchMode:mode,connect:async()=>({state:"healthy"}),status:async()=>({learnerActive:false}),'+
  'querySnapshot:async request=>{if(request&&request.schemaVersion)return '+JSON.stringify(operator)+';throw new Error("BROWSER_SNAPSHOT_UNAVAILABLE")},'+
  'query:async request=>{if(request&&request.family==="salience")return {accepted:true,family:"salience",mode:request.mode,state:"PRESENT",coverage:"COMPLETE",records:['+JSON.stringify(salienceRecord)+'],next_cursor:null};'+
  'return {accepted:true,family:request&&request.family,mode:request&&request.mode,state:"EMPTY",coverage:"COMPLETE",records:[],next_cursor:null}},'+
  'subscribeEvents:()=>async()=>{},requestDryRun:async()=>{throw new Error("BROWSER_MUTATION_DISABLED")},requestCommand:async()=>{throw new Error("BROWSER_MUTATION_DISABLED")},fetchReceipt:async()=>null};';

function server() {
  return http.createServer((request, response) => {
    const url = new URL(request.url, "http://127.0.0.1");
    if (url.pathname === "/preview-bridge.mjs") { response.writeHead(200, { "Content-Type": "text/javascript" }); response.end(bridge); return; }
    if (url.pathname === "/axe.min.js") { response.writeHead(200, { "Content-Type": "text/javascript" }); response.end(fs.readFileSync(axePath)); return; }
    let file = path.join(repo, decodeURIComponent(url.pathname));
    if (url.pathname === "/" || url.pathname === "/apps/mission-control/renderer/") file = path.join(renderer, "index.html");
    if (!file.startsWith(repo) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { response.writeHead(404); response.end("not found"); return; }
    let body = fs.readFileSync(file);
    if (file.endsWith("index.html")) body = Buffer.from(body.toString().replace(
      '<script type="module" src="./renderer.mjs">',
      '<script src="/preview-bridge.mjs"></script><script type="module" src="./renderer.mjs">'));
    response.writeHead(200, { "Content-Type": mime[path.extname(file)] || "application/octet-stream" }); response.end(body);
  });
}

async function setDisplay(page, theme, density) {
  await page.evaluate(({ theme, density }) => {
    localStorage.setItem("bilqis.mc.theme", theme);
    localStorage.setItem("bilqis.mc.density", density);
  }, { theme, density });
  await page.reload({ waitUntil: "domcontentloaded" });
}

async function navigateSalience(page) {
  const nav = page.locator('[data-test-id="nav-destination-salience"]');
  await nav.waitFor(); await nav.click();
  await page.locator('[data-test-id="salience-view"]').waitFor();
}

async function activateTab(page, tab) {
  await page.locator(`[data-test-id="salience-tab-${tab}"]`).click();
  check(await page.locator(`[data-test-id="salience-tab-${tab}"]`).getAttribute("aria-selected") === "true",
    `Salience ${tab} tab did not activate`);
}

async function exerciseRovingTabs(page) {
  const observations = page.locator('[data-test-id="salience-tab-observations"]');
  await observations.focus(); await page.keyboard.press("ArrowRight");
  check(await page.locator('[data-test-id="salience-tab-aggregation"]').evaluate(node => node === document.activeElement),
    "Salience tab roving focus did not move to Aggregation");
  await page.keyboard.press("Enter");
  check(await page.locator('[data-test-id="salience-tab-aggregation"]').getAttribute("aria-selected") === "true",
    "Salience Aggregation tab did not activate from keyboard");
  await activateTab(page, "observations");
}

async function inspectAndReturn(page, launchMode) {
  const trigger = launchMode === "production"
    ? page.locator('[data-test-id="salience-production-inspect-salience-record-browser-current"]')
    : page.locator('[data-test-id="salience-observation-inspect-salience-record-fixture-unlock"]');
  const recordId = launchMode === "production" ? "salience-record:browser:current" : "salience-record:fixture:unlock";
  const selectedHook = launchMode === "production"
    ? "salience-production-observation-salience-record-browser-current"
    : "salience-observation-row-salience-record-fixture-unlock";
  await trigger.click();
  await page.waitForFunction(() => document.querySelector('[data-test-id="investigation-inspector"]')?.getAttribute("aria-hidden") === "false");
  await page.keyboard.press("Escape");
  await page.waitForFunction(() => document.querySelector('[data-test-id="investigation-inspector"]')?.getAttribute("aria-hidden") === "true");
  await activateTab(page, "aggregation"); await activateTab(page, "routing"); await activateTab(page, "observations");
  const selected = page.locator(`[data-test-id="${selectedHook}"]`);
  check(await selected.getAttribute("data-selected") === "true",
    launchMode + " Salience lost selected observation " + recordId + " across tab switches");
}

async function fixtureSnapshotPersistence(page) {
  const select = page.locator('[data-test-id="salience-snapshot-select"]');
  await select.selectOption("historical");
  await activateTab(page, "aggregation"); await activateTab(page, "routing"); await activateTab(page, "observations");
  check(await select.inputValue() === "historical", "Salience lost the selected fixture snapshot across tab switches");
}

async function audit(page, launchMode, viewport, theme, density) {
  await page.setViewportSize(viewport); await setDisplay(page, theme, density); await navigateSalience(page);
  await page.addScriptTag({ url: "/axe.min.js" }); await exerciseRovingTabs(page); await inspectAndReturn(page, launchMode);
  if (launchMode === "fixtures") await fixtureSnapshotPersistence(page);
  const root = page.locator('[data-test-id="salience-view"]');
  const result = await root.evaluate(async (node, mode) => {
    const axeResult = await axe.run(node, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] } });
    const scroller = node.querySelector(".salience-table-wrap");
    return {
      launchMode: mode,
      violations: axeResult.violations.map(item => ({ id: item.id, nodes: item.nodes.map(entry => entry.target) })),
      documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      localTableOwnsOverflow: Boolean(scroller && scroller.scrollWidth >= scroller.clientWidth),
      tablists: node.querySelectorAll('[role="tablist"]').length,
      tabs: node.querySelectorAll('[role="tab"]').length,
      visiblePanels: [...node.querySelectorAll('[role="tabpanel"]')].filter(panel => !panel.hidden).length,
      sourceTimes: [...node.querySelectorAll("[data-source-unix-seconds]")].map(item => item.getAttribute("data-source-unix-seconds")),
      text: node.innerText,
    };
  }, launchMode);
  check(result.violations.length === 0, launchMode + " Salience axe: " + JSON.stringify(result.violations));
  check(!result.documentOverflow, launchMode + " Salience created document overflow");
  check(result.localTableOwnsOverflow, launchMode + " Salience table lost local overflow ownership");
  check(result.tablists === 1 && result.tabs === 3 && result.visiblePanels === 1,
    launchMode + " Salience top-level tab contract failed");
  for (const id of ["concept", "elsewhere", "snapshot", "ordinal", "axis-impact", "axis-exigency", "axis-novelty"]) {
    check(await page.locator(`[data-test-id="salience-help-${id}-trigger"]`).count() === 1,
      launchMode + " Salience missing " + id + " help");
  }
  if (launchMode === "production") {
    check(!/fixture:/i.test(result.text), "production Salience rendered fixture evidence");
    check(result.text.includes("salience:browser:current"), "production Salience omitted live observation identity");
    check(result.sourceTimes.includes("1794700120"), "production Salience omitted observed time");
    check(result.sourceTimes.includes("1794700124"), "production Salience omitted materialized provenance time");
  } else {
    check(result.sourceTimes.includes("44237010"), "fixture Salience omitted historical observed time");
    check(result.sourceTimes.filter(value => value === "44237010").length >= 2, "fixture Salience omitted historical effective time");
    check(await page.locator('[data-test-id="shell-mode-badge"]').innerText() === "REFERENCE FIXTURES",
      "fixture Salience masqueraded as production mode");
  }
  await activateTab(page, "aggregation");
  check(await page.locator('[data-test-id="salience-help-aggregation-trigger"]').count() === 1,
    launchMode + " Salience missing aggregation help");
  await activateTab(page, "routing");
  check(await page.locator('[data-test-id="salience-help-routing-trigger"]').count() === 1,
    launchMode + " Salience missing routing help");
  return result;
}

(async () => {
  const app = server(); await new Promise(resolve => app.listen(0, "127.0.0.1", resolve));
  const browser = await playwright.chromium.launch({ executablePath: chrome, headless: true });
  const results = [];
  try {
    for (const launchMode of ["production", "fixtures"]) {
      const page = await browser.newPage();
      await page.goto(`http://127.0.0.1:${app.address().port}/apps/mission-control/renderer/?launchMode=${launchMode}`, { waitUntil: "domcontentloaded" });
      for (const variant of [
        [{ width: 1440, height: 960 }, "dark", "comfortable"],
        [{ width: 390, height: 844 }, "light", "compact"],
      ]) results.push({ launchMode, viewport: variant[0], theme: variant[1], density: variant[2], ...(await audit(page, launchMode, ...variant)) });
      await page.close();
    }
    console.log(JSON.stringify({ ok: true, results }, null, 2));
  } finally {
    await browser.close(); await new Promise(resolve => app.close(resolve));
  }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
