import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  FIDELITY_FIXTURES,
  STRATEGY_FIXTURES,
  TEACHER_CHECKPOINT,
  TEACHER_PROJECTION,
} from "../../renderer/teacher/teacher-fixture.mjs";
import {
  aggregateContext,
  comparisonScopes,
  fidelityForStrategy,
  roleCounts,
  strategyById,
  strategyComparison,
  strategyEpisodes,
  teacherProjectionBoundary,
} from "../../renderer/teacher/teacher-model.mjs";
import { teacherMarkupForTest } from "../../renderer/teacher/teacher-view.mjs";
import { assertUniqueTestIds, collectTestIds } from "../../renderer/foundation/test-hooks.mjs";
import { t } from "../../renderer/foundation/i18n.mjs";
import { INSPECTOR_OWNERS } from "../../renderer/shell-state.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../../../..");
const rendererRoot = path.resolve(here, "../../renderer");
const teacherCss = () => [
  "teacher/teacher.css",
  "teacher/teacher-core.css",
  "teacher/teacher-detail.css",
  "teacher/teacher-comparison.css",
].map((name) => fs.readFileSync(path.join(rendererRoot, name), "utf8")).join("\n");

test("strategy roster contains incumbent challenger canary and retired fixture roles", () => {
  assert.deepEqual(roleCounts(), {
    INCUMBENT: 1,
    CHALLENGER: 1,
    CANARY: 1,
    RETIRED: 1,
  });
  const retired = STRATEGY_FIXTURES.find((strategy) => strategy.role === "RETIRED");
  assert.equal(retired.status, "CHECKPOINT_LOCAL_RETIRED");
  assert.equal(retired.retiredCheckpoint, TEACHER_CHECKPOINT);
});

test("strategy metrics keep no-gain and interference numerically distinct", () => {
  for (const strategy of STRATEGY_FIXTURES) {
    assert.equal(Number.isInteger(strategy.noGain), true);
    assert.equal(Number.isInteger(strategy.interference), true);
    assert.equal(strategy.noGain >= 0 && strategy.interference >= 0, true);
    assert.equal(strategy.retained + strategy.noGain + strategy.interference, strategy.attempts);
  }
  const challenger = strategyById("strategy:fixture:challenger-balanced");
  assert.notEqual(challenger.noGain, challenger.interference);
  const css = teacherCss();
  assert.match(css, /\.teacher-no-gain/);
  assert.match(css, /\.teacher-interference/);
});

test("context aggregation reports attempts gains cost and partial resource coverage without synthetic memory", () => {
  const incumbent = strategyById("strategy:fixture:incumbent-deep-contrast");
  const metrics = aggregateContext(incumbent.contexts);
  assert.deepEqual(metrics, {
    observations: 14,
    retained: 8,
    noGain: 4,
    interference: 2,
    actualGain: 17,
    averageWallSeconds: 13.38,
    medianWallSeconds: 13.4,
    attemptedSteps: 112,
    coverage: "PRESENT",
  });
  assert.equal(incumbent.resourceState, "PARTIAL");
  assert.equal("memoryBytes" in incumbent, false);
});

test("comparison uses only common scopes and labels unequal denominators partial", () => {
  const strategies = [
    strategyById("strategy:fixture:incumbent-deep-contrast"),
    strategyById("strategy:fixture:challenger-balanced"),
  ];
  assert.deepEqual(comparisonScopes(strategies), {
    capabilities: ["B.AND"],
    sourceFamilies: ["factory:boolean-ast"],
  });
  const comparison = strategyComparison(
    strategies.map((strategy) => strategy.id),
    { kind: "capability", value: "B.AND" },
  );
  assert.equal(comparison.commonCoverageFloor, 5);
  assert.equal(comparison.coverage, "PARTIAL_OBSERVED_DENOMINATORS");
  assert.deepEqual(
    comparison.rows.map((row) => row.metrics.observations),
    [8, 5],
  );
});

test("equal observed denominators remain descriptive and do not imply ranking or cohort identity", () => {
  const comparison = strategyComparison(
    [
      "strategy:fixture:incumbent-deep-contrast",
      "strategy:fixture:retired-shallow",
    ],
    { kind: "capability", value: "B.IFF" },
  );
  assert.equal(comparison.commonCoverageFloor, 6);
  assert.equal(comparison.coverage, "EQUAL_OBSERVED_DENOMINATORS");
  assert.deepEqual(comparison.rows.map((row) => row.metrics.observations), [6, 6]);
  assert.equal("winner" in comparison, false);
  assert.equal("ranking" in comparison, false);
});

