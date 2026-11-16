"use strict";

const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const repo = path.resolve(__dirname, "../../../..");
const renderer = path.join(repo, "apps/mission-control/renderer");
const playwright = require(process.env.BILQIS_PLAYWRIGHT_MODULE || "playwright");
const axePath = process.env.BILQIS_AXE_MODULE || require.resolve("axe-core/axe.min.js");
const chrome = process.env.BILQIS_CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const operator = JSON.parse(fs.readFileSync(path.join(repo, "apps/mission-control/fixtures/operator-view-v1.json"), "utf8"));
const productionOperator = structuredClone(operator);
productionOperator.meta.record_id = "operator-view:memory-production";
productionOperator.meta.run.run_id = "memory-production";
productionOperator.meta.run.generation = 7;

function datum(value, units, origin = "MEASURED") {
  return { state: "PRESENT", value, units, origin };
}

function memoryRecord(id, generation, observedAt, usedMiB, hits, misses, requalifications) {
  return {
    schema_version: "bilqis.bamf.mission-control.memory-snapshot/v1",
    meta: {
      record_id: id,
      observed_at: observedAt,
      materialized_at: observedAt + 2,
      source_refs: [`source:${id}`],
      evidence_refs: [`evidence:${id}`],
      receipt_refs: [`receipt:${id}`],
      run: { run_id: "memory-production", generation },
    },
    used_bytes: datum(usedMiB * 1024 ** 2, "bytes"),
    budget_bytes: datum(512 * 1024 ** 2, "bytes", "CONFIGURED_LIMIT"),
    hits: datum(hits, "count"),
    misses: datum(misses, "count"),
    requalifications: datum(requalifications, "count"),
  };
}

const currentMemory = memoryRecord("memory:production:7", 7, 1790000118, 320, 64, 9, 2);
const historicalMemory = memoryRecord("memory:production:6", 6, 1789999000, 288, 58, 12, 1);

function page(records, mode = "current") {
  return {
    accepted: true,
    family: "memory",
    mode,
    state: records.length ? "PRESENT" : "EMPTY",
    coverage: "COMPLETE",
    records,
    markers: [], links: [], next_cursor: null,
  };
}

function bridgeSource() {
  return [
    "const mode=new URL(location.href).searchParams.get('launchMode')==='fixtures'?'fixtures':'production';",
    "const productionOperator=" + JSON.stringify(productionOperator) + ";",
    "const fixtureOperator=" + JSON.stringify(operator) + ";",
    "const currentMemory=" + JSON.stringify(page([currentMemory])) + ";",
    "const historicalMemory=" + JSON.stringify(page([historicalMemory], "historical")) + ";",
    "window.bamfMissionControl={launchMode:mode,",
    "connect:async()=>({state:'healthy',serviceLive:true,learnerReady:true,learnerActive:false}),",
    "querySnapshot:async()=>structuredClone(mode==='fixtures'?fixtureOperator:productionOperator),",
    "query:async request=>request?.family==='memory'?(request.mode==='historical'?historicalMemory:currentMemory):({accepted:true,state:'EMPTY',records:[]}),",
    "subscribeEvents:()=>async()=>{},requestDryRun:async()=>({accepted:false}),requestCommand:async()=>({accepted:false}),fetchReceipt:async()=>null};",
  ].join("");
}

const mime = { ".html": "text/html", ".mjs": "text/javascript", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };
function check(condition, message) { if (!condition) throw new Error(message); }

