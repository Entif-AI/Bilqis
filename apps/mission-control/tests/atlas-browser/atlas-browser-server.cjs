"use strict";

const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const {
  fixtureOperator, productionOperator, productionData, schemas, production,
  conceptId, stateId, secondaryConceptId, secondaryStateId, similarityId, repo,
} = require("./atlas-browser-data.cjs");
const renderer = path.join(repo, "apps/mission-control/renderer");
const axePath = process.env.BILQIS_AXE_MODULE || require.resolve("axe-core/axe.min.js");
const mime = { ".html": "text/html", ".mjs": "text/javascript", ".js": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };

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

module.exports = { server };
