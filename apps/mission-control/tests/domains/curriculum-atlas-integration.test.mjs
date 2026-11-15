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

test("current capability can resolve exact-release source-authoritative GUI07 semantic identity", async () => {
  const release = "a".repeat(64);
  const context = { mode: "LIVE", semanticRelease: release };
  const requests = [];
  const concept = {
    schema_version: "bilqis.bamf.mission-control.semantic-concept-snapshot/v1",
    semantic_id: "semantic:exact:C.NUMBER",
    atlas_release_sha256: release,
    capability_ids: ["C.NUMBER"],
    labels: [{ role: "prefLabel", value: "Number" }],
  };
  const api = {
    async query(request) {
      requests.push(request);
      if (request.family === "reference") {
        return {
          schema: "bilqis.bamf.control-plane.query-page/v1",
          query_id: "1".repeat(64), request, family: request.family, mode: request.mode,
          state: "PRESENT", coverage: "COMPLETE", total_matches: 1, returned: 1,
          truncated: false, next_cursor: null, records: [], markers: [],
          links: [{
            relation: "CAPABILITY", source_record_id: "concept:C.NUMBER",
            target_ref: "C.NUMBER", target_record_id: null,
          }], accepted: true,
        };
      }
      return {
        schema: "bilqis.bamf.control-plane.query-page/v1",
        query_id: "2".repeat(64), request, family: request.family, mode: request.mode,
        state: "PRESENT", coverage: "COMPLETE", total_matches: 1, returned: 1,
        truncated: false, next_cursor: null, records: [concept], markers: [], links: [],
        accepted: true,
      };
    },
  };
  const result = await resolveCapabilitySemanticBindings(api, context, "C.NUMBER");
  assert.equal(result.state, "PRESENT");
  assert.equal(result.concepts[0].semantic_id, "semantic:exact:C.NUMBER");
  assert.equal(requests[0].family, "reference");
  assert.equal(requests[1].record_id, "concept:C.NUMBER");
});

test("exact semantic ID search resolves through the selected semantic release without learned edges", async () => {
  const release = "c".repeat(64);
  const graph = currentGraph();
  const semanticId = "semantic:exact:C.NUMBER";
  const requests = [];
  const api = {
    async query(request) {
      requests.push(request);
      return {
        schema: "bilqis.bamf.control-plane.query-page/v1",
        query_id: "3".repeat(64), request, family: request.family, mode: request.mode,
        state: "PRESENT", coverage: "COMPLETE", total_matches: 1, returned: 1,
        truncated: false, next_cursor: null,
        records: [{
          schema_version: "bilqis.bamf.mission-control.semantic-concept-snapshot/v1",
          semantic_id: semanticId,
          atlas_release_sha256: release,
          capability_ids: ["C.NUMBER"],
          labels: [{ role: "prefLabel", value: "Number" }],
        }],
        markers: [], links: [], accepted: true,
      };
    },
  };
  const result = await resolveExactSemanticSearch(
    api, { mode: "LIVE", semanticRelease: release }, semanticId, graph,
  );
  assert.equal(result.state, "PRESENT");
  assert.deepEqual(result.capabilityIds, ["C.NUMBER"]);
  assert.equal(requests.length, 1);
  assert.equal(requests[0].family, "semantic");
  assert.match(requests[0].record_id, /^semantic-concept:/);
  assert.equal(requests.some((request) => request.family === "reference"), false);
});

test("historical exact semantic lookup fails closed rather than querying current source state", async () => {
  let calls = 0;
  const result = await resolveExactSemanticSearch({
    async query() { calls += 1; throw new Error("must not query"); },
  }, { mode: "HISTORICAL", semanticRelease: "b".repeat(64) }, "semantic:exact:B.NOT", currentGraph());
  assert.equal(result.state, "UNAVAILABLE");
  assert.equal(result.reason, "HISTORICAL_EXACT_SEMANTIC_LOOKUP_UNAVAILABLE");
  assert.equal(calls, 0);
});

