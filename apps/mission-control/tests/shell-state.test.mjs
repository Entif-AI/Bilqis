import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  DESTINATION_GROUPS,
  DESTINATIONS,
  assertOperatorView,
  createShellState,
  inspect,
  navigate,
  openEvidence,
  openSelectionOwner,
  returnFromEvidence,
  selectObject,
  shellPosture,
  withDefensiveState,
  withRoute,
} from "../renderer/shell-state.mjs";
import { buildDeepLink, parseDeepLink, routeFromState } from "../renderer/deep-link.mjs";

const context = JSON.parse(
  readFileSync(new URL("../fixtures/operator-view-v1.json", import.meta.url), "utf8"),
);

test("all required GUI01 destinations remain stable and reachable", () => {
  assert.deepEqual(
    DESTINATIONS.map(([id]) => id),
    ["mission-control", "school", "capability", "learning", "atlas", "model", "memory", "teacher", "salience", "corrections", "lineage", "resources", "evidence", "operate"],
  );
});

test("persistent navigation groups follow the target atlas task families without losing direct access", () => {
  assert.deepEqual(
    DESTINATION_GROUPS.map(({ id, destinations }) => [id, [...destinations]]),
    [
      ["overview-learning", ["mission-control", "school", "capability", "learning"]],
      ["representation-mechanisms", ["atlas", "model", "memory"]],
      ["decision-correction", ["teacher", "salience", "corrections"]],
      ["provenance-operations", ["lineage", "resources", "evidence", "operate"]],
    ],
  );
  assert.deepEqual(
    DESTINATION_GROUPS.flatMap(({ destinations }) => destinations),
    DESTINATIONS.map(([id]) => id),
  );
});

test("switching views preserves exact inspected context", () => {
  const initial = createShellState(context);
  const next = navigate(initial, "atlas");
  assert.equal(next.view, "atlas");
  assert.equal(next.context, initial.context);
  assert.equal(next.context.generation, 7);
  assert.equal(next.context.runId, "fixture-run");
  assert.equal(next.context.schemaVersion, "bilqis.bamf.mission-control.operator-view/v1");
});

test("deep links restore view and selected object with exact run and generation context", () => {
  const initial = inspect(navigate(createShellState(context), "evidence"), {
    kind: "evidence",
    id: "receipt:123",
  });
  const hash = buildDeepLink(initial);
  assert.equal(hash, "#/view/evidence?kind=evidence&id=receipt%3A123&run=fixture-run&generation=7&mode=LIVE");
  const restored = createShellState(context, parseDeepLink(hash));
  assert.equal(restored.context.runId, "fixture-run");
  assert.deepEqual(restored.selected, { kind: "evidence", id: "receipt:123" });
});

test("evidence selection can update URL identity without forcing inspector state", () => {
  const initial = navigate(createShellState(context), "evidence");
  const selected = selectObject(initial, { kind: "evidence", id: "receipt:exact" });
  assert.equal(selected.inspectorOpen, false);
  assert.equal(
    buildDeepLink(selected),
    "#/view/evidence?kind=evidence&id=receipt%3Aexact&run=fixture-run&generation=7&mode=LIVE",
  );
  const restored = createShellState(context, parseDeepLink(buildDeepLink(selected)));
  assert.deepEqual(restored.selected, { kind: "evidence", id: "receipt:exact" });
});

test("evidence round trip preserves and deep-links the originating inspected object", () => {
  const owner = inspect(navigate(createShellState(context), "school"), {
    kind: "capability", id: "B.AND",
  });
  const evidence = openEvidence(owner);
  const exact = selectObject(evidence, { kind: "evidence", id: "receipt:exact" });
  assert.deepEqual(exact.evidenceOrigin, {
    view: "school",
    selected: { kind: "capability", id: "B.AND" },
    inspectorOpen: true,
  });
  const hash = buildDeepLink(exact);
  const restored = createShellState(context, parseDeepLink(hash));
  assert.deepEqual(restored.evidenceOrigin, exact.evidenceOrigin);
  assert.deepEqual(routeFromState(exact).evidenceOrigin, exact.evidenceOrigin);
  const returned = returnFromEvidence(restored);
  assert.equal(returned.view, "school");
  assert.deepEqual(returned.selected, { kind: "capability", id: "B.AND" });
  assert.equal(returned.inspectorOpen, true);
  assert.equal(returned.evidenceOrigin, null);
});

test("hash-route updates reuse normalized state without re-decoding it as CP02", () => {
  const initial = createShellState(context);
  const route = parseDeepLink("#/view/evidence?kind=evidence&id=receipt%3A123");
  const restored = withRoute(initial, route);
  assert.equal(restored.context, initial.context);
  assert.equal(restored.view, "evidence");
  assert.deepEqual(restored.selected, { kind: "evidence", id: "receipt:123" });
});

