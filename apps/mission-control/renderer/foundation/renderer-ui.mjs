import { escapeText as esc } from "../frames/frame-model.mjs";
import { DESTINATIONS, shellPosture } from "../shell-state.mjs";
import {
  currentMemoryGeneration,
  stableMemoryIdentity,
} from "../memory/memory-model.mjs";
import { defensiveBannerMarkup } from "./defensive-state.mjs";
import { bindRovingNavigation } from "./accessibility.mjs";
import { renderCurrentView } from "./current-view.mjs";

export { renderCurrentView } from "./current-view.mjs";

const labels = new Map(DESTINATIONS);
const controllerSummaries = new Map([
  ["mission-control", "Outcome-first learner health, current work, learning pulse and actionable attention."],
  ["atlas", "Source-authoritative semantic identity and generation-scoped ABI state, with learned similarity isolated behind a separate lens."],
  ["capability", "Measured chronology, source support, and literal evidence. No inferred causes."],
  ["resources", "Measured resource budgets, decomposed where instrumented, with exact historical comparison and spike correlation."],
]);
const demoObjects = [
  ["capability", "B.AND"],
  ["episode", "episode-record:fixture:retained-44239"],
  ["semantic", "sem:logic.and"],
  ["frame", "frame:quad-fast"],
  ["memory", stableMemoryIdentity(currentMemoryGeneration().slots[0])],
  ["checkpoint", "generation:44238"],
  ["evidence", "receipt:fixture-001"],
  ["correction", "correction:fixture-1"],
  ["warning", "resource:disk-reserve"],
];

function compactIdentity(value) {
  return typeof value === "string" && /^[0-9a-f]{64}$/.test(value)
    ? `${value.slice(0, 8)}…${value.slice(-8)}`
    : value;
}

export function renderContext(state, defense) {
  const shell = document.querySelector("#shell");
  const contextBar = document.querySelector(".context-bar");
  const contextFacts = document.querySelector("#context-facts");
  contextBar.dataset.context = state ? "verified" : "empty";
  contextFacts.hidden = !state;
  if (!state) {
    shell.dataset.posture = defense.id;
    document.querySelector("#mode-badge").textContent = "INSPECTION";
    document.querySelector("#run-id").textContent = "No verified snapshot";
    document.querySelector("#generation-id").textContent = "Generation unavailable";
    document.querySelector("#freshness").textContent = defense.freshness;
    contextFacts.innerHTML = "";
    return;
  }
  const { context } = state;
  shell.dataset.posture = shellPosture(context);
  document.querySelector("#mode-badge").textContent = context.mode;
  document.querySelector("#run-id").textContent = context.runId;
  document.querySelector("#run-id").title = context.runId;
  const generationIdentity = document.querySelector("#generation-id");
  generationIdentity.textContent =
    `Generation ${context.generation} · manifest ${compactIdentity(context.generationManifest)}`;
  generationIdentity.setAttribute(
    "aria-label",
    `Generation ${context.generation}; manifest ${context.generationManifest}`,
  );
  document.querySelector("#freshness").textContent = context.freshness;
  document.querySelector("#run-selector").replaceChildren(new Option(context.runId, context.runId));
  const generations = context.fixture ? [1, 2, 3] : [context.generation];
  const generationSelector = document.querySelector("#generation-selector");
  generationSelector.replaceChildren(...generations.map((generation) =>
    new Option(`${generation} · ${generation === context.generation ? context.mode : "HISTORICAL"}`,
      String(generation), false, generation === context.generation)));
  generationSelector.disabled = !context.fixture;
  const facts = [
    ["Topology", context.topologyId], ["Factory", context.factoryRelease],
    ["Semantic", context.semanticRelease], ["Optimizer", context.optimizerStep],
    ["Lease", context.admissionLease], ["Frontier", context.correctionFrontier],
    ["Resources", context.resourceHealth], ["Coverage", context.coverage],
  ];
  contextFacts.innerHTML = facts
    .map(([label, value]) => `<span><small>${esc(label)}</small><strong title="${esc(value)}" aria-label="${esc(label)}: ${esc(value)}">${esc(compactIdentity(value))}</strong></span>`)
    .join("");
}

export function renderDefensiveStatus(defense, onReconnect) {
  const host = document.querySelector("#defensive-banner");
  host.dataset.state = defense.id;
  host.setAttribute("role", defense.role);
  host.hidden = defense.id === "live";
  host.innerHTML = defensiveBannerMarkup(defense);
  host.querySelector("[data-reconnect]")?.addEventListener("click", onReconnect);
}

