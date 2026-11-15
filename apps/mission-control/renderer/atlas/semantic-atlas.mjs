import { t } from "../foundation/i18n.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";

export const QUERY_SCHEMA = "bilqis.bamf.control-plane.query/v1";
export const QUERY_PAGE_SCHEMA = "bilqis.bamf.control-plane.query-page/v1";
export const CONCEPT_SCHEMA = "bilqis.bamf.mission-control.semantic-concept-snapshot/v1";
export const STATE_SCHEMA = "bilqis.bamf.mission-control.semantic-generation-state/v1";
export const BANK_SCHEMA = "bilqis.bamf.mission-control.semantic-bank-snapshot/v1";
export const HELD_SCHEMA = "bilqis.bamf.mission-control.semantic-held-mapping/v1";
export const SIMILARITY_SCHEMA = "bilqis.bamf.mission-control.semantic-similarity-snapshot/v1";
export const SUMMARY_SCHEMA = "bilqis.bamf.mission-control.semantic-atlas-snapshot/v1";

const PAGE_STATES = new Set([
  "PRESENT", "EMPTY", "MISSING", "UNAVAILABLE", "PARTIAL", "STALE", "DENIED", "UNKNOWN",
]);

function invalid(detail) {
  throw new TypeError(`MISSION_CONTROL_SEMANTIC_QUERY_INVALID:${detail}`);
}

export function conceptRecordId(semanticRelease, semanticId) {
  if (typeof semanticRelease !== "string" || !/^[0-9a-f]{64}$/.test(semanticRelease) ||
      typeof semanticId !== "string" || semanticId.length === 0 || semanticId.includes("\n")) {
    invalid("CONCEPT_ID");
  }
  return `semantic-concept:${semanticRelease}:${semanticId}`;
}

export function stateRecordId(context, bank, row) {
  if (!context || typeof context.runId !== "string" || !Number.isSafeInteger(context.generation) ||
      !Number.isSafeInteger(bank) || bank < 0 || !Number.isSafeInteger(row) || row < 0) {
    invalid("STATE_ID");
  }
  return `semantic-state:${context.runId}:${context.generation}:${bank}:${row}`;
}

export function queryRequest({
  family = "semantic", mode = "current", runId = null, recordId = null,
  schemaVersion = null, generation = null, frontierId = null, asOf = null,
  reference = null, cursor = null, limit = 32,
} = {}) {
  return Object.freeze({
    schema: QUERY_SCHEMA,
    family,
    mode,
    run_id: runId,
    record_id: recordId,
    schema_version: schemaVersion,
    generation,
    frontier_id: frontierId,
    as_of: asOf,
    reference,
    cursor,
    limit,
  });
}

function generationSelector(context) {
  if (context.mode === "HISTORICAL") {
    return { mode: "historical", runId: context.runId, generation: context.generation };
  }
  return { mode: "current", runId: context.runId };
}

export function generationQuery(context, options = {}) {
  return queryRequest({ ...generationSelector(context), ...options });
}

export function sourceQuery(options = {}) {
  return queryRequest({ mode: "current", ...options });
}

export function assertQueryPage(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) invalid("PAGE");
  if (raw.accepted === false) {
    if (typeof raw.reason !== "string" || raw.reason.length === 0) invalid("ERROR");
    return raw;
  }
  if (raw.schema !== QUERY_PAGE_SCHEMA || raw.accepted !== true ||
      !PAGE_STATES.has(raw.state) || !Array.isArray(raw.records) ||
      !Array.isArray(raw.markers) || !Array.isArray(raw.links) ||
      !Number.isSafeInteger(raw.total_matches) || raw.total_matches < 0) {
    invalid("PAGE_SHAPE");
  }
  return raw;
}

async function ask(api, request) {
  if (!api || typeof api.query !== "function") invalid("QUERY_CAPABILITY");
  return assertQueryPage(await api.query(request));
}

function firstRecord(page, schema) {
  return page.accepted === true
    ? page.records.find((record) => record?.schema_version === schema) ?? null
    : null;
}

export async function loadAtlasOverview(api, context) {
  const [summary, banks, held, similarities] = await Promise.all([
    ask(api, generationQuery(context, { schemaVersion: SUMMARY_SCHEMA, limit: 1 })),
    ask(api, generationQuery(context, { schemaVersion: BANK_SCHEMA, limit: 32 })),
    ask(api, sourceQuery({ schemaVersion: HELD_SCHEMA, limit: 8 })),
    ask(api, generationQuery(context, { schemaVersion: SIMILARITY_SCHEMA, limit: 8 })),
  ]);
  return Object.freeze({ summary, banks, held, similarities });
}

