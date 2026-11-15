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
const digest = character => character.repeat(64);
const productionOperator = structuredClone(operator);
productionOperator.meta.record_id = "operator-view:lineage-production";
productionOperator.meta.run.run_id = "lineage-production";
productionOperator.meta.run.generation = 17;
productionOperator.meta.run.generation_manifest_sha256 = digest("2");
productionOperator.meta.run.run_identity_sha256 = digest("1");
productionOperator.meta.run.candidate_identity_sha256 = digest("3");
productionOperator.meta.run.factory_release_sha256 = digest("4");
productionOperator.meta.run.semantic_release_sha256 = digest("5");
productionOperator.meta.run.topology_sha256 = digest("6");
const generation = {
  schema_version: "bilqis.bamf.mission-control.generation-manifest/v1",
  meta: {
    record_id: "generation:17",
    run: productionOperator.meta.run,
    materialized_at: 1790000120,
    observed_at: 1790000118,
    as_of: 1790000118,
    coverage: "COMPLETE",
    authority: "MEASURED",
    source_refs: ["source:generation:17"],
    evidence_refs: ["evidence:generation:17"],
    receipt_refs: ["receipt:generation:17"],
  },
  checkpoint_sha256: digest("7"),
  student_sha256: digest("8"),
  optimizer_state_sha256: digest("9"),
  parent_manifest_sha256: digest("a"),
  status: "ACCEPTED",
};
const rejected = {
  schema_version: "bilqis.bamf.mission-control.candidate-decision/v1",
  meta: {
    record_id: "candidate-decision:17",
    run: productionOperator.meta.run,
    materialized_at: 1790000117,
    observed_at: 1790000116,
    as_of: 1790000116,
    coverage: "COMPLETE",
    authority: "DERIVED",
    source_refs: [], evidence_refs: [], receipt_refs: ["receipt:rejected:17"],
  },
  candidate_id: "candidate:rejected:17",
  capability_id: "B.AND",
  outcome: "REJECTED",
  reason_code: "NO_MEASURABLE_TARGET_GAIN",
};
const mime = {
  ".html": "text/html", ".mjs": "text/javascript", ".js": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml",
};

function check(condition, message) {
  if (!condition) throw new Error(message);
}

function page(records, family) {
  return {
    accepted: true, family, mode: "current", state: records.length ? "PRESENT" : "EMPTY",
    coverage: "COMPLETE", total_matches: records.length, records, markers: [], links: [],
    next_cursor: null,
  };
}

function bridgeSource() {
  return [
    "const mode=new URL(location.href).searchParams.get('launchMode')==='fixtures'?'fixtures':'production';",
    "const productionOperator=" + JSON.stringify(productionOperator) + ";",
    "const fixtureOperator=" + JSON.stringify(operator) + ";",
    "const generation=" + JSON.stringify(generation) + ";",
    "const rejected=" + JSON.stringify(rejected) + ";",
    "window.bamfMissionControl={launchMode:mode,",
    "connect:async()=>({state:'healthy',serviceLive:true,learnerReady:true,learnerActive:false}),",
    "querySnapshot:async()=>structuredClone(mode==='fixtures'?fixtureOperator:productionOperator),",
    "query:async request=>request?.family==='generation'?" + JSON.stringify(page([generation], "generation")) + ":",
    "request?.family==='episode'?" + JSON.stringify(page([rejected], "episode")) + ":",
    JSON.stringify(page([], "other")) + ",",
    "subscribeEvents:()=>async()=>{},requestDryRun:async()=>({accepted:false}),",
    "requestCommand:async()=>({accepted:false}),fetchReceipt:async()=>null};",
  ].join("");
}

function server() {
  return http.createServer((request, response) => {
    const url = new URL(request.url, "http://127.0.0.1");
    if (url.pathname === "/preview-bridge.js") {
      response.writeHead(200, { "Content-Type": "text/javascript" });
      response.end(bridgeSource());
      return;
    }
    if (url.pathname === "/axe.min.js") {
      response.writeHead(200, { "Content-Type": "text/javascript" });
      response.end(fs.readFileSync(axePath));
      return;
    }
    let file = path.join(repo, decodeURIComponent(url.pathname));
    if (url.pathname === "/" || url.pathname === "/apps/mission-control/renderer/") {
      file = path.join(renderer, "index.html");
    }
    if (!file.startsWith(repo) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      response.writeHead(404); response.end("not found"); return;
    }
    let body = fs.readFileSync(file);
    if (file.endsWith("index.html")) {
      body = Buffer.from(body.toString().replace(
        '<script type="module" src="./renderer.mjs">',
        '<script src="/preview-bridge.js"></script><script type="module" src="./renderer.mjs">',
      ));
    }
    response.writeHead(200, { "Content-Type": mime[path.extname(file)] || "application/octet-stream" });
    response.end(body);
  });
}

async function setDisplay(pageRef, theme, density) {
  await pageRef.evaluate(({ theme: nextTheme, density: nextDensity }) => {
    localStorage.setItem("bilqis.mc.theme", nextTheme);
    localStorage.setItem("bilqis.mc.density", nextDensity);
  }, { theme, density });
  await pageRef.reload({ waitUntil: "domcontentloaded" });
}

