const fs = require("fs");
const http = require("http");
const path = require("path");
const playwright = require(process.env.BILQIS_PLAYWRIGHT_MODULE ||
  "/Users/emilie/Code/mission-control/node_modules/playwright");

const repo = path.resolve(__dirname, "../../../..");
const renderer = path.join(repo, "apps/mission-control/renderer");
const operator = JSON.parse(fs.readFileSync(
  path.join(repo, "apps/mission-control/fixtures/operator-view-v1.json"), "utf8"));
const productionOperator = JSON.parse(JSON.stringify(operator));
productionOperator.meta.record_id = "operator-view:accepted-run-7";
productionOperator.meta.run.run_id = "accepted-run-7";
productionOperator.meta.source_refs = ["run-state:accepted-run-7"];

const productionRecords = [{
  schema_version: "bilqis.bamf.mission-control.learning-episode/v1",
  meta: {
    record_id: "episode-record-accepted-7",
    run: productionOperator.meta.run,
    materialized_at: 1794725520,
    observed_at: 1794725515,
    as_of: 1794725515,
    coverage: "COMPLETE",
    authority: "DERIVED",
    source_refs: ["source:accepted"],
    evidence_refs: ["evidence:accepted"],
    receipt_refs: ["receipt:accepted"],
  },
  episode_id: "episode-accepted-7",
  capability_id: "B.AND",
  visit_id: "visit-accepted-7",
  state: "COMPLETED",
  started_at: 1794725400,
  completed_at: 1794725500,
}, {
  schema_version: "bilqis.bamf.mission-control.candidate-decision/v1",
  meta: {
    record_id: "decision-record-accepted-7",
    run: productionOperator.meta.run,
    materialized_at: 1794725521,
    observed_at: 1794725516,
    as_of: 1794725516,
    coverage: "COMPLETE",
    authority: "DERIVED",
    source_refs: ["source:decision"],
    evidence_refs: ["evidence:decision"],
    receipt_refs: ["receipt:decision"],
  },
  candidate_id: "candidate-accepted-7",
  capability_id: "B.AND",
  outcome: "ACCEPTED",
  reason_code: "SOURCE_GOLD_PASS",
}];

