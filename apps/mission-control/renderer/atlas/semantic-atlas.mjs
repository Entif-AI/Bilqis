import { t } from "../foundation/i18n.mjs";
import { contextHelpMarkup } from "../foundation/primitives.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";
import {
  ATLAS_TABS, bankTable, heldMappings, relationMarkup, tabMarkup, temporalFact,
} from "./atlas-view-parts.mjs";
import { firstRecord, invalid, SUMMARY_SCHEMA } from "./atlas-data.mjs";
export * from "./atlas-data.mjs";

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
    held: summary?.source_held?.value ?? null,
    similarityEdges: overview?.similarities?.accepted === true
      ? overview.similarities.total_matches : null,
    banks,
    meta: summary?.meta ?? null,
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

export function renderAtlasMarkup({ status, error, overview, selection, lens = "canonical",
  selectedBank = null, activeTab = "lookup", semanticQuery = "", abiBankQuery = "0",
  abiRowQuery = "", context = null } = {}) {
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
  const validTab = ATLAS_TABS.some(([id]) => id === activeTab) ? activeTab : "lookup";
  const fixturePosture = context?.fixture === true;
  const postureKey = context?.mode === "HISTORICAL" ? "atlas.posture.historical" : "atlas.posture.current";
  const postureLabel = fixturePosture
    ? `${t("shell.launchMode.fixtures")} · ${t("shell.inspector.generationLabel", { generation: context?.generation ?? t("atlas.value.unknown") })}`
    : t(postureKey, { generation: context?.generation ?? t("atlas.value.unknown") });
  return `
    <div class="atlas-workspace" ${testIdAttribute("atlas", "view")}>
      <header class="atlas-heading" ${testIdAttribute("atlas", "heading")}><div class="atlas-heading-copy">
        <span class="eyebrow">${esc(t("atlas.view.eyebrow"))}</span><h2>${esc(t("atlas.view.title"))}</h2>
        <p>${esc(t("atlas.view.summary"))}</p></div>
        <div class="atlas-heading-tools"><strong>${esc(postureLabel)}</strong>
          ${contextHelpMarkup({ label: t("atlas.help.posture.label"), description: t("atlas.help.posture.description"), testId: "atlas-help-posture" })}
        </div></header>

      <section class="atlas-overview-block" ${testIdAttribute("atlas", "overview", "block")}>
        <div class="atlas-overview-heading"><span class="eyebrow">${esc(t("atlas.overview.eyebrow"))}</span>
          ${contextHelpMarkup({ label: t("atlas.help.overview.label"), description: t("atlas.help.overview.description"), testId: "atlas-help-overview" })}</div>
        <section class="atlas-orientation" aria-label="${esc(t("atlas.overview.label"))}" ${testIdAttribute("atlas", "overview")}>
          <span data-authority="derived"><small>${esc(t("atlas.overview.active"))}</small><strong>${esc(valueOr("atlas.value.unknown", aggregate?.active))}</strong></span>
          <span data-authority="source"><small>${esc(t("atlas.overview.eligible"))}</small><strong>${esc(valueOr("atlas.value.unknown", aggregate?.eligible))}</strong></span>
          <span data-authority="source"><small>${esc(t("atlas.overview.held"))}</small><strong>${esc(valueOr("atlas.value.unknown", aggregate?.held))}</strong></span>
          <span data-authority="derived"><small>${esc(t("atlas.overview.learned"))}</small><strong>${esc(valueOr("atlas.value.unavailable", aggregate?.similarityEdges))}</strong></span>
        </section>
        ${Number.isSafeInteger(aggregate?.meta?.materialized_at) ? `<dl class="atlas-time-facts">${temporalFact("atlas.time.materialized", aggregate.meta.materialized_at, "atlas-overview-materialized")}</dl>` : ""}
      </section>

      <div class="atlas-tabs" role="tablist" aria-label="${esc(t("atlas.tabs.aria"))}" ${testIdAttribute("atlas", "tabs")}>
        ${tabMarkup(validTab)}
      </div>

      <section role="tabpanel" id="atlas-panel-lookup" aria-labelledby="atlas-tab-lookup"
        data-atlas-panel="lookup" ${validTab === "lookup" ? "" : "hidden"} ${testIdAttribute("atlas", "panel", "lookup")}>
        <section class="atlas-control-region" ${testIdAttribute("atlas", "lookup")}>
          <div class="atlas-panel-heading"><div><span class="eyebrow">${esc(t("atlas.lookup.eyebrow"))}</span><h3>${esc(t("atlas.lookup.title"))}</h3></div>
            ${contextHelpMarkup({ label: t("atlas.help.lookup.label"), description: t("atlas.help.lookup.description"), testId: "atlas-help-lookup" })}</div>
          <form class="atlas-form" ${testIdAttribute("atlas", "search", "form")}>
            <label>${esc(t("atlas.lookup.label"))}<input name="semanticId" value="${esc(semanticQuery)}" placeholder="${esc(t("atlas.lookup.placeholder"))}" required ${testIdAttribute("atlas", "search", "input")} /></label>
            <button type="submit" ${testIdAttribute("atlas", "search", "submit")}>${esc(t("atlas.lookup.submit"))}</button>
          </form>
          <div class="atlas-held-preview"><h4>${esc(t("atlas.lookup.heldTitle"))}</h4>${heldMappings(heldRows)}</div>
        </section>
      </section>

      <section role="tabpanel" id="atlas-panel-abi" aria-labelledby="atlas-tab-abi"
        data-atlas-panel="abi" ${validTab === "abi" ? "" : "hidden"} ${testIdAttribute("atlas", "panel", "abi")}>
        <section class="atlas-control-region" ${testIdAttribute("atlas", "abi")}>
          <div class="atlas-panel-heading"><div><span class="eyebrow">${esc(t("atlas.abi.eyebrow"))}</span><h3>${esc(t("atlas.abi.title"))}</h3></div>
            ${contextHelpMarkup({ label: t("atlas.help.abi.label"), description: t("atlas.help.abi.description"), testId: "atlas-help-abi" })}</div>
          <h4>${esc(t("atlas.abi.bankMap"))}</h4>${bankTable(banks, selectedBank)}
          <form class="atlas-form atlas-abi-form" ${testIdAttribute("atlas", "abi", "form")}>
            <label>${esc(t("atlas.abi.bank"))}<input name="bank" inputmode="numeric" value="${esc(abiBankQuery)}" required ${testIdAttribute("atlas", "abi", "bank", "input")} /></label>
            <label>${esc(t("atlas.abi.row"))}<input name="row" inputmode="numeric" value="${esc(abiRowQuery)}" placeholder="0" required ${testIdAttribute("atlas", "abi", "row", "input")} /></label>
            <button type="submit" ${testIdAttribute("atlas", "abi", "submit")}>${esc(t("atlas.abi.resolve"))}</button>
          </form>
        </section>
      </section>

      <section role="tabpanel" id="atlas-panel-dossier" aria-labelledby="atlas-tab-dossier"
        data-atlas-panel="dossier" ${validTab === "dossier" ? "" : "hidden"} ${testIdAttribute("atlas", "panel", "dossier")}>
      <article class="atlas-dossier" ${testIdAttribute("atlas", "semantic", "dossier")}>
        <header class="atlas-dossier-heading"><div><span class="eyebrow">${esc(t("atlas.dossier.eyebrow"))}</span><h3>${esc(selectedIdentity ?? t("atlas.dossier.none"))}</h3></div>
          <div class="atlas-dossier-actions">${selectedIdentity ? `<button type="button" class="atlas-inspect" data-atlas-inspect ${testIdAttribute("atlas", "semantic", "inspect")}>${esc(t("atlas.dossier.inspect"))}</button>` : ""}
          ${contextHelpMarkup({ label: t("atlas.help.dossier.label"), description: t("atlas.help.dossier.description"), testId: "atlas-help-dossier" })}</div></header>
        ${noExactProjection ? `<div class="atlas-projection-state" role="status" ${testIdAttribute("atlas", "request", "no", "projection")}>${esc(t("atlas.request.noProjection"))}</div>` : ""}
        ${held ? `<div class="atlas-held"><strong>${esc(t("atlas.held.label"))} · ${esc(held.reason_code)}</strong><span>${esc(held.teaching_reason)}</span><small>${esc(t("atlas.held.source", { domain: held.domain, table: held.table, key: held.key }))}</small></div>` : ""}
        ${concept ? `<div class="atlas-dossier-grid">
          <section data-authority="source"><div class="atlas-subheading"><h4>${esc(t("atlas.dossier.identity"))}</h4><span class="atlas-evidence-label atlas-evidence-label--source">${esc(t("atlas.evidence.source"))}</span></div><dl class="atlas-details">
            <dt>${esc(t("atlas.dossier.semanticId"))}</dt><dd><code>${esc(concept.semantic_id)}</code></dd>
            <dt>${esc(t("atlas.dossier.kind"))}</dt><dd>${esc(concept.kind)}</dd>
          </dl></section>
          <section data-authority="source"><div class="atlas-subheading"><h4>${esc(t("atlas.dossier.sourceAbi"))}</h4><span class="atlas-evidence-label atlas-evidence-label--source">${esc(t("atlas.evidence.source"))}</span></div><dl class="atlas-details">
            <dt>${esc(t("atlas.dossier.sourceRevision"))}</dt><dd><code>${esc(concept.atlas_release_sha256)}</code></dd>
            <dt>${esc(t("atlas.dossier.sourceLoci"))}</dt><dd>${concept.source_loci.map(esc).join("<br>") || esc(t("atlas.dossier.noneDeclared"))}</dd>
            <dt>${esc(t("atlas.dossier.abiAddress"))}</dt><dd><code>${esc(concept.abi_index)} · ${esc(t("atlas.abi.bank"))} ${esc(concept.abi_bank)} · ${esc(t("atlas.abi.row"))} ${esc(concept.abi_row)}</code></dd>
            ${temporalFact("atlas.time.sourceMaterialized", concept.meta?.materialized_at, "atlas-source-materialized")}
          </dl></section>
          <section data-authority="derived"><div class="atlas-subheading"><h4>${esc(t("atlas.dossier.generationObservation"))}</h4><span class="atlas-evidence-label atlas-evidence-label--derived">${esc(t("atlas.evidence.generationDerived"))}</span></div><dl class="atlas-details">
            <dt>${esc(t("atlas.dossier.generationState"))}</dt><dd><span class="atlas-state state-${statusClass(generationState?.admission_state)}"><span aria-hidden="true">${generationState ? "●" : "○"}</span>${esc(generationState?.admission_state ?? t("atlas.dossier.notMaterialized"))}</span></dd>
            <dt>${esc(t("atlas.dossier.activity"))}</dt><dd>${generationState ? `${generationState.newly_admitted} / ${generationState.recently_exercised} / ${generationState.requalification_affected}` : esc(t("atlas.value.unknown"))}</dd>
            ${temporalFact("atlas.time.observed", generationState?.meta?.observed_at, "atlas-generation-observed")}
            ${temporalFact("atlas.time.materialized", generationState?.meta?.materialized_at, "atlas-generation-materialized")}
          </dl></section>
          <section data-authority="source"><div class="atlas-subheading"><h4>${esc(t("atlas.dossier.bindings"))}</h4><span class="atlas-evidence-label atlas-evidence-label--source">${esc(t("atlas.evidence.source"))}</span></div><dl class="atlas-details">
            <dt>${esc(t("atlas.dossier.capabilities"))}</dt><dd>${concept.capability_ids.map(esc).join("<br>") || esc(t("atlas.dossier.noneDeclared"))}</dd>
            <dt>${esc(t("atlas.dossier.frames"))}</dt><dd>${concept.frame_schema_refs.map(esc).join("<br>") || esc(t("atlas.dossier.noneDeclared"))}</dd>
          </dl></section>
        </div>` : !held ? `<p class="atlas-muted">${esc(t("atlas.dossier.prompt"))}</p>` : ""}
        <section class="atlas-authority" aria-labelledby="atlas-lens-title" ${testIdAttribute("atlas", "lens")}>
          <div><div class="atlas-subheading"><span class="eyebrow" id="atlas-lens-title">${esc(t("atlas.lens.label"))}</span>
            ${contextHelpMarkup({ label: t("atlas.help.relations.label"), description: t("atlas.help.relations.description"), testId: "atlas-help-relations" })}</div>
            <div class="atlas-lens-controls">
              <button type="button" data-atlas-lens="canonical" aria-pressed="${lens === "canonical"}" data-authority="source" ${testIdAttribute("atlas", "lens", "canonical")}>${esc(t("atlas.lens.canonical"))}</button>
              <button type="button" data-atlas-lens="learned" aria-pressed="${lens === "learned"}" data-authority="derived" ${testIdAttribute("atlas", "lens", "learned")}>${esc(t("atlas.lens.learned"))}</button>
            </div></div>
          <p>${esc(t(lens === "canonical" ? "atlas.lens.canonicalHelp" : "atlas.lens.learnedHelp"))}</p>
        </section>
        ${relationMarkup(edges, lens)}
      </article>
      </section>
    </div>`;
}
