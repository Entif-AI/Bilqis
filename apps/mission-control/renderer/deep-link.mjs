export function parseDeepLink(hash = "") {
  const value = hash.replace(/^#\/?/, "");
  const [path, query = ""] = value.split("?");
  const [, view = "mission-control"] = path.split("/");
  const params = new URLSearchParams(query);
  const kind = params.get("kind");
  const id = params.get("id");
  const generation = Number(params.get("generation"));
  const context = params.has("run") && params.has("generation") &&
    Number.isSafeInteger(generation) && generation >= 0 && ["LIVE", "HISTORICAL"].includes(params.get("mode"))
    ? {
      runId: params.get("run"),
      generation,
      mode: params.get("mode"),
      fixture: params.get("fixture") === "true",
      historicalPinned: params.get("mode") === "HISTORICAL",
    } : null;
  const originView = params.get("originView");
  const originKind = params.get("originKind");
  const originId = params.get("originId");
  const modelSection = params.get("section");
  const modelDiagnosticMode = params.get("diagnostic");
  const route = {
    ...(context ? { context } : {}),
    view,
    selected: kind && id ? { kind, id } : null,
    ...(view === "model" && ["neural", "frames"].includes(modelSection)
      ? { modelSection } : {}),
    ...(view === "model" && ["current", "historical"].includes(modelDiagnosticMode)
      ? { modelDiagnosticMode } : {}),
  };
  if (originView) {
    route.evidenceOrigin = {
      view: originView,
      selected: originKind && originId ? { kind: originKind, id: originId } : null,
      inspectorOpen: params.get("originInspector") === "1",
    };
  }
  return route;
}

export function buildDeepLink(state) {
  const params = new URLSearchParams();
  if (state.selected?.kind) params.set("kind", state.selected.kind);
  if (state.selected?.id) params.set("id", state.selected.id);
  if (state.context) {
    params.set("run", state.context.runId);
    params.set("generation", state.context.generation);
    params.set("mode", state.context.historicalPinned ? "HISTORICAL" : "LIVE");
    if (state.context.fixture) params.set("fixture", "true");
  }
  if (state.view === "model" && ["neural", "frames"].includes(state.modelSection)) {
    params.set("section", state.modelSection);
  }
  if (state.view === "model" && ["current", "historical"].includes(state.modelDiagnosticMode)) {
    params.set("diagnostic", state.modelDiagnosticMode);
  }
  if (state.view === "evidence" && state.evidenceOrigin?.view) {
    params.set("originView", state.evidenceOrigin.view);
    if (state.evidenceOrigin.selected?.kind) {
      params.set("originKind", state.evidenceOrigin.selected.kind);
    }
    if (state.evidenceOrigin.selected?.id) {
      params.set("originId", state.evidenceOrigin.selected.id);
    }
    if (state.evidenceOrigin.inspectorOpen) params.set("originInspector", "1");
  }
  const query = params.toString();
  return `#/view/${state.view}${query ? `?${query}` : ""}`;
}

export function routeFromState(state) {
  return parseDeepLink(buildDeepLink(state));
}