test("capability-specific strategy evidence links to literal GUI06 learning episode record identities", () => {
  const incumbent = strategyById("strategy:fixture:incumbent-deep-contrast");
  const episodes = strategyEpisodes(incumbent);
  assert.equal(episodes.length, 2);
  assert.deepEqual(
    episodes.map((episode) => episode.recordId),
    [
      "episode-record:fixture:retained-44239",
      "episode-record:fixture:no-gain-reject",
    ],
  );
  for (const episode of episodes) {
    assert.equal(episode.href.startsWith("#/view/learning?"), true);
    assert.equal(episode.href.includes("kind=episode"), true);
  }
});

test("retired strategy history remains inspectable across checkpoint change", () => {
  const retired = strategyById("strategy:fixture:retired-shallow");
  assert.deepEqual(
    retired.history.map((item) => [item.checkpoint, item.role, item.state]),
    [
      ["checkpoint:fixture:g44237", "INCUMBENT", "ACTIVE"],
      ["checkpoint:fixture:g44238", "INCUMBENT", "ACTIVE"],
      [TEACHER_CHECKPOINT, "RETIRED", "CHECKPOINT_LOCAL_RETIRED"],
    ],
  );
  assert.equal(retired.lastUsedCheckpoint, "checkpoint:fixture:g44238");
});

test("multifidelity ladder remains observational at 2 4 8 16 and never changes authority", () => {
  for (const review of FIDELITY_FIXTURES) {
    assert.equal(review.schema, "bilqis.teacher-multifidelity-shadow/v1");
    assert.equal(review.mode, "SHADOW");
    assert.deepEqual(review.rungs, [2, 4, 8, 16]);
    assert.equal(review.actualAuthorityChanged, false);
    assert.equal(review.actualStepsSpent, 16);
  }
  assert.equal(
    fidelityForStrategy("strategy:fixture:retired-shallow")[0].firstWouldStopStep,
    8,
  );
});

test("fixture fidelity contract matches executable shadow policy authority boundary", () => {
  const source = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/learning/_teaching/teacher_multifidelity.py"),
    "utf8",
  );
  for (const literal of [
    "rungs=(2, 4, 8, 16)",
    '"mode": "SHADOW"',
    '"actual_authority_changed": False',
    '"authority_changed": False',
  ]) assert.equal(source.includes(literal), true, literal);
});

test("strategy population fixture roles respect bounded incumbent and active population semantics", () => {
  const source = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/learning/_teacher_strategy/population.py"),
    "utf8",
  );
  assert.equal(source.includes("ACTIVE_EFFECTIVE_STRATEGY_LIMIT = 16"), true);
  assert.equal(source.includes("ACTIVE_EFFECTIVE_INCUMBENT_LIMIT = 8"), true);
  assert.equal(source.includes("incumbents = sorted("), true);
  assert.equal(source.includes("challengers = sorted("), true);
});

test("canary fixture reflects bounded selected-canary authority without conflating shadow fidelity", () => {
  const canary = strategyById("strategy:fixture:vnext-canary");
  assert.equal(canary.role, "CANARY");
  assert.equal(canary.canaryStatus, "SELECTED");
  assert.equal(canary.actualAuthorityChanged, true);
  const source = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/learning/_teaching/teacher_vnext_replay.py"),
    "utf8",
  );
  assert.equal(source.includes('"actual_authority_changed": True'), true);
  assert.equal(source.includes("CANARY_EVERY_N_VISITS = 4"), true);
});

test("CP02 TeacherSnapshot boundary is explicit and rich strategy lab remains fixture-backed", () => {
  assert.equal(teacherProjectionBoundary(), TEACHER_PROJECTION);
  assert.equal(TEACHER_PROJECTION.richStrategyProjection, false);
  const source = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/mission_control/contracts/observability.py"),
    "utf8",
  );
  for (const field of [
    "teacher_identity: str",
    "teacher_epoch: int",
    "strategy_id: str",
    "attempts: DataValue",
    "accepted: DataValue",
    "rejected: DataValue",
  ]) assert.equal(source.includes(field), true, field);
});

