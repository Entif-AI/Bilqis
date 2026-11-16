import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  curriculumFixtureSnapshot,
  curriculumLargeFixture,
} from "../../renderer/school/curriculum-atlas-fixture.mjs";
import {
  boundedFamilyExpansion,
  CURRICULUM_NODE_HEIGHT,
  buildCurriculumGraph,
  curriculumConsequence,
  gradeFamilySummary,
  resolveCapabilitySemanticBindings,
  resolveExactSemanticSearch,
  stableLayout,
  strataFor,
  traceSelection,
  visibilityFor,
} from "../../renderer/school/curriculum-atlas-model.mjs";
import { curriculumFixtureModeForContext } from "../../renderer/school/curriculum-atlas-view.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../../../..");
const rendererRoot = path.resolve(here, "../../renderer");

function currentGraph() {
  return buildCurriculumGraph(curriculumFixtureSnapshot("current", 44239));
}

test("GUI22 reuses shared School rows and only declared prerequisites create graph edges", () => {
  const graph = currentGraph();
  assert.deepEqual(graph.edges.map((edge) => [edge.source, edge.target]), [
    ["A.IDENTITY", "B.NOT"],
    ["B.NOT", "B.AND"],
    ["B.AND", "B.OR"],
    ["B.AND", "B.IFF"],
    ["A.IDENTITY", "C.COUNT"],
    ["C.COUNT", "C.NUMBER"],
    ["C.NUMBER", "C.SUCCESSOR"],
    ["C.SUCCESSOR", "D.EVENT"],
  ]);
  assert.equal(graph.edges.every((edge) =>
    edge.kind === "DECLARED_PREREQUISITE" && edge.authority === "SCHOOL_DECLARED"), true);
  assert.equal(graph.edges.some((edge) => edge.source === "B.NOT" && edge.target === "C.COUNT"), false);
});

test("grade strata remain presentation layers rather than causal edge generators", () => {
  const graph = currentGraph();
  const strata = strataFor(graph);
  assert.deepEqual(strata.foundation.map((node) => node.id), ["A.IDENTITY", "B.NOT"]);
  assert.deepEqual(strata.current.map((node) => node.id), [
    "B.AND", "B.IFF", "B.OR", "C.COUNT", "C.NUMBER", "C.SUCCESSOR",
  ]);
  assert.deepEqual(strata.forward.map((node) => node.id), ["D.EVENT"]);
  assert.equal(graph.snapshot.currentGrade, "C");
  assert.equal(strata.current.find((node) => node.id === "B.OR").lifecycleState, "READY");
  assert.equal(strata.current.find((node) => node.id === "B.OR").newThisGrade, false);
  assert.equal(strata.current.find((node) => node.id === "C.NUMBER").newThisGrade, true);
  assert.equal(graph.nodes.every((node) =>
    node.schedulingSemantics === "EVIDENCE_DRIVEN_GRADE_NEUTRAL"), true);
});

test("trace modes return literal transitive prerequisite and unlock sets", () => {
  const graph = currentGraph();
  const both = traceSelection(graph, "C.NUMBER", "both");
  assert.deepEqual([...both.upstream].sort(), ["A.IDENTITY", "C.COUNT"]);
  assert.deepEqual([...both.downstream].sort(), ["C.SUCCESSOR", "D.EVENT"]);

  const prerequisites = traceSelection(graph, "C.NUMBER", "prerequisites");
  assert.deepEqual([...prerequisites.visibleUpstream].sort(), ["A.IDENTITY", "C.COUNT"]);
  assert.deepEqual([...prerequisites.visibleDownstream], []);

  const unlocks = traceSelection(graph, "C.NUMBER", "unlocks");
  assert.deepEqual([...unlocks.visibleUpstream], []);
  assert.deepEqual([...unlocks.visibleDownstream].sort(), ["C.SUCCESSOR", "D.EVENT"]);
});

test("show curriculum consequence reports later-grade reachability without scheduling semantics", () => {
  const graph = currentGraph();
  const result = curriculumConsequence(graph, "A.IDENTITY");
  assert.deepEqual(result.byGrade, [
    { grade: "B", ids: ["B.AND", "B.IFF", "B.NOT", "B.OR"] },
    { grade: "C", ids: ["C.COUNT", "C.NUMBER", "C.SUCCESSOR"] },
    { grade: "D", ids: ["D.EVENT"] },
  ]);
  assert.equal("priority" in result, false);
  assert.equal("schedule" in result, false);
});

test("held and uncovered blockers remain exact reason classes and unknown is not invented", () => {
  const graph = currentGraph();
  const successor = graph.nodes.find((node) => node.id === "C.SUCCESSOR");
  const event = graph.nodes.find((node) => node.id === "D.EVENT");
  const identity = graph.nodes.find((node) => node.id === "A.IDENTITY");
  assert.equal(successor.blocker.code, "IMPLEMENTATION_UNCOVERED");
  assert.equal(event.blocker.code, "SOURCE_HELD");
  assert.equal(identity.blocker, null);
});

test("filters alter visibility only and preserve graph evidence and denominators", () => {
  const graph = currentGraph();
  const before = JSON.stringify(graph.nodes);
  const visibility = visibilityFor(graph, {
    grade: "C", state: "all", family: "all", issue: "debt", search: "", newOnly: false,
  });
  assert.equal(visibility.get("C.NUMBER"), true);
  assert.equal(visibility.get("A.IDENTITY"), false);
  assert.equal(JSON.stringify(graph.nodes), before);
  assert.equal(graph.nodes.find((node) => node.id === "C.NUMBER").total, 12);
});