const mime = {
  ".html": "text/html", ".mjs": "text/javascript", ".js": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml",
};
function check(condition, message) {
  if (!condition) throw new Error(message);
}
function bridgeSource() {
  return [
    "const mode=new URL(location.href).searchParams.get('mode')==='fixtures'?'fixtures':'production';",
    "const productionOperator=" + JSON.stringify(productionOperator) + ";",
    "const fixtureOperator=" + JSON.stringify(operator) + ";",
    "const productionRecords=" + JSON.stringify(productionRecords) + ";",
    "window.bamfMissionControl={",
    "launchMode:mode,",
    "connect:async()=>({state:'healthy',serviceLive:true,learnerReady:true,learnerActive:false}),",
    "querySnapshot:async()=>structuredClone(mode==='fixtures'?fixtureOperator:productionOperator),",
    "query:async q=>q?.family==='episode'?{accepted:true,state:'PRESENT',coverage:'COMPLETE',",
    "total_matches:productionRecords.length,records:structuredClone(productionRecords),markers:[],links:[],next_cursor:null}:",
    "{accepted:true,state:'EMPTY',coverage:'COMPLETE',total_matches:0,records:[],markers:[],links:[],next_cursor:null},",
    "requestDryRun:async()=>({accepted:false}),requestCommand:async()=>({accepted:false}),",
    "fetchReceipt:async()=>null,subscribeEvents:()=>async()=>{},};",
  ].join("");
}
function server() {
  return http.createServer((req, res) => {
    const url = new URL(req.url, "http://127.0.0.1");
    if (url.pathname === "/preview-bridge.js") {
      res.writeHead(200, { "Content-Type": "text/javascript" });
      res.end(bridgeSource());
      return;
    }
    let file = path.join(repo, decodeURIComponent(url.pathname));
    if (url.pathname === "/" || url.pathname === "/apps/mission-control/renderer/") {
      file = path.join(renderer, "index.html");
    }
    if (!file.startsWith(repo) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404); res.end("not found"); return;
    }
    let body = fs.readFileSync(file);
    if (file.endsWith("index.html")) {
      body = Buffer.from(body.toString().replace(
        '<script type="module" src="./renderer.mjs">',
        '<script src="/preview-bridge.js"></script><script type="module" src="./renderer.mjs">',
      ));
    }
    res.writeHead(200, { "Content-Type": mime[path.extname(file)] || "application/octet-stream" });
    res.end(body);
  });
}
async function nav(page, view) {
  const control = page.locator('[data-test-id="nav-destination-' + view + '"]');
  await control.waitFor();
  await control.click();
}
async function openFixtureLearningInspector(page) {
  const custody = page.locator('[data-test-id="learning-forensics"]');
  await custody.waitFor();
  if (!await custody.evaluate(node => node.open)) {
    await custody.locator("summary").click();
  }
  const inspect = page.locator('[data-test-id="learning-candidate-inspect"]');
  await inspect.waitFor({ state: "visible" });
  await inspect.click();
  return inspect;
}
async function fixtureGeometry(page) {
  await page.goto(page.url().split("#")[0] + "#/view/learning", { waitUntil: "domcontentloaded" });
  const inspect = await openFixtureLearningInspector(page);
  const splitter = page.locator('[data-test-id="investigation-inspector-splitter"]');
  const geometry = await page.evaluate(() => {
    const main = document.querySelector("#main-content").getBoundingClientRect();
    const split = document.querySelector("#inspector-splitter").getBoundingClientRect();
    const inspector = document.querySelector("#inspector").getBoundingClientRect();
    return { mainRight: main.right, mainWidth: main.width, splitLeft: split.left,
      inspectorLeft: inspector.left, inspectorWidth: inspector.width };
  });
  check(geometry.mainRight <= geometry.splitLeft + 1, "desktop inspector overlaps primary");
  check(geometry.mainWidth >= 480, "desktop inspector crushes primary workspace");
  check(geometry.splitLeft <= geometry.inspectorLeft + 1, "splitter is outside inspector seam");
  await splitter.focus();
  await page.keyboard.press("Home");
  check(await splitter.getAttribute("aria-valuenow") === "160", "Home did not reach inspector minimum");
  const box = await splitter.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + 40);
  await page.mouse.down();
  await page.mouse.move(box.x - 80, box.y + 40);
  await page.mouse.up();
  const learningWidth = Number(await splitter.getAttribute("aria-valuenow"));
  check(learningWidth > 160, "pointer drag did not resize Learning inspector");
  await page.keyboard.press("Escape");
  check(await inspect.evaluate(node => node === document.activeElement),
    "Learning inspector Escape did not restore invoking control");

  await nav(page, "school");
  const capability = page.locator('[data-test-id="school-matrix-capability-b-and"]');
  await capability.waitFor();
  await capability.click();
  const schoolWidth = Number(await splitter.getAttribute("aria-valuenow"));
  check(schoolWidth !== learningWidth, "School inherited Learning inspector width");
  await splitter.focus();
  await page.keyboard.press("End");
  const schoolEnd = Number(await splitter.getAttribute("aria-valuenow"));
  check(schoolEnd > schoolWidth, "End did not expand School inspector");
  await page.keyboard.press("Escape");

  await nav(page, "learning");
  await openFixtureLearningInspector(page);
  check(Number(await splitter.getAttribute("aria-valuenow")) === learningWidth,
    "Learning width was not restored per destination");
  await page.keyboard.press("Escape");

  await page.setViewportSize({ width: 390, height: 844 });
  await openFixtureLearningInspector(page);
  const narrow = await page.evaluate(() => ({
    modal: document.querySelector("#inspector").getAttribute("aria-modal"),
    splitterDisplay: getComputedStyle(document.querySelector("#inspector-splitter")).display,
    splitterTab: document.querySelector("#inspector-splitter").tabIndex,
    mainInert: document.querySelector("#main-content").inert,
    railInert: document.querySelector(".rail").inert,
    skipInert: document.querySelector(".skip-link").inert,
  }));
  check(narrow.modal === "true", "narrow inspector is not modal");
  check(narrow.splitterDisplay === "none" && narrow.splitterTab === -1,
    "narrow inspector exposes desktop splitter");
  check(narrow.mainInert && narrow.railInert && narrow.skipInert,
    "narrow inspector leaves background focusable");
  await page.keyboard.press("Escape");
  check(await page.evaluate(() => !document.querySelector("#main-content").inert &&
    !document.querySelector(".rail").inert && !document.querySelector(".skip-link").inert),
  "narrow inspector did not clear background inert state");
}
async function productionLearning(page) {
  await page.goto(page.url().split("?")[0] + "?mode=production#/view/learning",
    { waitUntil: "domcontentloaded" });
  const view = page.locator('[data-test-id="learning-production-view"]');
  await view.waitFor();
  const text = await view.innerText();
  check(text.includes("Current accepted run"), "production Learning lacks accepted-run posture");
  check(text.includes("episode-accepted-7"), "production Learning lacks accepted episode");
  check(!text.toLowerCase().includes("reference evidence"), "production surfaced reference copy");
  check(!text.includes("44238") && !text.includes("44239"), "production surfaced fixture identity");
  check(await view.locator('[role="tab"]').count() === 4, "production Learning is not four tabs");
  check(await view.locator("time").count() >= 3, "production Learning omitted authoritative time");
}
(async () => {
  const srv = server();
  await new Promise(resolve => srv.listen(0, "127.0.0.1", resolve));
  const port = srv.address().port;
  const chrome = process.env.BILQIS_CHROME_PATH ||
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const browser = await playwright.chromium.launch({ executablePath: chrome, headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  try {
    await page.goto("http://127.0.0.1:" + port +
      "/apps/mission-control/renderer/?mode=fixtures#/view/learning",
    { waitUntil: "domcontentloaded" });
    await fixtureGeometry(page);
    await page.setViewportSize({ width: 1440, height: 960 });
    await productionLearning(page);
    check(errors.length === 0, "browser errors: " + errors.join(" | "));
    console.log("LEARNING_INSPECTOR_BROWSER_OK");
  } finally {
    await browser.close();
    await new Promise(resolve => srv.close(resolve));
  }
})().catch(error => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
