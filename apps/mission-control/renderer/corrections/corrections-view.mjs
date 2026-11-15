import { CORRECTION_FIXTURE, CORRECTION_FIXTURE_CONTRACT } from "./corrections-fixture.mjs";
import { assertReceiptBackedTerminalStates, evidencedDescendants, impactRows, requalificationQueue, unknownInfluenceRows } from "./corrections-model.mjs";
import { correctionsT } from "./corrections-messages.mjs";
import { escapeText as esc } from "../frames/frame-model.mjs";
import { controlClass } from "../foundation/primitives.mjs";

function hook(scope, identity, occurrence = 0) {
  return `corrections-${scope}-${Array.from(String(identity), (char) => char.codePointAt(0).toString(16)).join("-")}-${occurrence}`;
}

function stateBadge(state, t) {
  const key = `corrections.state.${state}`;
  let label;
  try { label = t(key); } catch (error) { if (!(error instanceof RangeError)) throw error; label = t("corrections.state.unknown", {state}); }
  return `<span class="correction-state" data-correction-state="${esc(state)}">${esc(label)}</span>`;
}

function inspectNode(node, scope, t, identity = node.id) {
  const id = hook(scope, identity);
  return `<button type="button" class="${controlClass("link")} correction-artifact" data-test-id="${id}" data-focus-key="${id}" data-correction-node="${esc(node.id)}"><code>${esc(node.id)}</code></button>`;
}

function references(values, scope, t, kind = "reference", owner = "") {
  if (!values.length) return `<span class="correction-untracked">${esc(t("corrections.evidence.none"))}</span>`;
  return `<ul class="correction-refs">${values.map((ref, index) => {
    const id = hook(scope, JSON.stringify([owner,ref]), values.slice(0,index).filter(value=>value===ref).length);
    return `<li><button type="button" class="${controlClass("link")}" data-test-id="${id}" data-focus-key="${id}" data-correction-ref="${esc(ref)}" data-correction-ref-kind="${kind}"><span>${esc(t(`corrections.inspect.${kind}`))}</span><code>${esc(ref)}</code></button></li>`;
  }).join("")}</ul>`;
}

