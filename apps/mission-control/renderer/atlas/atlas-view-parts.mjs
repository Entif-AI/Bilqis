import { t } from "../foundation/i18n.mjs";
import { temporalMarkup } from "../foundation/temporal.mjs";
import { testIdAttribute } from "../foundation/test-hooks.mjs";

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

export const ATLAS_TABS = Object.freeze([
  Object.freeze(["lookup", "atlas.tab.lookup"]),
  Object.freeze(["abi", "atlas.tab.abi"]),
  Object.freeze(["dossier", "atlas.tab.dossier"]),
]);

export function tabMarkup(activeTab) {
  return ATLAS_TABS.map(([id, key]) => `<button type="button" role="tab"
    id="atlas-tab-${id}" data-atlas-tab="${id}" aria-controls="atlas-panel-${id}"
    aria-selected="${activeTab === id}" tabindex="${activeTab === id ? 0 : -1}"
    ${testIdAttribute("atlas", "tab", id)}>${esc(t(key))}</button>`).join("");
}

export function temporalFact(labelKey, unixSeconds, testId) {
  if (!Number.isSafeInteger(unixSeconds)) return "";
  return `<dt>${esc(t(labelKey))}</dt><dd>${temporalMarkup({ unixSeconds, testId })}</dd>`;
}

export function bankTable(banks, selectedBank) {
  if (!banks.length) {
    return `<p class="atlas-muted" ${testIdAttribute("atlas", "bank", "empty")}>${esc(t("atlas.abi.noBanks"))}</p>`;
  }
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

export function heldMappings(rows) {
  if (!rows.length) {
    return `<p class="atlas-muted" ${testIdAttribute("atlas", "held", "empty")}>${esc(t("atlas.lookup.noHeld"))}</p>`;
  }
  return `<ul class="atlas-held-list" ${testIdAttribute("atlas", "held", "list")}>
    ${rows.map((row, index) => `<li ${testIdAttribute("atlas", "held", index)}><code>${esc(row.key)}</code><span>${esc(row.reason_code)}</span></li>`).join("")}
  </ul>`;
}

export function relationMarkup(edges, lens) {
  const titleKey = lens === "canonical"
    ? "atlas.dossier.relationshipsCanonical"
    : "atlas.dossier.relationshipsLearned";
  const emptyKey = lens === "canonical" ? "atlas.dossier.noCanonical" : "atlas.dossier.noLearned";
  return `<section class="atlas-relations" aria-labelledby="atlas-relations-title" ${testIdAttribute("atlas", "semantic", "relations")}>
    <div class="atlas-section-heading"><h3 id="atlas-relations-title">${esc(t(titleKey))}</h3>
      <span class="atlas-evidence-label atlas-evidence-label--${lens === "canonical" ? "source" : "derived"}" data-authority="${lens === "canonical" ? "source" : "derived"}">${esc(t(lens === "canonical" ? "atlas.evidence.source" : "atlas.evidence.derived"))}</span></div>
    ${lens === "learned" ? `<p class="atlas-boundary">${esc(t("atlas.dossier.learnedBoundary"))}</p>` : ""}
    ${edges.length ? `<div class="atlas-table-wrap" tabindex="0" ${testIdAttribute("atlas", "semantic", "relation", "table", "wrap")}><table class="atlas-relation-table" ${testIdAttribute("atlas", "semantic", "relation", "table")}><thead><tr><th scope="col">${esc(t("atlas.dossier.relation"))}</th><th scope="col">${esc(t("atlas.dossier.targetIdentity"))}</th><th scope="col">${esc(t("atlas.dossier.evidence"))}</th></tr></thead><tbody>
      ${edges.map((edge, index) => `<tr data-edge-kind="${edge.kind}" ${testIdAttribute("atlas", "semantic", "relation", index)}>
        <td><code>${esc(edge.relation)}</code></td><td><code>${esc(edge.target)}</code></td>
        <td>${edge.kind === "learned" ? esc(t("atlas.dossier.similarityBasis", { basis: edge.basis ?? t("atlas.value.unknown") })) : esc(t("atlas.dossier.sourceRelationship"))}</td>
      </tr>`).join("")}</tbody></table></div>` : `<p class="atlas-muted">${esc(t(emptyKey))}</p>`}
  </section>`;
}
