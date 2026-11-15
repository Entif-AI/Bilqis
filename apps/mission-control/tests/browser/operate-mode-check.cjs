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
const mime = { ".html": "text/html", ".mjs": "text/javascript", ".js": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };

function check(condition, message) { if (!condition) throw new Error(message); }

const operator = {
  schema_version: "bilqis.bamf.mission-control.operator-view/v1",
  learner_state: "READY",
  stage: "ASSESS_MAIN",
  active_capability_id: "B.BROWSER",
  related_record_ids: [],
  meta: {
    record_id: "operator-view:browser-production:7",
    run: {
      run_id: "browser-production-run",
      run_identity_sha256: "1".repeat(64),
      generation: 7,
      generation_manifest_sha256: "2".repeat(64),
      candidate_identity_sha256: "3".repeat(64),
      factory_release_sha256: "4".repeat(64),
      semantic_release_sha256: "5".repeat(64),
      topology_sha256: "6".repeat(64),
    },
    materialized_at: 1794700120,
    observed_at: 1794700118,
    as_of: 1794700118,
    coverage: "COMPLETE",
    authority: "DERIVED",
    source_refs: ["run-state:browser-production:7"],
    evidence_refs: [],
    receipt_refs: [],
  },
};

const bridge = `
const launchMode=new URL(location.href).searchParams.get("launchMode")==="fixtures"?"fixtures":"production";
const operator=${JSON.stringify(operator)};
const target={schema:"bilqis.bamf.control-plane.command-target-public/v1",target_ref:"command-target:${"a".repeat(64)}",run_id:operator.meta.run.run_id,run_seed:7,run_identity_sha256:operator.meta.run.run_identity_sha256,generation:operator.meta.run.generation,generation_manifest_sha256:operator.meta.run.generation_manifest_sha256,optimizer_step:42,candidate_identity_sha256:operator.meta.run.candidate_identity_sha256,factory_release_sha256:operator.meta.run.factory_release_sha256,semantic_release_sha256:operator.meta.run.semantic_release_sha256,topology_sha256:operator.meta.run.topology_sha256,acceptance_sha256:"7".repeat(64),source_identity:"source:browser-production"};
let lastRequest=null;
window.__operateCalls={preview:0,command:0,receipt:0};
function receipt(request,state="COMPLETED") { const now=Date.now(); return {schema_version:"bilqis.bamf.mission-control.operator-action-receipt/v2",meta:{record_id:"receipt:browser-production",run:null,materialized_at:now,observed_at:now,as_of:now,coverage:"COMPLETE",authority:"DERIVED",source_refs:["authority:c11-bamf-operator"],evidence_refs:[target.target_ref],receipt_refs:[]},request_id:request.request_id,request_sha256:"8".repeat(64),operation_id:"operation:${"b".repeat(64)}",state,acknowledged_at:now,target_ref:target.target_ref,postcondition_ref:"command-postcondition:browser",error_ref:null}; }
function inspection(request) { return {schema:"bilqis.bamf.control-plane.command-inspection/v1",operation_id:"operation:${"b".repeat(64)}",request,action:request.action,mode:request.dry_run?"dry-run":(["status","checkpoint-verify"].includes(request.action)?"read-only":"mutating"),target,target_ref:target.target_ref,expected_postcondition:"operator-run-completed",consequence:{mutation:request.dry_run||["status","checkpoint-verify"].includes(request.action)?"NONE":"MUTATING",neural_mutation_permitted:!request.dry_run&&!["status","checkpoint-verify"].includes(request.action)},preflight:{kind:"preflight",result:"READY",admission_policy:"staged",optimizer_hyperparameters:null,source_prefetch_workers:2,generation_manifest_sha256:target.generation_manifest_sha256,ready_for_training:true,neural_updates:0,resource_profile:{source_prefetch_workers:2,batch_size:8,reserve_gib:100,minutes:30,steps_per_visit:12,max_visits:1}},receipt:receipt(request),postcondition:{kind:"browser-proof",cli_exit:0},logs:{stdout_tail:"browser trainer ready\\n",stderr_tail:null}}; }
window.bamfMissionControl={
  launchMode,
  connect:async()=>({state:"healthy",serviceLive:true,learnerReady:true}),
  status:async()=>({learnerActive:false}),
  querySnapshot:async request=>request&&request.schemaVersion?operator:{accepted:true,family:request&&request.family,mode:request&&request.mode,state:"EMPTY",coverage:"COMPLETE",records:[],next_cursor:null},
  query:async request=>({accepted:true,family:request&&request.family,mode:request&&request.mode,state:"EMPTY",coverage:"COMPLETE",records:[],next_cursor:null}),
  subscribeEvents:()=>async()=>{},
  requestDryRun:async wrapper=>{window.__operateCalls.preview+=1;lastRequest=wrapper.request;return {...inspection(wrapper.request),schema:"bilqis.bamf.control-plane.command-preview/v1",receipt:null,postcondition:null,logs:null};},
  requestCommand:async wrapper=>{window.__operateCalls.command+=1;lastRequest=wrapper.request;return receipt(wrapper.request,"ACCEPTED");},
  fetchReceipt:async()=>{window.__operateCalls.receipt+=1;return inspection(lastRequest);},
};`;

