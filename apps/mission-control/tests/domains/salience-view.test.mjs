import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  ROUTING_FIXTURES,
  SALIENCE_AGGREGATION,
  SALIENCE_PROJECTION,
  SALIENCE_SNAPSHOTS,
} from "../../renderer/salience/salience-fixture.mjs";
import {
  aggregationForSnapshot,
  aggregationPathForEvent,
  axisPosture,
  constituentObservationIds,
  routingForSnapshot,
  salienceEventById,
  snapshotById,
} from "../../renderer/salience/salience-model.mjs";
import { salienceMarkupForTest } from "../../renderer/salience/salience-view.mjs";
import { salienceT } from "../../renderer/salience/salience-messages.mjs";
import { assertUniqueTestIds, collectTestIds } from "../../renderer/foundation/test-hooks.mjs";
import { INSPECTOR_OWNERS } from "../../renderer/shell-state.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../../../..");
const rendererRoot = path.resolve(here, "../../renderer");

test("same salience event preserves three independent ordinal axes", () => {
  const event = salienceEventById("salience-record:fixture:unlock");
  assert.deepEqual(
    [event.axes.impact.ordinal, event.axes.exigency.ordinal, event.axes.novelty.ordinal],
    ["HIGH", "LOW", "MODERATE"],
  );
  assert.equal("score" in event, false);
  assert.equal("scalar" in event, false);
});

test("UNKNOWN is distinct from an expected-missing observation", () => {
  const unknown = salienceEventById("salience-record:fixture:urgent").axes.novelty;
  const missing = salienceEventById("salience-record:fixture:expected-missing").axes.novelty;
  assert.equal(axisPosture(unknown), "UNKNOWN");
  assert.equal(axisPosture(missing), "EXPECTED_MISSING");
  assert.equal(missing.ordinal, "CRITICAL");
});

test("expected-missing novelty is distinct from observed negative LOW", () => {
  const missing = salienceEventById("salience-record:fixture:expected-missing").axes.novelty;
  const negative = salienceEventById("salience-record:fixture:negative").axes.novelty;
  assert.equal(missing.observationState, "EXPECTED_MISSING");
  assert.equal(negative.observationState, "REPORTED_NEGATIVE");
  assert.equal(negative.ordinal, "LOW");
});

test("every displayed axis carries source signed-policy rule and basis references", () => {
  for (const snapshot of SALIENCE_SNAPSHOTS) {
    for (const event of snapshot.events) {
      assert.equal(event.associatedObjectRef.length > 0, true);
      assert.equal(event.policy.sourceOwner.length > 0, true);
      assert.equal(event.policy.policyId.length > 0, true);
      assert.equal(event.policy.version.length > 0, true);
      assert.match(event.policy.policyDigest, /^[0-9a-f]{64}$/);
      for (const value of Object.values(event.axes)) {
        assert.equal(typeof value.sourceRef, "string");
        assert.equal(typeof value.ruleId, "string");
        assert.equal(value.basisRefs.length > 0, true);
      }
    }
  }
});

test("historical fixture preserves policy identity active at that time and historical values", () => {
  const historical = snapshotById("historical");
  const current = snapshotById("current");
  assert.equal(historical.mode, "HISTORICAL");
  assert.equal(historical.policy.version, "v1");
  assert.equal(current.policy.version, "v1");
  assert.equal(historical.policy.sourceOwner, "fixture:salience-owner");
  assert.equal(historical.events[0].axes.impact.ordinal, "MODERATE");
  assert.equal(current.events[0].axes.impact.ordinal, "HIGH");
});

test("historical as-of cannot inherit current aggregation or routing evidence", () => {
  const historical = snapshotById("historical");
  const current = snapshotById("current");
  assert.equal(aggregationForSnapshot(historical), null);
  assert.deepEqual(routingForSnapshot(historical), []);
  assert.equal(aggregationForSnapshot(current), SALIENCE_AGGREGATION);
  assert.equal(routingForSnapshot(current), ROUTING_FIXTURES);
});

