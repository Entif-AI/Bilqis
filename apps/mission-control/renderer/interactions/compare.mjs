import { EPISODE_FIXTURES } from "../episodes/episode-fixture.mjs";
import { scoreText } from "../episodes/episode-model.mjs";
import {
  compareGenerations,
  lineageNodes,
} from "../lineage/lineage-model.mjs";
import {
  STRATEGY_FIXTURES,
} from "../teacher/teacher-fixture.mjs";
import { strategyComparison } from "../teacher/teacher-model.mjs";
import { t } from "../foundation/i18n.mjs";

function row(key, label, left, right, state = null, reason = null) {
  const leftText = left ?? t("investigation.state.unavailable");
  const rightText = right ?? t("investigation.state.unavailable");
  return Object.freeze({
    key,
    label,
    left: String(leftText),
    right: String(rightText),
    state: state ?? (String(leftText) === String(rightText) ? "SAME" : "DIFFERENT"),
    reason,
  });
}

const GENERATION_ROWS = Object.freeze({
  "Capability debt": ["capability-debt", "investigation.compare.row.capabilityDebt"],
  "Retention disposition": ["retention-disposition", "investigation.compare.row.retentionDisposition"],
  "Active semantic set": ["active-semantic-set", "investigation.compare.row.activeSemanticSet"],
  "Active bank count": ["active-bank-count", "investigation.compare.row.activeBankCount"],
  "Memory allocation/state": ["memory-allocation-state", "investigation.compare.row.memoryAllocation"],
  "Source/correction frontier": ["source-correction-frontier", "investigation.compare.row.correctionFrontier"],
  "Teacher epoch": ["teacher-epoch", "investigation.compare.row.teacherEpoch"],
  "Topology digest/version": ["topology-digest-version", "investigation.compare.row.topology"],
  "Implementation digest": ["implementation-digest", "investigation.compare.row.implementationDigest"],
  "Resource profile": ["resource-profile", "investigation.compare.row.resourceProfile"],
  "Evaluation contract": ["evaluation-contract", "investigation.compare.row.evaluationContract"],
  "Projection frontier": ["projection-frontier", "investigation.compare.row.projectionFrontier"],
});

function generationLabel(label) {
  const row = GENERATION_ROWS[label];
  return row ? t(row[1]) : label;
}

function generationReason(reason) {
  return reason === "Topology/version changed; these resource profiles are not declared comparable."
    ? t("investigation.compare.topologyUnavailable")
    : reason;
}

function relationLabel(value) {
  return t({
    DIRECT_PARENT_CHILD: "investigation.compare.relation.directParentChild",
    SIBLING_BRANCHES: "investigation.compare.relation.siblingBranches",
    NON_ADJACENT_LINEAGE: "investigation.compare.relation.nonAdjacent",
  }[value]);
}

function result(kind, left, right, rows, {
  state = "PRESENT",
  note = t("investigation.compare.literalOnly"),
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
      note: t("investigation.compare.generationUnavailable"),
    });
  }
  const comparison = compareGenerations(leftNode.manifestSha256, rightNode.manifestSha256);
  const rows = [
    row("relation", t("investigation.compare.row.relation"), relationLabel(comparison.relation), relationLabel(comparison.relation), "SAME"),
    ...comparison.rows.map((item) =>
      row(GENERATION_ROWS[item.label]?.[0] ?? item.label, generationLabel(item.label), item.before, item.after, item.state, generationReason(item.reason))),
    ...comparison.capabilityChanges.map((item) =>
      row(`capability-${item.id}`, t("investigation.compare.row.capability", { id: item.id }), item.before, item.after, item.state)),
  ];
  return result("generation", left, right, rows, { note: t("investigation.compare.literalOnly") });
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
      note: t("investigation.compare.candidateUnavailable"),
    });
  }
  return result("candidate", left, right, [
    row("target-capability", t("investigation.compare.row.targetCapability"), a.capabilityId, b.capabilityId),
    row("parent-generation", t("investigation.compare.row.parentGeneration"), a.parentGeneration, b.parentGeneration),
    row("terminal-state", t("investigation.compare.row.terminalState"), a.terminalState, b.terminalState),
    row("retention-reason", t("investigation.compare.row.retentionReason"), a.retentionReason, b.retentionReason),
    row("target-before", t("investigation.compare.row.targetBefore"), scoreText(a.target.before), scoreText(b.target.before)),
    row("target-challenger", t("investigation.compare.row.targetChallenger"), scoreText(a.target.candidateAfter), scoreText(b.target.candidateAfter)),
    row("target-committed", t("investigation.compare.row.targetCommitted"), scoreText(a.target.committedAfter), scoreText(b.target.committedAfter)),
    row("protected-challenger", t("investigation.compare.row.protectedChallenger"), scoreText(a.protected.candidateAfter), scoreText(b.protected.candidateAfter)),
    row("protected-committed", t("investigation.compare.row.protectedCommitted"), scoreText(a.protected.committedAfter), scoreText(b.protected.committedAfter)),
    row("whole-school-challenger", t("investigation.compare.row.wholeSchoolChallenger"), a.wholeSchool.candidateDelta, b.wholeSchool.candidateDelta),
    row("whole-school-committed", t("investigation.compare.row.wholeSchoolCommitted"), a.wholeSchool.committedDelta, b.wholeSchool.committedDelta),
    row("debt-challenger", t("investigation.compare.row.debtChallenger"), a.debt.candidateAfter, b.debt.candidateAfter),
    row("debt-committed", t("investigation.compare.row.debtCommitted"), a.debt.committedAfter, b.debt.committedAfter),
    row("attempted-optimizer-steps", t("investigation.compare.row.attemptedOptimizer"), a.attemptedOptimizerSteps, b.attemptedOptimizerSteps),
    row("retained-optimizer-steps", t("investigation.compare.row.retainedOptimizer"), a.retainedOptimizerSteps, b.retainedOptimizerSteps),
    row("resulting-generation", t("investigation.compare.row.resultingGeneration"), a.resultingGeneration, b.resultingGeneration),
  ]);
}