function server() {
  return http.createServer((request, response) => {
    const url = new URL(request.url, "http://127.0.0.1");
    if (url.pathname === "/operate-bridge.mjs") {
      response.writeHead(200, { "Content-Type": "text/javascript" }); response.end(bridge); return;
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
      '<script src="/operate-bridge.mjs"></script><script type="module" src="./renderer.mjs">'));
    response.writeHead(200, { "Content-Type": mime[path.extname(file)] || "application/octet-stream" });
    response.end(body);
  });
}

async function setDisplay(page, theme, density) {
  await page.evaluate(({ theme, density }) => {
    localStorage.setItem("bilqis.mc.theme", theme);
    localStorage.setItem("bilqis.mc.density", density);
  }, { theme, density });
  await page.reload({ waitUntil: "domcontentloaded" });
}

async function axe(page, label) {
  const result = await page.locator('[data-test-id="operate-view"]').evaluate(async node => {
    const outcome = await axe.run(node, {
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
    });
    return {
      violations: outcome.violations.map(item => ({ id: item.id, nodes: item.nodes.map(entry => entry.target) })),
      overflow: document.documentElement.scrollWidth > innerWidth + 1,
      overflowers: [...node.querySelectorAll("*")].map(item => {
        const rect = item.getBoundingClientRect();
        return { item, rect };
      }).filter(({ rect }) => rect.right > innerWidth + 1 || rect.left < -1)
        .slice(0, 8).map(({ item, rect }) => ({
          tag: item.tagName, testId: item.getAttribute("data-test-id"), className: item.className,
          left: Math.round(rect.left), right: Math.round(rect.right), width: Math.round(rect.width),
          scrollWidth: item.scrollWidth, clientWidth: item.clientWidth,
        })),
    };
  });
  check(result.violations.length === 0, label + " axe: " + JSON.stringify(result.violations));
  check(!result.overflow, label + " caused document overflow: " + JSON.stringify(result.overflowers));
}

async function navigateFromEvidence(page) {
  await page.locator('[data-test-id="nav-destination-evidence"]').click();
  await page.waitForFunction(() => document.querySelector('[data-test-id="shell-destination-title"]')?.textContent === "Evidence");
  await page.evaluate(() => {
    document.querySelector("#domain-view").innerHTML = '<section data-test-id="stale-evidence-sentinel"><h2>Evidence</h2><p>Reference fixture catalog</p></section>';
  });
  await page.locator('[data-test-id="nav-destination-operate"]').click();
  await page.locator('[data-test-id="operate-view"]').waitFor();
  check(await page.locator('[data-test-id="shell-destination-title"]').innerText() === "Operate", "Operate shell heading did not switch");
  check(await page.locator('[data-test-id="stale-evidence-sentinel"]').count() === 0, "stale Evidence content survived Operate navigation");
  check(!(await page.locator('[data-test-id="operate-view"]').innerText()).includes("Reference fixture catalog"), "generic fixture copy leaked into Operate");
}

