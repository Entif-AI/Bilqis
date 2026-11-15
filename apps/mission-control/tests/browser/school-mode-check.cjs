"use strict";

const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const repo = path.resolve(__dirname, "../../../..");
const renderer = path.join(repo, "apps/mission-control/renderer");
const playwright = require(process.env.BILQIS_PLAYWRIGHT_MODULE || "playwright");
const axePath = process.env.BILQIS_AXE_MODULE || require.resolve("axe-core/axe.min.js");
const chrome = process.env.BILQIS_CHROME_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const operator = JSON.parse(fs.readFileSync(
  path.join(repo, "apps/mission-control/fixtures/operator-view-v1.json"), "utf8",
));
const mime = { ".html": "text/html", ".mjs": "text/javascript", ".js": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };

function check(condition, message) { if (!condition) throw new Error(message); }
function datum(value) { return { state: "PRESENT", origin: "MEASURED", value, units: null }; }
function capability(id, score, debt) {
  return {
    schema_version: "bilqis.bamf.mission-control.capability-snapshot/v1",
    meta: { record_id: "capability:browser:" + id, run: operator.meta.run,
      materialized_at: 1794700120, observed_at: 1794700118, as_of: operator.meta.as_of,
      authority: "MEASURED", coverage: "COMPLETE", source_refs: ["source:browser:" + id],
      evidence_refs: [], receipt_refs: [] },
    capability_id: id, grade_id: "B", status: "ADMITTED",
    score_correct: datum(score), score_total: datum(12), debt: datum(debt),
  };
}
const productionRows = [capability("B.PRODUCTION.AND", 11, 1), capability("B.PRODUCTION.OR", 9, 3)];
const bridge = 'const mode=new URL(location.href).searchParams.get("launchMode")==="fixtures"?"fixtures":"production";'+
  'window.bamfMissionControl={launchMode:mode,connect:async()=>({state:"healthy"}),'+
  'status:async()=>({learnerActive:false}),querySnapshot:async request=>{if(request&&request.schemaVersion)return '+JSON.stringify(operator)+';throw new Error("BROWSER_SNAPSHOT_UNAVAILABLE")},'+
  'query:async request=>{if(request&&request.family==="capability")return {accepted:true,family:"capability",mode:request.mode,state:"PRESENT",coverage:"COMPLETE",records:'+JSON.stringify(productionRows)+',next_cursor:null};return {accepted:true,family:request&&request.family,mode:request&&request.mode,state:"EMPTY",coverage:"COMPLETE",records:[],next_cursor:null}},'+
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
  await page.evaluate(({ theme, density }) => { localStorage.setItem("bilqis.mc.theme", theme); localStorage.setItem("bilqis.mc.density", density); }, { theme, density });
  await page.reload({ waitUntil: "domcontentloaded" });
}
async function navigateSchool(page) {
  const nav = page.locator('[data-test-id="nav-destination-school"]'); await nav.waitFor(); await nav.click();
  await page.locator('[data-test-id="school-root"]').waitFor();
}
async function auditAtlas(page, launchMode) {
  await page.locator('[data-test-id="shell-school-mode-atlas"]').click();
  if (launchMode === "fixtures") {
    const root = page.locator('[data-test-id="curriculum-root"]'); await root.waitFor();
    const result = await root.evaluate(async node => {
      const axeResult = await axe.run(node, { runOnly: { type: "tag", values: ["wcag2a","wcag2aa","wcag21a","wcag21aa","wcag22aa"] } });
      const graph = node.querySelector('[data-test-id="curriculum-graph-scroll"]');
      const table = node.querySelector('[data-test-id="curriculum-table-scroll"]');
      const firstHeader = node.querySelector(".curriculum-table thead th");
      const firstIdentity = node.querySelector(".curriculum-table tbody th");
      return {
        violations: axeResult.violations.map(item => item.id),
        documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
        graphOwnsOverflow: Boolean(graph && graph.scrollWidth >= graph.clientWidth),
        tableOwnsOverflow: Boolean(table && table.scrollWidth >= table.clientWidth),
        tableHeaderPosition: firstHeader ? getComputedStyle(firstHeader).position : null,
        tableIdentityPosition: firstIdentity ? getComputedStyle(firstIdentity).position : null,
        nestedTablists: node.querySelectorAll('[role="tablist"]').length,
      };
    });
    check(result.violations.length === 0, "fixtures Atlas axe: " + JSON.stringify(result.violations));
    check(!result.documentOverflow, "fixtures Atlas created document overflow");
    check(result.graphOwnsOverflow, "fixtures Atlas graph lost its local scroller");
    check(result.tableOwnsOverflow, "fixtures Atlas table lost its local scroller");
    check(result.tableHeaderPosition === "sticky", "fixtures Atlas table header is not sticky");
    check(result.tableIdentityPosition === "sticky", "fixtures Atlas identity column is not sticky");
    check(result.nestedTablists === 0, "fixtures Atlas introduced a nested tab hierarchy");
    return result;
  }
  const root = page.locator('[data-test-id="school-atlas-production"]'); await root.waitFor();
  const text = await root.innerText();
  check(!/Fixture ·|fixture-backed|shared School fixture/i.test(text), "production Atlas rendered fixture copy");
  check(await page.locator('[data-test-id="shell-school-subnav"]').count() === 1, "production School mode layer duplicated");
  return { productionPlaceholder: true, text };
}
async function audit(page, launchMode, viewport, theme, density) {
  await page.setViewportSize(viewport); await setDisplay(page, theme, density); await navigateSchool(page);
  await page.addScriptTag({ url: "/axe.min.js" });
  const root = page.locator('[data-test-id="school-root"]');
  const result = await root.evaluate(async node => {
    const axeResult = await axe.run(node, { runOnly: { type: "tag", values: ["wcag2a","wcag2aa","wcag21a","wcag21aa","wcag22aa"] } });
    const matrix = node.querySelector(".matrix-scroll"); const firstHeader = node.querySelector(".school-matrix thead th");
    const firstIdentity = node.querySelector(".school-matrix .capability-cell");
    return { violations: axeResult.violations.map(item => ({ id: item.id, nodes: item.nodes.map(node => ({ target: node.target, html: node.html, failureSummary: node.failureSummary })) })), documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      matrixOwnsOverflow: Boolean(matrix && matrix.scrollWidth >= matrix.clientWidth), headerPosition: firstHeader ? getComputedStyle(firstHeader).position : null,
      identityPosition: firstIdentity ? getComputedStyle(firstIdentity).position : null, fixtureNotice: Boolean(node.querySelector('[data-test-id="school-fixture"]')),
      sourceTimes: [...node.querySelectorAll("[data-source-unix-seconds]")].map(item => item.getAttribute("data-source-unix-seconds")), text: node.innerText };
  });
  check(result.violations.length === 0, launchMode + " School axe: " + JSON.stringify(result.violations));
  check(!result.documentOverflow, launchMode + " School created document overflow");
  check(result.matrixOwnsOverflow, launchMode + " matrix lost its owned scroller");
  check(result.headerPosition === "sticky", launchMode + " matrix header is not sticky");
  check(result.identityPosition === "sticky", launchMode + " identity column is not sticky");
  const firstCapability = page.locator('[data-test-id^="school-matrix-capability-"]').first();
  await firstCapability.click();
  const inspector = page.locator('[data-test-id="investigation-inspector"]');
  await inspector.waitFor();
  result.inspector = await root.evaluate(node => {
    const matrix = node.querySelector(".matrix-scroll");
    return {
      documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      matrixOwnsOverflow: Boolean(matrix && matrix.scrollWidth >= matrix.clientWidth),
    };
  });
  check(!result.inspector.documentOverflow, launchMode + " inspector opened document overflow");
  check(result.inspector.matrixOwnsOverflow, launchMode + " inspector displaced matrix overflow ownership");
  await page.keyboard.press("Escape");
  await page.waitForFunction(() => {
    const panel = document.querySelector('[data-test-id="investigation-inspector"]');
    return panel?.getAttribute("aria-hidden") === "true" && panel.getBoundingClientRect().left >= innerWidth - 1;
  });
  for (const id of ["matrix", "controls", "dependencies"]) {
    check(await page.locator('[data-test-id="school-help-' + id + '-trigger"]').count() === 1, launchMode + " missing shared " + id + " help");
  }
  if (launchMode === "production") {
    check(await page.locator('[data-test-id^="school-row-time-"][data-source-unix-seconds="1794700118"]').count() > 0, "production School omitted authoritative observation time");
    check(!result.sourceTimes.includes("1794700120"), "production School substituted materialization time");
  }
  if (launchMode === "production") {
    check(!result.fixtureNotice, "production rendered School fixture notice"); check(result.text.includes("B.PRODUCTION.AND"), "production capability evidence missing");
    check(!/Fixture · representative terminal metrics/.test(result.text), "production rendered fixture copy");
  } else {
    check(result.fixtureNotice, "fixture mode omitted School reference notice");
    const modeBadge = page.locator('[data-test-id="shell-mode-badge"]');
    const shellLaunchMode = await modeBadge.evaluate(node => node.closest(".shell")?.dataset.launchMode ?? null);
    check(shellLaunchMode === "fixtures", "fixture mode omitted launch-owned shell posture");
    const mode = await modeBadge.innerText();
    check(mode === "REFERENCE FIXTURES", "fixture mode masqueraded as production/current mode");
  }
  result.atlas = await auditAtlas(page, launchMode);
  check(await page.locator('[data-test-id="school-help-atlas-trigger"]').count() === 1, launchMode + " missing shared Atlas help");
  return result;
}
(async () => {
  const app = server(); await new Promise(resolve => app.listen(0, "127.0.0.1", resolve)); const port = app.address().port;
  const browser = await playwright.chromium.launch({ executablePath: chrome, headless: true }); const results = [];
  try {
    for (const launchMode of ["production", "fixtures"]) {
      const page = await browser.newPage(); await page.goto("http://127.0.0.1:" + port + "/apps/mission-control/renderer/?launchMode=" + launchMode, { waitUntil: "domcontentloaded" });
      for (const variant of [[{width:1440,height:960},"dark","comfortable"],[{width:1440,height:960},"light","compact"],[{width:390,height:844},"light","compact"]]) {
        results.push({ launchMode, viewport: variant[0], theme: variant[1], density: variant[2], ...(await audit(page, launchMode, ...variant)) });
      }
      await page.close();
    }
    console.log(JSON.stringify({ ok: true, results }, null, 2));
  } finally { await browser.close(); await new Promise(resolve => app.close(resolve)); }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
