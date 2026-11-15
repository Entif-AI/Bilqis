import { escapeText as esc } from "../frames/frame-model.mjs";
import { buildAppUri } from "../interactions/app-uri.mjs";
import { DESTINATION_GROUPS, DESTINATIONS, shellPosture, isFixtureCorrectionSelection } from "../shell-state.mjs";
import { defensiveBannerMarkup } from "./defensive-state.mjs";
import { bindRovingNavigation } from "./accessibility.mjs";
import { renderCurrentView } from "./current-view.mjs";
import { t } from "./i18n.mjs";
import { contextHelpMarkup, controlClass } from "./primitives.mjs";
import { testIdAttribute } from "./test-hooks.mjs";

export { renderCurrentView } from "./current-view.mjs";

const destinationIds = new Set(DESTINATIONS.map(([id]) => id));
function compactIdentity(value) {
  return typeof value === "string" && /^[0-9a-f]{64}$/.test(value)
    ? `${value.slice(0, 8)}…${value.slice(-8)}`
    : value;
}

function destinationLabel(id) {
  if (!destinationIds.has(id)) throw new RangeError(`MISSION_CONTROL_DESTINATION_UNKNOWN:${id}`);
  return t(`shell.destination.${id}`);
}

export function inspectorEvidenceLabelKey(state, defense, fixtureCorrection = false) {
  if (fixtureCorrection || state?.context?.fixture === true) return "shell.inspector.fixture";
  const historical = state?.context?.mode === "HISTORICAL" ||
    state?.context?.historicalPinned === true || defense?.historical === true;
  return historical ? "shell.inspector.historicalEvidence" : "shell.inspector.currentEvidence";
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
  const label = t(labelKey);
  const accessible = t("shell.context.factExact", { label, value: exact });
  return `<span><small>${esc(label)}</small><strong title="${esc(exact)}" aria-label="${esc(accessible)}">${esc(compactIdentity(value))}</strong></span>`;
}

function shellStateLabel(value) {
  const key = {
    LIVE: "shell.context.mode.live",
    HISTORICAL: "shell.context.mode.historical",
    CONNECTED: "shell.context.freshness.connected",
    WAITING: "shell.context.freshness.waiting",
    FRESH: "shell.context.freshness.fresh",
    STALE: "shell.context.freshness.stale",
    DISCONNECTED: "shell.context.freshness.disconnected",
    UNKNOWN: "shell.context.freshness.unknown",
    READY: "shell.context.value.ready",
    CONNECTING: "shell.context.value.connecting",
    DISCOVERING: "shell.context.value.discovering",
    "NOT STARTED": "shell.context.value.notStarted",
    STARTING: "shell.context.value.starting",
    FAILED: "shell.context.value.failed",
    HEALTHY: "shell.context.value.healthy",
    "LEARNER-UNAVAILABLE": "shell.context.value.learnerUnavailable",
  }[String(value ?? "").toUpperCase()];
  return key ? t(key) : String(value ?? "");
}