async function exerciseProduction(page, label) {
  await navigateFromEvidence(page);
  await page.addScriptTag({ url: "/axe.min.js" });
  const tabs = page.locator('[data-test-id="operate-tabs"]');
  check(await tabs.count() === 1, "Operate must render one stage tablist");
  check(await tabs.locator('[data-test-id^="operate-tab-"]').count() === 4, "Operate must render four stage tabs");
  check(await page.locator('[data-test-id^="operate-panel-"]').evaluateAll(nodes => nodes.filter(node => !node.hidden).length) === 1,
    "Operate must render one visible stage panel");
  await axe(page, label + ":request");

  const requestTab = page.locator('[data-test-id="operate-tab-request"]');
  await requestTab.focus();
  await page.keyboard.press("ArrowRight");
  const preflightTab = page.locator('[data-test-id="operate-tab-preflight"]');
  check(await preflightTab.evaluate(node => node === document.activeElement), "future Preflight tab was not keyboard reachable");
  await page.keyboard.press("Enter");
  check(await preflightTab.getAttribute("aria-selected") === "false", "future Preflight stage activated before request review");

  await page.locator('[data-test-id="operate-action-resume"]').click();
  const dryRun = page.locator('[data-test-id="operate-request-dry-run"]');
  check(await dryRun.isChecked(), "Resume did not start in dry-run posture");
  await dryRun.focus();
  await dryRun.uncheck();
  check(await page.locator('[data-test-id="operate-request-dry-run"]').evaluate(node => node === document.activeElement), "dry-run rerender lost keyboard focus");
  const parameters = page.locator('[data-test-id="operate-request-parameters"]');
  await parameters.fill('{"minutes":30}');
  await page.locator('[data-test-id="operate-request-preview"]').focus();
  await page.locator('[data-test-id="operate-request-preview"]').click();
  await page.locator('[data-test-id="operate-preflight"]').waitFor();
  check(await preflightTab.evaluate(node => node === document.activeElement), "Preview did not move focus to Preflight stage");
  check(await preflightTab.getAttribute("aria-selected") === "true", "Preflight stage did not activate after preview");
  check((await page.locator('[data-test-id="operate-preflight-fact-target-ref"]').innerText()).includes("command-target:"), "Preflight omitted exact target identity");
  await axe(page, label + ":preflight");

  const authTab = page.locator('[data-test-id="operate-tab-authorization"]');
  await authTab.click();
  const auth = page.locator('[data-test-id="operate-authorization-phrase"]');
  await auth.fill("AUTHORIZE RESUME");
  check(await page.locator('[data-test-id="operate-authorization-submit"]').isEnabled(), "exact authorization phrase did not unlock reviewed submission");
  await requestTab.click();
  check(await parameters.inputValue() === '{"minutes":30}', "request parameters were lost across stage navigation");
  check(!(await dryRun.isChecked()), "dry-run state was lost across stage navigation");
  await authTab.click();
  check(await auth.inputValue() === "AUTHORIZE RESUME", "authorization phrase was lost across stage navigation");
  await axe(page, label + ":authorization");

  await page.locator('[data-test-id="operate-authorization-submit"]').focus();
  await page.locator('[data-test-id="operate-authorization-submit"]').click();
  const outcomeTab = page.locator('[data-test-id="operate-tab-outcome"]');
  await page.locator('[data-test-id="operate-receipt"]').waitFor();
  check(await outcomeTab.evaluate(node => node === document.activeElement), "Submit did not move focus to Outcome stage");
  check(await page.locator('[data-test-id="operate-receipt-state"]').innerText() === "COMPLETED", "authoritative outcome was not rendered");
  const times = await page.locator('[data-test-id="operate-receipt-times"] [data-source-unix-seconds]').evaluateAll(nodes => nodes.map(node => ({ source: node.dataset.sourceUnixSeconds, iso: node.getAttribute("datetime") })));
  check(times.length >= 4, "Operate omitted authoritative receipt times");
  check(times.every(item => Number(item.source) > 1_700_000_000 && /^20\d\d-/.test(item.iso)), "Operate rendered implausible command time: " + JSON.stringify(times));
  check(await page.locator('[data-test-id="operate-help-receipt-trigger"]').count() === 1, "Outcome missing receipt help");
  check(await page.locator('[data-test-id="operate-help-logs-trigger"]').count() === 1, "Outcome missing log help");
  await axe(page, label + ":outcome");

  await requestTab.click();
  const stop = page.locator('[data-test-id="operate-action-stop"]');
  check(await stop.getAttribute("data-posture") === "destructive", "Stop lacks structural destructive posture");
  check((await stop.innerText()).toLowerCase().includes("authorization required"), "Stop lacks non-color authorization cue");
  const text = await page.locator('[data-test-id="operate-view"]').innerText();
  check(!/REFERENCE FIXTURES|fixture-run|Reference fixture evidence/.test(text), "production Operate leaked fixture copy or identity");
  const calls = await page.evaluate(() => window.__operateCalls);
  check(calls.preview === 1 && calls.command === 1, "production browser workflow did not use exactly one reviewed preview/command: " + JSON.stringify(calls));
}

