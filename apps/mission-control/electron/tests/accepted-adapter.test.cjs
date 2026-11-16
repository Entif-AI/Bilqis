"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  AcceptedControlPlaneAdapter,
  disconnectedStatus,
} = require("../accepted-control-plane-adapter.cjs");
const {
  OPERATOR_VIEW_SCHEMA,
  QUERY_PAGE_SCHEMA,
  QUERY_REQUEST_SCHEMA,
  SNAPSHOT_QUERY_SCHEMA,
  createAcceptedValidators,
} = require("../accepted-contracts.cjs");
const { ControlPlaneBridge } = require("../control-plane-bridge.cjs");
const OPERATOR_VIEW = require("../../fixtures/operator-view-v1.json");
const {
  OPERATION_ID, TARGET_REF, actionRequest, inspection, preview, receipt,
} = require("./_operator-fixture.cjs");

function brokerFixture({ fail = false } = {}) {
  const calls = [];
  let eventListener = null;
  return {
    calls,
    async connect() {
      calls.push("connect");
      if (fail) throw new Error("socket path must not escape");
      return {
        schemaVersion: "bamf.gui20.cp01-status/v1",
        state: "learner-unavailable",
        protocolVersion: "bilqis.bamf.control-plane/v1",
        serviceLive: true,
        serviceReady: true,
        learnerReady: false,
        learnerActive: false,
        learnerState: "learner-unavailable",
        runId: null,
        generation: null,
        optimizerStep: null,
        failureCode: null,
      };
    },
    async status() {
      calls.push("status");
      if (fail) throw new Error("private run path");
      return {
        schemaVersion: "bamf.gui20.cp01-status/v1",
        state: "healthy",
        protocolVersion: "bilqis.bamf.control-plane/v1",
        serviceLive: true,
        serviceReady: true,
        learnerReady: true,
        learnerActive: true,
        learnerState: "healthy",
        runId: "fixture-run",
        generation: 7,
        optimizerStep: 19,
        failureCode: null,
      };
    },
    async query(request) {
      calls.push(["query", request]);
      const records = request.family === "run" ? [structuredClone(OPERATOR_VIEW)] : [];
      return {
        schema: QUERY_PAGE_SCHEMA,
        query_id: "a".repeat(64),
        request,
        family: request.family,
        mode: request.mode,
        state: records.length ? "PRESENT" : "EMPTY",
        coverage: "COMPLETE",
        total_matches: records.length,
        returned: records.length,
        truncated: false,
        next_cursor: null,
        records,
        markers: [],
        links: [],
        accepted: true,
      };
    },
    async previewCommand(request) {
      calls.push(["previewCommand", request]);
      return preview(request);
    },
    async submitCommand(request, expectedTargetRef) {
      calls.push(["submitCommand", request, expectedTargetRef]);
      return receipt(request);
    },
    async inspectCommand(operationId) {
      calls.push(["inspectCommand", operationId]);
      return inspection(actionRequest({ humanAuthorized: true }));
    },
    subscribe(listener) {
      calls.push("subscribe");
      eventListener = listener;
      return () => { calls.push("unsubscribe"); eventListener = null; };
    },
    emit(value) { eventListener?.(value); },
    async disconnect() { calls.push("disconnect"); },
    close() { calls.push("close"); },
  };
}

async function acceptedBridge(broker) {
  const { assertOperatorView } = await import("../../renderer/shell-state.mjs");
  const adapter = new AcceptedControlPlaneAdapter({ broker });
  return {
    adapter,
    bridge: new ControlPlaneBridge(adapter, createAcceptedValidators(assertOperatorView)),
  };
}

test("accepted adapter derives the shell OperatorView from the live CP03 run projection", async () => {
  const broker = brokerFixture();
  const { adapter, bridge } = await acceptedBridge(broker);

  const connected = await bridge.connect();
  const status = await bridge.status();
  const snapshot = await bridge.snapshot({
    schemaVersion: SNAPSHOT_QUERY_SCHEMA,
    schema: OPERATOR_VIEW_SCHEMA,
  });

  assert.equal(connected.state, "learner-unavailable");
  assert.equal(connected.serviceLive, true);
  assert.equal(status.state, "healthy");
  assert.equal(snapshot.schema_version, OPERATOR_VIEW_SCHEMA);
  assert.equal(snapshot.meta.run.run_id, "fixture-run");
  assert.equal(JSON.stringify(connected).includes("session"), false);
  await bridge.disconnect();
  adapter.close();
  assert.equal(broker.calls[0], "connect");
  assert.equal(broker.calls[1], "status");
  assert.deepEqual(broker.calls[2][0], "query");
  assert.equal(broker.calls[2][1].family, "run");
  assert.deepEqual(broker.calls.slice(3), ["disconnect", "close"]);
});

