import { FILTERS, matchesSchoolFilter } from "./school-model.mjs";
import {
  CONCEPT_SCHEMA,
  assertQueryPage,
  conceptRecordId,
  queryRequest,
} from "../atlas/semantic-atlas.mjs";

const TRACE_MODES = new Set(["prerequisites", "both", "unlocks"]);
export const CURRICULUM_NODE_HEIGHT = 160;
const CURRICULUM_ROW_STEP = 192;

export function gradeRank(grade) {
  const value = String(grade ?? "").trim();
  if (/^[A-Z]$/.test(value)) return value.charCodeAt(0) - 64;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : Number.MAX_SAFE_INTEGER;
}

export function buildCurriculumGraph(snapshot) {
  const nodes = snapshot.nodes.map((node) => Object.freeze({ ...node }));
  const ids = new Set(nodes.map((node) => node.id));
  const edges = [];
  for (const node of nodes) {
    for (const prerequisite of node.prerequisites) {
      if (!ids.has(prerequisite)) continue;
      edges.push(Object.freeze({
        id: prerequisite + "->" + node.id,
        source: prerequisite,
        target: node.id,
        kind: "DECLARED_PREREQUISITE",
        authority: "SCHOOL_DECLARED",
      }));
    }
  }
  return Object.freeze({
    snapshot,
    nodes: Object.freeze(nodes),
    edges: Object.freeze(edges),
  });
}

function closure(graph, seed, direction) {
  const seen = new Set();
  const queue = [seed];
  while (queue.length) {
    const current = queue.shift();
    for (const edge of graph.edges) {
      const matches = direction === "up"
        ? edge.target === current
        : edge.source === current;
      if (!matches) continue;
      const next = direction === "up" ? edge.source : edge.target;
      if (seen.has(next)) continue;
      seen.add(next);
      queue.push(next);
    }
  }
  return seen;
}

export function traceSelection(graph, selectedId, mode = "both") {
  const safeMode = TRACE_MODES.has(mode) ? mode : "both";
  const upstream = closure(graph, selectedId, "up");
  const downstream = closure(graph, selectedId, "down");
  return Object.freeze({
    mode: safeMode,
    selectedId,
    upstream,
    downstream,
    visibleUpstream: safeMode === "unlocks" ? new Set() : upstream,
    visibleDownstream: safeMode === "prerequisites" ? new Set() : downstream,
  });
}

export function dependentsFor(graph, id) {
  return graph.edges.filter((edge) => edge.source === id).map((edge) => edge.target);
}

export function nodeRelation(trace, id) {
  if (id === trace.selectedId) return "selected";
  if (trace.visibleUpstream.has(id)) return "upstream";
  if (trace.visibleDownstream.has(id)) return "downstream";
  return "unrelated";
}

export function curriculumConsequence(graph, selectedId) {
  const selected = graph.nodes.find((node) => node.id === selectedId);
  if (!selected) return Object.freeze({ selectedId, byGrade: Object.freeze([]), ids: Object.freeze([]) });
  const downstream = [...closure(graph, selectedId, "down")]
    .map((id) => graph.nodes.find((node) => node.id === id))
    .filter(Boolean)
    .filter((node) => gradeRank(node.grade) > gradeRank(selected.grade));
  const grouped = new Map();
  for (const node of downstream) {
    if (!grouped.has(node.grade)) grouped.set(node.grade, []);
    grouped.get(node.grade).push(node.id);
  }
  const byGrade = [...grouped.entries()]
    .sort(([a], [b]) => gradeRank(a) - gradeRank(b))
    .map(([grade, ids]) => Object.freeze({ grade, ids: Object.freeze([...ids].sort()) }));
  return Object.freeze({
    selectedId,
    byGrade: Object.freeze(byGrade),
    ids: Object.freeze(downstream.map((node) => node.id).sort()),
  });
}

