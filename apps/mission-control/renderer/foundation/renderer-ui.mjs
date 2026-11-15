import { escapeText as esc } from "../frames/frame-model.mjs";
import { DESTINATION_GROUPS, DESTINATIONS, shellPosture } from "../shell-state.mjs";
import {
  currentMemoryGeneration,
  stableMemoryIdentity,
} from "../memory/memory-model.mjs";
import { defensiveBannerMarkup } from "./defensive-state.mjs";
import { bindRovingNavigation } from "./accessibility.mjs";
import { renderCurrentView } from "./current-view.mjs";
import { t } from "./i18n.mjs";
import { controlClass } from "./primitives.mjs";
import { testIdAttribute } from "./test-hooks.mjs";

export { renderCurrentView } from "./current-view.mjs";

const destinationIds = new Set(DESTINATIONS.map(([id]) => id));
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

function destinationLabel(id) {
  if (!destinationIds.has(id)) throw new RangeError(`MISSION_CONTROL_DESTINATION_UNKNOWN:${id}`);
  return t(`shell.destination.${id}`);
}

export function localizeShellStatic(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  root.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
  });
}

function contextFactMarkup(labelKey, value) {
  const exact = String(value);
  return `<span><small>${esc(t(labelKey))}</small><strong title="${esc(exact)}">${esc(compactIdentity(value))}</strong></span>`;
}

export function renderContext(state, defense, bootstrap = null) {
  const shell = document.querySelector("#shell");
  const contextBar = document.querySelector(".context-bar");
  const contextFacts = document.querySelector("#context-facts");
  contextBar.dataset.context = state ? "verified" : "empty";
  if (!state) {
    shell.dataset.posture = defense.id;
    const connection = bootstrap?.connection ?? null;
    document.querySelector("#mode-badge").textContent = connection?.serviceLive
      ? t("shell.context.bootstrapMode")
      : t("shell.context.inspectionMode");
    document.querySelector("#run-id").textContent = connection?.runId ?? t("shell.context.discoveringLearner");
    document.querySelector("#generation-id").textContent = Number.isSafeInteger(connection?.generation)
      ? t("shell.context.generationBootstrap", { generation: connection.generation })
      : t("shell.context.generationUnknown");
    document.querySelector("#freshness").textContent = connection?.serviceLive
      ? connection?.learnerReady ? "CONNECTED" : "WAITING"
      : defense.freshness;
    const facts = [
      ["shell.context.fact.service", connection?.serviceReady ? "READY" : connection?.serviceLive ? "LIVE" : "WAITING"],
      ["shell.context.fact.learner", connection?.learnerReady ? "READY" : connection?.learnerState ?? "DISCOVERING"],
      ["shell.context.fact.optimizer", Number.isSafeInteger(connection?.optimizerStep) ? connection.optimizerStep : "NOT STARTED"],
      ["shell.context.fact.telemetry", bootstrap?.phase === "telemetry-pending" ? "STARTING" : bootstrap?.phase ?? "WAITING"],
    ];
    contextFacts.innerHTML = facts.map(([labelKey, value]) => contextFactMarkup(labelKey, value)).join("");
    return;
  }
  const { context } = state;
  shell.dataset.posture = shellPosture(context);
  document.querySelector("#mode-badge").textContent = context.mode;
  document.querySelector("#run-id").textContent = context.runId;
  document.querySelector("#run-id").title = context.runId;
  const generationIdentity = document.querySelector("#generation-id");
  generationIdentity.textContent = context.mode === "HISTORICAL"
    ? t("shell.context.generationHistorical", { generation: context.generation })
    : t("shell.context.generationCurrent", { generation: context.generation });
  document.querySelector("#freshness").textContent = context.freshness;
  const facts = [
    ["shell.context.fact.manifest", context.generationManifest],
    ["shell.context.fact.topology", context.topologyId],
    ["shell.context.fact.factory", context.factoryRelease],
    ["shell.context.fact.semantic", context.semanticRelease],
    ["shell.context.fact.optimizer", context.optimizerStep],
    ["shell.context.fact.lease", context.admissionLease],
    ["shell.context.fact.frontier", context.correctionFrontier],
    ["shell.context.fact.resources", context.resourceHealth],
    ["shell.context.fact.coverage", context.coverage],
  ];
  contextFacts.innerHTML = facts.map(([labelKey, value]) => contextFactMarkup(labelKey, value)).join("");
}

export function renderDefensiveStatus(defense, onReconnect, bootstrap = null) {
  const host = document.querySelector("#defensive-banner");
  if (bootstrap && bootstrap.phase !== "ready") {
    const connection = bootstrap.connection;
    const detail = bootstrap.error?.code ?? bootstrap.error?.message ?? null;
    const copyKeys = {
      connecting: ["foundation.bootstrap.connecting.label", "foundation.bootstrap.connecting.description"],
      discovering: ["foundation.bootstrap.discovering.label", "foundation.bootstrap.discovering.description"],
      "telemetry-pending": ["foundation.bootstrap.telemetryPending.label", "foundation.bootstrap.telemetryPending.description"],
      "learner-unavailable": ["foundation.bootstrap.learnerUnavailable.label", "foundation.bootstrap.learnerUnavailable.description"],
      failed: ["foundation.bootstrap.failed.label", "foundation.bootstrap.failed.description"],
    }[bootstrap.phase] ?? ["foundation.bootstrap.starting.label", "foundation.bootstrap.starting.description"];
    const copy = copyKeys.map((key) => t(key));
    host.dataset.state = bootstrap.phase;
    host.setAttribute("role", bootstrap.phase === "failed" ? "alert" : "status");
    host.hidden = false;
    const reconnect = `<button type="button" data-reconnect data-test-id="foundation-reconnect">${esc(t("foundation.defensive.reconnect"))}</button>`;
    const detailParts = [];
    if (connection?.runId) detailParts.push(t("foundation.bootstrap.run", { runId: connection.runId }));
    if (Number.isSafeInteger(connection?.generation)) detailParts.push(t("foundation.bootstrap.generation", { generation: connection.generation }));
    detailParts.push(detail ? t("foundation.bootstrap.detail", { detail }) : t("foundation.bootstrap.noError"));
    host.innerHTML = `<div class="defensive-copy"><strong>${esc(copy[0])}</strong><span>${esc(copy[1])}</span><small>${esc(detailParts.join(" · "))}</small></div>${bootstrap.phase === "failed" || bootstrap.phase === "learner-unavailable" ? reconnect : ""}`;
    host.querySelector("[data-reconnect]")?.addEventListener("click", onReconnect);
    return;
  }
  host.dataset.state = defense.id;
  host.setAttribute("role", defense.role);
  host.hidden = defense.id === "live";
  host.innerHTML = defensiveBannerMarkup(defense);
  host.querySelector("[data-reconnect]")?.addEventListener("click", onReconnect);
}

