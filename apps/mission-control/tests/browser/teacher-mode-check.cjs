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

const teacherRecord = {
  schema_version: "bilqis.bamf.mission-control.teacher-snapshot/v1",
  meta: {
    record_id: "teacher:browser:current",
    run: operator.meta.run,
    materialized_at: 1794700120,
    observed_at: 1794700118,
    as_of: operator.meta.as_of,
    authority: "MEASURED",
    coverage: "COMPLETE",
    source_refs: ["source:browser:teacher"],
    evidence_refs: ["evidence:browser:teacher"],
    receipt_refs: ["receipt:browser:teacher"],
  },
  teacher_identity: "teacher:browser:accepted",
  teacher_epoch: 12,
  strategy_id: "strategy:browser:accepted",
  attempts: datum(9),
  accepted: datum(6),
  rejected: datum(3),
};

const bridge = 'const mode=new URL(location.href).searchParams.get("launchMode")==="fixtures"?"fixtures":"production";'+
  'window.bamfMissionControl={launchMode:mode,connect:async()=>({state:"healthy"}),'+
  'status:async()=>({learnerActive:false}),querySnapshot:async request=>{if(request&&request.schemaVersion)return '+JSON.stringify(operator)+';throw new Error("BROWSER_SNAPSHOT_UNAVAILABLE")},'+
  'query:async request=>{if(request&&request.family==="teacher")return {accepted:true,family:"teacher",mode:request.mode,state:"PRESENT",coverage:"COMPLETE",records:['+JSON.stringify(teacherRecord)+'],next_cursor:null};return {accepted:true,family:request&&request.family,mode:request&&request.mode,state:"EMPTY",coverage:"COMPLETE",records:[],next_cursor:null}},'+
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

async function navigateTeacher(page) {
  const nav = page.locator('[data-test-id="nav-destination-teacher"]');
  await nav.waitFor();
  await nav.click();
  await page.locator('[data-test-id="teacher-view"]').waitFor();
}

async function teacherLayout(page, launchMode) {
  const root = page.locator('[data-test-id="teacher-view"]');
  return root.evaluate(async (node, mode) => {
    const axeResult = await axe.run(node, {
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
    });
    const scroll = node.querySelector(".teacher-table-wrap");
    const visiblePanels = [...node.querySelectorAll('[role="tabpanel"]')]
      .filter(panel => !panel.hidden).length;
    return {
      launchMode: mode,
      violations: axeResult.violations.map(item => ({
        id: item.id,
        nodes: item.nodes.map(entry => entry.target),
      })),
      documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      localTableOwnsOverflow: Boolean(scroll && scroll.scrollWidth >= scroll.clientWidth),
      tablists: node.querySelectorAll('[role="tablist"]').length,
      tabs: node.querySelectorAll('[role="tab"]').length,
      visiblePanels,
      sourceTimes: [...node.querySelectorAll("[data-source-unix-seconds]")]
        .map(item => item.getAttribute("data-source-unix-seconds")),
      text: node.innerText,
    };
  }, launchMode);
}

async function exerciseTabs(page) {
  const roster = page.locator('[data-test-id="teacher-tab-roster"]');
  await roster.focus();
  await page.keyboard.press("ArrowRight");
  check(await page.locator('[data-test-id="teacher-tab-comparison"]').evaluate(node => node === document.activeElement),
    "Teacher tab roving focus did not move to Comparison");
  await page.keyboard.press("Enter");
  check(await page.locator('[data-test-id="teacher-tab-comparison"]').getAttribute("aria-selected") === "true",
    "Teacher Comparison tab did not activate from keyboard");
  await page.locator('[data-test-id="teacher-tab-roster"]').click();
}

async function exerciseFixturePersistence(page) {
  await page.locator('[data-test-id="teacher-roster-select-0d8ac6d2d042"]').click();
  await page.locator('[data-test-id="teacher-tab-comparison"]').click();
  await page.locator('[data-test-id="teacher-compare-strategy-7c4f5cd172b9"]').click();
  const scope = page.locator('[data-test-id="teacher-compare-scope"]');
  await scope.selectOption("capability:B.AND");
  await page.locator('[data-test-id="teacher-tab-fidelity"]').click();
  await page.locator('[data-test-id="teacher-tab-comparison"]').click();
  check(await page.locator('[data-test-id="teacher-compare-strategy-7c4f5cd172b9"]').getAttribute("aria-pressed") === "true",
    "Teacher comparison strategy set was lost across tab switches");
  check(await scope.inputValue() === "capability:B.AND",
    "Teacher comparison scope was lost across tab switches");
  await page.locator('[data-test-id="teacher-tab-roster"]').click();
  check(await page.locator('[data-test-id="teacher-roster-select-0d8ac6d2d042"]').getAttribute("aria-pressed") === "true",
    "Teacher selected strategy was lost across tab switches");
}

