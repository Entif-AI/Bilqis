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
const fixtureOperator = JSON.parse(fs.readFileSync(
  path.join(repo, "apps/mission-control/fixtures/operator-view-v1.json"), "utf8",
));
const mime = { ".html": "text/html", ".mjs": "text/javascript", ".js": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };

const schemas = Object.freeze({
  summary: "bilqis.bamf.mission-control.semantic-atlas-snapshot/v1",
  bank: "bilqis.bamf.mission-control.semantic-bank-snapshot/v1",
  held: "bilqis.bamf.mission-control.semantic-held-mapping/v1",
  concept: "bilqis.bamf.mission-control.semantic-concept-snapshot/v1",
  state: "bilqis.bamf.mission-control.semantic-generation-state/v1",
  similarity: "bilqis.bamf.mission-control.semantic-similarity-snapshot/v1",
});
const production = Object.freeze({
  runId: "production-run",
  generation: 7,
  release: "7".repeat(64),
  semantic: "https://production.example/id/sense/atlas/primary-with-a-long-semantic-identity",
  secondary: "https://production.example/id/sense/atlas/secondary-inspector-selection",
  neighbor: "https://production.example/id/sense/atlas/neighbor-with-an-even-longer-semantic-identity",
  root: "https://production.example/id/root/atlas/source-root-with-a-long-identity",
  sourceMaterialized: 1794699000,
  summaryMaterialized: 1794699900,
  materialized: 1794700120,
  observed: 1794700118,
});
const fixtureSemantic = "https://example.test/id/sense/atlas-fixture/primary";

function check(condition, message) {
  if (!condition) throw new Error(message);
}

function runRef() {
  return {
    run_id: production.runId,
    run_identity_sha256: "4".repeat(64),
    generation: production.generation,
    generation_manifest_sha256: "1".repeat(64),
    candidate_identity_sha256: "2".repeat(64),
    factory_release_sha256: "2".repeat(64),
    semantic_release_sha256: production.release,
    topology_sha256: "4".repeat(64),
  };
}

function meta(recordId, authority, {
  run = true, observedAt = production.observed, materializedAt = production.materialized,
} = {}) {
  return {
    record_id: recordId,
    run: run ? runRef() : null,
    materialized_at: materializedAt,
    observed_at: observedAt,
    as_of: observedAt,
    coverage: "COMPLETE",
    authority,
    source_refs: [],
    evidence_refs: [],
    receipt_refs: [],
  };
}

const productionOperator = structuredClone(fixtureOperator);
productionOperator.meta.record_id = `operator-view:${production.runId}:${production.generation}`;
productionOperator.meta.run = runRef();
productionOperator.meta.source_refs = [`run-state:${production.runId}:${production.generation}`];
productionOperator.meta.evidence_refs = [`evidence:${production.runId}:${production.generation}`];
productionOperator.meta.receipt_refs = [`receipt:${production.runId}:${production.generation}`];