async function learnedEdges(api, context, semanticId) {
  const references = await ask(api, generationQuery(context, {
    family: "reference", reference: semanticId, limit: 32,
  }));
  if (references.accepted !== true) return [];
  const recordIds = [...new Set(references.links
    .filter((link) => link.relation === "LEARNED_SIMILARITY_SOURCE" ||
      link.relation === "LEARNED_SIMILARITY_TARGET")
    .map((link) => link.source_record_id))];
  const pages = await Promise.all(recordIds.slice(0, 32).map((recordId) =>
    ask(api, generationQuery(context, { recordId, limit: 1 }))));
  return pages.map((page) => firstRecord(page, SIMILARITY_SCHEMA)).filter(Boolean);
}

async function heldForIdentity(api, semanticId) {
  const references = await ask(api, sourceQuery({
    family: "reference", reference: semanticId, limit: 32,
  }));
  if (references.accepted !== true) return null;
  const held = references.links.find((link) => link.relation === "HELD_SEMANTIC_IDENTITY");
  if (!held) return null;
  const page = await ask(api, sourceQuery({ recordId: held.source_record_id, limit: 1 }));
  return firstRecord(page, HELD_SCHEMA);
}

export async function loadSemanticIdentity(api, context, semanticId) {
  const conceptPage = await ask(api, sourceQuery({
    recordId: conceptRecordId(context.semanticRelease, semanticId), limit: 1,
  }));
  const concept = firstRecord(conceptPage, CONCEPT_SCHEMA);
  if (!concept) {
    return Object.freeze({ semanticId, concept: null, state: null,
      held: await heldForIdentity(api, semanticId), similarities: [] });
  }
  const statePage = await ask(api, generationQuery(context, {
    recordId: stateRecordId(context, concept.abi_bank, concept.abi_row), limit: 1,
  }));
  const state = firstRecord(statePage, STATE_SCHEMA);
  const similarities = await learnedEdges(api, context, semanticId);
  return Object.freeze({ semanticId, concept, state, held: null, similarities });
}

export async function loadAbiRow(api, context, bank, row) {
  const statePage = await ask(api, generationQuery(context, {
    recordId: stateRecordId(context, bank, row), limit: 1,
  }));
  const state = firstRecord(statePage, STATE_SCHEMA);
  if (!state) return Object.freeze({ bank, row, state: null, concept: null, similarities: [] });
  const conceptPage = state.concept_record_id
    ? await ask(api, sourceQuery({ recordId: state.concept_record_id, limit: 1 }))
    : null;
  const concept = conceptPage ? firstRecord(conceptPage, CONCEPT_SCHEMA) : null;
  const similarities = await learnedEdges(api, context, state.semantic_id);
  return Object.freeze({ bank, row, state, concept, similarities });
}

export function lensEdges(selection, lens) {
  if (!selection) return [];
  if (lens === "learned") {
    return (selection.similarities ?? []).map((record) => {
      if (record.canonical_equivalence !== false) {
        invalid("SIMILARITY_CANONICAL_EQUIVALENCE");
      }
      return Object.freeze({
        kind: "learned",
        source: record.source_semantic_id,
        target: record.target_semantic_id,
        relation: `similarity · ${record.similarity?.value ?? "unknown"}`,
        canonicalEquivalence: record.canonical_equivalence,
        basis: record.basis_ref,
      });
    });
  }
  return (selection.concept?.relations ?? []).map((relation) => Object.freeze({
    kind: "canonical",
    source: selection.concept.semantic_id,
    target: relation.target_semantic_id,
    relation: relation.predicate,
  }));
}

