import { LINEAGE_FIXTURE, LINEAGE_FIXTURE_CONTRACT } from "./lineage-fixture.mjs";
import {
  compareGenerations,
  currentLineageNode,
  historicalGenerationQuery,
  lineageDeepLink,
  lineageNodes,
  manifestFieldRows,
  nodeByIdentity,
} from "./lineage-model.mjs";
import { lineageT } from "./lineage-messages.mjs";
import { objectDomAttributes } from "../interactions/dom-ref.mjs";
import { escapeText as esc } from "../frames/frame-model.mjs";
import { controlClass } from "../foundation/primitives.mjs";
import { assertUniqueTestIds, testId, testIdAttribute } from "../foundation/test-hooks.mjs";

const ui = {
  selected: currentLineageNode().manifestSha256,
  compareBefore: LINEAGE_FIXTURE.nodes[1].manifestSha256,
  compareAfter: LINEAGE_FIXTURE.nodes.at(-1).manifestSha256,
};

function slug(value) {
  return String(value).replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "value";
}

function hook(...segments) {
  return testId("lineage", ...segments.map(slug));
}

function compact(value) {
  return typeof value === "string" && /^[0-9a-f]{64}$/.test(value)
    ? `${value.slice(0, 9)}…${value.slice(-9)}`
    : value;
}

function exactCode(value, t = lineageT) {
  const text = String(value ?? "");
  const shown = compact(text);
  return `<code title="${esc(text)}" aria-label="${esc(t("lineage.value.exact", { value: text }))}">${esc(shown)}</code>`;
}

function stateLabel(value, t = lineageT) {
  try { return t(`lineage.state.${value}`); }
  catch (error) {
    if (!(error instanceof RangeError)) throw error;
    return t("lineage.state.unknown", { state: value });
  }
}

function stateBadge(value, t, ...hookSegments) {
  return `<span class="lineage-state" data-lineage-state="${esc(slug(value))}" ${testIdAttribute("lineage", ...hookSegments)}>${esc(stateLabel(value, t))}</span>`;
}

function transitionLabel(value, t) {
  return t(`lineage.transition.${value}`);
}

function generationButton(node, selected, t, scope, pinnedGeneration = null) {
  const nodes = lineageNodes();
  const parent = node.parentManifestSha256
    ? nodes.find((candidate) => candidate.manifestSha256 === node.parentManifestSha256) ?? null
    : null;
  const disabled = pinnedGeneration !== null && node.generation !== pinnedGeneration;
  return `<button type="button" class="${controlClass("inspect")} lineage-node"
    data-lineage-select="${esc(node.manifestSha256)}" data-transition="${esc(slug(node.transitionClass))}"
    ${testIdAttribute("lineage", scope, "generation", node.generation)}
    ${objectDomAttributes({
      kind: "generation",
      id: node.recordId,
      relations: [
        { kind: "checkpoint", id: `checkpoint:${node.checkpointSha256}`, relation: "checkpoint" },
        ...(parent ? [{ kind: "generation", id: parent.recordId, relation: "parent" }] : []),
      ],
    })}
    aria-pressed="${selected.manifestSha256 === node.manifestSha256}" ${disabled ? "disabled" : ""}>
      <span class="lineage-node-generation">${esc(t("lineage.graph.generation", { generation: node.generation }))}</span>
      <strong>${esc(transitionLabel(node.transitionClass, t))}</strong>
      <span class="lineage-node-parent">${esc(parent ? t("lineage.graph.parent", { generation: parent.generation }) : t("lineage.graph.genesis"))}</span>
      <span class="lineage-node-id"><span>${esc(t("lineage.graph.manifest"))}</span>${exactCode(node.manifestSha256, t)}</span>
      <span class="lineage-node-id"><span>${esc(t("lineage.graph.checkpoint"))}</span>${exactCode(node.checkpointSha256, t)}</span>
    </button>`;
}

function lineageTreeMarkup(selected, t, pinnedGeneration = null) {
  const nodes = lineageNodes();
  const children = new Map();
  for (const node of nodes) {
    const key = node.parentManifestSha256 ?? "ROOT";
    if (!children.has(key)) children.set(key, []);
    children.get(key).push(node);
  }
  const branch = (node) => {
    const descendants = children.get(node.manifestSha256) ?? [];
    return `<li class="lineage-tree-item" ${testIdAttribute("lineage", "graph", "branch", node.generation)}>
      ${generationButton(node, selected, t, "graph", pinnedGeneration)}
      ${descendants.length ? `<ol class="lineage-children">${descendants.map(branch).join("")}</ol>` : ""}
    </li>`;
  };
  const roots = children.get("ROOT") ?? [];
  return `<div class="lineage-graph-scroll" tabindex="0" role="region" aria-label="${esc(t("lineage.graph.region"))}" ${testIdAttribute("lineage", "graph", "scroll")}>
    <ol class="lineage-tree" ${testIdAttribute("lineage", "graph", "tree")}>${roots.map(branch).join("")}</ol>
  </div><p class="lineage-scroll-hint">${esc(t("lineage.graph.scrollHint"))}</p>`;
}