test("aggregation path is reversible from observation through trend", () => {
  const path = aggregationPathForEvent("salience-record:fixture:negative");
  assert.equal(path.cluster.id, SALIENCE_AGGREGATION.clusters[0].id);
  assert.equal(path.pattern.id, SALIENCE_AGGREGATION.pattern.id);
  assert.equal(path.trend.id, SALIENCE_AGGREGATION.trend.id);
  assert.equal(path.window.size, 20);
  assert.deepEqual(
    constituentObservationIds("trend", path.trend.id),
    SALIENCE_AGGREGATION.pattern.eventIds,
  );
});

test("fixed aggregation window and scope metadata remain explicit", () => {
  const window = SALIENCE_AGGREGATION.windows[0];
  assert.equal(window.size, 20);
  assert.equal(window.acceptedAppendCount, 20);
  assert.equal(window.observedBounds.length, 2);
  assert.equal(SALIENCE_AGGREGATION.clusters[0].partition.includes("source-family"), true);
});

test("clusters contain only defect-present LOW impact and LOW exigency observations", () => {
  for (const cluster of SALIENCE_AGGREGATION.clusters) {
    for (const eventId of cluster.eventIds) {
      const event = salienceEventById(eventId);
      assert.equal(event.capabilityId, cluster.capabilityId);
      assert.equal(event.scope, "capability:" + cluster.capabilityId);
      assert.equal(event.sourceFamily, "factory:boolean-ast");
      assert.equal(event.defectPresent, true);
      assert.equal(event.axes.impact.ordinal, "LOW");
      assert.equal(event.axes.exigency.ordinal, "LOW");
    }
  }
});

test("pattern remains conjecture and never becomes source gold or teaching authority", () => {
  const pattern = SALIENCE_AGGREGATION.pattern;
  assert.equal(pattern.status, "CONJECTURE");
  assert.equal(pattern.sourceGold, false);
  assert.equal(pattern.qualifiedForTeaching, false);
});

test("routing fixture cites observations and literal dispatch rationale without hidden weights", () => {
  const route = ROUTING_FIXTURES[0];
  assert.equal(route.tier, "URGENT_RELEVANT");
  assert.equal(route.rule, "relevant && exigency >= HIGH");
  assert.deepEqual(route.ordering, ["dispatch-tier", "eligible-since", "stable-id"]);
  assert.equal(route.hiddenWeighting, "NOT_EXPOSED_OR_INFERRED");
  assert.equal(route.citedObservationIds.length > 0, true);
});

test("routing rationale matches executable tier and sort semantics", () => {
  const source = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/learning/_salience/atlas_salience.py"),
    "utf8",
  );
  assert.equal(source.includes("evidence.exigency.ordinal >= Ordinal.HIGH"), true);
  assert.equal(source.includes("ranked.sort(key=lambda item: item[:3])"), true);
});

test("novelty missing and negative mappings match executable C06 authority", () => {
  const source = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/runtime/_teacher/priority_authority.py"),
    "utf8",
  );
  assert.equal(source.includes("(NoveltyState.EXPECTED_MISSING, Ordinal.CRITICAL)"), true);
  assert.equal(source.includes("(NoveltyState.REPORTED_NEGATIVE, Ordinal.LOW)"), true);
});

test("recursive aggregation fixture matches C06 window and conjecture doctrine", () => {
  const history = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/learning/_salience/salience_history.py"),
    "utf8",
  );
  const patterns = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/learning/_salience/salience_patterns.py"),
    "utf8",
  );
  assert.equal(history.includes("window_size: int = field(default=20"), true);
  assert.equal(patterns.includes("status: str = field(default='CONJECTURE'"), true);
  assert.equal(patterns.includes("qualified_for_teaching: bool = field(default=False"), true);
});