export function summarizeOverview(overview) {
  const summary = firstRecord(overview?.summary ?? {}, SUMMARY_SCHEMA);
  const banks = overview?.banks?.accepted === true ? overview.banks.records : [];
  return Object.freeze({
    active: summary?.active_concepts?.value ?? null,
    eligible: summary?.source_eligible?.value ?? null,
    held: overview?.held?.accepted === true ? overview.held.total_matches : null,
    similarityEdges: overview?.similarities?.accepted === true
      ? overview.similarities.total_matches : null,
    banks,
  });
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function statusClass(value) {
  return String(value ?? "unknown").toLowerCase().replace(/[^a-z0-9_-]+/g, "-");
}

function valueOr(key, value) {
  return value === null || value === undefined ? t(key) : value;
}

function bankTable(banks, selectedBank) {
  if (!banks.length) return `<p class="atlas-muted" ${testIdAttribute("atlas", "bank", "empty")}>${esc(t("atlas.abi.noBanks"))}</p>`;
  return `<div class="atlas-table-wrap" tabindex="0" ${testIdAttribute("atlas", "bank", "table", "wrap")}>
    <table class="atlas-bank-table" ${testIdAttribute("atlas", "bank", "table")}>
      <thead><tr>
        <th scope="col">${esc(t("atlas.abi.bank"))}</th>
        <th scope="col">${esc(t("atlas.abi.allocated"))}</th>
        <th scope="col">${esc(t("atlas.abi.active"))}</th>
        <th scope="col">${esc(t("atlas.abi.masked"))}</th>
        <th scope="col"><span class="visually-hidden">${esc(t("atlas.abi.select", { bank: "#" }))}</span></th>
      </tr></thead>
      <tbody>${banks.map((bank) => `<tr data-selected="${selectedBank === bank.bank}">
        <th scope="row"><code>${esc(bank.bank)}</code></th>
        <td>${esc(bank.allocated_rows)}</td><td>${esc(bank.active_rows)}</td><td>${esc(bank.masked_rows)}</td>
        <td><button type="button" class="atlas-bank-select" data-atlas-bank="${esc(bank.bank)}"
          ${testIdAttribute("atlas", "bank", bank.bank, "select")}>${esc(t("atlas.abi.select", { bank: bank.bank }))}</button></td>
      </tr>`).join("")}</tbody>
    </table></div>`;
}

function heldMappings(rows) {
  if (!rows.length) return `<p class="atlas-muted" ${testIdAttribute("atlas", "held", "empty")}>${esc(t("atlas.lookup.noHeld"))}</p>`;
  return `<ul class="atlas-held-list" ${testIdAttribute("atlas", "held", "list")}>
    ${rows.map((row, index) => `<li ${testIdAttribute("atlas", "held", index)}><code>${esc(row.key)}</code><span>${esc(row.reason_code)}</span></li>`).join("")}
  </ul>`;
}

function relationMarkup(edges, lens) {
  const titleKey = lens === "canonical" ? "atlas.dossier.relationshipsCanonical" : "atlas.dossier.relationshipsLearned";
  const emptyKey = lens === "canonical" ? "atlas.dossier.noCanonical" : "atlas.dossier.noLearned";
  return `<section class="atlas-relations" aria-labelledby="atlas-relations-title" ${testIdAttribute("atlas", "semantic", "relations")}>
    <div class="atlas-section-heading"><h3 id="atlas-relations-title">${esc(t(titleKey))}</h3>
      ${lens === "learned" ? `<span class="atlas-derived-label">${esc(t("foundation.authority.derived"))}</span>` : ""}</div>
    ${lens === "learned" ? `<p class="atlas-boundary">${esc(t("atlas.dossier.learnedBoundary"))}</p>` : ""}
    ${edges.length ? `<div class="atlas-table-wrap" tabindex="0" ${testIdAttribute("atlas", "semantic", "relation", "table", "wrap")}><table class="atlas-relation-table" ${testIdAttribute("atlas", "semantic", "relation", "table")}><thead><tr><th scope="col">${esc(t("atlas.dossier.relation"))}</th><th scope="col">${esc(t("atlas.dossier.targetIdentity"))}</th><th scope="col">${esc(t("atlas.dossier.evidence"))}</th></tr></thead><tbody>
      ${edges.map((edge, index) => `<tr data-edge-kind="${edge.kind}" ${testIdAttribute("atlas", "semantic", "relation", index)}>
        <td><code>${esc(edge.relation)}</code></td><td><code>${esc(edge.target)}</code></td>
        <td>${edge.kind === "learned" ? esc(t("atlas.dossier.similarityBasis", { basis: edge.basis ?? t("atlas.value.unknown"), equivalence: edge.canonicalEquivalence })) : esc(t("atlas.dossier.authority"))}</td>
      </tr>`).join("")}</tbody></table></div>` : `<p class="atlas-muted">${esc(t(emptyKey))}</p>`}
  </section>`;
}

export function renderAtlasMarkup({ status, error, overview, selection, lens = "canonical",
  selectedBank = null } = {}) {
  if (status === "loading") return `<div class="atlas-request-state" role="status" aria-live="polite" ${testIdAttribute("atlas", "request", "loading")}>${esc(t("atlas.request.loading"))}</div>`;
  if (status === "error") return `<div class="atlas-request-state atlas-error" role="alert" ${testIdAttribute("atlas", "request", "error")}><strong>${esc(t("atlas.request.error"))}</strong><code>${esc(error)}</code></div>`;
  const aggregate = overview ? summarizeOverview(overview) : null;
  const banks = aggregate?.banks ?? [];
  const heldRows = overview?.held?.accepted === true ? overview.held.records : [];
  const edges = lensEdges(selection, lens);
  const concept = selection?.concept;
  const generationState = selection?.state;
  const held = selection?.held;
  const selectedIdentity = concept?.semantic_id ?? held?.semantic_id ?? selection?.state?.semantic_id ?? null;
  const noExactProjection = selection && !held && !generationState;
  return `
    <div class="atlas-workspace" ${testIdAttribute("atlas", "view")}>
      <header class="atlas-heading" ${testIdAttribute("atlas", "heading")}><div>
        <span class="eyebrow">${esc(t("atlas.view.eyebrow"))}</span><h2>${esc(t("atlas.view.title"))}</h2>
      </div><p>${esc(t("atlas.view.summary"))}</p></header>

      <section class="atlas-authority" aria-labelledby="atlas-lens-title" ${testIdAttribute("atlas", "lens")}>
        <div><span class="eyebrow" id="atlas-lens-title">${esc(t("atlas.lens.label"))}</span>
          <div class="atlas-lens-controls">
            <button type="button" data-atlas-lens="canonical" aria-pressed="${lens === "canonical"}" data-authority="source" ${testIdAttribute("atlas", "lens", "canonical")}>${esc(t("atlas.lens.canonical"))}</button>
            <button type="button" data-atlas-lens="learned" aria-pressed="${lens === "learned"}" data-authority="derived" ${testIdAttribute("atlas", "lens", "learned")}>${esc(t("atlas.lens.learned"))}</button>
          </div></div>
        <p>${esc(t(lens === "canonical" ? "atlas.lens.canonicalHelp" : "atlas.lens.learnedHelp"))}</p>
      </section>

      <section class="atlas-orientation" aria-label="${esc(t("atlas.overview.label"))}" ${testIdAttribute("atlas", "overview")}>
        <span><small>${esc(t("atlas.overview.active"))}</small><strong>${esc(valueOr("atlas.value.unknown", aggregate?.active))}</strong></span>
        <span><small>${esc(t("atlas.overview.eligible"))}</small><strong>${esc(valueOr("atlas.value.unknown", aggregate?.eligible))}</strong></span>
        <span><small>${esc(t("atlas.overview.held"))}</small><strong>${esc(valueOr("atlas.value.unknown", aggregate?.held))}</strong></span>
        <span data-derived="true"><small>${esc(t("atlas.overview.learned"))}</small><strong>${esc(valueOr("atlas.value.unavailable", aggregate?.similarityEdges))}</strong></span>
      </section>

      <div class="atlas-workbench">
        <section class="atlas-control-region" ${testIdAttribute("atlas", "lookup")}>
          <div class="atlas-section-heading"><div><span class="eyebrow">${esc(t("atlas.lookup.eyebrow"))}</span><h3>${esc(t("atlas.lookup.title"))}</h3></div></div>
          <form class="atlas-form" ${testIdAttribute("atlas", "search", "form")}>
            <label>${esc(t("atlas.lookup.label"))}<input name="semanticId" placeholder="${esc(t("atlas.lookup.placeholder"))}" required ${testIdAttribute("atlas", "search", "input")} /></label>
            <button type="submit" ${testIdAttribute("atlas", "search", "submit")}>${esc(t("atlas.lookup.submit"))}</button>
          </form>
          <div class="atlas-held-preview"><h4>${esc(t("atlas.lookup.heldTitle"))}</h4>${heldMappings(heldRows)}</div>
        </section>

        <section class="atlas-control-region" ${testIdAttribute("atlas", "abi")}>
          <div class="atlas-section-heading"><div><span class="eyebrow">${esc(t("atlas.abi.eyebrow"))}</span><h3>${esc(t("atlas.abi.title"))}</h3></div></div>
          <h4>${esc(t("atlas.abi.bankMap"))}</h4>${bankTable(banks, selectedBank)}
          <form class="atlas-form atlas-abi-form" ${testIdAttribute("atlas", "abi", "form")}>
            <label>${esc(t("atlas.abi.bank"))}<input name="bank" inputmode="numeric" value="${esc(selectedBank ?? 0)}" required ${testIdAttribute("atlas", "abi", "bank", "input")} /></label>
            <label>${esc(t("atlas.abi.row"))}<input name="row" inputmode="numeric" placeholder="0" required ${testIdAttribute("atlas", "abi", "row", "input")} /></label>
            <button type="submit" ${testIdAttribute("atlas", "abi", "submit")}>${esc(t("atlas.abi.resolve"))}</button>
          </form>
        </section>
      </div>

      <article class="atlas-dossier" ${testIdAttribute("atlas", "semantic", "dossier")}>
        <header class="atlas-dossier-heading"><div><span class="eyebrow">${esc(t("atlas.dossier.eyebrow"))}</span><h3>${esc(selectedIdentity ?? t("atlas.dossier.none"))}</h3></div>
          ${concept ? `<span class="atlas-authority-label">${esc(t("atlas.dossier.authority"))}</span>` : ""}</header>
        ${noExactProjection ? `<div class="atlas-projection-state" role="status" ${testIdAttribute("atlas", "request", "no", "projection")}>${esc(t("atlas.request.noProjection"))}</div>` : ""}
        ${held ? `<div class="atlas-held"><strong>${esc(t("atlas.held.label"))} · ${esc(held.reason_code)}</strong><span>${esc(held.teaching_reason)}</span><small>${esc(t("atlas.held.source", { domain: held.domain, table: held.table, key: held.key }))}</small></div>` : ""}
        ${concept ? `<div class="atlas-dossier-grid">
          <section><h4>${esc(t("atlas.dossier.identity"))}</h4><dl class="atlas-details">
            <dt>${esc(t("atlas.dossier.semanticId"))}</dt><dd><code>${esc(concept.semantic_id)}</code></dd>
            <dt>${esc(t("atlas.dossier.kind"))}</dt><dd>${esc(concept.kind)}</dd>
          </dl></section>
          <section><h4>${esc(t("atlas.dossier.sourceAbi"))}</h4><dl class="atlas-details">
            <dt>${esc(t("atlas.dossier.sourceRevision"))}</dt><dd><code>${esc(concept.atlas_release_sha256)}</code></dd>
            <dt>${esc(t("atlas.dossier.sourceLoci"))}</dt><dd>${concept.source_loci.map(esc).join("<br>") || esc(t("atlas.dossier.noneDeclared"))}</dd>
            <dt>${esc(t("atlas.dossier.abiAddress"))}</dt><dd><code>${esc(concept.abi_index)} · ${esc(t("atlas.abi.bank"))} ${esc(concept.abi_bank)} · ${esc(t("atlas.abi.row"))} ${esc(concept.abi_row)}</code></dd>
            <dt>${esc(t("atlas.dossier.generationState"))}</dt><dd><span class="atlas-state state-${statusClass(generationState?.admission_state)}"><span aria-hidden="true">${generationState ? "●" : "○"}</span>${esc(generationState?.admission_state ?? t("atlas.dossier.notMaterialized"))}</span></dd>
            <dt>${esc(t("atlas.dossier.activity"))}</dt><dd>${generationState ? `${generationState.newly_admitted} / ${generationState.recently_exercised} / ${generationState.requalification_affected}` : esc(t("atlas.value.unknown"))}</dd>
          </dl></section>
          <section><h4>${esc(t("atlas.dossier.bindings"))}</h4><dl class="atlas-details">
            <dt>${esc(t("atlas.dossier.capabilities"))}</dt><dd>${concept.capability_ids.map(esc).join("<br>") || esc(t("atlas.dossier.noneDeclared"))}</dd>
            <dt>${esc(t("atlas.dossier.frames"))}</dt><dd>${concept.frame_schema_refs.map(esc).join("<br>") || esc(t("atlas.dossier.noneDeclared"))}</dd>
          </dl></section>
        </div>` : !held ? `<p class="atlas-muted">${esc(t("atlas.dossier.prompt"))}</p>` : ""}
        ${relationMarkup(edges, lens)}
      </article>
    </div>`;
}