export function renderNavigation(state, onNavigate) {
  const nav = document.querySelector("#primary-nav");
  nav.setAttribute("aria-label", "Mission Control destinations");
  const active = state?.view ?? "mission-control";
  nav.innerHTML = DESTINATIONS.map(([id, label]) => {
    const blocked = !state || (id === "operate" && !state.mutationAvailable);
    const reason = id === "operate" && blocked
      ? " title=\"Operate is unavailable until a verified live command context is re-established.\""
      : "";
    return `<button type="button" data-view="${id}" data-focus-key="nav:${id}" aria-current="${active === id ? "page" : "false"}" ${blocked ? "disabled" : ""}${reason}>${label}</button>`;
  }).join("");
  nav.querySelectorAll("button:not(:disabled)").forEach((button) => {
    button.addEventListener("click", () => onNavigate(button.dataset.view));
  });
  bindRovingNavigation(nav);
}

export function renderInspector(state, defense) {
  const panel = document.querySelector("#inspector");
  const selected = state?.selected ?? null;
  const open = Boolean(state?.inspectorOpen);
  document.querySelector("#shell").dataset.inspector = open ? "open" : "closed";
  panel.setAttribute("aria-hidden", String(!open));
  panel.inert = !open;
  document.querySelector("#inspector-title").textContent = selected ? selected.id : "No selection";
  const exact = selected?.details
    ? Object.entries(selected.details).map(([label, value]) =>
      `<dt>${esc(label)}</dt><dd>${esc(Array.isArray(value) ? value.join(", ") : value)}</dd>`,
    ).join("")
    : "";
  document.querySelector("#inspector-details").innerHTML = selected
    ? `<dt>Object class</dt><dd>${esc(selected.kind)}</dd>
       <dt>Identity</dt><dd>${esc(selected.id)}</dd>
       <dt>Posture</dt><dd>${state.context.mode}</dd>
       <dt>Generation</dt><dd>${state.context.generation}</dd>
       <dt>Evidence</dt><dd>${defense.historical ? "Verified prior evidence · inspection only" : "Current verified fixture/reference"}</dd>${exact}`
    : "";
  document.querySelector("#open-owner").disabled = !selected;
  document.querySelector("#open-evidence").disabled = !selected;
}

export function renderDemoActions(state, onInspect) {
  const host = document.querySelector("#demo-actions");
  if (!state) {
    host.innerHTML = "";
    return;
  }
  host.innerHTML = demoObjects
    .map(([kind, id]) => `<button type="button" data-kind="${kind}" data-id="${id}" data-focus-key="demo:${kind}:${id}">Inspect ${kind}</button>`)
    .join("");
  host.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => onInspect({
      kind: button.dataset.kind,
      id: button.dataset.id,
    }));
  });
}

export function renderPaletteOptions(state, onNavigate) {
  const host = document.querySelector("#palette-options");
  host.innerHTML = DESTINATIONS.map(([id, label]) => {
    const blocked = !state || (id === "operate" && !state.mutationAvailable);
    return `<button type="button" data-view="${id}" data-focus-key="palette:${id}" ${blocked ? "disabled" : ""}>${label}${id === "operate" && blocked ? " · unavailable offline" : ""}</button>`;
  }).join("");
  host.querySelectorAll("button:not(:disabled)").forEach((button) => {
    button.addEventListener("click", () => onNavigate(button.dataset.view));
  });
  bindRovingNavigation(host);
}

export function renderChrome(state, defense, displaySettings, handlers) {
  renderContext(state, defense);
  renderDefensiveStatus(defense, handlers.onReconnect);
  renderNavigation(state, handlers.onNavigate);
  renderInspector(state, defense);
  renderDemoActions(state, handlers.onInspect);
  renderCurrentView(
    state, defense, handlers.onInspect, handlers.api,
    handlers.onEvidenceSelect, handlers.onEvidenceReturn,
  );
  document.querySelector("#view-title").textContent = labels.get(state?.view ?? "mission-control");
  document.querySelector("#view-title").setAttribute("tabindex", "-1");
  document.querySelector("#theme-trigger").textContent = "Theme · " + displaySettings.theme;
  document.querySelector("#density-trigger").textContent = "Density · " + displaySettings.density;
  document.querySelector("#theme-trigger").setAttribute("aria-label", `Change theme. Current theme ${displaySettings.theme}`);
  document.querySelector("#density-trigger").setAttribute("aria-label", `Change information density. Current density ${displaySettings.density}`);
}