function server() {
  return http.createServer((request, response) => {
    const url = new URL(request.url, "http://127.0.0.1");
    if (url.pathname === "/preview-bridge.js") {
      response.writeHead(200, { "Content-Type": "text/javascript" }); response.end(bridgeSource()); return;
    }
    if (url.pathname === "/axe.min.js") {
      response.writeHead(200, { "Content-Type": "text/javascript" }); response.end(fs.readFileSync(axePath)); return;
    }
    let file = path.join(repo, decodeURIComponent(url.pathname));
    if (url.pathname === "/" || url.pathname === "/apps/mission-control/renderer/") file = path.join(renderer, "index.html");
    if (!file.startsWith(repo) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      response.writeHead(404); response.end("not found"); return;
    }
    let body = fs.readFileSync(file);
    if (file.endsWith("index.html")) body = Buffer.from(body.toString().replace(
      '<script type="module" src="./renderer.mjs">',
      '<script src="/preview-bridge.js"></script><script type="module" src="./renderer.mjs">',
    ));
    response.writeHead(200, { "Content-Type": mime[path.extname(file)] || "application/octet-stream" });
    response.end(body);
  });
}

async function inspectGeometry(pageRef) {
  await pageRef.locator('[data-test-id="memory-tab-overview"]').click();
  await pageRef.locator('[data-test-id="memory-production-inspect"]').click();
  await pageRef.waitForFunction(() => document.querySelector("#inspector")?.getAttribute("aria-hidden") === "false");
  const geometry = await pageRef.evaluate(() => {
    const main = document.querySelector("#main-content").getBoundingClientRect();
    const inspector = document.querySelector("#inspector").getBoundingClientRect();
    const splitter = document.querySelector("#inspector-splitter").getBoundingClientRect();
    return {
      mainRight: main.right, inspectorLeft: inspector.left, splitterLeft: splitter.left,
      inspectorWidth: inspector.width, viewportWidth: innerWidth,
      splitterDisplay: getComputedStyle(document.querySelector("#inspector-splitter")).display,
      modal: document.querySelector("#inspector").getAttribute("aria-modal"),
      overflow: document.documentElement.scrollWidth > innerWidth + 1,
    };
  });
  if (geometry.viewportWidth > 980) {
    check(geometry.mainRight <= geometry.splitterLeft + 1, "Memory inspector overlaps desktop workspace");
    check(geometry.splitterLeft <= geometry.inspectorLeft + 1, "Memory splitter is detached from inspector");
  } else {
    check(geometry.modal === "true", "Memory narrow inspector is not modal");
    check(geometry.splitterDisplay === "none", "Memory narrow inspector exposes desktop splitter");
    check(geometry.inspectorWidth >= geometry.viewportWidth * 0.8, "Memory narrow inspector is too narrow");
  }
  check(!geometry.overflow, "Memory inspector created document overflow");
  await pageRef.keyboard.press("Escape");
}