const conceptId = `semantic-concept:${production.release}:${production.semantic}`;
const stateId = `semantic-state:${production.runId}:${production.generation}:0:1`;
const secondaryConceptId = `semantic-concept:${production.release}:${production.secondary}`;
const secondaryStateId = `semantic-state:${production.runId}:${production.generation}:0:2`;
const similarityId = "semantic-similarity:production:primary-neighbor";
const productionData = Object.freeze({
  summary: {
    schema_version: schemas.summary,
    meta: meta(`semantic-atlas:${production.runId}:${production.generation}`, "DERIVED", {
      materializedAt: production.summaryMaterialized,
    }),
    atlas_bundle_id: "5".repeat(64),
    atlas_release_sha256: production.release,
    source_bundle_id: "6".repeat(64),
    active_concepts: { state: "PRESENT", origin: "DERIVED", value: 742, units: null },
    source_eligible: { state: "PRESENT", origin: "SOURCE_AUTHORITATIVE", value: 801, units: null },
    source_held: { state: "PRESENT", origin: "SOURCE_AUTHORITATIVE", value: 1, units: null },
  },
  bank: {
    schema_version: schemas.bank,
    meta: meta(`semantic-bank:${production.runId}:${production.generation}:0`, "DERIVED"),
    bank: 0, row_capacity: 8192, allocated_rows: 500, active_rows: 482, masked_rows: 18,
    newly_admitted_rows: 6, recently_exercised_rows: 41, requalification_affected_rows: 3,
  },
  held: {
    schema_version: schemas.held,
    meta: meta("semantic-held:production:ambiguous", "SOURCE_AUTHORITATIVE", {
      run: false, materializedAt: production.sourceMaterialized,
    }),
    atlas_release_sha256: production.release,
    domain: "mapping", table: "production_mapping", key: "ambiguous-production",
    semantic_id: null, source_disposition: "HELD", implementation_status: "UNRESOLVED",
    reason_code: "AMBIGUOUS_MAPPING", teaching_reason: "HOLD_FOR_REVIEW", owner: "SOURCE_OWNER",
  },
  concept: {
    schema_version: schemas.concept,
    meta: meta(conceptId, "SOURCE_AUTHORITATIVE", {
      run: false, materializedAt: production.sourceMaterialized,
    }),
    atlas_release_sha256: production.release,
    semantic_id: production.semantic,
    kind: "sense",
    types: ["skos:Concept"], labels: [], realizations: [],
    source_loci: ["Production semantic source row 12 with a deliberately long source locus value"],
    source_rows: [],
    relations: Array.from({ length: 14 }, (_, index) => ({
      predicate: index % 2 ? "skos:related" : "skos:broader",
      target_semantic_id: `${production.root}/relation-${String(index).padStart(2, "0")}-with-long-target-identity`,
    })),
    abi_index: 1, abi_bank: 0, abi_row: 1,
    implementation_status: "ADMITTED", teaching_candidate: true,
    teaching_reason: "SOURCE_ELIGIBLE", frame_schema_refs: ["frame:relation/v2"],
    capability_ids: ["B.PRODUCTION.ATLAS"],
  },
  secondaryConcept: {
    schema_version: schemas.concept,
    meta: meta(secondaryConceptId, "SOURCE_AUTHORITATIVE", {
      run: false, materializedAt: production.sourceMaterialized,
    }),
    atlas_release_sha256: production.release,
    semantic_id: production.secondary,
    kind: "sense",
    types: ["skos:Concept"], labels: [], realizations: [],
    source_loci: ["Production semantic source row 13"], source_rows: [],
    relations: [{ predicate: "skos:broader", target_semantic_id: production.root }],
    abi_index: 2, abi_bank: 0, abi_row: 2,
    implementation_status: "ADMITTED", teaching_candidate: true,
    teaching_reason: "SOURCE_ELIGIBLE", frame_schema_refs: ["frame:relation/v2"],
    capability_ids: ["B.PRODUCTION.ATLAS"],
  },
  state: {
    schema_version: schemas.state,
    meta: meta(stateId, "DERIVED"),
    semantic_id: production.semantic,
    concept_record_id: conceptId,
    abi_index: 1, abi_bank: 0, abi_row: 1,
    admission_state: "ACTIVE", newly_admitted: false,
    recently_exercised: true, requalification_affected: false,
  },
  secondaryState: {
    schema_version: schemas.state,
    meta: meta(secondaryStateId, "DERIVED"),
    semantic_id: production.secondary,
    concept_record_id: secondaryConceptId,
    abi_index: 2, abi_bank: 0, abi_row: 2,
    admission_state: "ACTIVE", newly_admitted: false,
    recently_exercised: false, requalification_affected: false,
  },
  similarity: {
    schema_version: schemas.similarity,
    meta: meta(similarityId, "DERIVED"),
    source_semantic_id: production.semantic,
    target_semantic_id: production.neighbor,
    basis_ref: "embedding:production:g7",
    similarity: { state: "PRESENT", origin: "DERIVED", value: 0.91, units: "similarity" },
    canonical_equivalence: false,
  },
});