test("historical route context stays historical and cannot expose mutation", () => {
  const routed = withRoute(createShellState(context), {
    view: "capability",
    context: {
      runId: "fixture:gui05", generation: 1, mode: "HISTORICAL",
      fixture: true, historicalPinned: true,
    },
  });
  const guarded = withDefensiveState(routed, {
    id: "live", historical: false, snapshotAvailable: true,
    freshness: "FRESH", mutationAllowed: true,
  });
  assert.equal(guarded.context.runId, "fixture:gui05");
  assert.equal(guarded.context.generation, 1);
  assert.equal(guarded.context.mode, "HISTORICAL");
  assert.equal(guarded.mutationAvailable, false);
});

test("defensive historical posture does not become explicit historical deep-link intent", () => {
  const offline = withDefensiveState(createShellState(context), {
    id: "offline",
    historical: true,
    snapshotAvailable: true,
    mutationAllowed: false,
    freshness: "DISCONNECTED",
  });
  assert.equal(offline.context.mode, "HISTORICAL");
  assert.equal(offline.context.historicalPinned, false);
  const hash = buildDeepLink(offline);
  assert.match(hash, /mode=LIVE/);
  assert.doesNotMatch(hash, /mode=HISTORICAL/);
  const routed = parseDeepLink(hash);
  assert.equal(routed.context.mode, "LIVE");
  assert.equal(routed.context.historicalPinned, false);
});

test("historical and stale states are shell-global postures", () => {
  const normalized = createShellState(context).context;
  assert.equal(shellPosture({ ...normalized, mode: "HISTORICAL" }), "historical");
  assert.equal(shellPosture({ ...normalized, freshness: "STALE" }), "stale");
  assert.equal(shellPosture(normalized), "unknown");
  assert.equal(shellPosture({ ...normalized, freshness: "FRESH" }), "live");
});

test("coverage remains distinct from freshness and never implies staleness", () => {
  for (const coverage of ["COMPLETE", "PARTIAL", "UNKNOWN", "NOT_APPLICABLE"]) {
    const candidate = structuredClone(context);
    candidate.meta.coverage = coverage;
    const normalized = createShellState(candidate).context;
    assert.equal(normalized.coverage, coverage);
    assert.equal(normalized.freshness, "UNKNOWN");
    assert.equal(shellPosture(normalized), "unknown");
  }
});

test("unversioned bootstrap context fails closed", () => {
  assert.throws(
    () => createShellState({ runId: "legacy" }),
    /MISSION_CONTROL_OPERATOR_VIEW_SCHEMA_UNSUPPORTED/,
  );
});

test("malformed versioned operator views fail closed at the Electron boundary", () => {
  const malformed = structuredClone(context);
  malformed.meta.run.run_id = null;
  malformed.meta.run.generation = "seven";
  malformed.meta.run.topology_sha256 = "abc";
  assert.throws(
    () => createShellState(malformed),
    /MISSION_CONTROL_OPERATOR_VIEW_INVALID:/,
  );

  const missing = structuredClone(context);
  delete missing.meta.record_id;
  assert.throws(
    () => assertOperatorView(missing),
    /MISSION_CONTROL_OPERATOR_VIEW_INVALID:meta\.fields/,
  );

  const surrogate = structuredClone(context);
  surrogate.stage = "\uD800";
  assert.throws(
    () => assertOperatorView(surrogate),
    /MISSION_CONTROL_OPERATOR_VIEW_INVALID:stage/,
  );

  for (const pythonOnlyWhitespace of ["\u0085", "\u001c", "\u001f"]) {
    const blankName = structuredClone(context);
    blankName.meta.run.run_id = pythonOnlyWhitespace;
    assert.throws(
      () => assertOperatorView(blankName),
      /MISSION_CONTROL_OPERATOR_VIEW_INVALID:run\.run_id/,
    );
  }

  for (const unsafeInteger of [Number.MAX_SAFE_INTEGER + 1, -(Number.MAX_SAFE_INTEGER + 1)]) {
    const unsafe = structuredClone(context);
    unsafe.meta.run.generation = unsafeInteger;
    assert.throws(
      () => assertOperatorView(unsafe),
      /MISSION_CONTROL_OPERATOR_VIEW_INVALID:run\.generation/,
    );
  }
});

test("inspector routes at least five stable object classes to owning views", () => {
  const samples = [
    ["capability", "capability"],
    ["episode", "learning"],
    ["semantic", "atlas"],
    ["memory", "memory"],
    ["checkpoint", "lineage"],
    ["evidence", "evidence"],
    ["correction", "corrections"],
    ["warning", "resources"],
  ];
  for (const [kind, owner] of samples) {
    const selected = inspect(createShellState(context), { kind, id: `${kind}:1` });
    const opened = openSelectionOwner(selected);
    assert.equal(opened.view, owner);
    assert.equal(opened.context, selected.context);
  }
});
