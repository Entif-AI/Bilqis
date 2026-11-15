import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseDeepLink } from "../../renderer/deep-link.mjs";
import { EPISODE_FIXTURES, EPISODE_STAGES } from "../../renderer/episodes/episode-fixture.mjs";
import {
  diffRows,
  episodeById,
  episodeDeepLink,
  episodesForCapability,
  lifecycleCoverage,
  rejectionClass,
  replaySlice,
  retainedTransition,
  rollbackInvariant,
} from "../../renderer/episodes/episode-model.mjs";
import { episodeMarkupForTest } from "../../renderer/episodes/episode-view.mjs";
import { INSPECTOR_OWNERS } from "../../renderer/shell-state.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../../../..");
const rendererRoot = path.resolve(here, "../../renderer");

function fixture(id) {
  const value = EPISODE_FIXTURES.find((episode) => episode.episodeId === id);
  assert.ok(value, id);
  return value;
}

test("episode fixtures expose the complete GUI06 transaction header contract", () => {
  for (const episode of EPISODE_FIXTURES) {
    for (const field of [
      "recordId", "episodeId", "candidateId", "capabilityId", "parentGeneration", "strategy",
      "sourceFamily", "lessonFamily", "intendedOptimizerSteps", "attemptedOptimizerSteps",
      "terminalState", "resourceCost", "stages",
    ]) assert.notEqual(episode[field], undefined, field);
    assert.equal(episode.stages.length, 7);
  }
});

test("retained fixture proves exact parent to child generation transition", () => {
  const retained = fixture("episode:fixture:retained-44239");
  assert.deepEqual(retainedTransition(retained), {
    parentGeneration: 44238,
    childGeneration: 44239,
    checkpointId: "checkpoint:fixture:g44239",
    committed: true,
  });
  assert.equal(retained.retainedOptimizerSteps, retained.attemptedOptimizerSteps);
  assert.notEqual(retained.parentState.before.student, retained.parentState.after.student);
  assert.equal(retained.target.committedAfter.correct, retained.target.candidateAfter.correct);
});

test("destructive-interference rejection proves parent state and committed evidence are unchanged", () => {
  const rejected = fixture("episode:fixture:interference-reject");
  assert.equal(rejectionClass(rejected), "INTERFERENCE");
  assert.deepEqual(rollbackInvariant(rejected), {
    neuralUnchanged: true,
    optimizerUnchanged: true,
    allocationUnchanged: true,
    retainedOptimizerStepsZero: true,
    noChildGeneration: true,
  });
  assert.equal(rejected.target.candidateAfter.correct > rejected.target.before.correct, true);
  assert.equal(rejected.protected.candidateAfter.correct < rejected.protected.before.correct, true);
  assert.deepEqual(rejected.target.committedAfter, rejected.target.before);
  assert.deepEqual(rejected.protected.committedAfter, rejected.protected.before);
  assert.equal(rejected.wholeSchool.committedDelta, 0);
  assert.equal(rejected.memory.state, "UNAVAILABLE");
  assert.equal(rejected.allocation.committedAfterSlots, rejected.allocation.beforeSlots);
  assert.equal(rejected.allocation.candidateAfterSlots, null);
});

test("no-gain rejection is semantically and visually distinct from interference rejection", () => {
  const noGain = fixture("episode:fixture:no-gain-reject");
  const interference = fixture("episode:fixture:interference-reject");
  assert.equal(noGain.retentionReason, "NO_MEASURABLE_TARGET_GAIN");
  assert.equal(rejectionClass(noGain), "NO_GAIN");
  assert.equal(rejectionClass(interference), "INTERFERENCE");
  assert.deepEqual(noGain.target.candidateAfter, noGain.target.before);
  assert.equal(noGain.protected.candidateAfter, null);
  assert.equal(noGain.protected.reason, "TARGET_DID_NOT_GAIN");
  assert.equal(noGain.stages.find((stage) => stage.id === "protected").state, "MISSING");
  const noGainMarkup = episodeMarkupForTest(noGain.recordId);
  const interferenceMarkup = episodeMarkupForTest(interference.recordId);
  assert.match(noGainMarkup, /data-class="NO_GAIN"/);
  assert.match(interferenceMarkup, /data-class="INTERFERENCE"/);
  assert.match(noGainMarkup, /No measurable target gain/);
  assert.match(interferenceMarkup, /Protected-capability regression/);
});