test("grade labels cannot create teacher strategy priority quota or synthetic recommendations", () => {
  for (const strategy of STRATEGY_FIXTURES) {
    for (const forbidden of [
      "gradePriority", "gradeQuota", "priorityScore", "recommendation", "rank",
    ]) assert.equal(forbidden in strategy, false, forbidden);
  }
  assert.equal(INSPECTOR_OWNERS.strategy, "teacher");
  const source = fs.readFileSync(path.join(rendererRoot, "teacher/teacher-view.mjs"), "utf8").toLowerCase();
  for (const forbidden of ["best strategy", "recommended strategy", "winner badge"]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
});

test("teacher target markup is roster-first with selected detail rather than strategy card wall", () => {
  const markup = teacherMarkupForTest();
  assert.equal(assertUniqueTestIds(markup), true);
  const ids = new Set(collectTestIds(markup));
  for (const id of [
    "teacher-view",
    "teacher-heading",
    "teacher-roster",
    "teacher-roster-scroll",
    "teacher-strategy-detail",
    "teacher-strategy-inspect",
    "teacher-comparison",
    "teacher-comparison-table",
    "teacher-fidelity",
    "teacher-fidelity-table",
    "teacher-projection",
    "teacher-glossary",
  ]) assert.equal(ids.has(id), true, id);

  assert.match(markup, /<table class="teacher-roster-table">/);
  assert.match(markup, /<section class="teacher-strategy-detail"/);
  assert.doesNotMatch(markup, /class="strategy-card"/);
  assert.doesNotMatch(markup, /class="fidelity-card"/);
  assert.doesNotMatch(markup, /class="ui-glossary"/);
});

test("teacher interaction grammars keep roster selection, comparison toggles, scope, links, and status distinct", () => {
  const markup = teacherMarkupForTest();
  assert.match(markup, /class="teacher-strategy-select"[^>]+aria-pressed=/);
  assert.match(markup, /class="teacher-compare-strategy"[^>]+aria-pressed=/);
  assert.match(markup, /<select data-compare-scope/);
  assert.match(markup, /<a href="#\/view\/learning\?/);
  assert.match(markup, /class="teacher-state"/);
});

test("teacher comparison and fidelity remain aligned descriptive evidence without ranking", () => {
  const markup = teacherMarkupForTest();
  assert.match(markup, /<table class="teacher-comparison-table"/);
  assert.match(markup, /<table class="teacher-fidelity-table"/);
  assert.match(markup, /Descriptive evidence only/);
  assert.match(markup, /Observational only/);
  assert.match(markup, /Shadow observations do not authorize early termination/);
  for (const forbidden of ["winner", "rank #", "recommended", "trophy"]) {
    assert.equal(markup.toLowerCase().includes(forbidden), false, forbidden);
  }
});

test("teacher projection limitation and metric guidance are progressive disclosures", () => {
  const markup = teacherMarkupForTest();
  assert.match(markup, /<details class="teacher-projection"/);
  assert.match(markup, /<details class="teacher-glossary"/);
  assert.doesNotMatch(markup, /<div class="ui-glossary"/);
});

test("teacher owned human copy resolves through stable i18n keys", () => {
  for (const key of [
    "teacher.view.title",
    "teacher.roster.title",
    "teacher.detail.outcomes",
    "teacher.comparison.title",
    "teacher.fidelity.title",
    "teacher.projection.summary",
    "teacher.inspector.role",
  ]) assert.ok(t(key));
});

test("teacher CSS is table-oriented, responsive, compact-aware, and free of retired decoration", () => {
  const css = teacherCss();
  assert.match(css, /\.teacher-table-wrap\s*\{[^}]*overflow:\s*auto/s);
  assert.match(css, /\.teacher-roster-table,/);
  assert.match(css, /font-variant-numeric:\s*tabular-nums/);
  assert.match(css, /:root\[data-density="compact"\]/);
  assert.match(css, /@media \(max-width: 980px\)/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)/);
  assert.doesNotMatch(css, /repeating-linear-gradient/);
  assert.doesNotMatch(css, /data-density="terminal"/);
  assert.doesNotMatch(css, /\.strategy-roster\s*\{[^}]*repeat\(2,/s);
});
