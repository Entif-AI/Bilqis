export const FILTERS = Object.freeze([
  "imperfect", "regression", "stale-debt", "recent-gain", "held", "uncovered", "qualified",
]);

export function scoreQuad(row) {
  const top = Number.isInteger(row.top) ? String(row.top).padStart(3, " ") : "  -";
  return [row.was, top, row.now, row.total].map((value) => String(value).padStart(3, " ")).join("/");
}

export function dependentsById(rows) {
  const result = new Map(rows.map((row) => [row.id, []]));
  for (const row of rows) {
    for (const prerequisite of row.prerequisites) {
      if (!result.has(prerequisite)) result.set(prerequisite, []);
      result.get(prerequisite).push(row.id);
    }
  }
  return result;
}

export function selectionNeighborhood(rows, selectedId) {
  const row = rows.find((item) => item.id === selectedId);
  const dependents = dependentsById(rows).get(selectedId) ?? [];
  return {
    selected: selectedId,
    prerequisites: row ? [...row.prerequisites] : [],
    dependents: [...dependents],
  };
}

export function matchesSchoolFilter(row, filter) {
  if (filter === "imperfect") {
    return Number.isFinite(row.now) && Number.isFinite(row.total) && row.now < row.total;
  }
  if (filter === "regression") return Boolean(row.lastRegression && row.lastRegression !== "none");
  if (filter === "stale-debt") return row.staleDebt;
  if (filter === "recent-gain") return row.recentGain;
  if (filter === "held") return row.sourceState === "SOURCE_HELD" || row.lifecycleState === "HELD";
  if (filter === "uncovered") return row.implementationState === "IMPLEMENTATION_UNCOVERED";
  if (filter === "qualified") return row.qualificationState === "QUALIFIED";
  return true;
}

export function projectRows(rows, { filters = [], sortKey = "id", direction = "asc", groupByFamily = false } = {}) {
  const activeFilters = filters.filter((filter) => FILTERS.includes(filter));
  const filtered = rows.filter((row) => activeFilters.every((filter) => matchesSchoolFilter(row, filter)));
  const factor = direction === "desc" ? -1 : 1;
  return [...filtered].sort((a, b) => {
    if (groupByFamily && a.family !== b.family) {
      return a.family.localeCompare(b.family);
    }
    const av = a[sortKey] ?? "";
    const bv = b[sortKey] ?? "";
    return factor * (typeof av === "number" && typeof bv === "number"
      ? av - bv
      : String(av).localeCompare(String(bv)));
  });
}

export function paginateRows(rows, page = 1, pageSize = 50) {
  const safeSize = Math.max(1, pageSize);
  const pages = Math.max(1, Math.ceil(rows.length / safeSize));
  const safePage = Math.min(Math.max(1, page), pages);
  const start = (safePage - 1) * safeSize;
  return {
    page: safePage,
    pages,
    total: rows.length,
    start,
    end: Math.min(start + safeSize, rows.length),
    rows: rows.slice(start, start + safeSize),
  };
}

export function evidenceTotals(rows) {
  return rows.reduce((acc, row) => ({
    nowCorrect: acc.nowCorrect + (Number.isFinite(row.now) ? row.now : 0),
    denominator: acc.denominator + (Number.isFinite(row.total) ? row.total : 0),
    debt: acc.debt + (Number.isFinite(row.debt) ? row.debt : 0),
    retainedSteps: acc.retainedSteps + (Number.isFinite(row.retainedSteps) ? row.retainedSteps : 0),
  }), { nowCorrect: 0, denominator: 0, debt: 0, retainedSteps: 0 });
}

export function exportSchoolCsv(rows) {
  const header = ["capability_id", "grade", "family", "WAS", "TOP", "NOW", "ALL", "debt", "P_RET", "qualification_state"];
  const lines = rows.map((row) => [
    row.id, row.grade, row.family, row.was, row.top, row.now, row.total, row.debt,
    row.pRet ?? "", row.qualificationState,
  ].map((value) => '"' + String(value ?? "").replaceAll('"', '""') + '"').join(","));
  return [header.join(","), ...lines].join("\n");
}

export function equalSchedulingSemantics(left, right) {
  return left.schedulingSemantics === right.schedulingSemantics;
}
