import { CORRECTION_FIXTURE, CORRECTION_FIXTURE_CONTRACT } from "./corrections-fixture.mjs";
import {
  assertReceiptBackedTerminalStates,
  evidencedDescendants,
  historyFor,
  impactRows,
  requalificationQueue,
  unknownInfluenceRows,
} from "./corrections-model.mjs";

function stateBadge(state) {
  return `<span class="correction-state" data-correction-state="${state}">${state.replaceAll("_", " ")}</span>`;
}

function graphMarkup() {
  const nodes = evidencedDescendants();
  return `<section class="correction-panel"><header><div><span class="eyebrow">Impact graph</span><h3>Evidenced dependency closure</h3></div><p>Only explicit fixture edges are traversed. Similarity or proximity does not create exposure.</p></header>
    <div class="correction-graph" role="list">${nodes.map((node) => `<button type="button" role="listitem" data-correction-node="${node.id}" data-kind="${node.kind}"><small>${node.kind}</small><strong>${node.label}</strong>${stateBadge(node.state)}<span>${node.evidenceRefs.length ? node.evidenceRefs.join(" · ") : "No tracked receipt · influence remains unknown"}</span></button>`).join("")}</div>
    <div class="correction-edges" aria-label="Dependency edges">${CORRECTION_FIXTURE.edges.map((edge) => `<div><span>${edge.from}</span><strong aria-label="${edge.relation}">→ ${edge.relation} →</strong><span>${edge.to}</span></div>`).join("")}</div>
  </section>`;
}

function tableMarkup() {
  const rows = impactRows();
  return `<section class="correction-panel"><header><div><span class="eyebrow">Accessible alternative</span><h3>Impact table</h3></div><p>Same identities and states as the graph.</p></header>
    <div class="correction-table-wrap"><table><thead><tr><th>Identity</th><th>Class</th><th>State</th><th>Evidence</th></tr></thead><tbody>${rows.map((row) => `<tr><td><button type="button" data-correction-node="${row.id}" data-kind="${row.kind}">${row.id}</button></td><td>${row.kind}</td><td>${stateBadge(row.state)}</td><td>${row.evidenceRefs.length ? row.evidenceRefs.join("<br>") : "UNTRACKED / UNKNOWN"}</td></tr>`).join("")}</tbody></table></div>
  </section>`;
}

function queueMarkup() {
  return `<section class="correction-panel"><header><div><span class="eyebrow">Requalification queue</span><h3>Owned correction work</h3></div><p>Queue status is descriptive. This view cannot perform or certify requalification.</p></header>
    <div class="requalification-queue">${requalificationQueue().map((task) => `<article><div><small>${task.urgency} · ${task.owner}</small><strong>${task.id}</strong></div>${stateBadge(task.status)}<dl><dt>Generation</dt><dd>${task.generation}</dd><dt>Checkpoint</dt><dd>${task.checkpoint}</dd><dt>Source revision</dt><dd>${task.sourceRevision}</dd><dt>Implications</dt><dd>${task.implicatedRefs.join("<br>")}</dd><dt>Evidence</dt><dd>${task.evidenceRefs.join("<br>") || "UNKNOWN"}</dd><dt>Receipts</dt><dd>${task.receiptRefs.join("<br>") || "NONE · NOT REQUALIFIED"}</dd></dl></article>`).join("")}</div>
  </section>`;
}

function historyMarkup() {
  const id = "capability:C.SUCCESSOR";
  return `<section class="correction-panel"><header><div><span class="eyebrow">Append-only history</span><h3>${id}</h3></div><p>Later qualification adds evidence; it does not rewrite the correction-era state.</p></header>
    <ol class="correction-history">${historyFor(id).map((entry) => `<li><strong>Generation ${entry.generation} · ${entry.phase}</strong>${stateBadge(entry.state)}<span>${entry.receipt}</span></li>`).join("")}</ol>
  </section>`;
}

export function renderCorrectionsView(container, inspectCorrection) {
  assertReceiptBackedTerminalStates();
  const correction = CORRECTION_FIXTURE.correction;
  const unknown = unknownInfluenceRows();
  container.innerHTML = `<div class="corrections-view">
    <header class="corrections-heading"><div><span class="eyebrow">GUI13 · Corrections &amp; Requalification</span><h2>Correction impact and exposure</h2></div><p>Follow evidenced dependencies from a source revision through retained artifacts and qualification. Known exposure is not proof of invalidity, and no UI state claims arbitrary neural influence was erased.</p></header>
    <div class="corrections-fixture-notice" role="status"><strong>${CORRECTION_FIXTURE_CONTRACT.projection}</strong><span>CP03 exposes CorrectionEvent records; the richer impact/queue projection below is a checked-in fixture grounded in current C09 correction and requalification contracts.</span></div>
    <div class="ui-glossary" aria-label="Correction state definitions"><span><strong>Known exposure</strong> a recorded dependency path exists.</span><span><strong>Invalidated</strong> prior evidence can no longer support the same claim.</span><span><strong>Requalification required</strong> fresh evidence is needed before reuse.</span><span><strong>Unknown influence</strong> is preserved rather than guessed away.</span></div>
    <section class="correction-summary"><div><small>Correction</small><strong>${correction.id}</strong></div><div><small>Source revision</small><strong>${correction.priorRevision} → ${correction.currentRevision}</strong></div><div><small>Correction generation</small><strong>${correction.correctionGeneration}</strong></div><div><small>Unknown influence</small><strong>${unknown.length} explicit</strong></div></section>
    ${graphMarkup()}
    ${tableMarkup()}
    ${queueMarkup()}
    ${historyMarkup()}
  </div>`;
  container.querySelectorAll("[data-correction-node]").forEach((button) => button.addEventListener("click", () => {
    const id = button.dataset.correctionNode;
    const node = CORRECTION_FIXTURE.nodes.find((item) => item.id === id);
    if (node) inspectCorrection(id, node);
  }));
}