async function exerciseInspector(page, launchMode) {
  const trigger = launchMode === "production"
    ? page.locator('[data-test-id="teacher-production-strategy"]')
    : page.locator('[data-test-id="teacher-strategy-inspect"]');
  await trigger.click();
  const inspector = page.locator('[data-test-id="investigation-inspector"]');
  await inspector.waitFor();
  await page.waitForFunction(() => document.querySelector('[data-test-id="investigation-inspector"]')
    ?.getAttribute("aria-hidden") === "false");
  const geometry = await page.locator('[data-test-id="teacher-view"]').evaluate((node) => {
    const scroller = node.querySelector(".teacher-table-wrap");
    return {
      documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      localTableOwnsOverflow: Boolean(scroller && scroller.scrollWidth >= scroller.clientWidth),
    };
  });
  check(!geometry.documentOverflow, launchMode + " Teacher inspector caused document overflow");
  check(geometry.localTableOwnsOverflow, launchMode + " Teacher inspector displaced table overflow ownership");
  await page.keyboard.press("Escape");
  await page.waitForFunction(() => document.querySelector('[data-test-id="investigation-inspector"]')
    ?.getAttribute("aria-hidden") === "true");
}

async function audit(page, launchMode, viewport, theme, density) {
  await page.setViewportSize(viewport);
  await setDisplay(page, theme, density);
  await navigateTeacher(page);
  await page.addScriptTag({ url: "/axe.min.js" });
  await exerciseTabs(page);
  if (launchMode === "fixtures") await exerciseFixturePersistence(page);
  await exerciseInspector(page, launchMode);

  const result = await teacherLayout(page, launchMode);
  check(result.violations.length === 0, launchMode + " Teacher axe: " + JSON.stringify(result.violations));
  check(!result.documentOverflow, launchMode + " Teacher created document overflow");
  check(result.localTableOwnsOverflow, launchMode + " Teacher table lost local overflow ownership");
  check(result.tablists === 1, launchMode + " Teacher must have exactly one tablist");
  check(result.tabs === 3, launchMode + " Teacher must have exactly three top-level tabs");
  check(result.visiblePanels === 1, launchMode + " Teacher must expose one active tabpanel");

  for (const id of ["mutation", "provenance", "strategy", "metrics"]) {
    check(await page.locator(`[data-test-id="teacher-help-${id}-trigger"]`).count() === 1,
      launchMode + " Teacher missing " + id + " contextual help");
  }
  await page.locator('[data-test-id="teacher-tab-comparison"]').click();
  check(await page.locator('[data-test-id="teacher-help-comparison-trigger"]').count() === 1,
    launchMode + " Teacher missing comparison help");
  await page.locator('[data-test-id="teacher-tab-fidelity"]').click();
  check(await page.locator('[data-test-id="teacher-help-fidelity-trigger"]').count() === 1,
    launchMode + " Teacher missing fidelity help");
  await page.locator('[data-test-id="teacher-tab-roster"]').click();

  if (launchMode === "production") {
    check(!result.text.includes("Reference fixture evidence"), "production Teacher rendered fixture posture");
    check(result.text.includes("strategy:browser:accepted"), "production Teacher omitted accepted strategy identity");
    check(result.sourceTimes.includes("1794700118"), "production Teacher omitted authoritative observation time");
    check(!result.sourceTimes.includes("1794700120"), "production Teacher substituted materialization time");
    check(await page.locator('[data-test-id="teacher-fixture-notice"]').count() === 0,
      "production Teacher rendered fixture notice");
  } else {
    check(result.text.includes("Reference fixture evidence"), "fixture Teacher omitted reference provenance");
    const mode = await page.locator('[data-test-id="shell-mode-badge"]').innerText();
    check(mode === "REFERENCE FIXTURES", "fixture Teacher masqueraded as production mode");
  }
  return result;
}

(async () => {
  const app = server();
  await new Promise(resolve => app.listen(0, "127.0.0.1", resolve));
  const port = app.address().port;
  const browser = await playwright.chromium.launch({ executablePath: chrome, headless: true });
  const results = [];
  try {
    for (const launchMode of ["production", "fixtures"]) {
      const page = await browser.newPage();
      await page.goto("http://127.0.0.1:" + port + "/apps/mission-control/renderer/?launchMode=" + launchMode,
        { waitUntil: "domcontentloaded" });
      for (const variant of [
        [{ width: 1440, height: 960 }, "dark", "comfortable"],
        [{ width: 1440, height: 960 }, "light", "compact"],
        [{ width: 390, height: 844 }, "light", "compact"],
      ]) {
        results.push({ launchMode, viewport: variant[0], theme: variant[1], density: variant[2],
          ...(await audit(page, launchMode, ...variant)) });
      }
      await page.close();
    }
    console.log(JSON.stringify({ ok: true, results }, null, 2));
  } finally {
    await browser.close();
    await new Promise(resolve => app.close(resolve));
  }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