export function gradeFamilySummary(nodes) {
  const groups = new Map();
  for (const node of nodes) {
    const key = node.grade + "::" + node.family;
    if (!groups.has(key)) groups.set(key, { grade: node.grade, family: node.family, ids: [] });
    groups.get(key).ids.push(node.id);
  }
  return Object.freeze([...groups.values()]
    .sort((a, b) => gradeRank(a.grade) - gradeRank(b.grade) || a.family.localeCompare(b.family))
    .map((group) => Object.freeze({
      grade: group.grade,
      family: group.family,
      count: group.ids.length,
      ids: Object.freeze([...group.ids].sort()),
    })));
}

export function boundedFamilyExpansion(nodes, grade, family, limit = 24) {
  const safeLimit = Math.max(1, Math.min(64, Number(limit) || 24));
  return Object.freeze(nodes
    .filter((node) => node.grade === grade && node.family === family)
    .sort((a, b) => a.id.localeCompare(b.id))
    .slice(0, safeLimit));
}

export function visibilityFor(graph, {
  grade = "all",
  state = "all",
  family = "all",
  issue = "all",
  search = "",
  newOnly = false,
} = {}, semanticBindings = null) {
  const needle = search.trim().toLowerCase();
  const result = new Map();
  for (const node of graph.nodes) {
    const binding = semanticBindings?.get?.(node.id);
    const liveTerms = binding?.concepts?.flatMap((concept) => [
      concept.semantic_id,
      ...(concept.labels ?? []).map((label) => label.value),
    ]) ?? [];
    const searchable = [
      node.id, node.label, node.semanticId, node.family, ...liveTerms,
    ].join(" ").toLowerCase();
    const matchesGrade = grade === "all" || node.grade === grade;
    const matchesState = state === "all" ||
      node.lifecycleState === state || node.qualificationState === state;
    const matchesFamily = family === "all" || node.family === family;
    const matchesIssue = issue === "all" ||
      (issue === "debt" && node.debt > 0) ||
      (issue === "regression" && node.lastRegression !== "none") ||
      (issue === "blocked" && node.blocker !== null) ||
      (FILTERS.includes(issue) && matchesSchoolFilter(node, issue));
    const matchesSearch = !needle || searchable.includes(needle);
    result.set(node.id, matchesGrade && matchesState && matchesFamily &&
      matchesIssue && matchesSearch && (!newOnly || node.newThisGrade));
  }
  return result;
}

export function strataFor(graph) {
  const currentRank = gradeRank(graph.snapshot.currentGrade);
  const result = { foundation: [], current: [], forward: [] };
  for (const node of graph.nodes) {
    const rank = gradeRank(node.grade);
    if (rank < currentRank && node.qualificationState === "QUALIFIED") result.foundation.push(node);
    else if (rank <= currentRank) result.current.push(node);
    else if (rank > currentRank) result.forward.push(node);
  }
  for (const nodes of Object.values(result)) nodes.sort((a, b) => a.id.localeCompare(b.id));
  return result;
}

export function stableLayout(graph) {
  const strata = strataFor(graph);
  const xByStratum = { foundation: 34, current: 374, forward: 714 };
  const positions = new Map();
  let maxRows = 1;
  for (const [stratum, nodes] of Object.entries(strata)) {
    maxRows = Math.max(maxRows, nodes.length);
    nodes.forEach((node, index) => {
      positions.set(node.id, Object.freeze({
        x: xByStratum[stratum],
        y: 72 + index * CURRICULUM_ROW_STEP,
        stratum,
      }));
    });
  }
  return Object.freeze({
    positions,
    height: Math.max(420,
      92 + ((maxRows - 1) * CURRICULUM_ROW_STEP) + CURRICULUM_NODE_HEIGHT + 28),
  });
}

export function blockerExplanation(node) {
  return node?.blocker ?? Object.freeze({
    code: "UNKNOWN",
    detail: "No explicit blocker is projected for this semantic.",
    evidence: Object.freeze([]),
  });
}

