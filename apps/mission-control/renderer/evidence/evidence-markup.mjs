import { SEARCH_KINDS } from "./evidence-query.mjs";
import { evidenceT } from "./evidence-messages.mjs";
import { controlClass, surfaceClass } from "../foundation/primitives.mjs";
import { esc, hookFactory, linksMarkup, markersMarkup, pageStatus, recordDetail } from "./evidence-record.mjs";

function recordResults(state, t) {
  const hook = hookFactory("record-result");
  return state.records.map((record, index) => {
    const meta = record.meta ?? {};
    return `<li><button class="evidence-result" type="button" data-test-id="${hook(meta.record_id ?? JSON.stringify(record))}" data-evidence-record="${index}" aria-pressed="${Boolean(state.selected && state.selected.meta?.record_id === meta.record_id)}">
      <code>${esc(meta.record_id ?? t("evidence.value.unidentified"))}</code>
      <span class="evidence-result-schema">${esc(record.schema_version ?? t("evidence.value.unknown"))}</span>
      <span>${esc(t("evidence.record.posture", {authority: meta.authority ?? t("evidence.value.unknown"), coverage: meta.coverage ?? t("evidence.value.unknown")}))}</span>
      ${meta.run ? `<span>${esc(t("evidence.record.generation", {generation: meta.run.generation}))}</span>` : ""}</button></li>`;
  }).join("");
}

function originMarkup(state, t) {
  if (!state.returnAvailable) return "";
  const origin = state.origin;
  return `<div class="evidence-origin" data-test-id="evidence-origin"><button type="button" class="${controlClass("link")}" data-test-id="evidence-return" data-evidence-return>← ${esc(t("evidence.origin.return"))}</button>
    ${origin ? `<span>${esc(t("evidence.origin.context", {view: origin.view, kind: origin.selected?.kind ?? "", identity: origin.selected?.id ?? ""}))}</span>
` : ""}</div>`;
}

export function renderEvidenceMarkup(state, t = evidenceT) {
  const page = state.page;
  const failed = state.status === "error";
  const loading = state.status === "loading";
  const markers = markersMarkup(page?.markers, t);
  const empty = loading ? t("evidence.results.pending") : failed ? t("evidence.query.failure")
    : t(state.criteria.kind === "memory" ? "evidence.results.memoryEmpty" : "evidence.results.empty");
  return `<div class="evidence-view" data-test-id="evidence-workspace">
    <header class="evidence-heading"><div><h2>${esc(t("evidence.title"))}</h2><p>${esc(t("evidence.summary"))}</p></div>${originMarkup(state, t)}</header>
    <section class="evidence-query" data-test-id="evidence-query">
      <form class="evidence-search" data-test-id="evidence-query-form"><label>${esc(t("evidence.query.kind"))}<select name="kind" data-test-id="evidence-query-kind">${SEARCH_KINDS.map(([value]) => `<option value="${value}"${state.criteria.kind === value ? " selected" : ""}>${esc(t(`evidence.kind.${value}`))}</option>`).join("")}</select></label>
      <label>${esc(t("evidence.query.identity"))}<input name="value" value="${esc(state.criteria.value)}" autocomplete="off" data-test-id="evidence-query-value" /></label><button type="submit" class="${controlClass("primary")}" data-test-id="evidence-query-submit">${esc(t("evidence.query.submit"))}</button></form>
      <div class="evidence-query-state" data-state="${esc(failed ? "error" : page?.state ?? state.status)}" data-test-id="evidence-query-status" role="${failed ? "alert" : "status"}" aria-live="polite" aria-atomic="true">
      ${failed ? `<strong>${esc(t("evidence.query.failure"))}</strong><span>${esc(t("evidence.query.recovery"))}</span>`
    : loading ? `<strong>${esc(t("evidence.query.loading"))}</strong><span>${esc(t("evidence.query.waiting"))}</span>` : !page ? esc(t("evidence.query.ready")) : ""}
      ${page ? pageStatus(page, t, "evidence-page-status") : ""}</div>
      ${failed ? `<details class="ui-disclosure" data-test-id="evidence-query-error"><summary data-test-id="evidence-query-error-toggle">${esc(t("evidence.query.detail"))}</summary><code>${esc(state.error)}</code></details>` : ""}
      <details class="evidence-help ui-disclosure" data-test-id="evidence-query-help"><summary data-test-id="evidence-query-help-toggle">${esc(t("evidence.query.help"))}</summary><p>${esc(t("evidence.query.guidance"))}</p></details>
    </section>
    ${markers ? `<section class="evidence-omissions" data-test-id="evidence-omissions"><h3>${esc(t("evidence.markers.title"))}</h3><ul class="evidence-markers">${markers}</ul></section>` : ""}
    ${!state.selected && state.traversalError ? `<div role="alert" class="evidence-notice" data-test-id="evidence-traversal-error"><strong>${esc(t("evidence.links.failure"))}</strong><code>${esc(state.traversalError)}</code></div>` : ""}
    <div class="evidence-workbench">
      <section class="evidence-results" data-test-id="evidence-results" aria-busy="${loading}"><h3 tabindex="-1" data-test-id="evidence-results-heading">${esc(t("evidence.results.title"))}</h3>
        ${state.records.length ? `<h4>${esc(t("evidence.results.records"))}</h4><ul class="evidence-record-list">${recordResults(state, t)}</ul>` : ""}
        ${state.links.length ? `<h4>${esc(t("evidence.results.relationships"))}</h4><ul class="evidence-links">${linksMarkup(state.links, t)}</ul>` : ""}
        ${!state.records.length && !state.links.length ? `<p class="evidence-empty" data-test-id="evidence-results-empty">${esc(empty)}</p>` : ""}
        ${page?.next_cursor ? `<button type="button" class="${controlClass("secondary")}" data-test-id="evidence-more" data-evidence-more${loading ? " disabled" : ""}>${esc(t("evidence.query.more"))}</button>` : ""}
      </section>
      <div class="${surfaceClass("surface-1")} evidence-document">${recordDetail(state, t)}</div>
    </div></div>`;
}