function tableWrap(id, caption, head, rows, t) {
  return `<div class="correction-table-wrap" data-test-id="${id}-scroll" tabindex="0" role="region" aria-label="${esc(caption)}"><table data-test-id="${id}"><caption>${esc(caption)}</caption><thead><tr>${head.map(label=>`<th scope="col">${esc(label)}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table></div><p class="correction-scroll-hint">${esc(t("corrections.table.scroll"))}</p>`;
}

function graphMarkup(t) {
  const nodes = new Map(evidencedDescendants().map(node=>[node.id,node]));
  const edges = CORRECTION_FIXTURE.edges;
  const endpoint = (id, scope, edgeId) => {
    const node = nodes.get(id);
    return `<article class="correction-endpoint" data-test-id="${hook("graph-endpoint",JSON.stringify([scope,edgeId,node.id]))}"><span>${esc(node.kind)}</span><span>${esc(node.label)}</span>${inspectNode(node, scope, t, JSON.stringify([edgeId,node.id]))}${stateBadge(node.state,t)}<span>${esc(t("corrections.evidence.count",{count:node.evidenceRefs.length}))}</span></article>`;
  };
  return `<details class="correction-graph-disclosure" data-test-id="corrections-graph"><summary data-test-id="corrections-graph-toggle">${esc(t("corrections.graph.toggle",{count:edges.length}))}</summary>
    <ol class="correction-graph" aria-label="${esc(t("corrections.graph.label"))}" data-test-id="corrections-graph-edges">${edges.map((edge,index)=>{
      const identity = JSON.stringify(edge);
      const occurrence = edges.slice(0,index).filter(other=>JSON.stringify(other)===identity).length;
      const edgeId = hook("graph-edge",identity,occurrence);
      return `<li data-test-id="${edgeId}"><div><span class="correction-endpoint-label">${esc(t("corrections.graph.from"))}</span>${endpoint(edge.from,"graph-from",edgeId)}</div><div class="correction-relation"><span aria-hidden="true">→</span><code>${esc(edge.relation)}</code><span aria-hidden="true">→</span></div><div><span class="correction-endpoint-label">${esc(t("corrections.graph.to"))}</span>${endpoint(edge.to,"graph-to",edgeId)}</div></li>`;}).join("")}</ol>
    ${tableWrap("corrections-edge-table",t("corrections.graph.edgeTable"),[t("corrections.graph.from"),t("corrections.graph.relation"),t("corrections.graph.to")],edges.map(edge=>`<tr><td><code>${esc(edge.from)}</code></td><td><code>${esc(edge.relation)}</code></td><td><code>${esc(edge.to)}</code></td></tr>`).join(""),t)}</details>`;
}

function impactMarkup(t) {
  const nodes = evidencedDescendants();
  const rows = impactRows().map(row=>`<tr data-test-id="${hook("impact-row",row.id)}"><th scope="row">${inspectNode(row,"artifact",t)}</th><td>${esc(row.kind)}</td><td>${stateBadge(row.state,t)}</td><td>${references(row.evidenceRefs,"artifact-ref",t,"reference",row.id)}</td></tr>`).join("");
  return `<section class="correction-impact" data-test-id="corrections-impact"><header><h3>${esc(t("corrections.impact.title"))}</h3><p>${esc(t("corrections.impact.summary",{artifacts:nodes.length,edges:CORRECTION_FIXTURE.edges.length}))}</p></header><p>${esc(t("corrections.impact.boundary"))}</p>
    ${graphMarkup(t)}${tableWrap("corrections-impact-table",t("corrections.table.caption"),["identity","class","state","evidence"].map(key=>t(`corrections.table.${key}`)),rows,t)}</section>`;
}

function queueMarkup(t) {
  const rows = requalificationQueue().map(task=>`<tr data-test-id="${hook("task",task.id)}"><th scope="row"><code>${esc(task.id)}</code></th><td>${esc(t(`corrections.urgency.${task.urgency}`))}</td><td>${task.owner==="UNTRACKED"?esc(t("corrections.owner.untracked")):`<code>${esc(task.owner)}</code>`}</td><td>${stateBadge(task.status,t)}</td><td><span>${esc(t("corrections.queue.generation",{generation:task.generation}))}</span><details data-test-id="${hook("custody",task.id)}"><summary data-test-id="${hook("custody-toggle",task.id)}">${esc(t("corrections.queue.details"))}</summary><dl><dt>${esc(t("corrections.queue.checkpoint"))}</dt><dd><code>${esc(task.checkpoint)}</code></dd><dt>${esc(t("corrections.queue.revision"))}</dt><dd><code>${esc(task.sourceRevision)}</code></dd><dt>${esc(t("corrections.queue.implicated"))}</dt><dd>${task.implicatedRefs.map(ref=>`<code>${esc(ref)}</code>`).join("<br>")}</dd></dl></details></td><td>${references(task.evidenceRefs,"task-evidence",t,"reference",task.id)}${task.receiptRefs.length?references(task.receiptRefs,"task-receipt",t,"receipt",task.id):`<p class="correction-untracked">${esc(t("corrections.queue.noReceipt"))}</p>`}</td></tr>`).join("");
  return `<section class="correction-queue" data-test-id="corrections-queue"><h3>${esc(t("corrections.queue.title"))}</h3><p>${esc(t("corrections.queue.summary"))}</p>${tableWrap("corrections-queue-table",t("corrections.queue.caption"),[t("corrections.queue.task"),t("corrections.queue.urgency"),t("corrections.queue.owner"),t("corrections.table.state"),t("corrections.queue.custody"),t("corrections.queue.evidence")],rows,t)}</section>`;
}

function historyMarkup(t) {
  const events = CORRECTION_FIXTURE.history;
  return `<section class="correction-history-section" data-test-id="corrections-history"><h3>${esc(t("corrections.history.title"))}</h3><p>${esc(t("corrections.history.summary"))}</p><ol class="correction-history">${events.map(entry=>`<li data-test-id="${hook("history",entry.id)}"><header><h4>${esc(t(`corrections.phase.${entry.phase}`))}</h4><span>${esc(t("corrections.history.generation",{generation:entry.atGeneration}))}</span></header><code>${esc(entry.id)}</code>${references(entry.receipt?[entry.receipt]:[],"history-receipt",t,"receipt",entry.id)}<dl aria-label="${esc(t("corrections.history.states"))}">${Object.entries(entry.states).map(([id,state])=>`<dt><code>${esc(id)}</code></dt><dd>${stateBadge(state,t)}</dd>`).join("")}</dl></li>`).join("") || `<li>${esc(t("corrections.history.empty"))}</li>`}</ol></section>`;
}

export function renderCorrectionsMarkup(t = correctionsT) {
  assertReceiptBackedTerminalStates();
  const correction = CORRECTION_FIXTURE.correction;
  const fields = [["id",correction.id],["before",correction.priorRevision],["after",correction.currentRevision],["generation",correction.correctionGeneration],["unknown",t("corrections.context.unknownCount",{count:unknownInfluenceRows().length})]];
  return `<div class="corrections-view" data-test-id="corrections-workspace"><header class="corrections-heading"><h2>${esc(t("corrections.title"))}</h2><p>${esc(t("corrections.summary"))}</p></header>
    <aside class="corrections-fixture-notice" data-test-id="corrections-fixture-notice" role="note"><strong>${esc(t("corrections.fixture.title"))}</strong><p>${esc(t("corrections.fixture.description"))}</p><p>${esc(t("corrections.boundary"))}</p></aside>
    <section class="correction-context" data-test-id="corrections-context"><h3>${esc(t("corrections.context.title"))}</h3><dl>${fields.map(([key,value])=>`<dt>${esc(t(`corrections.context.${key}`))}</dt><dd>${typeof value==="number"?esc(value):`<code>${esc(value)}</code>`}</dd>`).join("")}</dl><details data-test-id="corrections-context-receipts"><summary data-test-id="corrections-context-receipts-toggle">${esc(t("corrections.context.receipts"))}</summary>${references([correction.sourceReceipt,correction.recordedReceipt],"context-receipt",t,"receipt")}<code>${esc(CORRECTION_FIXTURE_CONTRACT.projection)}</code></details><details data-test-id="corrections-guide"><summary data-test-id="corrections-guide-toggle">${esc(t("corrections.guide.title"))}</summary><p>${esc(t("corrections.guide.description"))}</p></details></section>
    ${impactMarkup(t)}${queueMarkup(t)}${historyMarkup(t)}</div>`;
}

export function renderCorrectionsView(container, inspectCorrection, {onReference = null} = {}) {
  const openIds = [...container.querySelectorAll("details[data-test-id][open]")].map(item=>item.dataset.testId);
  container.innerHTML = renderCorrectionsMarkup();
  for (const id of openIds) {
    const item = container.querySelector(`[data-test-id="${id}"]`);
    if (item) item.open = true;
  }
  container.querySelectorAll("[data-correction-node]").forEach(button=>button.addEventListener("click",()=>{
    const node = CORRECTION_FIXTURE.nodes.find(item=>item.id===button.dataset.correctionNode);
    if(node) inspectCorrection(node.id,node);
  }));
  container.querySelectorAll("[data-correction-ref]").forEach(button=>{
    if(!onReference) {button.disabled=true;return;}
    button.addEventListener("click",()=>onReference(button.dataset.correctionRef,button.dataset.correctionRefKind));
  });
}
