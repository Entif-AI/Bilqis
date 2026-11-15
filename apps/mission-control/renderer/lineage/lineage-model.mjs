import { LINEAGE_FIXTURE } from "./lineage-fixture.mjs";

export function lineageNodes() {
  return LINEAGE_FIXTURE.nodes;
}

export function nodeByIdentity(identity) {
  return LINEAGE_FIXTURE.nodes.find((node) =>
    node.id === identity ||
    node.manifestSha256 === identity ||
    node.recordId === identity ||
    `checkpoint:${node.checkpointSha256}` === identity,
  ) ?? LINEAGE_FIXTURE.nodes.at(-1);
}

export function currentLineageNode() {
  return nodeByIdentity(LINEAGE_FIXTURE.currentManifestSha256);
}

export function lineageEdges() {
  const byManifest = new Map(LINEAGE_FIXTURE.nodes.map((node) => [node.manifestSha256, node]));
  return Object.freeze(LINEAGE_FIXTURE.nodes.flatMap((node) => {
    if (node.parentManifestSha256 === null) return [];
    const parent = byManifest.get(node.parentManifestSha256);
    return parent ? [Object.freeze({
      parentId: parent.id,
      childId: node.id,
      parentGeneration: parent.generation,
      childGeneration: node.generation,
      transitionClass: node.transitionClass,
    })] : [];
  }));
}

export function manifestFieldRows(node) {
  return node.manifestFields;
}

export function lineageDeepLink(node) {
  const params = new URLSearchParams({ kind: "generation", id: node.recordId });
  return "#/view/lineage?" + params.toString();
}

export function historicalGenerationQuery(node) {
  return Object.freeze({
    family: "generation",
    mode: "historical",
    run_id: node.runId,
    generation: node.generation,
    record_id: node.recordId,
  });
}

function scoreText(value) {
  return value ? `${value[0]}/${value[1]}` : "ABSENT";
}

function ratio(value) {
  return value ? value[0] / value[1] : null;
}

export function capabilityChanges(before, after) {
  const ids = [...new Set([
    ...Object.keys(before.compare.capabilities),
    ...Object.keys(after.compare.capabilities),
  ])].sort();
  return Object.freeze(ids.map((id) => {
    const left = before.compare.capabilities[id] ?? null;
    const right = after.compare.capabilities[id] ?? null;
    let state = "UNCHANGED";
    if (left === null) state = "GAINED_EVIDENCE";
    else if (right === null) state = "LOST_EVIDENCE";
    else if (ratio(right) < ratio(left)) state = "REGRESSED";
    else if (ratio(right) > ratio(left)) state = "SCORE_CHANGED";
    return Object.freeze({ id, before: scoreText(left), after: scoreText(right), state });
  }));
}

const literal = (key, before, after, sourceKey, availability = "AVAILABLE", reasonKey = null) =>
  Object.freeze({
    key,
    before: String(before),
    after: String(after),
    state: availability === "AVAILABLE"
      ? (String(before) === String(after) ? "SAME" : "DIFFERENT")
      : "UNAVAILABLE",
    sourceKey,
    reasonKey,
  });

export function compareGenerations(beforeIdentity, afterIdentity) {
  const before = nodeByIdentity(beforeIdentity);
  const after = nodeByIdentity(afterIdentity);
  const sameRun = before.runId === after.runId;
  const topologyComparable = before.compare.topologyVersion === after.compare.topologyVersion;
  const rows = [
    literal("debt", before.compare.debt, after.compare.debt, "generationCapability"),
    literal("retention", before.compare.retention, after.compare.retention, "acceptance"),
    literal("activeSemanticSet", before.compare.activeSetDigest, after.compare.activeSetDigest, "semanticAbi"),
    literal("bankCount", before.compare.bankCount, after.compare.bankCount, "semanticAbi"),
    literal("memory", before.compare.memory, after.compare.memory, "motif"),
    literal("correctionFrontier", before.compare.correctionFrontier, after.compare.correctionFrontier, "correction"),
    literal("teacherEpoch", before.compare.teacherEpoch, after.compare.teacherEpoch, "teacher"),
    literal("topology",
      `${before.compare.topologyDigest} · ${before.compare.topologyVersion}`,
      `${after.compare.topologyDigest} · ${after.compare.topologyVersion}`,
      "generationManifest"),
    literal("implementation", before.compare.implementationDigest, after.compare.implementationDigest, "generationManifest"),
    literal("resources", before.compare.resources, after.compare.resources, "resource",
      topologyComparable ? "AVAILABLE" : "UNAVAILABLE",
      topologyComparable ? null : "topologyMismatch"),
    literal("evaluation", before.compare.evaluationContract, after.compare.evaluationContract, "evaluation"),
    literal("projection", before.compare.projectionFrontier, after.compare.projectionFrontier, "projection"),
  ];
  return Object.freeze({
    before,
    after,
    sameRun,
    relation: after.parentManifestSha256 === before.manifestSha256
      ? "DIRECT_PARENT_CHILD"
      : before.parentManifestSha256 === after.parentManifestSha256
        ? "SIBLING_BRANCHES"
        : "NON_ADJACENT_LINEAGE",
    capabilityChanges: capabilityChanges(before, after),
    rows: Object.freeze(rows),
    interpretationKey: "literalOnly",
  });
}

export function rejectedCandidateCommitted(candidateId) {
  const candidate = LINEAGE_FIXTURE.rejectedCandidates.find((item) => item.candidateId === candidateId);
  return candidate ? LINEAGE_FIXTURE.nodes.some((node) => node.generation === candidate.committedGeneration) : false;
}
