import { EPISODE_FIXTURES } from "../episodes/episode-fixture.mjs";
import { scoreText } from "../episodes/episode-model.mjs";
import {
  compareGenerations,
  lineageNodes,
} from "../lineage/lineage-model.mjs";
import { lineageT } from "../lineage/lineage-messages.mjs";
import {
  STRATEGY_FIXTURES,
} from "../teacher/teacher-fixture.mjs";
import { strategyComparison } from "../teacher/teacher-model.mjs";

function row(label, left, right, state = null, reason = null) {
  const leftText = left ?? "UNAVAILABLE";
  const rightText = right ?? "UNAVAILABLE";
  return Object.freeze({
    label,
    left: String(leftText),
    right: String(rightText),
    state: state ?? (String(leftText) === String(rightText) ? "SAME" : "DIFFERENT"),
    reason,
  });
}

function result(kind, left, right, rows, {
  state = "PRESENT",
  note = "Literal differences only. No winner is synthesized.",
} = {}) {
  return Object.freeze({
    state,
    kind,
    left,
    right,
    rows: Object.freeze(rows),
    note,
  });
}

function findGeneration(ref) {
  return lineageNodes().find((node) =>
    [node.id, node.recordId, node.manifestSha256, `checkpoint:${node.checkpointSha256}`]
      .includes(ref.id),
  ) ?? null;
}

function compareGenerationRefs(left, right) {
  const leftNode = findGeneration(left);
  const rightNode = findGeneration(right);
  if (!leftNode || !rightNode) {
    return result("generation", left, right, [], {
      state: "UNAVAILABLE",
      note: lineageT("lineage.compare.unavailableIdentity"),
    });
  }
  const comparison = compareGenerations(leftNode.manifestSha256, rightNode.manifestSha256);
  const rows = [
    row(lineageT("lineage.compare.relation"), comparison.relation, comparison.relation, "SAME"),
    ...comparison.rows.map((item) =>
      row(
        lineageT(`lineage.compare.dimension.${item.key}`),
        item.before,
        item.after,
        item.state,
        item.reasonKey ? lineageT(`lineage.compare.reason.${item.reasonKey}`) : null,
      )),
    ...comparison.capabilityChanges.map((item) =>
      row(lineageT("lineage.compare.capabilityRow", { id: item.id }), item.before, item.after, item.state)),
  ];
  return result("generation", left, right, rows, {
    note: lineageT(`lineage.compare.${comparison.interpretationKey}`),
  });
}

function findCandidate(ref) {
  return EPISODE_FIXTURES.find((episode) =>
    [episode.candidateId, episode.episodeId, episode.recordId].includes(ref.id),
  ) ?? null;
}

function compareCandidateRefs(left, right) {
  const a = findCandidate(left);
  const b = findCandidate(right);
  if (!a || !b) {
    return result("candidate", left, right, [], {
      state: "UNAVAILABLE",
      note: "One or both candidate identities are unavailable.",
    });
  }
  return result("candidate", left, right, [
    row("Target capability", a.capabilityId, b.capabilityId),
    row("Parent generation", a.parentGeneration, b.parentGeneration),
    row("Terminal state", a.terminalState, b.terminalState),
    row("Retention reason", a.retentionReason, b.retentionReason),
    row("Target before", scoreText(a.target.before), scoreText(b.target.before)),
    row("Target challenger", scoreText(a.target.candidateAfter), scoreText(b.target.candidateAfter)),
    row("Target committed", scoreText(a.target.committedAfter), scoreText(b.target.committedAfter)),
    row("Protected challenger", scoreText(a.protected.candidateAfter), scoreText(b.protected.candidateAfter)),
    row("Protected committed", scoreText(a.protected.committedAfter), scoreText(b.protected.committedAfter)),
    row("Whole-school challenger Δ", a.wholeSchool.candidateDelta, b.wholeSchool.candidateDelta),
    row("Whole-school committed Δ", a.wholeSchool.committedDelta, b.wholeSchool.committedDelta),
    row("Debt challenger", a.debt.candidateAfter, b.debt.candidateAfter),
    row("Debt committed", a.debt.committedAfter, b.debt.committedAfter),
    row("Attempted optimizer steps", a.attemptedOptimizerSteps, b.attemptedOptimizerSteps),
    row("Retained optimizer steps", a.retainedOptimizerSteps, b.retainedOptimizerSteps),
    row("Resulting generation", a.resultingGeneration, b.resultingGeneration),
  ]);
}

