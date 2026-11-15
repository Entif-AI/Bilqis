"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { FixtureControlPlaneAdapter } = require("../fixture-control-plane-adapter.cjs");
const { ControlPlaneBridge } = require("../control-plane-bridge.cjs");
const { createAcceptedValidators } = require("../accepted-contracts.cjs");

async function setup() {
  const { assertOperatorView } = await import("../../renderer/shell-state.mjs");
  const contracts = await import("../../renderer/frames/frame-contract.mjs");
  const bridge = new ControlPlaneBridge(
    new FixtureControlPlaneAdapter(),
    createAcceptedValidators(assertOperatorView, contracts),
  );
  await bridge.connect();
  return { bridge, request: { schemaVersion: contracts.FRAME_QUERY, runId: "fixture-run", generation: 7, mode: "current" } };
}

test("GUI08 accepted snapshot crosses the existing bridge with exact fixture context", async () => {
  const { bridge, request } = await setup();
  const current = await bridge.snapshot(request);
  const past = await bridge.snapshot({ ...request, generation: 6, mode: "historical" });
  assert.equal(current.examples[0].frameId, "frame:quad-fast");
  assert.equal(past.operatorView.meta.run.generation, 6);
  assert.equal(past.request.mode, "historical");
  assert.notEqual(current.examples[0].compiler.digest, past.examples[0].compiler.digest);
  current.examples[0].positions = null;
  assert.notEqual((await bridge.snapshot(request)).examples[0].positions, null, "fixtures remain immutable");
});

test("GUI08 main binds response schema and exact generation to the original query", async () => {
  const { assertOperatorView } = await import("../../renderer/shell-state.mjs");
  const contracts = await import("../../renderer/frames/frame-contract.mjs");
  const { frameFixturePage } = require("../frame-fixtures.cjs");
  const current = { schemaVersion: contracts.FRAME_QUERY, runId: "fixture-run", generation: 7, mode: "current" };
  const wrong = frameFixturePage({ ...current, generation: 6, mode: "historical" });
  const adapter = {
    async connect() { return { session: "fixture", publicStatus: require("../accepted-control-plane-adapter.cjs").disconnectedStatus() }; },
    async snapshot() { return wrong; },
  };
  const bridge = new ControlPlaneBridge(adapter, createAcceptedValidators(assertOperatorView, contracts));
  await bridge.connect();
  await assert.rejects(bridge.snapshot(current), /FRAME_INSPECTION|ACCEPTED_CONTRACT_INVALID/);
  adapter.snapshot = async () => frameFixturePage(current).operatorView;
  await assert.rejects(bridge.snapshot(current), /FRAME_INSPECTION|ACCEPTED_CONTRACT_INVALID/);
  adapter.snapshot = async () => frameFixturePage(current);
  await assert.rejects(bridge.snapshot({ schemaVersion: "bamf.gui20.operator-view-query/v1", schema: "bilqis.bamf.mission-control.operator-view/v1" }), /OPERATOR_VIEW/);
});

test("GUI08 missing exact historical identity stays missing", async () => {
  const { bridge, request } = await setup();
  for (const identity of [{ generation: 99 }, { runId: "unrelated-run" }]) {
    const result = await bridge.snapshot({ ...request, ...identity, mode: "historical" });
    assert.equal(result.state, "MISSING");
    assert.equal(result.operatorView, null);
    assert.deepEqual(result.examples, []);
  }
});

test("GUI08 main rejects invalid query shapes and cannot cross the GUI17 command contract", async () => {
  const { bridge, request } = await setup();
  for (const changed of [{ generation: -1 }, { generation: 6 }, { generation: 1.5 }, { mode: "latest" }, { path: "/tmp" }]) {
    await assert.rejects(bridge.snapshot({ ...request, ...changed }), /FRAME_INSPECTION_INVALID/);
  }
  await assert.rejects(bridge.command(request), /BAMF_GUI17_OPERATOR_CONTRACT_INVALID/);
});
