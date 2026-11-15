import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { parseDeepLink } from "../../renderer/deep-link.mjs";
import { LINEAGE_FIXTURE } from "../../renderer/lineage/lineage-fixture.mjs";
import { lineageT } from "../../renderer/lineage/lineage-messages.mjs";
import { renderLineageMarkup } from "../../renderer/lineage/lineage-view.mjs";
import {
  capabilityChanges,
  compareGenerations,
  currentLineageNode,
  historicalGenerationQuery,
  lineageDeepLink,
  lineageEdges,
  manifestFieldRows,
  nodeByIdentity,
  rejectedCandidateCommitted,
} from "../../renderer/lineage/lineage-model.mjs";
import { assertUniqueTestIds, collectTestIds } from "../../renderer/foundation/test-hooks.mjs";
import { INSPECTOR_OWNERS } from "../../renderer/shell-state.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../../../..");
const rendererRoot = path.join(repoRoot, "apps/mission-control/renderer");

test("fixture lineage reconstructs exact manifest parent child identities", () => {
  const nodes = LINEAGE_FIXTURE.nodes;
  const byManifest = new Map(nodes.map((node) => [node.manifestSha256, node]));
  for (const edge of lineageEdges()) {
    const child = byManifest.get(edge.childId);
    assert.equal(child.parentManifestSha256, edge.parentId);
    assert.equal(byManifest.has(edge.parentId), true);
  }
  assert.equal(nodes[0].parentManifestSha256, null);
});

test("recovery fork is distinct from ordinary retained candidate progression", () => {
  const recovery = LINEAGE_FIXTURE.nodes.find((node) => node.transitionClass === "RECOVERY_FORK");
  const ordinary = LINEAGE_FIXTURE.nodes.find((node) => node.transitionClass === "RETAINED_CANDIDATE");
  assert.ok(recovery);
  assert.ok(ordinary);
  assert.equal(recovery.parentManifestSha256, ordinary.manifestSha256);
  assert.notEqual(recovery.transitionClass, ordinary.transitionClass);
  assert.ok(recovery.generation > ordinary.generation + 1);
  const css = fs.readFileSync(path.join(rendererRoot, "lineage/lineage.css"), "utf8");
  assert.match(css, /recovery-fork/);
  assert.match(css, /dotted/);
});

test("every displayed manifest field resolves to an explicit source receipt or manifest", () => {
  for (const node of LINEAGE_FIXTURE.nodes) {
    const rows = manifestFieldRows(node);
    assert.equal(rows.length >= 12, true);
    for (const row of rows) {
      assert.equal(typeof row.value, "string");
      assert.equal(typeof row.sourceRef, "string");
      assert.notEqual(row.sourceRef.length, 0);
      assert.match(row.sourceRef, /^(manifest:|receipt:|generation:)/);
    }
  }
});

test("compare is literal, branch aware, and preserves descriptive evidence states", () => {
  const before = LINEAGE_FIXTURE.nodes[1];
  const after = currentLineageNode();
  const comparison = compareGenerations(before.id, after.id);
  assert.equal(comparison.sameRun, true);
  assert.match(lineageT(`lineage.compare.${comparison.interpretationKey}`), /recorded values/);
  assert.equal(comparison.rows.some((row) => row.state === "DIFFERENT"), true);
  assert.equal(comparison.capabilityChanges.some((row) => row.state !== "UNCHANGED"), false);
});

test("capability diff reports gained and changed score evidence without ranking generations", () => {
  const baseline = LINEAGE_FIXTURE.nodes[0];
  const expansion = LINEAGE_FIXTURE.nodes[2];
  const comparison = compareGenerations(baseline.id, expansion.id);
  assert.equal(comparison.capabilityChanges.find((row) => row.id === "C.ADD").state, "GAINED_EVIDENCE");
  assert.equal(comparison.capabilityChanges.find((row) => row.id === "C.SUCCESSOR").state, "SCORE_CHANGED");
});