test("historical semantic reverse lookup fails closed rather than borrowing current release mappings", async () => {
  let calls = 0;
  const result = await resolveCapabilitySemanticBindings({
    async query() { calls += 1; throw new Error("must not query"); },
  }, { mode: "HISTORICAL", semanticRelease: "b".repeat(64) }, "B.NOT");
  assert.equal(result.state, "UNAVAILABLE");
  assert.equal(calls, 0);
});

test("GUI22 source keeps learned similarity out of causal edges and destination availability explicit", () => {
  const markup = fs.readFileSync(
    path.join(rendererRoot, "school", "curriculum-atlas-markup.mjs"), "utf8",
  );
  const model = fs.readFileSync(
    path.join(rendererRoot, "school", "curriculum-atlas-model.mjs"), "utf8",
  );
  assert.match(model, /DECLARED_PREREQUISITE/);
  assert.match(model, /SCHOOL_DECLARED/);
  assert.match(markup, /route\("capability", "capability", node\.id\)/);
  assert.match(markup, /Open in Capability/);
  assert.match(markup, /Open in Lineage · capability route unavailable/);
  assert.match(markup, /no scheduling guarantee/);
});

test("GUI22 graph is keyboard-first, text-redundant, and reduced-motion safe", () => {
  const view = fs.readFileSync(
    path.join(rendererRoot, "school", "curriculum-atlas-view.mjs"), "utf8",
  );
  const markup = fs.readFileSync(
    path.join(rendererRoot, "school", "curriculum-atlas-markup.mjs"), "utf8",
  );
  const css = fs.readFileSync(
    path.join(rendererRoot, "school", "curriculum-atlas.css"), "utf8",
  );
  assert.match(markup, /data-focus-key="curriculum:/);
  assert.match(markup, /NEW THIS GRADE/);
  assert.match(css, /SOURCE_HELD/);
  assert.match(css, /IMPLEMENTATION_UNCOVERED/);
  assert.match(css, /prefers-reduced-motion/);
  assert.match(view, /aria-live="polite"/);
  assert.match(view, /equivalent non-visual representation/);
  assert.match(view, /semanticEpoch/);
  assert.match(view, /isActive/);
  assert.match(view, /bindContext/);
  assert.match(view, /restoreFocus/);
  assert.match(view, /onInspect\(node\.id, node,/);
  assert.match(markup, /data-focus-key="curriculum:trace:/);
  assert.match(markup, /data-focus-key="curriculum:filter:/);
  assert.match(css, /height: 160px/);
});

test("GUI22 open-in Semantic Atlas handoff is backed by route hydration", () => {
  const controller = fs.readFileSync(
    path.join(rendererRoot, "atlas", "atlas-controller.mjs"), "utf8",
  );
  const domains = fs.readFileSync(
    path.join(rendererRoot, "foundation", "domain-controller.mjs"), "utf8",
  );
  assert.match(controller, /ensureAtlasSelection/);
  assert.match(domains, /state\.selected\?\.kind === "semantic"/);
  assert.match(domains, /ensureAtlasSelection/);
});

test("School domain keeps GUI22 as a subview instead of a second curriculum authority destination", () => {
  const shell = fs.readFileSync(path.join(rendererRoot, "shell-state.mjs"), "utf8");
  const controller = fs.readFileSync(
    path.join(rendererRoot, "school", "school-domain-controller.mjs"), "utf8",
  );
  const i18n = fs.readFileSync(path.join(rendererRoot, "foundation", "i18n-shell.mjs"), "utf8");
  assert.equal(shell.includes('["curriculum-atlas"'), false);
  assert.match(controller, /shell\.school\.matrix/);
  assert.match(controller, /shell\.school\.atlas/);
  assert.match(i18n, /"shell\.school\.matrix": "Capability matrix"/);
  assert.match(i18n, /"shell\.school\.atlas": "Curriculum Semantic Atlas"/);
});
