import { controlClass } from "../foundation/primitives.mjs";

export function esc(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

// Scope and identity form the hook; only duplicate occurrences need a suffix.
export function hookFactory(scope) {
  const counts = new Map();
  return (identity) => {
    const key = Array.from(String(identity), (char) => char.codePointAt(0).toString(16)).join("-") || "empty";
    const count = (counts.get(key) ?? 0) + 1;
    counts.set(key, count);
    return `evidence-${scope}-${key}-${count}`;
  };
}

export function pageStatus(page, t, id) {
  return `<div class="evidence-page-status" data-test-id="${id}">
    <span>${esc(t("evidence.query.state", { state: page.state }))}</span>
    <span>${esc(t("evidence.query.coverage", { coverage: page.coverage }))}</span>
    ${page.truncated ? `<strong>${esc(t("evidence.query.truncated"))}</strong>` : ""}
    <span>${esc(t("evidence.query.count", { returned: page.returned ?? 0, total: page.total_matches ?? 0 }))}</span></div>`;
}

export function markersMarkup(markers, t, scope = "query") {
  const hook = hookFactory(`${scope}-marker`);
  return (markers ?? []).map((marker) => {
    const details = [
      ...(marker.missing_fields ?? []), marker.reason, marker.resource, marker.stale_record_id,
      Number.isSafeInteger(marker.requested_as_of) ? t("evidence.marker.requested", {value: marker.requested_as_of}) : null,
      Number.isSafeInteger(marker.available_as_of) ? t("evidence.marker.available", {value: marker.available_as_of}) : null,
    ].filter((value) => value !== null && value !== undefined);
    return `<li class="evidence-marker" data-test-id="${hook(marker.meta?.record_id ?? JSON.stringify(marker))}">
      <strong>${esc(marker.schema_version ?? t("evidence.marker.fallback"))}</strong>
      <code>${esc(marker.meta?.record_id ?? "marker:unidentified")}</code>
      <span>${esc(details.length ? details.join(" · ") : t("evidence.marker.detail"))}</span></li>`;
  }).join("");
}

export function linksMarkup(links, t, scope = "page") {
  const hook = hookFactory(`${scope}-link`);
  return (links ?? []).map((link, index) => {
    const id = hook(JSON.stringify([link.relation, link.source_record_id, link.target_ref, link.target_record_id]));
    return `<li class="evidence-link" data-test-id="${id}"><strong>${esc(link.relation)}</strong>
      <code>${esc(link.source_record_id)}</code><span aria-hidden="true">→</span><code>${esc(link.target_ref)}</code>
      ${link.target_record_id ? `<button class="${controlClass("link")}" type="button" data-test-id="${id.replace("-link-", "-open-")}" ${scope === "selected" ? "data-evidence-selected-target" : "data-evidence-target"}="${index}">${esc(t("evidence.links.open"))}</button>`
    : `<span class="evidence-unresolved">${esc(t("evidence.links.external"))}</span>`}</li>`;
  }).join("");
}

function structured(value, label, id) {
  return `<pre tabindex="0" role="region" aria-label="${esc(label)}" data-test-id="${id}">${esc(JSON.stringify(value, null, 2))}</pre>`;
}

function provenance(meta, t) {
  return `<section class="evidence-provenance" data-test-id="evidence-provenance"><h4>${esc(t("evidence.provenance.title"))}</h4>${[
    ["source", meta.source_refs], ["evidence", meta.evidence_refs], ["receipt", meta.receipt_refs],
  ].map(([kind, values]) => {
    const hook = hookFactory(`ref-${kind}`);
    return `<section class="evidence-ref-group" data-test-id="evidence-provenance-${kind}"><h5>${esc(t(`evidence.provenance.${kind}`))}</h5><ul>${values?.length ? values.map((value) => {
      const id = hook(value);
      return `<li><code>${esc(value)}</code><button type="button" class="${controlClass("link")}" data-test-id="${id}" data-evidence-ref="${esc(value)}">${esc(t("evidence.provenance.search"))}</button></li>`;
    }).join("") : `<li class="evidence-unresolved">${esc(t("evidence.provenance.empty"))}</li>`}</ul></section>`;
  }).join("")}</section>`;
}

export function recordDetail(state, t) {
  const record = state.selected;
  if (!record) return `<section class="evidence-detail evidence-detail--empty" data-test-id="evidence-detail"><h3>${esc(t("evidence.selection.title"))}</h3><p>${esc(t("evidence.selection.empty"))}</p></section>`;
  const meta = record.meta ?? {};
  const unknown = t("evidence.value.unknown");
  const facts = [
    ["recordId", meta.record_id], ["schema", record.schema_version], ["authority", meta.authority], ["coverage", meta.coverage],
    ["verification", record.verification_state ?? record.verification_status ?? t("evidence.value.verificationAbsent")],
    ["materialized", meta.materialized_at], ["observed", meta.observed_at], ["asOf", meta.as_of],
  ].map(([key, value]) => `<dt>${esc(t(`evidence.field.${key}`))}</dt><dd><code>${esc(value ?? unknown)}</code></dd>`).join("");
  const hook = hookFactory("field");
  const fields = Object.entries(record).filter(([key]) => key !== "meta" && key !== "schema_version")
    .map(([key, value]) => `<dt><code>${esc(key)}</code></dt><dd>${typeof value === "object" && value !== null
      ? structured(value, t("evidence.field.structured", {field: key}), hook(key))
      : `<code>${esc(value === null ? "null" : value)}</code>`}</dd>`).join("");
  const links = state.selectedLinks;
  const related = state.traversalError ? `<div role="alert" class="evidence-notice" data-test-id="evidence-traversal-error"><strong>${esc(t("evidence.links.failure"))}</strong><p>${esc(t("evidence.links.recovery"))}</p><code>${esc(state.traversalError)}</code></div>`
    : !links ? `<p role="status" data-test-id="evidence-selected-links-loading">${esc(t("evidence.links.loading"))}</p>`
      : `${pageStatus(links, t, "evidence-selected-links-status")}<ul class="evidence-markers">${markersMarkup(links.markers, t, "selected")}</ul><ul class="evidence-links">${linksMarkup(links.links, t, "selected") || `<li>${esc(t("evidence.links.empty"))}</li>`}</ul>`;
  return `<section class="evidence-detail" data-test-id="evidence-detail">
    <header><span class="evidence-section-label">${esc(t("evidence.selection.title"))}</span><h3 tabindex="-1" data-test-id="evidence-detail-heading">${esc(meta.record_id ?? t("evidence.value.unidentified"))}</h3>
    <div class="evidence-modes" role="group" aria-label="${esc(t("evidence.mode.label"))}">${["readable", "raw"].map((mode) => `<button type="button" class="${controlClass("mode")}" data-evidence-mode="${mode}" data-test-id="evidence-mode-${mode}" aria-pressed="${Boolean(state.raw) === (mode === "raw")}">${esc(t(`evidence.mode.${mode}`))}</button>`).join("")}</div></header>
    ${state.raw ? structured(record, t("evidence.raw.label"), "evidence-raw-payload")
    : `<div class="evidence-readable"><dl class="evidence-facts" data-test-id="evidence-record-facts">${facts}</dl>
      <section><h4>${esc(t("evidence.fields.title"))}</h4><dl class="evidence-fields" data-test-id="evidence-record-fields">${fields || `<dd>${esc(t("evidence.fields.empty"))}</dd>`}</dl></section>
      <details data-test-id="evidence-metadata" class="ui-disclosure"><summary data-test-id="evidence-metadata-toggle">${esc(t("evidence.field.metadata"))}</summary>${structured(meta, t("evidence.field.metadata"), "evidence-metadata-payload")}</details>
      ${provenance(meta, t)}</div>`}<section data-test-id="evidence-related"><h4>${esc(t("evidence.links.title"))}</h4>${related}</section></section>`;
}
