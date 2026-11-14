"use strict";

const { Cp01PythonBroker } = require("./cp01-python-broker.cjs");
const { frameFixturePage } = require("./frame-fixtures.cjs");

const OPERATOR_VIEW_SCHEMA = "bilqis.bamf.mission-control.operator-view/v1";
const SNAPSHOT_QUERY_SCHEMA = "bamf.gui20.operator-view-query/v1";

function runQuery() {
  return {
    schema: "bilqis.bamf.control-plane.query/v1",
    family: "run",
    mode: "current",
    run_id: null,
    record_id: null,
    schema_version: null,
    generation: null,
    frontier_id: null,
    as_of: null,
    reference: null,
    cursor: null,
    limit: 32,
  };
}

function operatorViewUnavailable(state = "UNKNOWN") {
  const error = new Error(`BAMF_GUI20_OPERATOR_VIEW_UNAVAILABLE:${state}`);
  error.code = "BAMF_GUI20_OPERATOR_VIEW_UNAVAILABLE";
  return error;
}

function disconnectedStatus() {
  return {
    schemaVersion: "bamf.gui20.cp01-status/v1",
    state: "disconnected",
    protocolVersion: "bilqis.bamf.control-plane/v1",
    serviceLive: false,
    serviceReady: false,
    learnerReady: false,
    learnerActive: null,
    learnerState: null,
    runId: null,
    generation: null,
    optimizerStep: null,
    failureCode: null,
  };
}

class AcceptedControlPlaneAdapter {
  constructor({ broker = new Cp01PythonBroker() } = {}) {
    this.broker = broker;
    this.session = Object.freeze({ session: Symbol("gui20-main-session") });
  }

  async connect() {
    let publicStatus;
    try {
      publicStatus = await this.broker.connect();
    } catch (_error) {
      publicStatus = disconnectedStatus();
    }
    return { session: this.session, publicStatus };
  }

  async disconnect(session) {
    this.#requireSession(session);
    try {
      await this.broker.disconnect();
    } catch (_error) {
      // A lost broker is already disconnected from the renderer's perspective.
    }
  }

  async status(session) {
    this.#requireSession(session);
    try {
      return await this.broker.status();
    } catch (_error) {
      return disconnectedStatus();
    }
  }

  async snapshot(session, request) {
    this.#requireSession(session);
    if (request?.schema === "bilqis.bamf.control-plane.query/v1") {
      const { accepted, ...page } = await this.broker.query(request);
      if (accepted !== true) throw new Error("BAMF_GUI05_QUERY_UNAVAILABLE");
      return page;
    }
    if (request?.schemaVersion === "bamf.gui08.frame-query/v1") return frameFixturePage(request);
    if (request?.schemaVersion === SNAPSHOT_QUERY_SCHEMA && request?.schema === OPERATOR_VIEW_SCHEMA) {
      const page = await this.broker.query(runQuery());
      if (page?.accepted !== true || !Array.isArray(page.records)) {
        throw operatorViewUnavailable(page?.state);
      }
      const operatorView = [...page.records].reverse().find(
        (record) => record?.schema_version === OPERATOR_VIEW_SCHEMA,
      );
      if (!operatorView) throw operatorViewUnavailable(page.state);
      return structuredClone(operatorView);
    }
    throw operatorViewUnavailable();
  }

  async query(session, request) {
    this.#requireSession(session);
    return this.broker.query(request);
  }

  async dryRun(session, request) {
    this.#requireSession(session);
    return this.broker.previewCommand(request.request);
  }

  async command(session, request) {
    this.#requireSession(session);
    return this.broker.submitCommand(request.request, request.expectedTargetRef);
  }

  async receipt(session, operationId) {
    this.#requireSession(session);
    return this.broker.inspectCommand(operationId);
  }

  async subscribe(session, next) {
    this.#requireSession(session);
    if (typeof next !== "function") {
      throw new TypeError("BAMF_GUI03_EVENT_LISTENER_REQUIRED");
    }
    return this.broker.subscribe(next);
  }

  close() {
    this.broker.close();
  }

  #requireSession(session) {
    if (session !== this.session) {
      const error = new Error("BAMF_GUI20_SESSION_INVALID");
      error.code = "BAMF_GUI20_SESSION_INVALID";
      throw error;
    }
  }
}

module.exports = { AcceptedControlPlaneAdapter, disconnectedStatus };
