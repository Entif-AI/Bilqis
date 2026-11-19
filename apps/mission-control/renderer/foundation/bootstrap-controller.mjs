import {
  assertOperatorView,
  createShellState,
  normalizeContext,
  withDefensiveState,
} from "../shell-state.mjs";
import { parseDeepLink, routeFromState } from "../deep-link.mjs";
import {
  cacheOperatorView,
  defensiveState,
  defensiveStateForConnection,
  defensiveStateForError,
  loadCachedOperatorView,
} from "./defensive-state.mjs";
import { t } from "./i18n.mjs";

const SNAPSHOT_REQUEST = Object.freeze({
  schemaVersion: "bamf.gui20.operator-view-query/v1",
  schema: "bilqis.bamf.mission-control.operator-view/v1",
});
const SNAPSHOT_UNAVAILABLE_SCHEMA = "bamf.gui20.operator-view-unavailable/v1";

export function constrainRouteToLaunchMode(route, launchMode = "production") {
  if (!route) return route;
  const fixtureMode = launchMode === "fixtures";
  const selectedLooksFixture = typeof route.selected?.id === "string" &&
    /(^|:)fixture(:|$)/.test(route.selected.id);
  const originLooksFixture = typeof route.evidenceOrigin?.selected?.id === "string" &&
    /(^|:)fixture(:|$)/.test(route.evidenceOrigin.selected.id);
  const requestedFixture = route.context?.fixture === true;
  return {
    ...route,
    ...(route.context ? {
      context: Object.freeze({
        ...route.context,
        fixture: fixtureMode,
      }),
    } : {}),
    selected: !fixtureMode && (requestedFixture || selectedLooksFixture)
      ? null
      : route.selected ?? null,
    ...(!fixtureMode && (requestedFixture || originLooksFixture)
      ? { evidenceOrigin: null }
      : {}),
  };
}