export function renderContext(state, defense, bootstrap = null, launchMode = "production") {
  const shell = document.querySelector("#shell");
  shell.dataset.launchMode = launchMode;
  const contextBar = document.querySelector(".context-bar");
  const contextFacts = document.querySelector("#context-facts");
  document.querySelector("#context-help-host").innerHTML = contextHelpMarkup({
    label: t("shell.help.run.label"),
    description: t("shell.help.run.description"),
    testId: "shell-help-run-context",
  });
  contextBar.dataset.context = state ? "verified" : "empty";
  if (!state) {
    shell.dataset.posture = defense.id;
    const connection = bootstrap?.connection ?? null;
    document.querySelector("#mode-badge").textContent = launchMode === "fixtures"
      ? t("shell.launchMode.fixtures")
      : connection?.serviceLive ? t("shell.context.bootstrapMode") : t("shell.context.inspectionMode");
    document.querySelector("#run-id").textContent = connection?.runId ?? t("shell.context.discoveringLearner");
    document.querySelector("#generation-id").textContent = Number.isSafeInteger(connection?.generation)
      ? t("shell.context.generationBootstrap", { generation: connection.generation })
      : t("shell.context.generationUnknown");
    document.querySelector("#freshness").textContent = connection?.serviceLive
      ? shellStateLabel(connection?.learnerReady ? "CONNECTED" : "WAITING")
      : shellStateLabel(defense.freshness);
    const facts = [
      ["shell.context.fact.service", shellStateLabel(connection?.serviceReady ? "READY" : connection?.serviceLive ? "LIVE" : "WAITING")],
      ["shell.context.fact.learner", shellStateLabel(connection?.learnerReady ? "READY" : connection?.learnerState ?? "DISCOVERING")],
      ["shell.context.fact.optimizer", Number.isSafeInteger(connection?.optimizerStep) ? connection.optimizerStep : shellStateLabel("NOT STARTED")],
      ["shell.context.fact.telemetry", shellStateLabel(bootstrap?.phase === "telemetry-pending" ? "STARTING" : bootstrap?.phase ?? "WAITING")],
    ];
    contextFacts.innerHTML = facts.map(([labelKey, value]) => contextFactMarkup(labelKey, value)).join("");
    return;
  }
  const { context } = state;
  shell.dataset.posture = shellPosture(context);
  document.querySelector("#mode-badge").textContent = launchMode === "fixtures"
    ? t("shell.launchMode.fixtures")
    : shellStateLabel(context.mode);
  document.querySelector("#run-id").textContent = context.runId;
  document.querySelector("#run-id").title = context.runId;
  const generationIdentity = document.querySelector("#generation-id");
  generationIdentity.textContent = context.mode === "HISTORICAL"
    ? t("shell.context.generationHistorical", { generation: context.generation })
    : t("shell.context.generationCurrent", { generation: context.generation });
  document.querySelector("#freshness").textContent = shellStateLabel(context.freshness);
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
    const helpId = `nav-help-${group.helpKey.split(".").at(-1)}`;
    return `<section class="nav-group" aria-labelledby="${groupLabelId}" ${testIdAttribute("nav", "group", group.id)}>
      <div class="nav-group-heading">
        <h2 id="${groupLabelId}" class="nav-group-label">${esc(t(group.labelKey))}</h2>
        ${contextHelpMarkup({
          label: t(`${group.helpKey}.label`),
          description: t(`${group.helpKey}.description`),
          testId: helpId,
        })}
      </div>
      <div class="nav-group-items">${destinations}</div>
    </section>`;
  }).join("");
  nav.querySelectorAll("button[data-view]:not(:disabled)").forEach((button) => {
    button.addEventListener("click", () => onNavigate(button.dataset.view));
  });
  bindRovingNavigation(nav, "button[data-view]:not(:disabled)");
}

