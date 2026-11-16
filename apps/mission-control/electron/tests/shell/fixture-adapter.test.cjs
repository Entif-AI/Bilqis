"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const { createAcceptedValidators } = require("../../accepted-contracts.cjs");
const { ControlPlaneBridge } = require("../../control-plane-bridge.cjs");
const { FixtureControlPlaneAdapter } = require("../../fixture-control-plane-adapter.cjs");

async function fixtureBridge() {
  const { assertOperatorView } = await import("../../../renderer/shell-state.mjs");
  const frameContracts = await import("../../../renderer/frames/frame-contract.mjs");
  const adapter = new FixtureControlPlaneAdapter();
  return {
    adapter,
    bridge: new ControlPlaneBridge(
      adapter,
      createAcceptedValidators(assertOperatorView, frameContracts),
    ),
    frameContracts,
  };
}

test("fixture adapter owns a reference identity without contacting production", async () => {
  const { bridge } = await fixtureBridge();
  const status = await bridge.connect();
  const snapshot = await bridge.snapshot({
    schemaVersion: "bamf.gui20.operator-view-query/v1",
    schema: "bilqis.bamf.mission-control.operator-view/v1",
  });
  assert.equal(status.runId, "fixture-run");
  assert.equal(status.generation, 7);
  assert.equal(status.learnerActive, false);
  assert.equal(snapshot.meta.run.run_id, "fixture-run");
  assert.equal(snapshot.meta.run.generation, 7);
});

test("fixture adapter serves fixture frames but rejects command surfaces", async () => {
  const { bridge, frameContracts } = await fixtureBridge();
  await bridge.connect();
  const page = await bridge.snapshot({
    schemaVersion: frameContracts.FRAME_QUERY,
    runId: "fixture-run",
    generation: 7,
    mode: "current",
  });
  assert.equal(page.operatorView.meta.run.run_id, "fixture-run");
  assert.equal(page.examples[0].frameId, "frame:quad-fast");
  await assert.rejects(
    bridge.command({
      schemaVersion: "bamf.gui17.command-submit-request/v1",
      expectedTargetRef: "operation:fixture",
      request: {},
    }),
  );
});