function compareCapabilityRefs(left, right) {
  const leftDetails = left.details ?? {};
  const rightDetails = right.details ?? {};
  const keys = [...new Set([...Object.keys(leftDetails), ...Object.keys(rightDetails)])].sort();
  if (!keys.length) {
    return result("capability", left, right, [], {
      state: "UNAVAILABLE",
      note: "The selected capability references do not expose a common literal fact set.",
    });
  }
  return result("capability", left, right, [
    row("Capability ID", left.id, right.id),
    ...keys.map((key) => row(key, leftDetails[key], rightDetails[key],
      Object.hasOwn(leftDetails, key) && Object.hasOwn(rightDetails, key)
        ? null : "UNAVAILABLE",
      Object.hasOwn(leftDetails, key) && Object.hasOwn(rightDetails, key)
        ? null : "Fact is not exposed on both capability references.")),
  ]);
}

function compareStrategyRefs(left, right) {
  const ids = [left.id, right.id];
  if (!ids.every((id) => STRATEGY_FIXTURES.some((strategy) => strategy.id === id))) {
    return result("strategy", left, right, [], {
      state: "UNAVAILABLE",
      note: "One or both strategy identities are unavailable.",
    });
  }
  const comparison = strategyComparison(ids, { kind: "whole-school", value: "ALL" });
  const [leftRow, rightRow] = comparison.rows;
  const leftMetrics = leftRow.metrics;
  const rightMetrics = rightRow.metrics;
  return result("strategy", left, right, [
    row("Strategy identity", leftRow.strategy.id, rightRow.strategy.id),
    row("Role", leftRow.strategy.role, rightRow.strategy.role),
    row("Observed contexts", leftRow.matchedContexts.join(", ") || "NONE",
      rightRow.matchedContexts.join(", ") || "NONE"),
    row("Observations", leftMetrics.observations, rightMetrics.observations),
    row("Retained", leftMetrics.retained, rightMetrics.retained),
    row("No gain", leftMetrics.noGain, rightMetrics.noGain),
    row("Interference", leftMetrics.interference, rightMetrics.interference),
    row("Actual capability gain", leftMetrics.actualGain, rightMetrics.actualGain),
    row("Average wall seconds", leftMetrics.averageWallSeconds, rightMetrics.averageWallSeconds),
    row("Median wall seconds", leftMetrics.medianWallSeconds, rightMetrics.medianWallSeconds),
    row("Attempted steps", leftMetrics.attemptedSteps, rightMetrics.attemptedSteps),
    row("Coverage", leftMetrics.coverage, rightMetrics.coverage),
  ], {
    note: `Whole-school descriptive evidence. Coverage: ${comparison.coverage}. No strategy ranking is synthesized.`,
  });
}

function compareIdentityRefs(left, right) {
  const keys = [...new Set([
    ...Object.keys(left.details ?? {}),
    ...Object.keys(right.details ?? {}),
  ])].sort();
  return result(left.kind, left, right, [
    row("Identity", left.id, right.id),
    ...keys.map((key) => row(key, left.details?.[key], right.details?.[key],
      Object.hasOwn(left.details ?? {}, key) && Object.hasOwn(right.details ?? {}, key)
        ? null : "UNAVAILABLE")),
  ], { note: "Exact identity and exposed source/release facts only." });
}

export function compareStableRefs(left, right) {
  if (!left || !right) {
    return result("none", left, right, [], {
      state: "EMPTY",
      note: "Choose both comparison sides.",
    });
  }
  if (left.kind !== right.kind) {
    return result("mixed", left, right, [
      row("Object class", left.kind, right.kind, "INCOMPATIBLE"),
    ], {
      state: "INCOMPATIBLE",
      note: "Different object classes are not coerced into one comparison.",
    });
  }
  if (["generation", "checkpoint"].includes(left.kind)) {
    return compareGenerationRefs(left, right);
  }
  if (["candidate", "episode"].includes(left.kind)) {
    return compareCandidateRefs(left, right);
  }
  if (left.kind === "capability") return compareCapabilityRefs(left, right);
  if (left.kind === "strategy") return compareStrategyRefs(left, right);
  if (["source", "semantic"].includes(left.kind)) return compareIdentityRefs(left, right);
  return result(left.kind, left, right, [
    row("Identity", left.id, right.id),
  ], {
    state: "UNAVAILABLE",
    note: "This object class has no declared GUI18 comparison adapter.",
  });
}
