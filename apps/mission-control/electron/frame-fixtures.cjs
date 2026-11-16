"use strict";

const pages = require("../fixtures/frame-inspections-v1.json");

function frameFixturePage(request) {
  const found = pages.find(page => page.request.runId === request.runId &&
    page.request.generation === request.generation);
  return found ? { ...structuredClone(found), request: structuredClone(request) } : {
    schemaVersion: "bamf.gui08.frame-page/v1", request: structuredClone(request),
    state: "MISSING", coverage: "UNKNOWN", provenance: "ILLUSTRATIVE_FIXTURE",
    operatorView: null, examples: [],
  };
}

module.exports = { frameFixturePage };
