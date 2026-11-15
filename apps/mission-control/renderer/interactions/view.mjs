import { t } from "../foundation/i18n.mjs";

function esc(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function hookPart(value) {
  const normalized = String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  return normalized || "item";
}

function refLabel(ref) {
  return ref
    ? t("investigation.ref.label", { kind: ref.kind, label: ref.label ?? ref.id })
    : t("investigation.ref.empty");
}

function exactContext(ref) {
  return ref
    ? t("investigation.context.exact", { runId: ref.runId, generation: ref.generation })
    : t("investigation.context.empty");
}

function stateLabel(state) {
  return t(`investigation.state.${String(state).toLowerCase()}`);
}

function compareSlot(side, ref) {
  const label = t(`investigation.compare.${side}`);
  const clear = t(`investigation.compare.clear${side[0].toUpperCase()}${side.slice(1)}`);
  return `<div data-compare-side="${side}" data-test-id="investigation-compare-${side}">
    <dt>${esc(label)}</dt>
    <dd><strong>${esc(refLabel(ref))}</strong><span>${esc(exactContext(ref))}</span>
      ${ref ? `<button type="button" data-clear-compare="${side}" data-test-id="investigation-compare-clear-${side}">${esc(clear)}</button>` : ""}
    </dd>
  </div>`;
}

function compareMarkup(interaction, comparison) {
  return `<div class="investigation-compare" data-test-id="investigation-compare-workspace">
    <dl class="compare-slots" data-test-id="investigation-compare-slots">
      ${compareSlot("left", interaction.compare.left)}
      ${compareSlot("right", interaction.compare.right)}
    </dl>
    <p class="investigation-doctrine" data-compare-state="${esc(comparison.state)}" data-test-id="investigation-compare-state">
      <strong>${esc(stateLabel(comparison.state))}</strong><span>${esc(comparison.note)}</span>
    </p>
    ${comparison.rows.length ? `<div class="investigation-table-wrap" data-test-id="investigation-compare-table-wrap"><table class="investigation-table" data-test-id="investigation-compare-table">
      <thead><tr><th>${esc(t("investigation.compare.dimension"))}</th><th>${esc(t("investigation.compare.left"))}</th><th>${esc(t("investigation.compare.right"))}</th><th>${esc(t("investigation.compare.state"))}</th></tr></thead>
      <tbody>${comparison.rows.map((row) => `<tr data-state="${esc(row.state.toLowerCase())}" data-test-id="investigation-compare-row-${hookPart(row.key)}">
        <th>${esc(row.label)}</th><td>${esc(row.left)}</td><td>${esc(row.right)}</td>
        <td><strong>${esc(stateLabel(row.state))}</strong>${row.reason ? `<small>${esc(row.reason)}</small>` : ""}</td>
      </tr>`).join("")}</tbody>
    </table></div>` : ""}
  </div>`;
}

function pinsMarkup(metadata) {
  if (!metadata.pins.length) {
    return `<p class="investigation-empty" data-test-id="investigation-pins-empty">${esc(t("investigation.pins.empty"))}</p>`;
  }
  return `<ul class="pin-list" data-test-id="investigation-pins-list">${metadata.pins.map((pin, index) => `<li ${pin.kind ? `data-object-kind="${esc(pin.kind)}" data-object-id="${esc(pin.id)}"` : ""} data-test-id="investigation-pin-${index}">
    <div class="pin-identity"><strong>${esc(pin.label)}</strong><span>${esc(t("investigation.pins.context", { kind: pin.kind, generation: pin.generation }))}</span><code>${esc(pin.runId)}</code><code>${esc(pin.id)}</code></div>
    <div class="pin-actions"><button type="button" data-open-pin="${index}" data-test-id="investigation-pin-open-${index}">${esc(t("investigation.pins.open"))}</button><button type="button" data-remove-pin="${index}" data-test-id="investigation-pin-remove-${index}">${esc(t("investigation.pins.remove"))}</button></div>
  </li>`).join("")}</ul>`;
}

function annotationsMarkup(metadata, currentRef) {
  const notes = metadata.annotations.filter((note) =>
    !currentRef || (note.target.kind === currentRef.kind && note.target.id === currentRef.id &&
      note.target.runId === currentRef.runId && note.target.generation === currentRef.generation));
  return `<div class="annotation-workspace" data-test-id="investigation-notes-workspace">
    <ul class="annotation-list" data-test-id="investigation-notes-list">
      ${notes.length ? notes.map((note, index) => `<li data-test-id="investigation-note-${index}">
        <header><strong>${esc(t("investigation.notes.marker"))}</strong><small>${esc(note.author)} · ${new Date(note.createdAt).toISOString()} · ${esc(note.scope)}</small></header>
        <p>${esc(note.body)}</p>
        <small>${esc(t("investigation.notes.context", { kind: note.target.kind, id: note.target.id, runId: note.target.runId, generation: note.target.generation }))}</small>
      </li>`).join("") : `<li class="investigation-empty" data-test-id="investigation-notes-empty">${esc(t("investigation.notes.empty"))}</li>`}
    </ul>
    ${currentRef ? `<form data-annotation-form data-test-id="investigation-note-form">
      <label>${esc(t("investigation.notes.target", { id: currentRef.id }))}
        <textarea name="body" maxlength="2000" required data-test-id="investigation-note-body"></textarea>
      </label>
      <p>${esc(t("investigation.notes.help"))}</p>
      <button type="submit" data-test-id="investigation-note-save">${esc(t("investigation.notes.save"))}</button>
    </form>` : `<p data-test-id="investigation-note-select">${esc(t("investigation.notes.select"))}</p>`}
  </div>`;
}

function timeLensMarkup(state, currentAvailable) {
  const generation = state?.context.generation;
  const lens = state
    ? t(state.context.historicalPinned ? "investigation.time.historical" : "investigation.time.current", { generation })
    : t("investigation.context.empty");
  return `<details class="investigation-time" data-test-id="investigation-time-lens">
    <summary data-test-id="investigation-time-toggle"><span>${esc(t("investigation.time.label"))}</span><strong data-test-id="investigation-time-state">${esc(lens)}</strong></summary>
    <form data-time-lens-form data-test-id="investigation-time-form">
      <label>${esc(t("investigation.time.generation"))}
        <input name="generation" type="number" min="0" step="1" value="${state ? generation : ""}" ${state ? "" : "disabled"} data-test-id="investigation-time-generation" />
      </label>
      <div><button type="submit" ${state ? "" : "disabled"} data-test-id="investigation-time-apply">${esc(t("investigation.time.apply"))}</button>
      <button type="button" data-use-current ${currentAvailable ? "" : "disabled"} data-test-id="investigation-time-current">${esc(t("investigation.time.currentAction"))}</button></div>
    </form>
  </details>`;
}

export function renderInvestigationMarkup({ state, interaction, metadata, currentRef, comparison, currentAvailable }) {
  const panel = interaction.panel;
  const compareCount = Number(Boolean(interaction.compare.left)) + Number(Boolean(interaction.compare.right));
  const panelBody = panel === "compare" ? compareMarkup(interaction, comparison)
    : panel === "pins" ? pinsMarkup(metadata)
      : panel === "annotations" ? annotationsMarkup(metadata, currentRef)
        : "";
  return `<div class="investigation-strip-row" data-test-id="investigation-toolbar">
    ${timeLensMarkup(state, currentAvailable)}
    <div class="investigation-tabs" role="group" aria-label="${esc(t("investigation.toolbar.label"))}" data-test-id="investigation-tools">
      <button type="button" data-investigation-panel="compare" data-test-id="investigation-open-compare" aria-pressed="${panel === "compare"}">${esc(t("investigation.panel.compare", { count: compareCount }))}</button>
      <button type="button" data-investigation-panel="pins" data-test-id="investigation-open-pins" aria-pressed="${panel === "pins"}">${esc(t("investigation.panel.pins", { count: metadata.pins.length }))}</button>
      <button type="button" data-investigation-panel="annotations" data-test-id="investigation-open-notes" aria-pressed="${panel === "annotations"}">${esc(t("investigation.panel.notes", { count: metadata.annotations.length }))}</button>
    </div>
  </div>
  <section id="investigation-panel" aria-label="${esc(t("investigation.toolbar.label"))}" data-test-id="investigation-panel" ${panel === "closed" ? "hidden" : ""}>
    ${panelBody}
  </section>`;
}