test("CP02 SalienceEvent projection boundary stays explicit and narrow", () => {
  assert.equal(SALIENCE_PROJECTION.richRecursiveProjection, false);
  assert.equal(SALIENCE_PROJECTION.policyVersionProjected, false);
  assert.equal(SALIENCE_PROJECTION.aggregationProjected, false);
  assert.equal(SALIENCE_PROJECTION.routingRationaleProjected, false);
  const source = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/mission_control/contracts/events.py"),
    "utf8",
  );
  for (const field of [
    "salience_id: str",
    "capability_id: str",
    "impact: DataValue",
    "exigency: DataValue",
    "novelty: DataValue",
    "action_kind: str",
  ]) assert.equal(source.includes(field), true, field);
});

test("only durable salience observation identity owns a global deep-link route", () => {
  assert.equal(INSPECTOR_OWNERS["salience-observation"], "salience");
  for (const kind of ["salience-cluster", "salience-pattern", "salience-trend", "salience-routing"]) {
    assert.equal(kind in INSPECTOR_OWNERS, false);
  }
});

test("GUI12 source contains no universal score or recommendation control", () => {
  const source = [
    "salience/salience-fixture.mjs",
    "salience/salience-model.mjs",
    "salience/salience-view.mjs",
    "salience/salience-observation-view.mjs",
    "salience/salience-aggregation-view.mjs",
    "salience/salience-routing-view.mjs",
  ].map((name) => fs.readFileSync(path.join(rendererRoot, name), "utf8").toLowerCase()).join("\n");
  for (const forbidden of ["weightedscore", "priorityscore", "best salience", "recommended salience"]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
});

test("inspector-opening salience controls preserve keyboard focus identity", () => {
  const observations = salienceMarkupForTest("current", null, "observations");
  const aggregation = salienceMarkupForTest("current", null, "aggregation");
  const routing = salienceMarkupForTest("current", null, "routing");
  assert.match(observations, /data-focus-key="salience:salience-record:fixture:unlock:inspect"/);
  assert.match(aggregation, /data-focus-key="salience:aggregate:salience-record:fixture:negative"/);
  assert.match(aggregation, /data-focus-key="salience:trend:salience-record:fixture:negative"/);
  assert.match(routing, /data-focus-key="salience:routing:salience-record:fixture:urgent"/);
});

test("salience target markup is table-first and removes the legacy card-lane composition", () => {
  const observations = salienceMarkupForTest("current", null, "observations");
  const aggregation = salienceMarkupForTest("current", null, "aggregation");
  const routing = salienceMarkupForTest("current", null, "routing");
  for (const markup of [observations, aggregation, routing]) assert.equal(assertUniqueTestIds(markup), true);
  const ids = new Set([
    ...collectTestIds(observations),
    ...collectTestIds(aggregation),
    ...collectTestIds(routing),
  ]);
  for (const id of [
    "salience-view",
    "salience-controls",
    "salience-snapshot-select",
    "salience-tabs",
    "salience-observations",
    "salience-observation-table",
    "salience-observation-scroll",
    "salience-axis-guide",
    "salience-aggregation",
    "salience-routing",
    "salience-projection",
  ]) assert.equal(ids.has(id), true, id);
  assert.match(observations, /<table class="salience-observation-table"/);
  for (const markup of [observations, aggregation, routing]) {
    assert.doesNotMatch(markup, /class="ui-glossary"/);
    assert.doesNotMatch(markup, /class="salience-axis-cell"/);
    assert.doesNotMatch(markup, /class="salience-provenance-grid"/);
    assert.doesNotMatch(markup, /class="routing-record"/);
  }
});

test("Impact Exigency and Osmotic Novelty remain independent table columns", () => {
  const markup = salienceMarkupForTest("current");
  assert.match(markup, /<th scope="col">Impact<\/th>/);
  assert.match(markup, /<th scope="col">Exigency<\/th>/);
  assert.match(markup, /<th scope="col">Osmotic Novelty<\/th>/);
  assert.match(markup, /independent ordinals shown side by side/);
  assert.doesNotMatch(markup.toLowerCase(), /priority score|weighted score|combined score/);
});

test("per-observation provenance is progressively disclosed with exact source rule and basis values", () => {
  const markup = salienceMarkupForTest("current");
  assert.match(markup, /<details class="salience-provenance"/);
  assert.match(markup, /salience-fact:B\.AND:impact\.declared/);
  assert.match(markup, /bamf\/foundation\/declared\/v1/);
  assert.match(markup, /source:curriculum:B\.AND/);
  assert.match(markup, /Stable observation link/);
});

test("recursive aggregation is a nested reversible disclosure hierarchy rather than peer cards", () => {
  const markup = salienceMarkupForTest("current", null, "aggregation");
  assert.match(markup, /class="salience-aggregate-node" data-depth="0"/);
  assert.match(markup, /class="salience-aggregate-node" data-depth="1"/);
  assert.match(markup, /cluster:fixture:boolean-defect:w20/);
  assert.match(markup, /pattern:fixture:boolean-defect/);
  assert.match(markup, /trend:fixture:boolean-defect/);
  assert.match(markup, /Aggregation is derived evidence/);
});

test("routing and projection are lower-depth collapsed disclosures", () => {
  const markup = salienceMarkupForTest("current", null, "routing");
  assert.match(markup, /<details class="salience-routing ui-disclosure"/);
  assert.match(markup, /<details class="salience-projection ui-disclosure"/);
  assert.doesNotMatch(markup, /<details class="salience-routing ui-disclosure" open/);
  assert.match(markup, /NOT_EXPOSED_OR_INFERRED/);
  assert.match(markup, /recorded tier, ordering keys, and cited observations/);
});

test("historical snapshot stays exact and does not borrow current aggregation or routing", () => {
  const observations = salienceMarkupForTest("historical", null, "observations");
  const aggregation = salienceMarkupForTest("historical", null, "aggregation");
  const routing = salienceMarkupForTest("historical", null, "routing");
  assert.match(observations, /Historical · generation 44237/);
  assert.match(observations, /salience:fixture:unlock:g44237/);
  assert.match(aggregation, /historical snapshot contains observation evidence only/);
  assert.match(routing, /historical snapshot contains observation evidence only/);
  assert.doesNotMatch(routing, /routing:fixture:urgent-relevant/);
});

test("salience owned human copy resolves through stable message keys", () => {
  for (const key of [
    "salience.summary",
    "salience.snapshot.label",
    "salience.action.OBSERVATION",
    "salience.observations.title",
    "salience.provenance.source",
    "salience.aggregation.title",
    "salience.routing.summary",
    "salience.projection.summary",
    "salience.inspector.capability",
  ]) assert.ok(salienceT(key));
});

test("salience CSS is analytical, responsive, compact-aware, focus-visible and pattern-free", () => {
  const css = ["salience.css", "salience-core.css", "salience-evidence.css", "salience-analysis.css"]
    .map(name => fs.readFileSync(path.join(rendererRoot, "salience", name), "utf8"))
    .join("\n");
  assert.match(css, /\.salience-table-wrap\s*\{[^}]*overflow:\s*auto/s);
  assert.match(css, /\.salience-observation-table\s*\{[^}]*min-width:/s);
  assert.match(css, /font-variant-numeric:\s*tabular-nums/);
  assert.match(css, /:root\[data-density="compact"\]/);
  assert.match(css, /@media \(max-width: 980px\)/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(css, /@media \(forced-colors: active\)/);
  assert.doesNotMatch(css, /repeating-linear-gradient/);
  assert.doesNotMatch(css, /data-density="terminal"/);
  assert.doesNotMatch(css, /\.salience-lanes/);
});