async function exerciseFixture(page, label) {
  await page.addScriptTag({ url: "/axe.min.js" });
  await page.locator('[data-test-id="operate-view"]').waitFor();
  check(await page.locator('[data-test-id="shell-mode-badge"]').innerText() === "REFERENCE FIXTURES", "fixture launch did not persistently identify itself");
  check(await page.locator('[data-test-id="nav-destination-operate"]').isDisabled(), "fixture launch left Operate navigation enabled");
  check(await page.locator('[data-test-id="operate-unavailable"]').count() === 1, "fixture deep link did not render Operate-specific unavailable posture");
  check(await page.locator('[data-test-id="operate-request-preview"]').isDisabled(), "fixture deep link exposed command preflight");
  const calls = await page.evaluate(() => window.__operateCalls);
  check(calls.preview === 0 && calls.command === 0, "fixture launch reached command surfaces: " + JSON.stringify(calls));
  await axe(page, label + ":fixture");
}

(async () => {
  const app = server();
  await new Promise(resolve => app.listen(0, "127.0.0.1", resolve));
  const port = app.address().port;
  const browser = await playwright.chromium.launch({ executablePath: chrome, headless: true });
  const results = [];
  try {
    for (const variant of [
      { viewport: { width: 1440, height: 960 }, theme: "dark", density: "comfortable" },
      { viewport: { width: 390, height: 844 }, theme: "light", density: "compact" },
    ]) {
      const page = await browser.newPage({ viewport: variant.viewport, reducedMotion: "reduce" });
      await page.goto(`http://127.0.0.1:${port}/apps/mission-control/renderer/?launchMode=production`, { waitUntil: "domcontentloaded" });
      await setDisplay(page, variant.theme, variant.density);
      if (variant.viewport.width < 500) await page.evaluate(() => { document.documentElement.dir = "rtl"; });
      await exerciseProduction(page, `production:${variant.viewport.width}`);
      results.push({ mode: "production", ...variant });
      await page.close();
    }

    const fixture = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await fixture.goto(`http://127.0.0.1:${port}/apps/mission-control/renderer/?launchMode=fixtures#/view/operate`, { waitUntil: "domcontentloaded" });
    await exerciseFixture(fixture, "fixtures:390");
    results.push({ mode: "fixtures", viewport: { width: 390, height: 844 } });
    await fixture.close();
    console.log(JSON.stringify({ ok: true, results }, null, 2));
  } finally {
    await browser.close();
    await new Promise(resolve => app.close(resolve));
  }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