function compareCapabilityRefs(left, right) {
  const leftDetails = left.details ?? {};
  const rightDetails = right.details ?? {};
  const keys = [...new Set([...Object.keys(leftDetails), ...Object.keys(rightDetails)])].sort();
  if (!keys.length) {
    return result("capability", left, right, [], {
      state: "UNAVAILABLE",
      note: t("investigation.compare.capabilityUnavailable"),
    });
  }
  return result("capability", left, right, [
    row("capability-id", t("investigation.compare.row.capabilityId"), left.id, right.id),
    ...keys.map((key, index) => row(`detail-${index}`, key, leftDetails[key], rightDetails[key],
      Object.hasOwn(leftDetails, key) && Object.hasOwn(rightDetails, key)
        ? null : "UNAVAILABLE",
      Object.hasOwn(leftDetails, key) && Object.hasOwn(rightDetails, key)
        ? null : t("investigation.compare.factUnavailable"))),
  ]);
}

function compareStrategyRefs(left, right) {
  const ids = [left.id, right.id];
  if (!ids.every((id) => STRATEGY_FIXTURES.some((strategy) => strategy.id === id))) {
    return result("strategy", left, right, [], {
      state: "UNAVAILABLE",
      note: t("investigation.compare.strategyUnavailable"),
    });
  }
  const comparison = strategyComparison(ids, { kind: "whole-school", value: "ALL" });
  const [leftRow, rightRow] = comparison.rows;
  const leftMetrics = leftRow.metrics;
  const rightMetrics = rightRow.metrics;
  return result("strategy", left, right, [
    row("strategy-identity", t("investigation.compare.row.strategyIdentity"), leftRow.strategy.id, rightRow.strategy.id),
    row("role", t("investigation.compare.row.role"), leftRow.strategy.role, rightRow.strategy.role),
    row("observed-contexts", t("investigation.compare.row.contexts"), leftRow.matchedContexts.join(", ") || t("investigation.value.none"),
      rightRow.matchedContexts.join(", ") || t("investigation.value.none")),
    row("observations", t("investigation.compare.row.observations"), leftMetrics.observations, rightMetrics.observations),
    row("retained", t("investigation.compare.row.retained"), leftMetrics.retained, rightMetrics.retained),
    row("no-gain", t("investigation.compare.row.noGain"), leftMetrics.noGain, rightMetrics.noGain),
    row("interference", t("investigation.compare.row.interference"), leftMetrics.interference, rightMetrics.interference),
    row("actual-capability-gain", t("investigation.compare.row.actualGain"), leftMetrics.actualGain, rightMetrics.actualGain),
    row("average-wall-seconds", t("investigation.compare.row.averageWall"), leftMetrics.averageWallSeconds, rightMetrics.averageWallSeconds),
    row("median-wall-seconds", t("investigation.compare.row.medianWall"), leftMetrics.medianWallSeconds, rightMetrics.medianWallSeconds),
    row("attempted-steps", t("investigation.compare.row.attemptedSteps"), leftMetrics.attemptedSteps, rightMetrics.attemptedSteps),
    row("coverage", t("investigation.compare.row.coverage"), leftMetrics.coverage, rightMetrics.coverage),
  ], {
    note: t("investigation.compare.strategyNote", { coverage: comparison.coverage }),
  });
}

function compareIdentityRefs(left, right) {
  const keys = [...new Set([
    ...Object.keys(left.details ?? {}),
    ...Object.keys(right.details ?? {}),
  ])].sort();
  return result(left.kind, left, right, [
    row("identity", t("investigation.compare.row.identity"), left.id, right.id),
    ...keys.map((key, index) => row(`detail-${index}`, key, left.details?.[key], right.details?.[key],
      Object.hasOwn(left.details ?? {}, key) && Object.hasOwn(right.details ?? {}, key)
        ? null : "UNAVAILABLE")),
  ], { note: t("investigation.compare.identityOnly") });
}

export function compareStableRefs(left, right) {
  if (!left || !right) {
    return result("none", left, right, [], {
      state: "EMPTY",
      note: t("investigation.compare.empty"),
    });
  }
  if (left.kind !== right.kind) {
    return result("mixed", left, right, [
      row("object-class", t("investigation.compare.row.objectClass"), left.kind, right.kind, "INCOMPATIBLE"),
    ], {
      state: "INCOMPATIBLE",
      note: t("investigation.compare.mixed"),
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
    row("identity", t("investigation.compare.row.identity"), left.id, right.id),
  ], {
    state: "UNAVAILABLE",
    note: t("investigation.compare.adapterUnavailable"),
  });
}