async function audit(pageRef, launchMode) {
  const root = pageRef.locator('[data-test-id="memory-workspace"]');
  await root.waitFor();
  await pageRef.addScriptTag({ url: "/axe.min.js" });
  const common = await root.evaluate(async node => {
    const result = await axe.run(node, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] } });
    const wrap = node.querySelector(".memory-table-wrap");
    return {
      violations: result.violations.map(item => item.id),
      documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      tableOverflow: wrap ? getComputedStyle(wrap).overflowX : null,
      tablists: node.querySelectorAll('[role="tablist"]').length,
      tabs: node.querySelectorAll('[role="tab"]').length,
      helpTriggers: node.querySelectorAll(".ui-context-help__trigger").length,
    };
  });
  check(common.violations.length === 0, launchMode + " Memory axe: " + JSON.stringify(common.violations));
  check(!common.documentOverflow, launchMode + " Memory created document overflow");
  check(common.tablists === 1 && common.tabs === 4, launchMode + " Memory tab hierarchy is wrong");
  check(common.helpTriggers >= 8, launchMode + " Memory help coverage is incomplete");
  const overview = pageRef.locator('[data-test-id="memory-tab-overview"]');
  await overview.focus();
  await pageRef.keyboard.press("End");
  check(await pageRef.locator('[data-test-id="memory-tab-comparison"]').getAttribute("aria-selected") === "true", "End did not select Memory Comparison");
  await pageRef.keyboard.press("Home");
  check(await overview.getAttribute("aria-selected") === "true", "Home did not select Memory Overview");

  if (launchMode === "production") {
    const text = await root.innerText();
    check(!/REFERENCE MEMORY DATA|fixture:|44239/.test(text), "production Memory surfaced fixture content");
    check((await pageRef.locator('[data-test-id="memory-production-time"]').getAttribute("data-source-unix-seconds")) === "1790000118", "production Memory lost exact observation time");
    await pageRef.locator('[data-test-id="memory-tab-atlas"]').click();
    check((await pageRef.locator('[data-test-id="memory-production-atlas-state"]').innerText()).includes("aggregate memory state"), "production Memory invented slot detail");
    await pageRef.locator('[data-test-id="memory-tab-comparison"]').click();
    const input = pageRef.locator('[data-test-id="memory-production-compare-generation"]');
    await input.fill("6");
    await pageRef.locator('[data-test-id="memory-tab-dossier"]').click();
    await pageRef.locator('[data-test-id="memory-tab-comparison"]').click();
    check(await input.inputValue() === "6", "production comparison draft did not survive tab switching");
    await pageRef.locator('[data-test-id="memory-production-compare-submit"]').click();
    await pageRef.waitForFunction(() => document.querySelector('[data-test-id="memory-production-comparison-status"]')?.textContent.includes("Generation 6"));
    await pageRef.locator('[data-test-id="memory-tab-overview"]').click();
    await pageRef.locator('[data-test-id="memory-tab-comparison"]').click();
    check((await pageRef.locator('[data-test-id="memory-production-comparison-status"]').innerText()).includes("Generation 6"), "production loaded comparison did not persist");
    await inspectGeometry(pageRef);
  } else {
    check((await root.innerText()).includes("REFERENCE MEMORY DATA"), "fixture Memory omitted reference posture");
    check((await pageRef.locator('[data-test-id="shell-mode-badge"]').innerText()) === "REFERENCE FIXTURES", "fixture shell posture is missing");
    await pageRef.locator('[data-test-id="memory-tab-atlas"]').click();
    const second = pageRef.locator('[data-test-id="memory-slot-select-0-1"]');
    await second.click();
    await pageRef.keyboard.press("Escape");
    await pageRef.locator('[data-test-id="memory-tab-overview"]').click();
    await pageRef.locator('[data-test-id="memory-tab-atlas"]').click();
    check(await second.getAttribute("aria-pressed") === "true", "fixture selected slot did not persist across tabs");
    check((await pageRef.locator('[data-test-id="memory-page-position"]').innerText()).includes("Page 1"), "fixture page state did not persist across tabs");
    await pageRef.locator('[data-test-id="memory-tab-comparison"]').click();
    const compare = pageRef.locator('[data-test-id="memory-compare-generation"]');
    const value = await compare.inputValue();
    await pageRef.locator('[data-test-id="memory-tab-dossier"]').click();
    await pageRef.locator('[data-test-id="memory-tab-comparison"]').click();
    check(await compare.inputValue() === value, "fixture comparison state did not persist across tabs");
  }
  return common;
}

(async () => {
  const app = server();
  await new Promise(resolve => app.listen(0, "127.0.0.1", resolve));
  const browser = await playwright.chromium.launch({ executablePath: chrome, headless: true });
  const results = [];
  try {
    for (const launchMode of ["production", "fixtures"]) {
      for (const viewport of [{ width: 1440, height: 960 }, { width: 390, height: 844 }]) {
        const pageRef = await browser.newPage({ viewport });
        await pageRef.goto(`http://127.0.0.1:${app.address().port}/apps/mission-control/renderer/?launchMode=${launchMode}#/view/memory`, { waitUntil: "domcontentloaded" });
        results.push({ launchMode, viewport, ...(await audit(pageRef, launchMode)) });
        await pageRef.close();
      }
    }
    console.log(JSON.stringify({ ok: true, results }, null, 2));
  } finally {
    await browser.close();
    await new Promise(resolve => app.close(resolve));
  }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