const bridge = `
const mode = new URL(location.href).searchParams.get("launchMode") === "fixtures" ? "fixtures" : "production";
const fixtureOperator = ${JSON.stringify(fixtureOperator)};
const productionOperator = ${JSON.stringify(productionOperator)};
const data = ${JSON.stringify(productionData)};
const schemas = ${JSON.stringify(schemas)};
const semantic = ${JSON.stringify(production.semantic)};
const conceptId = ${JSON.stringify(conceptId)};
const stateId = ${JSON.stringify(stateId)};
const secondaryConceptId = ${JSON.stringify(secondaryConceptId)};
const secondaryStateId = ${JSON.stringify(secondaryStateId)};
const similarityId = ${JSON.stringify(similarityId)};
function page(request, records = [], links = []) {
  const total = records.length + links.length;
  return { schema: "bilqis.bamf.control-plane.query-page/v1", query_id: "e".repeat(64), request,
    family: request.family, mode: request.mode, state: total ? "PRESENT" : "EMPTY", coverage: "COMPLETE",
    total_matches: total, returned: total, truncated: false, next_cursor: null,
    records, markers: [], links, accepted: true };
}
async function productionQuery(request) {
  if (request.schema_version === schemas.summary) return page(request, [data.summary]);
  if (request.schema_version === schemas.bank) return page(request, [data.bank]);
  if (request.schema_version === schemas.held) return page(request, [data.held]);
  if (request.schema_version === schemas.similarity) return page(request, [data.similarity]);
  if (request.record_id === conceptId) return page(request, [data.concept]);
  if (request.record_id === stateId) return page(request, [data.state]);
  if (request.record_id === secondaryConceptId) return page(request, [data.secondaryConcept]);
  if (request.record_id === secondaryStateId) return page(request, [data.secondaryState]);
  if (request.record_id === similarityId) return page(request, [data.similarity]);
  if (request.family === "reference" && request.reference === semantic) return page(request, [], [{
    relation: "LEARNED_SIMILARITY_SOURCE", source_record_id: similarityId,
    target_ref: semantic, target_record_id: similarityId,
  }]);
  return page(request);
}
window.bamfMissionControl = {
  launchMode: mode,
  connect: async () => ({ state: "healthy", serviceLive: true, serviceReady: true, learnerReady: true,
    learnerActive: false, learnerState: "READY", runId: mode === "fixtures" ? "fixture-run" : "production-run",
    generation: 7 }),
  status: async () => ({ learnerActive: false }),
  querySnapshot: async request => request?.schemaVersion
    ? structuredClone(mode === "fixtures" ? fixtureOperator : productionOperator)
    : Promise.reject(new Error("BROWSER_SNAPSHOT_UNAVAILABLE")),
  query: productionQuery,
  subscribeEvents: () => async () => {},
  requestDryRun: async () => { throw new Error("BROWSER_MUTATION_DISABLED"); },
  requestCommand: async () => { throw new Error("BROWSER_MUTATION_DISABLED"); },
  fetchReceipt: async () => null,
};`;

function server() {
  return http.createServer((request, response) => {
    const url = new URL(request.url, "http://127.0.0.1");
    if (url.pathname === "/preview-bridge.mjs") {
      response.writeHead(200, { "Content-Type": "text/javascript" }); response.end(bridge); return;
    }
    if (url.pathname === "/axe.min.js") {
      response.writeHead(200, { "Content-Type": "text/javascript" }); response.end(fs.readFileSync(axePath)); return;
    }
    let file = path.join(repo, decodeURIComponent(url.pathname));
    if (url.pathname === "/" || url.pathname === "/apps/mission-control/renderer/") {
      file = path.join(renderer, "index.html");
    }
    if (!file.startsWith(repo) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      response.writeHead(404); response.end("not found"); return;
    }
    let body = fs.readFileSync(file);
    if (file.endsWith("index.html")) body = Buffer.from(body.toString().replace(
      '<script type="module" src="./renderer.mjs">',
      '<script src="/preview-bridge.mjs"></script><script type="module" src="./renderer.mjs">',
    ));
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