function tableWrap(id, caption, headers, rows, t) {
  return `<div class="lineage-table-wrap" tabindex="0" role="region" aria-label="${esc(caption)}" ${testIdAttribute("lineage", id, "scroll")}>
    <table class="ui-table lineage-table" ${testIdAttribute("lineage", id)}><caption>${esc(caption)}</caption><thead><tr>${headers.map((label, index) => `<th scope="col" ${index === 0 ? 'data-sticky="identity"' : ""}>${esc(label)}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table>
  </div><p class="lineage-scroll-hint">${esc(t("lineage.table.scrollHint"))}</p>`;
}

function acceptedLineageMarkup(selected, t, context = null) {
  const nodes = lineageNodes();
  const byManifest = new Map(nodes.map((node) => [node.manifestSha256, node]));
  const pinned = context?.mode === "HISTORICAL" ? context.generation : null;
  const rows = nodes.map((node) => {
    const parent = node.parentManifestSha256 ? byManifest.get(node.parentManifestSha256) ?? null : null;
    return `<tr data-selected="${selected.manifestSha256 === node.manifestSha256}" ${testIdAttribute("lineage", "table", "row", node.generation)}>
      <th scope="row" data-sticky="identity">${generationButton(node, selected, t, "table", pinned)}</th>
      <td>${exactCode(node.manifestSha256, t)}</td>
      <td>${parent ? `<span>${esc(t("lineage.graph.generation", { generation: parent.generation }))}</span>${exactCode(parent.manifestSha256, t)}` : esc(t("lineage.graph.genesis"))}</td>
      <td>${esc(transitionLabel(node.transitionClass, t))}</td>
      <td>${exactCode(node.checkpointSha256, t)}</td>
    </tr>`;
  }).join("");
  return `<section class="lineage-section lineage-lineage" ${testIdAttribute("lineage", "accepted")}>
    <header class="lineage-section-heading"><div><span class="eyebrow">${esc(t("lineage.graph.eyebrow"))}</span><h3>${esc(t("lineage.graph.title"))}</h3><p>${esc(t("lineage.graph.summary"))}</p></div>${stateBadge("READ_ONLY", t, "graph", "state")}</header>
    ${pinned !== null ? `<p class="lineage-context-note" ${testIdAttribute("lineage", "historical", "pinned")}>${esc(t("lineage.historical.pinned", { generation: pinned }))}</p>` : ""}
    ${lineageTreeMarkup(selected, t, pinned)}
    ${tableWrap("accepted-table", t("lineage.graph.tableCaption"), [t("lineage.graph.column.generation"), t("lineage.graph.column.manifest"), t("lineage.graph.column.parent"), t("lineage.graph.column.transition"), t("lineage.graph.column.checkpoint")], rows, t)}
  </section>`;
}

function dossierMarkup(node, t) {
  const query = historicalGenerationQuery(node);
  const primary = [
    ["generation", node.generation, false], ["transition", transitionLabel(node.transitionClass, t), false],
    ["manifest", node.manifestSha256, true], ["parent", node.parentManifestSha256 ?? t("lineage.graph.genesis"), node.parentManifestSha256 !== null],
    ["checkpoint", node.checkpointSha256, true], ["receipt", node.receiptId, true],
  ];
  const rows = manifestFieldRows(node).map((field) => `<tr ${testIdAttribute("lineage", "manifest", "row", field.key)}><th scope="row" data-sticky="identity">${esc(t(`lineage.manifest.${field.key}`))}</th><td>${esc(field.value)}</td><td><code>${esc(field.sourceRef)}</code></td></tr>`).join("");
  return `<section class="lineage-section lineage-dossier" ${testIdAttribute("lineage", "dossier")}>
    <header class="lineage-section-heading"><div><span class="eyebrow">${esc(t("lineage.dossier.eyebrow"))}</span><h3>${esc(t("lineage.dossier.title", { generation: node.generation }))}</h3><p>${esc(t("lineage.dossier.summary"))}</p></div>${stateBadge(node.transitionClass, t, "dossier", "state")}</header>
    <dl class="lineage-dossier-facts">${primary.map(([key, value, code]) => `<div ${testIdAttribute("lineage", "dossier", "fact", key)}><dt>${esc(t(`lineage.dossier.${key}`))}</dt><dd>${code ? `<code>${esc(value)}</code>` : esc(value)}</dd></div>`).join("")}</dl>
    <details class="ui-disclosure lineage-manifest-detail" ${testIdAttribute("lineage", "dossier", "manifest")}><summary ${testIdAttribute("lineage", "dossier", "manifest", "toggle")}>${esc(t("lineage.dossier.fields"))}</summary>
      ${tableWrap("manifest-table", t("lineage.dossier.fields"), [t("lineage.dossier.field"), t("lineage.dossier.value"), t("lineage.dossier.source")], rows, t)}
    </details>
    <div class="lineage-dossier-actions"><a class="${controlClass("link")}" href="${esc(lineageDeepLink(node))}" ${testIdAttribute("lineage", "dossier", "deep-link")}>${esc(t("lineage.dossier.deepLink"))}</a></div>
    <details class="ui-disclosure" ${testIdAttribute("lineage", "dossier", "query")}><summary ${testIdAttribute("lineage", "dossier", "query", "toggle")}>${esc(t("lineage.dossier.route"))}</summary><div class="ui-disclosure__body"><strong>${esc(t("lineage.dossier.query"))}</strong><code class="lineage-query">CP03 ${esc(query.mode)} generation=${esc(query.generation)} record_id=${esc(query.record_id)}</code></div></details>
  </section>`;
}

function valueMarkup(value, t) {
  if (value === "ABSENT") return esc(t("lineage.value.absent"));
  return /^[0-9a-f]{64}$/.test(String(value)) ? exactCode(value, t) : esc(value);
}

function compareMarkup(t) {
  const comparison = compareGenerations(ui.compareBefore, ui.compareAfter);
  const options = lineageNodes().map((node) => `<option value="${esc(node.manifestSha256)}">${esc(t("lineage.compare.option", { generation: node.generation, manifest: compact(node.manifestSha256) }))}</option>`).join("");
  const dimensionRows = comparison.rows.map((row) => `<tr data-state="${esc(slug(row.state))}" ${testIdAttribute("lineage", "diff", "row", slug(row.key))}>
    <th scope="row" data-sticky="identity">${esc(t(`lineage.compare.dimension.${row.key}`))}</th><td>${valueMarkup(row.before, t)}</td><td>${valueMarkup(row.after, t)}</td>
    <td>${stateBadge(row.state, t, "diff", "state", slug(row.key))}${row.reasonKey ? `<small>${esc(t(`lineage.compare.reason.${row.reasonKey}`))}</small>` : ""}</td><td>${esc(t(`lineage.compare.source.${row.sourceKey}`))}</td></tr>`).join("");
  const capabilityRows = comparison.capabilityChanges.map((row) => `<tr data-state="${esc(slug(row.state))}" data-test-id="${hook("capability", "row", row.id)}">
    <th scope="row" data-sticky="identity"><code>${esc(row.id)}</code></th><td>${valueMarkup(row.before, t)}</td><td>${valueMarkup(row.after, t)}</td>
    <td>${stateBadge(row.state, t, "capability", "state", slug(row.id))}</td><td>${esc(t("lineage.compare.source.capability"))}</td></tr>`).join("");
  const headers = [t("lineage.compare.column.dimension"), t("lineage.compare.column.before"), t("lineage.compare.column.after"), t("lineage.compare.column.state"), t("lineage.compare.column.source")];
  return `<section class="lineage-section lineage-compare" ${testIdAttribute("lineage", "compare")}>
    <header class="lineage-section-heading"><div><span class="eyebrow">${esc(t("lineage.compare.eyebrow"))}</span><h3>${esc(t("lineage.compare.title"))}</h3><p>${esc(t("lineage.compare.summary"))}</p></div>${stateBadge(comparison.relation, t, "compare", "relation")}</header>
    <div class="lineage-compare-controls"><label>${esc(t("lineage.compare.from"))}<select class="lineage-select" data-lineage-before ${testIdAttribute("lineage", "compare", "before")}>${options}</select></label><label>${esc(t("lineage.compare.to"))}<select class="lineage-select" data-lineage-after ${testIdAttribute("lineage", "compare", "after")}>${options}</select></label></div>
    <p class="lineage-doctrine" ${testIdAttribute("lineage", "compare", "boundary")}>${esc(t(`lineage.compare.${comparison.interpretationKey}`))}</p>
    ${tableWrap("diff-table", t("lineage.compare.dimensionCaption"), headers, dimensionRows, t)}
    ${tableWrap("capability-table", t("lineage.compare.capabilityCaption"), [t("lineage.compare.column.capability"), ...headers.slice(1)], capabilityRows, t)}
  </section>`;
}

function rejectedMarkup(t) {
  return `<aside class="lineage-boundary lineage-rejected" ${testIdAttribute("lineage", "rejected", "boundary")}><header><div><span class="eyebrow">${esc(t("lineage.rejected.eyebrow"))}</span><h3>${esc(t("lineage.rejected.title"))}</h3><p>${esc(t("lineage.rejected.summary"))}</p></div>${stateBadge("REJECTED", t, "rejected", "state")}</header>
    <dl>${LINEAGE_FIXTURE.rejectedCandidates.map((candidate) => `<div data-test-id="${hook("rejected", "candidate", candidate.candidateId)}"><dt>${esc(t("lineage.rejected.candidate"))}</dt><dd><code>${esc(candidate.candidateId)}</code></dd><dt>${esc(t("lineage.rejected.reason"))}</dt><dd><code>${esc(candidate.reason)}</code></dd><dt>${esc(t("lineage.rejected.committed"))}</dt><dd>${esc(t("lineage.value.none"))}</dd></div>`).join("")}</dl>
  </aside>`;
}

function historicalUnavailableMarkup(context, t) {
  return `<div class="lineage-view" ${testIdAttribute("lineage", "workspace")}><header class="lineage-heading" ${testIdAttribute("lineage", "heading")}><div><span class="eyebrow">${esc(t("lineage.eyebrow"))}</span><h2>${esc(t("lineage.title"))}</h2><p>${esc(t("lineage.summary"))}</p></div></header>
    <section class="lineage-boundary lineage-historical-unavailable" role="status" ${testIdAttribute("lineage", "historical", "unavailable")}><header><div><span class="eyebrow">${esc(t("lineage.historical.eyebrow"))}</span><h3>${esc(t("lineage.historical.title"))}</h3><p>${esc(t("lineage.historical.summary", { generation: context.generation }))}</p></div>${stateBadge("MISSING", t, "historical", "state")}</header><dl><dt>${esc(t("lineage.historical.requested"))}</dt><dd>${esc(context.generation)}</dd><dt>${esc(t("lineage.historical.record"))}</dt><dd>${esc(t("lineage.historical.none"))}</dd></dl></section>
  </div>`;
}

function resolveSelection(selectedIdentity, context) {
  if (context?.mode === "HISTORICAL") return lineageNodes().find((node) => node.generation === context.generation) ?? null;
  return nodeByIdentity(selectedIdentity ?? ui.selected);
}

export function renderLineageMarkup({ selectedIdentity = null, context = null, t = lineageT } = {}) {
  const selected = resolveSelection(selectedIdentity, context);
  const markup = selected === null
    ? historicalUnavailableMarkup(context, t)
    : `<div class="lineage-view" ${testIdAttribute("lineage", "workspace")}><header class="lineage-heading" ${testIdAttribute("lineage", "heading")}><div><span class="eyebrow">${esc(t("lineage.eyebrow"))}</span><h2>${esc(t("lineage.title"))}</h2><p>${esc(t("lineage.summary"))}</p></div></header>
      <aside class="lineage-fixture-notice" role="note" ${testIdAttribute("lineage", "fixture")}><strong>${esc(t(`lineage.fixture.${LINEAGE_FIXTURE_CONTRACT.posture}`))}</strong><p>${esc(t("lineage.fixture.description"))}</p></aside>
      ${acceptedLineageMarkup(selected, t, context)}${dossierMarkup(selected, t)}${compareMarkup(t)}${rejectedMarkup(t)}
      <p class="lineage-authority" ${testIdAttribute("lineage", "authority")}><strong>${esc(t("lineage.boundary.label"))}:</strong> ${esc(t("lineage.boundary.detail"))}</p></div>`;
  assertUniqueTestIds(markup);
  return markup;
}

function bind(container, inspectGeneration, context) {
  container.querySelectorAll("[data-lineage-select]").forEach((button) => button.addEventListener("click", () => {
    const node = nodeByIdentity(button.dataset.lineageSelect);
    ui.selected = node.manifestSha256;
    renderLineageView(container, inspectGeneration, node.manifestSha256, context);
    inspectGeneration(node.recordId, node);
  }));
  const before = container.querySelector("[data-lineage-before]");
  const after = container.querySelector("[data-lineage-after]");
  if (before) {
    before.value = ui.compareBefore;
    before.addEventListener("change", (event) => {
      ui.compareBefore = event.currentTarget.value;
      renderLineageView(container, inspectGeneration, ui.selected, context);
      container.querySelector('[data-test-id="lineage-compare-before"]')?.focus();
    });
  }
  if (after) {
    after.value = ui.compareAfter;
    after.addEventListener("change", (event) => {
      ui.compareAfter = event.currentTarget.value;
      renderLineageView(container, inspectGeneration, ui.selected, context);
      container.querySelector('[data-test-id="lineage-compare-after"]')?.focus();
    });
  }
}

export function renderLineageView(container, inspectGeneration, selectedIdentity = null, context = null) {
  const selected = resolveSelection(selectedIdentity, context);
  if (selected) ui.selected = selected.manifestSha256;
  container.innerHTML = renderLineageMarkup({ selectedIdentity, context });
  if (selected) bind(container, inspectGeneration, context);
}