test("before/after diff keeps challenger effects separate from committed parent effects", () => {
  const rejected = fixture("episode:fixture:interference-reject");
  const rows = diffRows(rejected);
  const target = rows.find((row) => row.labelKey === "learning.comparison.targetScore");
  const protectedRow = rows.find((row) => row.labelKey === "learning.comparison.protectedScore");
  assert.deepEqual([target.before, target.challenger, target.committed], ["8/12", "10/12", "8/12"]);
  assert.deepEqual([protectedRow.before, protectedRow.challenger, protectedRow.committed], ["48/48", "44/48", "48/48"]);
});

test("lifecycle replay can stop at every evidenced stage without inventing later evidence", () => {
  const retained = fixture("episode:fixture:retained-44239");
  assert.deepEqual(EPISODE_STAGES.map((stage) => stage.id), [
    "proposed", "lesson", "optimizer", "target", "protected", "decision", "finalize",
  ]);
  for (let index = 0; index < EPISODE_STAGES.length; index += 1) {
    const replay = replaySlice(retained, index);
    assert.equal(replay.stageIndex, index);
    assert.equal(replay.visibleStages.length, index + 1);
    assert.equal(replay.active.id, EPISODE_STAGES[index].id);
  }
});

test("pending or lost episode renders partial and missing stages instead of fabricated terminal values", () => {
  const pending = fixture("episode:fixture:reconciliation-pending");
  assert.equal(pending.terminalState, "UNKNOWN");
  assert.equal(pending.commandState, "OUTCOME_UNKNOWN");
  assert.equal(pending.retainedOptimizerSteps, null);
  assert.equal(pending.resultingGeneration, null);
  assert.equal(pending.target.candidateAfter, null);
  assert.deepEqual(lifecycleCoverage(pending), {
    PRESENT: 2,
    PARTIAL: 1,
    PENDING: 2,
    MISSING: 2,
  });
});

test("stage evidence provides drill-through classes required by GUI06", () => {
  const retained = fixture("episode:fixture:retained-44239");
  const types = new Set(retained.stages.flatMap((stage) => stage.evidence.map((item) => item.type)));
  for (const type of [
    "rows", "lesson", "grader", "rubric", "source-revision", "resource", "checkpoint", "receipt",
  ]) assert.equal(types.has(type), true, type);
});

test("episode deep link is origin-neutral and capability explorers can resolve the same stable route", () => {
  const retained = fixture("episode:fixture:retained-44239");
  const link = episodeDeepLink(retained.recordId);
  assert.deepEqual(parseDeepLink(link), {
    view: "learning",
    selected: { kind: "episode", id: retained.recordId },
  });
  assert.equal(INSPECTOR_OWNERS.episode, "learning");
  const capabilityEpisodes = episodesForCapability("B.AND");
  assert.equal(capabilityEpisodes.some((episode) => episode.recordId === retained.recordId), true);
  assert.equal(episodeById(retained.candidateId).episodeId, retained.episodeId);
  assert.equal(episodeById(retained.recordId).episodeId, retained.episodeId);
  const catalog = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/mission_control/query_catalog.py"),
    "utf8",
  );
  assert.equal(catalog.includes('"EPISODE", meta.record_id, item.meta.record_id,'), true);
  assert.equal(catalog.includes("item.meta.record_id))"), true);
});

test("fixture reason codes and rollback claims match executable retention contracts", () => {
  const policy = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/learning/_retention/retention_policy.py"),
    "utf8",
  );
  const visit = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/runtime/_visits/retention.py"),
    "utf8",
  );
  const acceptance = fs.readFileSync(
    path.join(repoRoot, "bilqis_mlx/learning/_retention/atlas_acceptance.py"),
    "utf8",
  );
  for (const reason of [
    "NO_MEASURABLE_TARGET_GAIN",
    "PROTECTED_CAPABILITY_REGRESSION",
    "PAIRED_SCREEN_WITHIN_BUDGET",
  ]) assert.equal(policy.includes(reason), true, reason);
  assert.equal(visit.includes('if s.outcome["decision"] == "PROVISIONAL":'), true);
  assert.equal(visit.includes("s.after = s.before"), true);
  assert.equal(visit.includes("s.attempted_optimizer_updates"), true);
  assert.equal(visit.includes("s.retained_optimizer_updates"), true);
  for (const field of [
    "generation: int",
    "parent_candidate_identity_sha256: str",
    "optimizer_step: int",
    "retention_reason: str",
    "decision_sha256: str",
    "evidence_sha256: str",
  ]) assert.equal(acceptance.includes(field), true, field);
});