async function auditFixture(pageRef) {
  const root = pageRef.locator('[data-test-id="lineage-workspace"]');
  await root.waitFor();
  check(await root.locator('[data-test-id="lineage-tabs"]').count() === 1, "fixture Lineage tab hierarchy duplicated");
  await pageRef.locator('[data-test-id="lineage-graph-generation-44239"]').click();
  if (await pageRef.locator('[data-test-id="investigation-inspector"]').getAttribute("aria-hidden") === "false") {
    await pageRef.keyboard.press("Escape");
  }
  await pageRef.locator('[data-test-id="lineage-tab-selected"]').click();
  check((await pageRef.locator('[data-test-id="lineage-dossier-fact-generation"]').innerText()).includes("44239"),
    "selected generation did not survive tab change");
  await pageRef.locator('[data-test-id="lineage-tab-comparison"]').click();
  const before = pageRef.locator('[data-test-id="lineage-compare-before"]');
  const after = pageRef.locator('[data-test-id="lineage-compare-after"]');
  const originalAfter = await after.inputValue();
  await before.selectOption({ index: 0 });
  const firstValue = await before.inputValue();
  check(await pageRef.locator('[data-test-id="lineage-tab-comparison"]').getAttribute("aria-selected") === "true",
    "comparison tab was lost after endpoint rerender");
  await pageRef.locator('[data-test-id="lineage-tab-selected"]').click();
  await pageRef.locator('[data-test-id="lineage-tab-comparison"]').click();
  check(await before.inputValue() === firstValue, "comparison before operand did not persist");
  check(await after.inputValue() === originalAfter, "comparison after operand did not persist");
  const mode = await pageRef.locator('[data-test-id="shell-mode-badge"]').innerText();
  check(mode === "REFERENCE FIXTURES", "fixture Lineage omitted launch-owned fixture posture");
}

async function auditProduction(pageRef) {
  const root = pageRef.locator('[data-test-id="lineage-production-view"]');
  await root.waitFor();
  check(await root.locator('[data-test-id="lineage-production-tabs"]').count() === 1, "production Lineage tab hierarchy duplicated");
  const text = await root.innerText();
  check(!/FIXTURE|fixture-lineage-run|4424[0-9]/.test(text), "production Lineage surfaced fixture content");
  await pageRef.locator('[data-test-id="lineage-production-tab-selected"]').click();
  const identities = pageRef.locator('[data-test-id="lineage-production-identities"]');
  check(!(await identities.evaluate(node => node.open)), "forensic identities are expanded by default");
  const times = await root.locator('[data-test-id^="lineage-production-time-"]').evaluateAll(nodes =>
    nodes.map(node => node.getAttribute("data-source-unix-seconds")));
  check(times.includes("1790000118") && times.includes("1790000120"),
    "production Lineage omitted recorded generation timestamps");
  await pageRef.locator('[data-test-id="lineage-production-inspect"]').click();
  await pageRef.waitForFunction(() => {
    const panel = document.querySelector("#inspector");
    if (panel?.getAttribute("aria-hidden") !== "false") return false;
    if (innerWidth > 980) return true;
    return panel.getBoundingClientRect().left < innerWidth - 1;
  });
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
    check(geometry.mainRight <= geometry.splitterLeft + 1,
      "Lineage inspector overlaps desktop primary workspace: " + JSON.stringify(geometry));
    check(geometry.splitterLeft <= geometry.inspectorLeft + 1,
      "Lineage splitter left inspector seam");
  } else {
    check(geometry.modal === "true", "Lineage narrow inspector is not modal");
    check(geometry.splitterDisplay === "none", "Lineage narrow inspector exposes desktop splitter");
    check(geometry.inspectorWidth >= geometry.viewportWidth * 0.8,
      "Lineage narrow inspector is too narrow for deliberate overlay posture");
  }
  check(!geometry.overflow, "Lineage inspector created document overflow");
  await pageRef.keyboard.press("Escape");
}

async function audit(pageRef, launchMode, viewport, theme, density) {
  await pageRef.setViewportSize(viewport);
  await setDisplay(pageRef, theme, density);
  await pageRef.addScriptTag({ url: "/axe.min.js" });
  const root = pageRef.locator(launchMode === "production"
    ? '[data-test-id="lineage-production-view"]'
    : '[data-test-id="lineage-workspace"]');
  await root.waitFor();
  const common = await root.evaluate(async node => {
    const result = await axe.run(node, {
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
    });
    const table = node.querySelector(".lineage-table-wrap");
    return {
      violations: result.violations.map(item => item.id),
      documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      tableOverflow: table ? getComputedStyle(table).overflowX : null,
      tablists: node.querySelectorAll('[role="tablist"]').length,
    };
  });
  check(common.violations.length === 0, launchMode + " Lineage axe: " + JSON.stringify(common.violations));
  check(!common.documentOverflow, launchMode + " Lineage created document overflow");
  check(common.tablists === 1, launchMode + " Lineage introduced nested tabs");
  if (launchMode === "production") await auditProduction(pageRef);
  else await auditFixture(pageRef);
  return common;
}

(async () => {
  const app = server();
  await new Promise(resolve => app.listen(0, "127.0.0.1", resolve));
  const port = app.address().port;
  const browser = await playwright.chromium.launch({ executablePath: chrome, headless: true });
  const results = [];
  try {
    for (const launchMode of ["production", "fixtures"]) {
      for (const variant of [
        [{ width: 1440, height: 960 }, "dark", "comfortable"],
        [{ width: 390, height: 844 }, "light", "compact"],
      ]) {
        const pageRef = await browser.newPage();
        const url = "http://127.0.0.1:" + port +
          "/apps/mission-control/renderer/?launchMode=" + launchMode + "#/view/lineage";
        await pageRef.goto(url, { waitUntil: "domcontentloaded" });
        results.push({ launchMode, viewport: variant[0], ...(await audit(pageRef, launchMode, ...variant)) });
        await pageRef.close();
      }
    }
    console.log(JSON.stringify({ ok: true, results }, null, 2));
  } finally {
    await browser.close();
    await new Promise(resolve => app.close(resolve));
  }
})().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