export function renderInspector(state, defense) {
  const panel = document.querySelector("#inspector");
  const splitter = document.querySelector("#inspector-splitter");
  const selected = state?.selected ?? null;
  const open = Boolean(state?.inspectorOpen);
  const narrowOverlay = open && globalThis.matchMedia?.("(max-width: 980px)")?.matches === true;
  document.querySelector("#shell").dataset.inspector = open ? "open" : "closed";
  panel.setAttribute("aria-hidden", String(!open));
  panel.inert = !open;
  if (narrowOverlay) panel.setAttribute("aria-modal", "true");
  else panel.removeAttribute("aria-modal");
  for (const background of [
    document.querySelector(".skip-link"),
    document.querySelector(".rail"),
    document.querySelector("#main-content"),
  ]) {
    if (background) background.inert = narrowOverlay;
  }
  splitter.setAttribute("aria-hidden", String(!open || narrowOverlay));
  splitter.tabIndex = open && !narrowOverlay ? 0 : -1;
  document.querySelector("#inspector-title").textContent = selected?.label ?? selected?.id ?? t("shell.inspector.noSelection");
  document.querySelector("#inspector-help-host").innerHTML = (
    open && state?.view === "learning"
  ) ? contextHelpMarkup({
      label: t("shell.inspector.learningHelp.label"),
      description: t("shell.inspector.learningHelp.description"),
      testId: "learning-inspector-help",
    }) : "";
  const fixtureCorrection = isFixtureCorrectionSelection(state);
  const evidencePosture = t(inspectorEvidenceLabelKey(state, defense, fixtureCorrection));
  const summary = document.querySelector("#inspector-summary");
  const exact = selected?.details
    ? Object.entries(selected.details).map(([label, value]) =>
      `<dt>${esc(label)}</dt><dd>${esc(Array.isArray(value) ? value.join(", ") : value)}</dd>`,
    ).join("")
    : "";
  summary.innerHTML = selected
    ? `<dt>${esc(t("shell.inspector.objectClass"))}</dt><dd>${esc(selected.kind)}</dd>
       <dt>${esc(t("shell.inspector.posture"))}</dt><dd>${esc(state.context.mode)}</dd>
       <dt>${esc(t("shell.inspector.evidence"))}</dt><dd>${esc(evidencePosture)}</dd>
       ${fixtureCorrection ? `<dt>${esc(t("shell.inspector.navigation"))}</dt><dd data-test-id="corrections-inspector-fixture-note">${esc(t("shell.inspector.fixtureNavigation"))}</dd>` : ""}`
    : "";
  document.querySelector("#inspector-details").innerHTML = selected
    ? `<dt>${esc(t("shell.inspector.run"))}</dt><dd>${esc(state.context.runId)}</dd>
       <dt>${esc(t("shell.inspector.generation"))}</dt><dd>${esc(state.context.generation)}</dd>
       <dt>${esc(t("shell.inspector.objectClass"))}</dt><dd>${esc(selected.kind)}</dd>
       <dt>${esc(t("shell.inspector.exactId"))}</dt><dd>${esc(selected.id)}</dd>${exact}`
    : "";
  const deepLink = selected ? buildAppUri({
    kind: selected.kind,
    id: selected.id,
    label: selected.label ?? selected.id,
    runId: state.context.runId,
    generation: state.context.generation,
    fixture: state.context.fixture === true,
  }) : "";
  document.querySelector("#inspector-deep-link-value").textContent = deepLink;
  document.querySelector("#copy-deep-link").disabled = !selected;
  document.querySelector("#open-owner").disabled = !selected || fixtureCorrection;
  document.querySelector("#open-evidence").disabled = !selected || fixtureCorrection;
}

export function renderPaletteOptions(state, onNavigate) {
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
  host.innerHTML = destinationGroups;
  host.querySelectorAll("button:not(:disabled)").forEach((button) => {
    button.addEventListener("click", () => onNavigate(button.dataset.view));
  });
  bindRovingNavigation(host);
}

function renderRailControl(shellPreferences) {
  const toggle = document.querySelector("#rail-toggle");
  const collapsed = shellPreferences?.rail === "collapsed";
  const label = t(collapsed ? "shell.nav.expand" : "shell.nav.collapse");
  toggle.setAttribute("aria-pressed", String(collapsed));
  toggle.setAttribute("aria-label", label);
  toggle.setAttribute("title", label);
  toggle.querySelector("[aria-hidden]")?.replaceChildren(collapsed ? "›" : "‹");
}

export function renderChrome(
  state,
  defense,
  displaySettings,
  shellPreferences,
  handlers,
  bootstrap = null,
) {
  localizeShellStatic();
  renderRailControl(shellPreferences);
  renderContext(state, defense, bootstrap, handlers.launchMode);
  renderDefensiveStatus(defense, handlers.onReconnect, bootstrap);
  renderNavigation(state, handlers.onNavigate);
  renderInspector(state, defense);
  renderCurrentView(
    state, defense, handlers.onInspect, handlers.api,
    handlers.onEvidenceSelect, handlers.onEvidenceReturn, bootstrap,
    handlers.fixtureSupport?.currentViews ?? null,
    handlers.onModelDiagnosticMode ?? null,
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
  document.querySelector("#context-controls-help-host").innerHTML = contextHelpMarkup({
    label: t("shell.help.contextControls.label"),
    description: t("shell.help.contextControls.description"),
    testId: "shell-help-context-controls",
  });
}
