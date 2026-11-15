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
productionOperator.meta.record_id = "operator-view:resources-production";
productionOperator.meta.run.run_id = "resources-production";
productionOperator.meta.run.generation = 7;

function datum(value, units, origin = "MEASURED") {
  return { state: "PRESENT", value, units, origin };
}

function resourceRecord(id, generation, observedAt, memoryGiB, diskGiB, stepsPerMinute) {
  return {
    schema_version: "bilqis.bamf.mission-control.resource-sample/v1",
    meta: {
      record_id: id,
      observed_at: observedAt,
      materialized_at: observedAt + 2,
      source_refs: [`source:${id}`],
      evidence_refs: [`evidence:${id}`],
      receipt_refs: [`receipt:${id}`],
      run: { generation },
    },
    memory_used_bytes: datum(memoryGiB * 1024 ** 3, "bytes"),
    memory_budget_bytes: datum(64 * 1024 ** 3, "bytes", "SOURCE_AUTHORITATIVE"),
    disk_used_bytes: datum(diskGiB * 1024 ** 3, "bytes"),
    step_rate_per_minute: datum(stepsPerMinute, "steps/minute"),
  };
}

const currentRecord = resourceRecord("resource:production:7", 7, 1790000118, 16, 100, 2.5);
const historicalRecord = resourceRecord("resource:production:6", 6, 1789999000, 12, 90, 2);

function page(records, mode = "current") {
  return {
    accepted: true,
    family: "resource",
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
    "const currentResource=" + JSON.stringify(page([currentRecord])) + ";",
    "const historicalResource=" + JSON.stringify(page([historicalRecord], "historical")) + ";",
    "const emptyResource=" + JSON.stringify(page([])) + ";",
    "window.bamfMissionControl={launchMode:mode,",
    "connect:async()=>({state:'healthy',serviceLive:true,learnerReady:true,learnerActive:false}),",
    "querySnapshot:async()=>structuredClone(mode==='fixtures'?fixtureOperator:productionOperator),",
    "query:async request=>request?.family==='resource'?(mode==='fixtures'?emptyResource:(request.mode==='historical'?historicalResource:currentResource)):({accepted:true,state:'EMPTY',records:[]}),",
    "subscribeEvents:()=>async()=>{},requestDryRun:async()=>({accepted:false}),",
    "requestCommand:async()=>({accepted:false}),fetchReceipt:async()=>null};",
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
  await pageRef.locator('[data-test-id="resources-tab-timeline"]').click();
  await pageRef.locator('[data-test-id="resources-inspect-0"]').click();
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
    check(geometry.mainRight <= geometry.splitterLeft + 1, "Resources inspector overlaps desktop workspace");
    check(geometry.splitterLeft <= geometry.inspectorLeft + 1, "Resources splitter is detached from inspector");
  } else {
    check(geometry.modal === "true", "Resources narrow inspector is not modal");
    check(geometry.splitterDisplay === "none", "Resources narrow inspector exposes desktop splitter");
    check(geometry.inspectorWidth >= geometry.viewportWidth * 0.8, "Resources narrow inspector is too narrow");
  }
  check(!geometry.overflow, "Resources inspector created document overflow");
  await pageRef.keyboard.press("Escape");
}

async function audit(pageRef, launchMode) {
  const root = pageRef.locator('[data-test-id="resources-view"]');
  await root.waitFor();
  await pageRef.addScriptTag({ url: "/axe.min.js" });
  const common = await root.evaluate(async node => {
    const result = await axe.run(node, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] } });
    const wrap = node.querySelector(".resource-table-wrap");
    const input = node.querySelector(".resource-compare-input");
    return {
      violations: result.violations.map(item => item.id),
      documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      tableOverflow: wrap ? getComputedStyle(wrap).overflowX : null,
      tablists: node.querySelectorAll('[role="tablist"]').length,
      tabs: node.querySelectorAll('[role="tab"]').length,
      helpTriggers: node.querySelectorAll(".ui-context-help__trigger").length,
      inputBackground: input ? getComputedStyle(input).backgroundColor : null,
    };
  });
  check(common.violations.length === 0, launchMode + " Resources axe: " + JSON.stringify(common.violations));
  check(!common.documentOverflow, launchMode + " Resources created document overflow");
  check(common.tablists === 1 && common.tabs === 4, launchMode + " Resources tab hierarchy is wrong");
  check(common.helpTriggers >= 7, launchMode + " Resources help coverage is incomplete");
  check(common.inputBackground && common.inputBackground !== "rgba(0, 0, 0, 0)", "comparison input blends into canvas");
  const overviewTab = pageRef.locator('[data-test-id="resources-tab-overview"]');
  await overviewTab.focus();
  await pageRef.keyboard.press("End");
  check(await pageRef.locator('[data-test-id="resources-tab-comparison"]').getAttribute("aria-selected") === "true",
    "End did not move Resources to the last peer tab");
  await pageRef.keyboard.press("Home");
  check(await overviewTab.getAttribute("aria-selected") === "true", "Home did not return Resources to Overview");
  await pageRef.locator('[data-test-id="resources-tab-comparison"]').click();
  const input = pageRef.locator('[data-test-id="resources-compare-generation"]');
  await input.fill("6");
  await pageRef.locator('[data-test-id="resources-tab-compute"]').click();
  await pageRef.locator('[data-test-id="resources-tab-comparison"]').click();
  check(await input.inputValue() === "6", "comparison draft did not survive tab switching");
  if (launchMode === "production") {
    const text = await root.innerText();
    check(!/REFERENCE RESOURCE DATA|resource:fixture|44239/.test(text), "production Resources surfaced fixture content");
    await pageRef.locator('[data-test-id="resources-compare-submit"]').click();
    await pageRef.waitForFunction(() => document.querySelector('[data-test-id="resources-comparison-status"]')?.textContent.includes("generation 6"));
    await pageRef.locator('[data-test-id="resources-tab-compute"]').click();
    await pageRef.locator('[data-test-id="resources-tab-comparison"]').click();
    check((await pageRef.locator('[data-test-id="resources-comparison-status"]').innerText()).includes("generation 6"),
      "loaded comparison state did not survive tab switching");
    check(await pageRef.locator('[data-test-id="resources-compare-generation"]').inputValue() === "6",
      "loaded comparison generation did not survive tab switching");
    await pageRef.locator('[data-test-id="resources-tab-timeline"]').click();
    check(await pageRef.locator('[data-test-id="resources-time-0"]').getAttribute("data-source-unix-seconds") === "1790000118", "production timeline lost exact observation time");
    await inspectGeometry(pageRef);
  } else {
    check((await root.innerText()).includes("REFERENCE RESOURCE DATA"), "fixture Resources omitted reference posture");
    check((await pageRef.locator('[data-test-id="shell-mode-badge"]').innerText()) === "REFERENCE FIXTURES", "fixture shell posture is missing");
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
        await pageRef.goto(`http://127.0.0.1:${app.address().port}/apps/mission-control/renderer/?launchMode=${launchMode}#/view/resources`, { waitUntil: "domcontentloaded" });
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
