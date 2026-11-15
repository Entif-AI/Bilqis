"use strict";

const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const playwright = require(process.env.BILQIS_PLAYWRIGHT_MODULE || "playwright");
const axePath = process.env.BILQIS_AXE_MODULE || require.resolve("axe-core/axe.min.js");
const chrome = process.env.BILQIS_CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const repo = path.resolve(__dirname, "../../../..");
const renderer = path.join(repo, "apps/mission-control/renderer");
const fixtureOperator = JSON.parse(fs.readFileSync(path.join(repo, "apps/mission-control/fixtures/operator-view-v1.json"), "utf8"));
const framePages = JSON.parse(fs.readFileSync(path.join(repo, "apps/mission-control/fixtures/frame-inspections-v1.json"), "utf8"));
const productionOperator = structuredClone(fixtureOperator);
productionOperator.meta.record_id = "operator-view:production-run:7";
productionOperator.meta.run.run_id = "production-run";
productionOperator.meta.source_refs = ["run-state:production-run:7"];
const neuralRecord = {
  schema_version: "bilqis.bamf.mission-control.neural-runtime-sample/v1",
  meta: { record_id: "neural:production:7", run: productionOperator.meta.run,
    materialized_at: 1794700120, observed_at: 1794700118, as_of: 1794700118,
    coverage: "COMPLETE", authority: "MEASURED", source_refs: ["source:neural:7"],
    evidence_refs: ["evidence:neural:7"], receipt_refs: ["receipt:neural:7"] },
  optimizer_step: 411, step_duration_ms: { state: "PRESENT", origin: "MEASURED", value: 12.5, units: "ms" },
  active_parameters: { state: "PRESENT", origin: "MEASURED", value: 173948416, units: "parameters" },
  refinement_fraction: { state: "PRESENT", origin: "MEASURED", value: 0.25, units: "ratio" },
};
const mime = { ".html": "text/html", ".mjs": "text/javascript", ".js": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };
const check = (condition, message) => { if (!condition) throw new Error(message); };

function bridgeSource() {
  return `const mode=new URL(location.href).searchParams.get("launchMode")==="fixtures"?"fixtures":"production";
const fixtureOperator=${JSON.stringify(fixtureOperator)};const productionOperator=${JSON.stringify(productionOperator)};
const framePages=${JSON.stringify(framePages)};const neural=${JSON.stringify(neuralRecord)};window.__frameQueries=0;
const empty=q=>({accepted:true,family:q.family,mode:q.mode,state:"EMPTY",coverage:"COMPLETE",records:[],markers:[],links:[],total_matches:0,returned:0,truncated:false,next_cursor:null});
window.bamfMissionControl={launchMode:mode,connect:async()=>({state:"healthy",serviceLive:true,serviceReady:true,learnerReady:true,learnerActive:false,learnerState:"READY",runId:mode==="fixtures"?"fixture-run":"production-run",generation:7}),status:async()=>({learnerActive:false}),
querySnapshot:async q=>{if(q?.schemaVersion==="bamf.gui08.frame-query/v1"){window.__frameQueries+=1;if(mode!=="fixtures")throw new Error("PRODUCTION_FRAME_QUERY_FORBIDDEN");const p=framePages.find(x=>x.request.generation===q.generation);return structuredClone(p)}if(q?.schemaVersion)return structuredClone(mode==="fixtures"?fixtureOperator:productionOperator);throw new Error("SNAPSHOT_UNAVAILABLE")},
query:async q=>mode==="production"&&q?.family==="neural"?{...empty(q),state:"PRESENT",records:[structuredClone(neural)],total_matches:1,returned:1}:empty(q),
subscribeEvents:()=>async()=>{},requestDryRun:async()=>{throw new Error("BROWSER_MUTATION_DISABLED")},requestCommand:async()=>{throw new Error("BROWSER_MUTATION_DISABLED")},fetchReceipt:async()=>null};`;
}