export async function resolveCapabilitySemanticBindings(api, context, capabilityId) {
  if (context?.mode === "HISTORICAL") {
    return Object.freeze({
      state: "UNAVAILABLE",
      reason: "Historical reverse capability lookup is not release-bounded by CP03.",
      concepts: Object.freeze([]),
    });
  }
  if (!api || typeof api.query !== "function") {
    return Object.freeze({ state: "UNAVAILABLE", reason: "CP03 query capability unavailable.", concepts: Object.freeze([]) });
  }
  const reference = queryRequest({ family: "reference", mode: "current", reference: capabilityId, limit: 32 });
  const page = assertQueryPage(await api.query(reference));
  if (page.accepted !== true) {
    return Object.freeze({ state: "UNAVAILABLE", reason: page.reason, concepts: Object.freeze([]) });
  }
  const recordIds = [...new Set(page.links
    .filter((link) => link.relation === "CAPABILITY" && link.target_ref === capabilityId)
    .map((link) => link.source_record_id))];
  const conceptPages = await Promise.all(recordIds.slice(0, 32).map(async (recordId) => {
    const request = queryRequest({ family: "semantic", mode: "current", recordId, limit: 1 });
    return assertQueryPage(await api.query(request));
  }));
  const concepts = conceptPages.flatMap((candidate) => candidate.accepted === true ? candidate.records : [])
    .filter((record) => record?.schema_version === CONCEPT_SCHEMA)
    .filter((record) => record.atlas_release_sha256 === context.semanticRelease)
    .filter((record) => Array.isArray(record.capability_ids) && record.capability_ids.includes(capabilityId));
  return Object.freeze({
    state: concepts.length ? "PRESENT" : "MISSING",
    reason: concepts.length ? "EXACT_RELEASE_CAPABILITY_BINDING" : "NO_EXACT_RELEASE_BINDING",
    concepts: Object.freeze(concepts),
  });
}

export async function resolveGraphSemanticBindings(api, context, graph) {
  const entries = await Promise.all(graph.nodes.slice(0, 64).map(async (node) => [
    node.id,
    await resolveCapabilitySemanticBindings(api, context, node.id),
  ]));
  return new Map(entries);
}

export async function resolveExactSemanticSearch(api, context, semanticId, graph) {
  if (context?.mode === "HISTORICAL") {
    return Object.freeze({
      state: "UNAVAILABLE",
      reason: "HISTORICAL_EXACT_SEMANTIC_LOOKUP_UNAVAILABLE",
      capabilityIds: Object.freeze([]),
      concept: null,
    });
  }
  if (!semanticId || !api || typeof api.query !== "function") {
    return Object.freeze({
      state: "UNAVAILABLE",
      reason: "EXACT_SEMANTIC_QUERY_UNAVAILABLE",
      capabilityIds: Object.freeze([]),
      concept: null,
    });
  }
  const request = queryRequest({
    family: "semantic",
    mode: "current",
    recordId: conceptRecordId(context.semanticRelease, semanticId),
    limit: 1,
  });
  const page = assertQueryPage(await api.query(request));
  const concept = page.accepted === true
    ? page.records.find((record) => record?.schema_version === CONCEPT_SCHEMA) ?? null
    : null;
  if (!concept || concept.atlas_release_sha256 !== context.semanticRelease) {
    return Object.freeze({
      state: "MISSING",
      reason: "NO_EXACT_RELEASE_SEMANTIC_IDENTITY",
      capabilityIds: Object.freeze([]),
      concept: null,
    });
  }
  const knownIds = new Set(graph.nodes.map((node) => node.id));
  const capabilityIds = concept.capability_ids.filter((id) => knownIds.has(id));
  return Object.freeze({
    state: capabilityIds.length ? "PRESENT" : "MISSING",
    reason: capabilityIds.length
      ? "EXACT_RELEASE_SEMANTIC_IDENTITY"
      : "SEMANTIC_IDENTITY_HAS_NO_VISIBLE_CAPABILITY",
    capabilityIds: Object.freeze(capabilityIds),
    concept,
  });
}