test("GUI22 attention filters reuse accepted School semantics", () => {
  const graph = currentGraph();
  const imperfect = visibilityFor(graph, { issue: "imperfect" });
  const held = visibilityFor(graph, { issue: "held" });
  const uncovered = visibilityFor(graph, { issue: "uncovered" });
  const qualified = visibilityFor(graph, { issue: "qualified" });
  assert.equal(imperfect.get("C.NUMBER"), true);
  assert.equal(imperfect.get("A.IDENTITY"), false);
  assert.deepEqual(graph.nodes.filter((node) => held.get(node.id)).map((node) => node.id), ["D.EVENT"]);
  assert.deepEqual(graph.nodes.filter((node) => uncovered.get(node.id)).map((node) => node.id).sort(), ["C.SUCCESSOR", "D.EVENT"]);
  assert.equal(qualified.get("A.IDENTITY"), true);
});

test("live semantic label search can compose exact-release GUI07 bindings without changing graph truth", () => {
  const graph = currentGraph();
  const bindings = new Map([["C.NUMBER", {
    state: "PRESENT",
    concepts: [{
      semantic_id: "https://example.invalid/id/sense/number",
      labels: [{ role: "prefLabel", value: "Canonical Number Sense" }],
    }],
  }]]);
  const visibility = visibilityFor(graph, { search: "canonical number sense" }, bindings);
  assert.deepEqual(
    graph.nodes.filter((node) => visibility.get(node.id)).map((node) => node.id),
    ["C.NUMBER"],
  );
  assert.deepEqual(graph.edges.map((edge) => edge.id), currentGraph().edges.map((edge) => edge.id));
});

test("defensive historical posture does not substitute the canned as-of fixture for retained current state", () => {
  assert.equal(curriculumFixtureModeForContext({ mode: "LIVE", freshness: "FRESH" }), "current");
  assert.equal(curriculumFixtureModeForContext({ mode: "HISTORICAL", freshness: "FRESH" }), "historical");
  assert.equal(curriculumFixtureModeForContext({ mode: "HISTORICAL", freshness: "STALE" }), "current");
  assert.equal(curriculumFixtureModeForContext({ mode: "HISTORICAL", freshness: "DISCONNECTED" }), "current");
});

test("historical event history never exposes events after the requested generation", () => {
  const historical = curriculumFixtureSnapshot("historical", 44218);
  const not = historical.nodes.find((node) => node.id === "B.NOT");
  const and = historical.nodes.find((node) => node.id === "B.AND");
  assert.equal(not.historyEvents.some((event) => event.generation === 44218), true);
  assert.equal(and.historyEvents.some((event) => event.generation === 44219), false);
});

test("historical fixture is materially different and does not leak current curriculum state backward", () => {
  const current = curriculumFixtureSnapshot("current", 44239);
  const historical = curriculumFixtureSnapshot("historical", 44220);
  assert.equal(current.currentGrade, "C");
  assert.equal(historical.currentGrade, "B");
  assert.equal(current.nodes.some((node) => node.id === "C.NUMBER"), true);
  assert.equal(historical.nodes.some((node) => node.id === "C.NUMBER"), false);
  assert.equal(current.nodes.some((node) => node.id === "D.EVENT"), true);
  assert.equal(historical.nodes.some((node) => node.id === "D.EVENT"), false);
  assert.equal(
    historical.nodes.find((node) => node.id === "B.NOT").qualificationState,
    "ADMITTED",
  );
  assert.equal(current.nodes.find((node) => node.id === "B.NOT").qualificationState, "QUALIFIED");
  assert.equal(historical.nodes.find((node) => node.id === "B.OR").lifecycleState, "READY");
  const currentNumber = current.nodes.find((node) => node.id === "C.NUMBER");
  assert.equal(currentNumber.historyEvents.at(-1).posture, "CURRENT_AS_OF");
  assert.equal(currentNumber.historyEvents.at(-1).generation, 44239);
  assert.equal(currentNumber.historyEvents.slice(0, -1).every((event) =>
    event.posture === "HISTORICAL"), true);
});

test("stable layout reserves full card geometry and does not move when trace or filters change", () => {
  const graph = currentGraph();
  const first = stableLayout(graph);
  const second = stableLayout(graph);
  assert.deepEqual([...first.positions.entries()], [...second.positions.entries()]);
  visibilityFor(graph, { search: "number", issue: "debt" });
  traceSelection(graph, "C.NUMBER", "unlocks");
  assert.deepEqual([...stableLayout(graph).positions.entries()], [...first.positions.entries()]);
  const currentY = strataFor(graph).current
    .map((node) => first.positions.get(node.id).y)
    .sort((a, b) => a - b);
  assert.equal(currentY.every((value, index) =>
    index === 0 || value - currentY[index - 1] > CURRICULUM_NODE_HEIGHT), true);
});

test("large fixtures summarize before bounded family and semantic dependency expansion", () => {
  const large = curriculumLargeFixture(243);
  const summary = gradeFamilySummary(large);
  assert.equal(summary.reduce((sum, group) => sum + group.count, 0), 243);
  const first = summary.find((group) => group.count > 1) ?? summary[0];
  const expanded = boundedFamilyExpansion(large, first.grade, first.family, 12);
  assert.equal(expanded.length <= 12, true);
  assert.equal(expanded.every((node) =>
    node.grade === first.grade && node.family === first.family), true);
  const graph = buildCurriculumGraph({ nodes: large, currentGrade: "C" });
  const selected = large.find((node) => node.prerequisites.length > 0);
  assert.ok(selected);
  assert.equal(selected.prerequisites.every((id) => graph.nodes.some((node) => node.id === id)), true);
  assert.ok(traceSelection(graph, selected.id, "both").upstream.size > 0);
});