export function createBootstrapController({
  api,
  launchMode = "production",
  storage,
  getState,
  setState,
  setDefense,
  setBootstrap,
  setVerifiedLiveContext,
  resetFrameShell,
  render,
  announce,
  currentHash,
  scheduleReconnect = (callback, delay) => globalThis.setTimeout(callback, delay),
  cancelReconnect = (token) => globalThis.clearTimeout(token),
  reconnectDelayMs = 1000,
}) {
  const fixtureMode = launchMode === "fixtures";
  let reconnectToken = null;

  function clearReconnect() {
    if (reconnectToken === null) return;
    cancelReconnect(reconnectToken);
    reconnectToken = null;
  }

  function armReconnect({ reuseConnection = false } = {}) {
    if (reconnectToken !== null) return;
    reconnectToken = scheduleReconnect(() => {
      reconnectToken = null;
      return establishSnapshot({ preserveRoute: true, reuseConnection });
    }, reconnectDelayMs);
  }

  async function establishSnapshot({ preserveRoute = false, reuseConnection = false } = {}) {
    clearReconnect();
    const current = getState();
    const quietRetry = reuseConnection && current !== null;
    if (!quietRetry) resetFrameShell();
    if (current) setState({ ...current, mutationAvailable: false });
    const requestedRoute = preserveRoute && current
      ? routeFromState(current)
      : parseDeepLink(currentHash());
    const route = constrainRouteToLaunchMode(requestedRoute, launchMode);
    if (!quietRetry) {
      setDefense(defensiveState("loading", {
        snapshotAvailable: Boolean(current),
        snapshotSource: current ? "previous" : "none",
      }));
      setBootstrap(Object.freeze({ phase: "connecting", connection: null, error: null }));
      render();
    }

    let connection = null;
    let connectError = null;
    try {
      connection = reuseConnection ? await api.status() : await api.connect();
      if (!quietRetry) {
        setBootstrap(Object.freeze({ phase: "discovering", connection, error: null }));
        render();
      }
    } catch (error) {
      connectError = error;
      setBootstrap(Object.freeze({ phase: "failed", connection: null, error }));
    }

    let operatorView = null;
    let snapshotSource = "none";
    let snapshotError = null;
    if (connection !== null) {
      try {
        const snapshot = await api.querySnapshot(SNAPSHOT_REQUEST);
        if (snapshot?.schemaVersion === SNAPSHOT_UNAVAILABLE_SCHEMA) {
          snapshotSource = "service";
        } else {
          assertOperatorView(snapshot);
          operatorView = snapshot;
          snapshotSource = "service";
          if (!fixtureMode) cacheOperatorView(storage, operatorView);
        }
      } catch (error) {
        operatorView = null;
        snapshotError = error;
      }
    }

    if (!fixtureMode && operatorView === null && current === null) {
      const cached = loadCachedOperatorView(storage);
      if (cached !== null) {
        try {
          assertOperatorView(cached.operatorView);
          operatorView = cached.operatorView;
          snapshotSource = "cache";
        } catch (error) {
          snapshotError ??= error;
        }
      }
    }

    if (operatorView === null && connection?.serviceLive === true) {
      const phase = connection.learnerReady === true ? "telemetry-pending" : "learner-unavailable";
      setBootstrap(Object.freeze({ phase, connection, error: snapshotError }));
      if (current) {
        setDefense(defensiveState("stale", {
          snapshotAvailable: true,
          snapshotSource: "previous",
        }));
        setState({ ...current, mutationAvailable: false });
      } else {
        setDefense(connection.learnerReady === true
          ? defensiveState("progressive", { snapshotAvailable: false, snapshotSource: "service" })
          : defensiveStateForConnection(connection.state, { snapshotAvailable: false, snapshotSource: "service" }));
        setState(null);
      }
      setVerifiedLiveContext(null);
      render();
      announce(connection.learnerReady === true
        ? t("foundation.bootstrap.announce.telemetryPending")
        : t("foundation.bootstrap.announce.learnerUnavailable"));
      armReconnect({ reuseConnection: true });
      return;
    }

    if (operatorView === null) {
      const options = {
        snapshotAvailable: Boolean(current),
        snapshotSource: current ? "previous" : "none",
      };
      let nextDefense = defensiveStateForError(snapshotError ?? connectError, options);
      if (current && ["unavailable", "unknown"].includes(nextDefense.id)) {
        nextDefense = defensiveState("stale", options);
      }
      setDefense(nextDefense);
      setState(current ? { ...current, mutationAvailable: false } : null);
      setVerifiedLiveContext(null);
      setBootstrap(Object.freeze({ phase: "failed", connection, error: snapshotError ?? connectError }));
      render();
      announce(t("foundation.bootstrap.announce.noSnapshot", { state: nextDefense.label }));
      armReconnect();
      return;
    }

    if (quietRetry) resetFrameShell();
    const options = { snapshotAvailable: true, snapshotSource };
    let nextDefense = snapshotError || connectError
      ? defensiveStateForError(snapshotError ?? connectError, options)
      : defensiveStateForConnection(connection?.state, options);
    if (snapshotSource === "cache" && ["live", "unavailable", "unknown"].includes(nextDefense.id)) {
      nextDefense = defensiveState("stale", options);
    }
    setDefense(nextDefense);
    setVerifiedLiveContext(!fixtureMode && snapshotSource === "service" && nextDefense.id === "live"
      ? normalizeContext(operatorView)
      : null);
    const shellState = withDefensiveState(createShellState(operatorView, route), nextDefense);
    setState({
      ...shellState,
      context: fixtureMode
        ? Object.freeze({ ...shellState.context, fixture: true })
        : shellState.context,
      mutationAvailable: fixtureMode ? false : shellState.mutationAvailable,
    });
    setBootstrap(Object.freeze({ phase: "ready", connection, error: null }));
    render();
    if (snapshotSource !== "service" || connection?.serviceLive !== true) armReconnect();
    announce(t(
      nextDefense.historical
        ? "foundation.bootstrap.announce.inspection"
        : "foundation.bootstrap.announce.live",
      { state: nextDefense.label },
    ));
  }

  return Object.freeze({ establishSnapshot });
}
