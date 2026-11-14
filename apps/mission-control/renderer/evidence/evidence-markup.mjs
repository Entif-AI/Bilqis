import { SEARCH_KINDS } from "./evidence-query.mjs";

function esc(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

function pageState(page) {
  if (!page) return "NOT QUERIED";
  return `${page.state} · ${page.coverage}${page.truncated ? " · TRUNCATED" : ""}`;
}

function markerSummary(marker) {
  const meta = marker?.meta ?? {};
  const details = [
    ...(Array.isArray(marker?.missing_fields) ? marker.missing_fields : []),
    marker?.reason ?? null, marker?.resource ?? null, marker?.stale_record_id ?? null,
    Number.isSafeInteger(marker?.requested_as_of) ? `requested as-of ${marker.requested_as_of}` : null,
    Number.isSafeInteger(marker?.available_as_of) ? `available as-of ${marker.available_as_of}` : null,
  ].filter((value) => value !== null && value !== undefined);
  return `<article class="evidence-marker"><strong>${esc(marker?.schema_version ?? "DEGRADED EVIDENCE MARKER")}</strong>
    <code>${esc(meta.record_id ?? "marker:unidentified")}</code>
    <span>${details.length ? esc(details.join(" · ")) : "Exact degraded-state marker; no additional detail reported."}</span></article>`;
}

function recordSummary(record, index) {
  const meta = record.meta ?? {};
  const run = meta.run ?? null;
  return `<button class="evidence-result" type="button" data-evidence-record="${index}">
    <strong>${esc(meta.record_id ?? "UNIDENTIFIED RECORD")}</strong>
    <span>${esc(record.schema_version ?? "SCHEMA UNKNOWN")}</span>
    <small>${esc(meta.authority ?? "AUTHORITY UNKNOWN")} · ${esc(meta.coverage ?? "COVERAGE UNKNOWN")}${run ? ` · gen ${esc(run.generation)}` : ""}</small>
  </button>`;
}

function linkSummary(link, index, scope = "page") {
  const targetAttribute = scope === "selected"
    ? `data-evidence-selected-target="${index}"` : `data-evidence-target="${index}"`;
  const target = link.target_record_id
    ? `<button type="button" ${targetAttribute}>Open exact record</button>`
    : `<span class="evidence-unresolved">EXTERNAL / NOT HYDRATED</span>`;
  return `<article class="evidence-link"><strong>${esc(link.relation)}</strong>
    <code>${esc(link.source_record_id)}</code><span>→</span><code>${esc(link.target_ref)}</code>${target}</article>`;
}

function refs(meta) {
  const groups = [
    ["SOURCE", meta?.source_refs ?? []], ["EVIDENCE", meta?.evidence_refs ?? []],
    ["RECEIPT", meta?.receipt_refs ?? []],
  ];
  return groups.map(([kind, values]) => values.map((value) =>
    `<button type="button" data-evidence-ref="${esc(value)}"><b>${kind}</b> ${esc(value)}</button>`,
  ).join("")).join("") || '<span class="evidence-unresolved">No provenance refs reported.</span>';
}

function readable(record, linksPage, linkError = null) {
  const meta = record.meta ?? {};
  const body = Object.entries(record).filter(([key]) => key !== "meta")
    .map(([key, value]) => `<dt>${esc(key)}</dt><dd><code>${esc(
      typeof value === "object" ? JSON.stringify(value) : value,
    )}</code></dd>`).join("");
  const verification = record.verification_state ?? record.verification_status ?? "NOT SEPARATELY REPORTED";
  return `<div class="evidence-readable"><dl><dt>Record ID</dt><dd>${esc(meta.record_id)}</dd>
    <dt>Schema / version</dt><dd>${esc(record.schema_version)}</dd><dt>Authority</dt><dd>${esc(meta.authority)}</dd>
    <dt>Coverage</dt><dd>${esc(meta.coverage)}</dd><dt>Verification</dt><dd>${esc(verification)}</dd>
    <dt>Materialized</dt><dd>${esc(meta.materialized_at ?? "UNKNOWN")}</dd><dt>Observed</dt><dd>${esc(meta.observed_at ?? "UNKNOWN")}</dd>
    <dt>As of</dt><dd>${esc(meta.as_of ?? "UNKNOWN")}</dd><dt>Record metadata</dt><dd><code>${esc(JSON.stringify(meta))}</code></dd>${body}</dl>
    <section><h4>Provenance chain</h4><div class="evidence-refs">${refs(meta)}</div></section>
    <section><h4>Exact links</h4><div class="evidence-links">${linkError
      ? `<span class="evidence-unresolved">LINK HYDRATION UNAVAILABLE · ${esc(linkError)}</span>`
      : (linksPage?.links ?? []).map((link, index) => linkSummary(link, index, "selected")).join("")
        || '<span class="evidence-unresolved">No resolvable links reported.</span>'}</div></section></div>`;
}

export function renderEvidenceMarkup(state) {
  const page = state.page;
  const markers = (page?.markers ?? []).map(markerSummary).join("");
  const results = [
    ...state.records.map(recordSummary),
    ...state.links.map((link, index) => linkSummary(link, index)),
  ].join("");
  const selectedMarkup = !state.selected ? "" : `<section class="evidence-detail">
    <header><div><span class="eyebrow">Exact evidence item</span><h3>${esc(state.selected.meta?.record_id)}</h3></div>
      <button type="button" data-evidence-raw>${state.raw ? "Readable view" : "Raw structured payload"}</button></header>
    ${state.raw ? `<pre>${esc(JSON.stringify(state.selected, null, 2))}</pre>` : readable(state.selected, state.selectedLinks, state.traversalError)}</section>`;
  const emptyText = state.criteria.kind === "memory"
    ? "No accepted CP03 record exposes this memory motif/slot identity. GUI10 display fixtures are not durable evidence."
    : "No evidence rows returned for this exact query.";
  const queryState = state.status === "error" ? "error" : page?.state ?? state.status;
  const queryLabel = state.status === "error"
    ? "QUERY UNAVAILABLE" : state.status === "loading" ? "LOADING" : pageState(page);
  const queryDetail = state.status === "error"
    ? state.error ?? "Evidence query failed"
    : state.status === "loading" ? "Awaiting bounded evidence page"
      : page ? `${page.returned} returned / ${page.total_matches} exact matches` : "Ready";
  const returnButton = state.returnAvailable
    ? '<button type="button" data-evidence-return>Return to inspected object</button>' : "";
  return `<div class="evidence-view"><header class="evidence-heading"><div><span class="eyebrow">GUI16 · Evidence &amp; Receipts</span>
    <h2>Forensic provenance browser</h2></div><p>Literal CP03 records only. External payloads remain external unless the control plane exposes an exact record identity.</p>${returnButton}</header>
    <div class="ui-glossary" aria-label="Evidence browser help"><span><strong>Exact identity</strong> searches a literal record/reference, not fuzzy text.</span><span><strong>Historical</strong> is inspection-only.</span><span><strong>Unavailable</strong> means the local evidence query surface is not connected.</span></div>
    <form id="evidence-search-form" class="evidence-search"><label>Search by<select name="kind">${SEARCH_KINDS.map(([value, label]) =>
      `<option value="${value}"${state.criteria.kind === value ? " selected" : ""}>${label}</option>`).join("")}</select></label>
      <label>Exact identity<input name="value" value="${esc(state.criteria.value)}" autocomplete="off" /></label><button type="submit">Search</button></form>
    <div class="evidence-query-state" data-state="${esc(queryState)}" role="${state.status === "error" ? "alert" : "status"}" aria-live="polite"><strong>${esc(queryLabel)}</strong><span>${esc(queryDetail)}</span></div>
    ${state.traversalError ? `<div class="evidence-traversal-error" role="alert" aria-live="polite"><strong>Provenance traversal unavailable</strong><span>${esc(state.traversalError)}</span></div>` : ""}
    ${markers ? `<section class="evidence-markers" aria-label="Omissions and degraded evidence">${markers}</section>` : ""}
    <div class="evidence-results">${results || `<div class="evidence-empty">${emptyText}</div>`}</div>
    ${page?.next_cursor ? '<button type="button" data-evidence-more>Load next bounded page</button>' : ""}${selectedMarkup}</div>`;
}
