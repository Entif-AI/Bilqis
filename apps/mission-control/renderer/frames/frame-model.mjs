function sumKnown(values, integer = true) {
  if (values.some(value => value === null)) return null;
  const total = values.reduce((sum, value) => sum + value, 0);
  return (integer ? Number.isSafeInteger(total) : Number.isFinite(total)) ? total : null;
}

export function packingMetrics(examples) {
  const complete = examples.every(example => example.positions !== null);
  const positions = examples.flatMap(example => example.positions ?? []);
  const total = complete ? positions.length : null;
  const pathCount = path => complete ? positions.filter(position => position.path === path).length : null;
  const atoms = complete ? positions.reduce((sum, position) => sum + position.constituents.length, 0) : null;
  return {
    atoms, positions: total,
    ratio: total ? atoms / total : null,
    fastFraction: total ? pathCount("FAST") / total : null,
    partial: pathCount("PARTIAL"), extended: pathCount("EXTENDED"), atomic: pathCount("ATOMIC"),
    expansions: sumKnown(examples.map(example => example.expansionCount)),
    passes: sumKnown(examples.map(example => example.expansionPasses)),
    sidecarBytes: sumKnown(examples.map(example => example.sidecarBytes)),
    preparationMs: sumKnown(examples.map(example => example.preparationMs), false),
  };
}

export function visibility(visibleAt, frontier) {
  return visibleAt === null ? "Unknown" : visibleAt <= frontier ? "Legal" : "Future-illegal";
}

export function visiblePosition(position, frontier) {
  const state = visibility(position.visibleAt, frontier);
  return {
    index: position.index, state,
    metadata: state === "Legal" ? position : null,
    fields: state === "Legal" ? position.fields?.filter(field => visibility(field.visibleAt, frontier) === "Legal") ?? null : null,
    constituents: [...position.constituents].sort((a, b) => a.sourceOrder - b.sourceOrder).map(atom => visibility(atom.visibleAt, frontier) === "Legal"
      ? atom : { sourceOrder: atom.sourceOrder, state: visibility(atom.visibleAt, frontier) }),
  };
}

export function escapeText(value) {
  return String(value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
}
