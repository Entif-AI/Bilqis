"use strict";

const crypto = require("node:crypto");
const OPERATOR_VIEW = require("../fixtures/operator-view-v1.json");
const { frameFixturePage } = require("./frame-fixtures.cjs");

const OPERATOR_VIEW_SCHEMA = "bilqis.bamf.mission-control.operator-view/v1";
const SNAPSHOT_QUERY_SCHEMA = "bamf.gui20.operator-view-query/v1";
const QUERY_SCHEMA = "bilqis.bamf.control-plane.query/v1";

function fixtureStatus() {
  return Object.freeze({
    schemaVersion: "bamf.gui20.cp01-status/v1",
    state: "healthy",
    protocolVersion: "bilqis.bamf.control-plane/v1",
    serviceLive: true,
    serviceReady: true,
    learnerReady: true,
    learnerActive: false,
    learnerState: "fixture-reference",
    runId: OPERATOR_VIEW.meta.run.run_id,
    generation: OPERATOR_VIEW.meta.run.generation,
    optimizerStep: null,
    failureCode: null,
  });
}

function fixturePage(request) {
  const canonical = JSON.stringify(request, Object.keys(request).sort());
  return Object.freeze({
    schema: "bilqis.bamf.control-plane.query-page/v1",
    query_id: crypto.createHash("sha256").update(canonical).digest("hex"),
    request: structuredClone(request),
    family: request.family,
    mode: request.mode,
    state: "EMPTY",
    coverage: "COMPLETE",
    total_matches: 0,
    returned: 0,
    truncated: false,
    next_cursor: null,
    records: Object.freeze([]),
    markers: Object.freeze([]),
    links: Object.freeze([]),
    accepted: true,
  });
}

class FixtureControlPlaneAdapter {
  constructor() {
    this.session = Object.freeze({ fixture: Symbol("mission-control-fixtures") });
  }

  async connect() {
    return { session: this.session, publicStatus: fixtureStatus() };
  }

  async disconnect(session) {
    this.#requireSession(session);
  }

  async status(session) {
    this.#requireSession(session);
    return fixtureStatus();
  }

  async snapshot(session, request) {
    this.#requireSession(session);
    if (request?.schemaVersion === "bamf.gui08.frame-query/v1") {
      return frameFixturePage(request);
    }
    if (request?.schemaVersion === SNAPSHOT_QUERY_SCHEMA &&
        request?.schema === OPERATOR_VIEW_SCHEMA) {
      return structuredClone(OPERATOR_VIEW);
    }
    if (request?.schema === QUERY_SCHEMA) {
      const { accepted: _accepted, ...page } = fixturePage(request);
      return page;
    }
    throw this.#unavailable();
  }

  async query(session, request) {
    this.#requireSession(session);
    return fixturePage(request);
  }

  async dryRun(session) {
    this.#requireSession(session);
    throw this.#unavailable();
  }

  async command(session) {
    this.#requireSession(session);
    throw this.#unavailable();
  }

  async receipt(session) {
    this.#requireSession(session);
    throw this.#unavailable();
  }

  async subscribe(session) {
    this.#requireSession(session);
    return () => {};
  }

  close() {}

  #requireSession(session) {
    if (session !== this.session) {
      throw new TypeError("BAMF_GUI20_FIXTURE_SESSION_INVALID");
    }
  }

  #unavailable() {
    const error = new Error("BAMF_GUI20_FIXTURE_OPERATION_UNAVAILABLE");
    error.code = "BAMF_GUI20_FIXTURE_OPERATION_UNAVAILABLE";
    return error;
  }
}

module.exports = { FixtureControlPlaneAdapter, fixtureStatus };