test("capability diff can report lost and regressed evidence explicitly", () => {
  const before = { compare: { capabilities: { A: [4, 4], B: [3, 4] } } };
  const after = { compare: { capabilities: { A: [3, 4] } } };
  const rows = capabilityChanges(before, after);
  assert.equal(rows.find((row) => row.id === "A").state, "REGRESSED");
  assert.equal(rows.find((row) => row.id === "B").state, "LOST_EVIDENCE");
});

test("incompatible topology explains resource comparison unavailability", () => {
  const v1 = LINEAGE_FIXTURE.nodes[2];
  const v2 = LINEAGE_FIXTURE.nodes[3];
  const row = compareGenerations(v1.id, v2.id).rows.find((item) => item.key === "resources");
  assert.equal(row.state, "UNAVAILABLE");
  assert.equal(row.reasonKey, "topologyMismatch");
  assert.match(lineageT(`lineage.compare.reason.${row.reasonKey}`), /Topology\/version changed/);
});

test("historical node is recursively immutable while current lineage advances", () => {
  const historical = LINEAGE_FIXTURE.nodes[0];
  const snapshot = JSON.stringify(historical);
  assert.equal(Object.isFrozen(historical), true);
  assert.equal(Object.isFrozen(historical.manifestFields), true);
  assert.throws(() => { historical.compare.debt = 999; }, TypeError);
  assert.equal(JSON.stringify(historical), snapshot);
  assert.ok(currentLineageNode().generation > historical.generation);
});

test("generation deep link selects the durable CP03 record and resolves the exact manifest", () => {
  const node = LINEAGE_FIXTURE.nodes[2];
  const route = parseDeepLink(lineageDeepLink(node));
  assert.equal(route.view, "lineage");
  assert.deepEqual(route.selected, { kind: "generation", id: node.recordId });
  assert.equal(nodeByIdentity(route.selected.id), node);
  assert.deepEqual(historicalGenerationQuery(node), {
    family: "generation", mode: "historical", run_id: node.runId,
    generation: node.generation, record_id: node.recordId,
  });
  assert.equal(INSPECTOR_OWNERS.generation, "lineage");
});

test("rejected candidate never appears as a committed lineage node", () => {
  const rejected = LINEAGE_FIXTURE.rejectedCandidates[0];
  assert.equal(rejected.committedGeneration, null);
  assert.equal(rejectedCandidateCommitted(rejected.candidateId), false);
  assert.equal(LINEAGE_FIXTURE.nodes.some((node) => node.id === rejected.candidateId), false);
});

test("GUI14 fixture is grounded in current CP03, B13 and C10 executable contracts", () => {
  const sources = [
    "bilqis_mlx/mission_control/contracts/observability.py",
    "bilqis_mlx/mission_control/query_support.py",
    "bilqis_mlx/runtime/_custody/bamf_bundle/records.py",
    "bilqis_mlx/runtime/_custody/bamf_bundle/feature/receipt.py",
    "bilqis_mlx/runtime/_projection/generation_projection.py",
  ].map((name) => fs.readFileSync(path.join(repoRoot, name), "utf8")).join("\n");
  for (const token of [
    "class GenerationManifest", "QueryFamily.GENERATION", "parent_manifest_sha256",
    "semantic_abi", "motif_allocation", "correction_frontier", "teacher_state",
    "evaluation_contract", "class AcceptedGenerationFeatureReceipt",
    "class GenerationProjection",
  ]) assert.equal(sources.includes(token), true, token);
});