test("accepted adapter never substitutes the checked-in fixture when live run telemetry is absent", async () => {
  const broker = brokerFixture();
  broker.query = async (request) => ({
    schema: QUERY_PAGE_SCHEMA, query_id: "b".repeat(64), request,
    family: request.family, mode: request.mode, state: "UNAVAILABLE", coverage: "UNKNOWN",
    total_matches: 0, returned: 0, truncated: false, next_cursor: null,
    records: [], markers: [], links: [], accepted: true,
  });
  const { bridge } = await acceptedBridge(broker);
  await bridge.connect();
  await assert.rejects(
    bridge.snapshot({ schemaVersion: SNAPSHOT_QUERY_SCHEMA, schema: OPERATOR_VIEW_SCHEMA }),
    /BAMF_GUI20_OPERATOR_VIEW_UNAVAILABLE:UNAVAILABLE/,
  );
});

test("accepted adapter exposes only the bounded CP03 query contract", async () => {
  const broker = brokerFixture();
  const { adapter, bridge } = await acceptedBridge(broker);
  await bridge.connect();
  const request = {
    schema: QUERY_REQUEST_SCHEMA,
    family: "semantic",
    mode: "current",
    run_id: "fixture-run",
    record_id: null,
    schema_version: "bilqis.bamf.mission-control.semantic-bank-snapshot/v1",
    generation: null,
    frontier_id: null,
    as_of: null,
    reference: null,
    cursor: null,
    limit: 32,
  };
  const page = await bridge.query(request);
  assert.equal(page.schema, QUERY_PAGE_SCHEMA);
  assert.equal(page.family, "semantic");
  assert.equal(page.total_matches, 0);
  assert.deepEqual(broker.calls.at(-1), ["query", request]);
  await assert.rejects(
    bridge.query({ ...request, limit: 33 }),
    /BAMF_GUI20_ACCEPTED_CONTRACT_INVALID:QUERY_REQUEST/,
  );
  await assert.rejects(
    bridge.query({ ...request, mode: "historical", generation: null }),
    /BAMF_GUI20_ACCEPTED_CONTRACT_INVALID:QUERY_HISTORICAL_IDENTITY/,
  );
  adapter.close();
});

test("missing CP01 service becomes disconnected state without leaking broker errors", async () => {
  const broker = brokerFixture({ fail: true });
  const { adapter, bridge } = await acceptedBridge(broker);

  assert.deepEqual(await bridge.connect(), {
    ...disconnectedStatus(),
    connectionEpoch: 1,
  });
  assert.deepEqual(await bridge.status(), disconnectedStatus());
  adapter.close();
});

test("accepted CP01 boundary exposes only validated CP05 preview submit and readback", async () => {
  const broker = brokerFixture();
  const { adapter, bridge } = await acceptedBridge(broker);
  await bridge.connect();
  const staged = actionRequest();
  const reviewed = await bridge.dryRun({
    schemaVersion: "bamf.gui17.command-preview-request/v1",
    request: staged,
  });
  assert.equal(reviewed.target_ref, TARGET_REF);
  const authorized = actionRequest({ humanAuthorized: true });
  const submitted = await bridge.command({
    schemaVersion: "bamf.gui17.command-submit-request/v1",
    expectedTargetRef: TARGET_REF,
    request: authorized,
  });
  assert.equal(submitted.state, "ACCEPTED");
  const readback = await bridge.receipt(OPERATION_ID);
  assert.equal(readback.operation_id, OPERATION_ID);
  assert.equal(readback.target_ref, TARGET_REF);
  const observed = [];
  const unsubscribe = await bridge.subscribe((event) => observed.push(event));
  broker.emit({
    schema_version: "bilqis.bamf.mission-control.event-envelope/v1",
    meta: { record_id: "event:1" },
    event_id: "event:1",
    position: {
      stream_id: "run-7:candidate",
      epoch_id: "epoch-1",
      ordinal: 1,
      cursor_sha256: "a".repeat(64),
      previous_cursor_sha256: "b".repeat(64),
    },
    event_family: "candidate.retained",
    payload_schema_version: "bilqis.bamf.mission-control.candidate-decision/v1",
    payload_record_id: "decision:1",
    payload_sha256: "c".repeat(64),
    payload_ref: "evidence:event:1",
  });
  assert.equal(observed.length, 1);
  assert.equal(observed[0].payload_record_id, "decision:1");
  assert.deepEqual(broker.calls.slice(1, 4).map((item) => item[0]), [
    "previewCommand", "submitCommand", "inspectCommand",
  ]);
  unsubscribe();
  adapter.close();
});

test("incompatible-version preserves the observed CP01 protocol version", async () => {
  const { assertOperatorView } = await import("../../renderer/shell-state.mjs");
  const validators = createAcceptedValidators(assertOperatorView);
  const mismatch = {
    schemaVersion: "bamf.gui20.cp01-status/v1",
    state: "incompatible-version",
    protocolVersion: "bilqis.bamf.control-plane/v999",
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
  assert.equal(validators.publicStatus(mismatch), mismatch);
  assert.throws(
    () => validators.publicStatus({ ...mismatch, state: "healthy" }),
    /BAMF_GUI20_ACCEPTED_CONTRACT_INVALID:CP01_STATUS/,
  );
});
