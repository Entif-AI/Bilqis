import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  FIDELITY_FIXTURES, STRATEGY_FIXTURES, TEACHER_CHECKPOINT, TEACHER_PROJECTION,
} from "../../renderer/teacher/teacher-fixture.mjs";
import {
  aggregateContext, comparisonScopes, fidelityForStrategy, roleCounts, strategyById,
  strategyComparison, strategyEpisodes, teacherProjectionBoundary,
} from "../../renderer/teacher/teacher-model.mjs";
import { INSPECTOR_OWNERS } from "../../renderer/shell-state.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../../../..");
const rendererRoot = path.resolve(here, "../../renderer");

test("strategy roster contains incumbent challenger canary and retired fixture roles", () => {
  assert.deepEqual(roleCounts(), { INCUMBENT: 1, CHALLENGER: 1, CANARY: 1, RETIRED: 1 });
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
  assert.notEqual(strategyById("strategy:fixture:challenger-balanced").noGain,
    strategyById("strategy:fixture:challenger-balanced").interference);
});

test("context aggregation reports attempts gains cost and partial resource coverage without synthetic memory", () => {
  const incumbent = strategyById("strategy:fixture:incumbent-deep-contrast");
  assert.deepEqual(aggregateContext(incumbent.contexts), {
    observations: 14, retained: 8, noGain: 4, interference: 2, actualGain: 17,
    averageWallSeconds: 13.38, medianWallSeconds: 13.4, attemptedSteps: 112,
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
    capabilities: ["B.AND"], sourceFamilies: ["factory:boolean-ast"],
  });
  const comparison = strategyComparison(strategies.map((strategy) => strategy.id), {
    kind: "capability", value: "B.AND",
  });
  assert.equal(comparison.commonCoverageFloor, 5);
  assert.equal(comparison.coverage, "PARTIAL_OBSERVED_DENOMINATORS");
  assert.deepEqual(comparison.rows.map((row) => row.metrics.observations), [8, 5]);
});

test("equal observed denominators remain descriptive and do not imply ranking or cohort identity", () => {
  const comparison = strategyComparison([
    "strategy:fixture:incumbent-deep-contrast", "strategy:fixture:retired-shallow",
  ], { kind: "capability", value: "B.IFF" });
  assert.equal(comparison.commonCoverageFloor, 6);
  assert.equal(comparison.coverage, "EQUAL_OBSERVED_DENOMINATORS");
  assert.deepEqual(comparison.rows.map((row) => row.metrics.observations), [6, 6]);
  assert.equal("winner" in comparison, false);
  assert.equal("ranking" in comparison, false);
});

test("capability-specific strategy evidence links to literal learning episode record identities", () => {
  const episodes = strategyEpisodes(strategyById("strategy:fixture:incumbent-deep-contrast"));
  assert.deepEqual(episodes.map((episode) => episode.recordId), [
    "episode-record:fixture:retained-44239", "episode-record:fixture:no-gain-reject",
  ]);
  for (const episode of episodes) {
    assert.equal(episode.href.startsWith("#/view/learning?"), true);
    assert.equal(episode.href.includes("kind=episode"), true);
  }
});

test("retired strategy history remains inspectable across checkpoint change", () => {
  const retired = strategyById("strategy:fixture:retired-shallow");
  assert.deepEqual(retired.history.map((item) => [item.checkpoint, item.role, item.state]), [
    ["checkpoint:fixture:g44237", "INCUMBENT", "ACTIVE"],
    ["checkpoint:fixture:g44238", "INCUMBENT", "ACTIVE"],
    [TEACHER_CHECKPOINT, "RETIRED", "CHECKPOINT_LOCAL_RETIRED"],
  ]);
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
  assert.equal(fidelityForStrategy("strategy:fixture:retired-shallow")[0].firstWouldStopStep, 8);
});

test("fixture fidelity contract matches executable shadow policy authority boundary", () => {
  const source = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/learning/_teaching/teacher_multifidelity.py"), "utf8",
  );
  for (const literal of [
    "rungs=(2, 4, 8, 16)", '"mode": "SHADOW"',
    '"actual_authority_changed": False', '"authority_changed": False',
  ]) assert.equal(source.includes(literal), true, literal);
});

test("strategy population fixture roles respect bounded active population semantics", () => {
  const source = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/learning/_teacher_strategy/population.py"), "utf8",
  );
  for (const literal of [
    "ACTIVE_EFFECTIVE_STRATEGY_LIMIT = 16", "ACTIVE_EFFECTIVE_INCUMBENT_LIMIT = 8",
    "incumbents = sorted(", "challengers = sorted(",
  ]) assert.equal(source.includes(literal), true, literal);
});

test("canary fixture reflects bounded selected-canary authority without conflating shadow fidelity", () => {
  const canary = strategyById("strategy:fixture:vnext-canary");
  assert.equal(canary.role, "CANARY");
  assert.equal(canary.canaryStatus, "SELECTED");
  assert.equal(canary.actualAuthorityChanged, true);
  const source = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/learning/_teaching/teacher_vnext_replay.py"), "utf8",
  );
  assert.equal(source.includes('"actual_authority_changed": True'), true);
  assert.equal(source.includes("CANARY_EVERY_N_VISITS = 4"), true);
});

test("CP02 TeacherSnapshot boundary is explicit and rich strategy lab remains fixture-backed", () => {
  assert.equal(teacherProjectionBoundary(), TEACHER_PROJECTION);
  assert.equal(TEACHER_PROJECTION.richStrategyProjection, false);
  const source = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/mission_control/contracts/observability.py"), "utf8",
  );
  for (const field of [
    "teacher_identity: str", "teacher_epoch: int", "strategy_id: str",
    "attempts: DataValue", "accepted: DataValue", "rejected: DataValue",
  ]) assert.equal(source.includes(field), true, field);
});

test("grade labels cannot create teacher strategy priority quota or synthetic recommendations", () => {
  for (const strategy of STRATEGY_FIXTURES) {
    for (const forbidden of ["gradePriority", "gradeQuota", "priorityScore", "recommendation", "rank"]) {
      assert.equal(forbidden in strategy, false, forbidden);
    }
  }
  assert.equal(INSPECTOR_OWNERS.strategy, "teacher");
  const source = fs.readFileSync(path.join(rendererRoot, "teacher/teacher-view.mjs"), "utf8").toLowerCase();
  for (const forbidden of ["best strategy", "recommended strategy", "winner badge"]) {
    assert.equal(source.includes(forbidden), false, forbidden);
  }
});