test("lineage view exposes no checkpoint mutation, pruning, restore, or champion controls", () => {
  const source = fs.readFileSync(path.join(rendererRoot, "lineage/lineage-view.mjs"), "utf8");
  assert.doesNotMatch(source, /data-(restore|prune|delete|champion|mutate)=/i);
  const markup = renderLineageMarkup();
  assert.match(markup, new RegExp(lineageT("lineage.boundary.detail").replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i"));
});

test("target lineage markup is graph-led, dossier-oriented, localized, and stable-hooked", () => {
  const markup = renderLineageMarkup();
  assert.equal(assertUniqueTestIds(markup), true);
  const hooks = new Set(collectTestIds(markup));
  for (const id of [
    "lineage-workspace", "lineage-heading", "lineage-fixture", "lineage-accepted",
    "lineage-tabs", "lineage-tab-generations", "lineage-tab-selected",
    "lineage-tab-comparison", "lineage-tab-rejected",
    "lineage-graph-scroll", "lineage-graph-tree", "lineage-accepted-table",
    "lineage-dossier", "lineage-dossier-manifest", "lineage-compare",
    "lineage-compare-before", "lineage-compare-after", "lineage-diff-table",
    "lineage-capability-table", "lineage-rejected-boundary", "lineage-authority",
  ]) assert.equal(hooks.has(id), true, id);
  assert.match(markup, new RegExp(lineageT("lineage.title")));
  assert.match(markup, /<ol class="lineage-tree"/);
  assert.equal((markup.match(/role="tablist"/g) ?? []).length, 1);
  assert.match(markup, /data-test-id="lineage-help-accepted-trigger"/);
  assert.match(markup, /data-test-id="lineage-help-custody-trigger"/);
  assert.match(markup, /data-test-id="lineage-help-comparison-trigger"/);
  assert.match(markup, /data-sticky="identity"/);
  assert.match(markup, /<th scope="col"[^>]*>Source<\/th>/);
  assert.doesNotMatch(markup, /overall winner is synthesized\.<\/strong>/i);
});

test("accepted lineage graph and table both expose exact generation selection hooks", () => {
  const markup = renderLineageMarkup();
  for (const node of LINEAGE_FIXTURE.nodes) {
    assert.match(markup, new RegExp(`data-test-id="lineage-graph-generation-${node.generation}"`));
    assert.match(markup, new RegExp(`data-test-id="lineage-table-generation-${node.generation}"`));
  }
});

test("historical generation unavailable is a no-substitution boundary state", () => {
  const markup = renderLineageMarkup({ context: { mode: "HISTORICAL", generation: 999999 } });
  assert.match(markup, /data-test-id="lineage-historical-unavailable"/);
  assert.match(markup, /999999/);
  assert.match(markup, /no exact record for generation 999999/i);
  assert.doesNotMatch(markup, /data-test-id="lineage-accepted"/);
  assert.doesNotMatch(markup, /data-test-id="lineage-dossier"/);
});

test("exact historical lineage pins the requested accepted generation without mutation", () => {
  const historical = LINEAGE_FIXTURE.nodes[1];
  const markup = renderLineageMarkup({ context: { mode: "HISTORICAL", generation: historical.generation } });
  assert.match(markup, /data-test-id="lineage-historical-pinned"/);
  assert.match(markup, new RegExp(`data-test-id="lineage-graph-generation-${historical.generation}"[^>]*aria-pressed="true"`));
  assert.match(markup, /Historical lens is fixed to generation/);
});

test("lineage owned human copy resolves through stable message keys", () => {
  for (const key of [
    "lineage.title", "lineage.graph.title", "lineage.dossier.fields", "lineage.compare.title",
    "lineage.rejected.title", "lineage.historical.title", "lineage.boundary.detail",
  ]) assert.equal(typeof lineageT(key), "string");
  assert.equal(lineageT("lineage.dossier.title", { generation: 42 }), "Generation 42");
});

test("lineage CSS owns wide overflow and responsive accessibility states", () => {
  const css = fs.readFileSync(path.join(rendererRoot, "lineage/lineage.css"), "utf8");
  assert.match(css, /\.lineage-graph-scroll, \.lineage-table-wrap[^}]*overflow:\s*auto/);
  assert.match(css, /data-sticky="identity"/);
  assert.match(css, /data-density="compact"/);
  assert.match(css, /@media \(max-width:\s*980px\)/);
  assert.match(css, /@media \(max-width:\s*720px\)/);
  assert.match(css, /prefers-reduced-motion/);
  assert.match(css, /forced-colors/);
  assert.match(css, /focus-visible/);
  assert.doesNotMatch(css, /repeating-linear-gradient|box-shadow:\s*0\s+\d+px\s+\d+px/);
});