export function renderNavigation(state, onNavigate) {
  const nav = document.querySelector("#primary-nav");
  nav.setAttribute("aria-label", t("shell.nav.label"));
  const active = state?.view ?? "mission-control";
  nav.innerHTML = DESTINATION_GROUPS.map((group) => {
    const groupLabelId = `nav-group-${group.id}-label`;
    const destinations = group.destinations.map((id) => {
      const blocked = !state || (id === "operate" && !state.mutationAvailable);
      const reason = id === "operate" && blocked
        ? ` title="${esc(t("shell.command.operateUnavailable"))}"`
        : "";
      return `<button type="button" class="${controlClass("navigate")}" data-view="${id}" data-focus-key="nav:${id}" aria-current="${active === id ? "page" : "false"}" ${testIdAttribute("nav", "destination", id)} ${blocked ? "disabled" : ""}${reason}>${esc(destinationLabel(id))}</button>`;
    }).join("");
    return `<section class="nav-group" aria-labelledby="${groupLabelId}" ${testIdAttribute("nav", "group", group.id)}>
      <h2 id="${groupLabelId}" class="nav-group-label">${esc(t(group.labelKey))}</h2>
      <div class="nav-group-items">${destinations}</div>
    </section>`;
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

export function renderPaletteOptions(state, onNavigate, onCommand = () => {}) {
  const host = document.querySelector("#palette-options");
  const destinationGroups = DESTINATION_GROUPS.map((group) => {
    const options = group.destinations.map((id) => {
      const blocked = !state || (id === "operate" && !state.mutationAvailable);
      const unavailable = id === "operate" && blocked
        ? `<small>${esc(t("shell.command.operateUnavailable"))}</small>`
        : "";
      return `<button type="button" class="${controlClass("navigate")}" data-view="${id}" data-focus-key="palette:${id}" ${testIdAttribute("palette", "destination", id)} ${blocked ? "disabled" : ""}><span>${esc(destinationLabel(id))}</span>${unavailable}</button>`;
    }).join("");
    return `<section class="palette-group" ${testIdAttribute("palette", "group", group.id)}>
      <h3>${esc(t(group.labelKey))}</h3>
      <div class="palette-group-items">${options}</div>
    </section>`;
  }).join("");
  host.innerHTML = `${destinationGroups}
    <section class="palette-group palette-command-group" ${testIdAttribute("palette", "group", "view-commands")}>
      <h3>${esc(t("shell.command.paletteViewCommands"))}</h3>
      <div class="palette-group-items">
        <button type="button" class="${controlClass("mode")}" data-palette-command="theme" ${testIdAttribute("palette", "command", "theme")}>${esc(t("shell.command.paletteToggleTheme"))}</button>
        <button type="button" class="${controlClass("mode")}" data-palette-command="density" ${testIdAttribute("palette", "command", "density")}>${esc(t("shell.command.paletteToggleDensity"))}</button>
      </div>
    </section>`;
  host.querySelectorAll("button:not(:disabled)").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.view) onNavigate(button.dataset.view);
      else if (button.dataset.paletteCommand) onCommand(button.dataset.paletteCommand);
    });
  });
  bindRovingNavigation(host);
}

export function renderChrome(state, defense, displaySettings, handlers, bootstrap = null) {
  localizeShellStatic();
  renderContext(state, defense, bootstrap);
  renderDefensiveStatus(defense, handlers.onReconnect, bootstrap);
  renderNavigation(state, handlers.onNavigate);
  renderInspector(state, defense);
  renderDemoActions(state, handlers.onInspect);
  renderCurrentView(
    state, defense, handlers.onInspect, handlers.api,
    handlers.onEvidenceSelect, handlers.onEvidenceReturn, bootstrap,
  );
  const currentView = state?.view ?? "mission-control";
  document.querySelector("#view-title").textContent = destinationLabel(currentView);
  document.querySelector("#view-title").setAttribute("tabindex", "-1");
  const posture = document.querySelector("#view-posture");
  posture.hidden = state?.context?.mode !== "HISTORICAL";
  posture.textContent = posture.hidden ? "" : t("shell.destination.posture.historical");
  document.querySelector("#theme-trigger").textContent = t("shell.settings.theme", { theme: displaySettings.theme });
  document.querySelector("#density-trigger").textContent = t("shell.settings.density", { density: displaySettings.density });
  document.querySelector("#theme-trigger").setAttribute("aria-label", t("shell.settings.themeAria", { theme: displaySettings.theme }));
  document.querySelector("#density-trigger").setAttribute("aria-label", t("shell.settings.densityAria", { density: displaySettings.density }));
}