function server() {
  return http.createServer((request, response) => {
    const url = new URL(request.url, "http://127.0.0.1");
    if (url.pathname === "/preview-bridge.mjs") { response.writeHead(200, { "Content-Type": "text/javascript" }); response.end(bridgeSource()); return; }
    if (url.pathname === "/axe.min.js") { response.writeHead(200, { "Content-Type": "text/javascript" }); response.end(fs.readFileSync(axePath)); return; }
    let file = path.join(repo, decodeURIComponent(url.pathname));
    if (url.pathname === "/" || url.pathname === "/apps/mission-control/renderer/") file = path.join(renderer, "index.html");
    if (!file.startsWith(repo) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { response.writeHead(404); response.end("not found"); return; }
    let body = fs.readFileSync(file);
    if (file.endsWith("index.html")) body = Buffer.from(body.toString().replace(
      '<script type="module" src="./renderer.mjs">', '<script src="/preview-bridge.mjs"></script><script type="module" src="./renderer.mjs">'));
    response.writeHead(200, { "Content-Type": mime[path.extname(file)] || "application/octet-stream" }); response.end(body);
  });
}

async function display(page, theme, density) {
  await page.evaluate(({ theme, density }) => { localStorage.setItem("bilqis.mc.theme", theme); localStorage.setItem("bilqis.mc.density", density); }, { theme, density });
  await page.reload({ waitUntil: "domcontentloaded" });
}
async function model(page) {
  await page.waitForFunction(() => location.hash.includes("run=") && location.hash.includes("generation="));
  const nav = page.locator('[data-test-id="nav-destination-model"]'); await nav.waitFor(); await nav.click();
  await page.locator('[data-test-id="shell-model-subnav"]').waitFor();
}
async function collapseRail(page) {
  const toggle = page.locator('[data-test-id="shell-rail-toggle"]');
  if (await toggle.getAttribute("aria-pressed") !== "true") await toggle.click();
}
async function inspectGeometry(page, trigger, localScroller) {
  const desktop = page.viewportSize().width >= 980;
  if (desktop) await collapseRail(page);
  if (trigger) await trigger.click();
  const inspector = page.locator('[data-test-id="investigation-inspector"]'); await inspector.waitFor();
  const splitter = page.locator('[data-test-id="investigation-inspector-splitter"]');
  if (desktop) { await splitter.focus(); await page.keyboard.press("End"); }
  const geometry = await page.evaluate(selector => {
    const local = document.querySelector(selector); return {
      overflow: document.documentElement.scrollWidth > innerWidth + 1,
      viewportWidth: innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      localOverflow: local ? local.scrollWidth >= local.clientWidth : true,
      inspectorWidth: document.querySelector("#inspector").getBoundingClientRect().width,
      modal: document.querySelector("#inspector").getAttribute("aria-modal"),
      splitterDisplay: getComputedStyle(document.querySelector("#inspector-splitter")).display,
      splitterTab: document.querySelector("#inspector-splitter").tabIndex,
      mainInert: document.querySelector("#main-content").inert,
      offenders: [...document.querySelectorAll('[data-test-id^="model-frame"], .frame-explorer, .frame-result-set, .frame-selected-summary')]
        .map(node => { const rect = node.getBoundingClientRect(); return { id: node.dataset.testId ?? node.className, left: rect.left, right: rect.right, width: rect.width, scrollWidth: node.scrollWidth, clientWidth: node.clientWidth }; })
        .filter(item => item.left < -1 || item.right > innerWidth + 1 || item.scrollWidth > item.clientWidth + 1)
        .slice(0, 20),
    };
  }, localScroller);
  check(!geometry.overflow, `Model inspector created document overflow: ${JSON.stringify(geometry)}`);
  check(geometry.localOverflow, "Model analytical surface lost local overflow ownership");
  if (desktop) check(geometry.inspectorWidth > 160, "Model inspector did not resize");
  else {
    check(geometry.modal === "true", "Model narrow inspector is not modal");
    check(geometry.splitterDisplay === "none" && geometry.splitterTab === -1,
      "Model narrow inspector exposes desktop splitter");
    check(geometry.mainInert, "Model narrow inspector leaves primary content interactive");
  }
  await page.keyboard.press("Escape");
}

async function productionAudit(page) {
  await model(page);
  await page.locator('[data-test-id="shell-model-neural"]').click();
  try {
    await page.locator('[data-test-id="model-neural-production-view"]').waitFor({ timeout: 5000 });
  } catch (error) {
    const diagnostic = await page.evaluate(() => ({
      view: document.querySelector("#shell")?.dataset?.view,
      domainHidden: document.querySelector("#domain-view")?.hidden,
      domain: document.querySelector("#domain-view")?.innerHTML,
      hash: location.hash,
    }));
    throw new Error(`production Neural route did not render: ${JSON.stringify(diagnostic)}\n${error.message}`);
  }
  const neural = page.locator('[data-test-id="model-neural-production-view"]');
  const text = await neural.innerText();
  check(await page.locator('[data-test-id="model-neural-production-sample"]').count() === 1,
    "production Neural omitted accepted sample");
  check(text.includes("411"), "production Neural omitted optimizer step");
  const provenance = page.locator('[data-test-id="model-neural-production-provenance"]');
  await provenance.evaluate(node => { node.open = true; });
  check((await provenance.innerText()).includes("neural:production:7"),
    "production Neural omitted accepted record identity");
  check(!/FIXTURE-BACKED|ILLUSTRATIVE FIXTURE|fixture-run|current fixture|historical fixture/i.test(text), "production Neural leaked fixture copy");
  check(await neural.locator('[data-source-unix-seconds="1794700118"]').count() === 1, "production Neural omitted observed time");
  check(await page.evaluate(() => location.hash.includes("section=neural")), "production Model route omitted Neural section");
  await inspectGeometry(page, page.locator('[data-test-id="model-neural-production-inspect"]'), ".runtime-metrics");
  await page.locator('[data-test-id="shell-model-frames"]').click();
  const frame = page.locator('[data-test-id="model-frame-production-unavailable"]'); await frame.waitFor();
  check(await page.evaluate(() => window.__frameQueries) === 0, "production Frames queried fixture data");
  check(!/fixture/i.test(await frame.innerText()), "production Frame unavailable state leaked fixture copy");
  check(await page.evaluate(() => location.hash.includes("section=frames")), "production Model route omitted Frames section");
}

async function fixtureAudit(page) {
  await model(page);
  await page.locator('[data-test-id="shell-model-neural"]').click();
  const neural = page.locator('[data-test-id="model-neural-workspace"]'); await neural.waitFor();
  check((await neural.innerText()).includes("FIXTURE-BACKED DIAGNOSTICS"), "fixture Neural omitted reference posture");
  await page.locator('[data-test-id="model-neural-fixture-historical"]').click();
  await page.locator('[data-test-id="model-neural-fixture-posture"]').getByText("Generation 6", { exact: false }).waitFor();
  check(await page.evaluate(() => location.hash.includes("diagnostic=historical")), "fixture Neural diagnostic mode missing from route");
  check(await page.evaluate(() => location.hash.includes("generation=6") && location.hash.includes("mode=HISTORICAL")),
    "fixture Neural historical diagnostics did not bind exact shell provenance");
  const historicalFacts = await page.locator("#context-facts strong").evaluateAll(nodes => nodes.map(node => node.title));
  check(historicalFacts.includes("8b5b2005ccf1656a56b35d817936c17816837d404cb92ce5231ff17947ac43f7"),
    "fixture Neural historical context retained the wrong generation manifest");
  check(historicalFacts.includes("da4f158d564c8439cdb8889a043847af3083795bd09e02faf44022fefe9d426f"),
    "fixture Neural historical context retained the wrong topology identity");
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.locator('[data-test-id="model-neural-fixture-posture"]').getByText("Generation 6", { exact: false }).waitFor();
  check(await page.evaluate(() => location.hash.includes("generation=6") && location.hash.includes("mode=HISTORICAL")),
    "fixture Neural historical provenance was not rehydrated from the route");
  await page.locator('[data-test-id="model-neural-fixture-current"]').click();
  if (page.viewportSize().width >= 980) await collapseRail(page);
  await page.locator('[data-test-id="model-neural-ccgqa-disclosure"] summary').click();
  await inspectGeometry(page, page.locator('[data-test-id="model-neural-ccgqa-layer-3-inspect"]'), '[data-test-id="model-neural-ccgqa-table-wrap"]');
  await page.locator('[data-test-id="shell-model-frames"]').click();
  await page.locator('[data-test-id="model-frame-result-set"]').waitFor();
  check(await page.locator('[data-test-id="model-frame-fixture-posture"]').innerText().then(t => t.includes("READ ONLY")), "fixture Frames omitted fixture posture");
  if (page.viewportSize().width >= 980) await collapseRail(page);
  await page.locator('[data-test-id="model-frame-example"]').selectOption("frame:quad-fast");
  await page.locator('[data-test-id="model-frame-position-0"]').evaluate(node => { node.open = true; });
  await page.locator('[data-test-id="model-frame-position-0-table-wrap"]').waitFor();
  await inspectGeometry(page, null, '[data-test-id="model-frame-position-0-table-wrap"]');
  await page.locator('[data-test-id="model-frame-generation"]').selectOption("6");
  await page.locator('[data-test-id="model-frame-example"]').waitFor();
  check(await page.locator('[data-test-id="model-frame-generation"]').inputValue() === "6", "fixture Frame generation did not switch");
  check(await page.evaluate(() => location.hash.includes("section=frames") &&
    location.hash.includes("generation=6") && location.hash.includes("mode=HISTORICAL")),
    "fixture Frame historical generation did not bind exact shell provenance");
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.locator('[data-test-id="model-frame-result-set"]').waitFor();
  check(await page.locator('[data-test-id="model-frame-generation"]').inputValue() === "6",
    "fixture Frame historical generation was not rehydrated");
  await page.locator('[data-test-id="shell-model-neural"]').click();
  await page.locator('[data-test-id="model-neural-fixture-posture"]').getByText("Generation 7", { exact: false }).waitFor();
  check(await page.evaluate(() => location.hash.includes("section=neural") &&
    location.hash.includes("generation=7") && location.hash.includes("mode=LIVE")),
    "fixture Neural current context inherited stale Frame historical provenance");
  const currentFacts = await page.locator("#context-facts strong").evaluateAll(nodes => nodes.map(node => node.title));
  check(currentFacts.includes("1111111111111111111111111111111111111111111111111111111111111111"),
    "fixture Neural current context did not restore the generation-7 manifest");
  await page.locator('[data-test-id="shell-model-frames"]').click();
  await page.locator('[data-test-id="model-frame-result-set"]').waitFor();
  check(await page.locator('[data-test-id="model-frame-generation"]').inputValue() === "6", "fixture Frame generation was lost across peer switch");
}

async function audit(page, launchMode, viewport, theme, density) {
  await page.setViewportSize(viewport); await display(page, theme, density); await page.addScriptTag({ url: "/axe.min.js" });
  if (launchMode === "production") await productionAudit(page); else await fixtureAudit(page);
  await page.addScriptTag({ url: "/axe.min.js" });
  const main = page.locator("#main-content");
  const result = await main.evaluate(async node => ({
    violations: (await axe.run(node, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"] } })).violations.map(v => v.id),
    overflow: document.documentElement.scrollWidth > innerWidth + 1,
    peerControls: document.querySelectorAll('[data-model-section]').length,
    nestedTabs: node.querySelectorAll('[role="tablist"]').length,
  }));
  check(result.violations.length === 0, `${launchMode} Model axe: ${result.violations}`);
  check(!result.overflow, `${launchMode} Model created document overflow`);
  check(result.peerControls === 2 && result.nestedTabs === 0, `${launchMode} Model violated single peer-mode layer`);
  return result;
}

(async () => {
  const app = server(); await new Promise(resolve => app.listen(0, "127.0.0.1", resolve));
  const browser = await playwright.chromium.launch({ executablePath: chrome, headless: true }); const results = [];
  fs.mkdirSync("output/playwright/1187", { recursive: true });
  try {
    for (const launchMode of ["production", "fixtures"]) {
      const page = await browser.newPage();
      const pageErrors = [];
      page.on("pageerror", error => pageErrors.push(String(error)));
      await page.goto(`http://127.0.0.1:${app.address().port}/apps/mission-control/renderer/?launchMode=${launchMode}`, { waitUntil: "domcontentloaded" });
      for (const variant of [[{ width: 1440, height: 960 }, "dark", "comfortable"], [{ width: 1440, height: 960 }, "light", "compact"], [{ width: 390, height: 844 }, "light", "compact"]]) {
        const result = await audit(page, launchMode, ...variant); results.push({ launchMode, viewport: variant[0], theme: variant[1], density: variant[2], ...result });
        await page.screenshot({ path: `output/playwright/1187/${launchMode}-${variant[1]}-${variant[2]}-${variant[0].width}.png`, fullPage: true });
      }
      check(pageErrors.length === 0, `${launchMode} browser errors: ${pageErrors.join(" | ")}`);
      await page.close();
    }
    fs.writeFileSync("output/playwright/1187/browser-result.json", `${JSON.stringify({ ok: true, results }, null, 2)}\n`);
    console.log(JSON.stringify({ ok: true, results }, null, 2));
  } finally { await browser.close(); await new Promise(resolve => app.close(resolve)); }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
