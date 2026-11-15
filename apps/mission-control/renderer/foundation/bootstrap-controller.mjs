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

export function createBootstrapController({
  api,
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
  let reconnectToken = null;

  function clearReconnect() {
    if (reconnectToken === null) return;
    cancelReconnect(reconnectToken);
    reconnectToken = null;
  }

  function armReconnect() {
    if (reconnectToken !== null) return;
    reconnectToken = scheduleReconnect(() => {
      reconnectToken = null;
      return establishSnapshot({ preserveRoute: true });
    }, reconnectDelayMs);
  }

  async function establishSnapshot({ preserveRoute = false } = {}) {
    clearReconnect();
    const current = getState();
    const modelSection = current?.modelSection;
    resetFrameShell();
    if (current) setState({ ...current, mutationAvailable: false });
    const route = preserveRoute && current
      ? routeFromState(current)
      : parseDeepLink(currentHash());
    setDefense(defensiveState("loading", {
      snapshotAvailable: Boolean(current),
      snapshotSource: current ? "previous" : "none",
    }));
    setBootstrap(Object.freeze({ phase: "connecting", connection: null, error: null }));
    render();

    let connection = null;
    let connectError = null;
    try {
      connection = await api.connect();
      setBootstrap(Object.freeze({ phase: "discovering", connection, error: null }));
      render();
    } catch (error) {
      connectError = error;
      setBootstrap(Object.freeze({ phase: "failed", connection: null, error }));
    }

    let operatorView = null;
    let snapshotSource = "none";
    let snapshotError = null;
    if (connection !== null) {
      try {
        operatorView = await api.querySnapshot(SNAPSHOT_REQUEST);
        assertOperatorView(operatorView);
        snapshotSource = "service";
        cacheOperatorView(storage, operatorView);
      } catch (error) {
        snapshotError = error;
      }
    }

    if (operatorView === null && (connection === null || connection.serviceLive !== true)) {
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
      setDefense(connection.learnerReady === true
        ? defensiveState("progressive", { snapshotAvailable: false, snapshotSource: "service" })
        : defensiveStateForConnection(connection.state, { snapshotAvailable: false, snapshotSource: "service" }));
      setState(null);
      setVerifiedLiveContext(null);
      render();
      announce(connection.learnerReady === true
        ? t("foundation.bootstrap.announce.telemetryPending")
        : t("foundation.bootstrap.announce.learnerUnavailable"));
      armReconnect();
      return;
    }

    if (operatorView === null) {
      const nextDefense = defensiveStateForError(snapshotError ?? connectError, {
        snapshotAvailable: false,
        snapshotSource: "none",
      });
      setDefense(nextDefense);
      setState(null);
      setVerifiedLiveContext(null);
      setBootstrap(Object.freeze({ phase: "failed", connection, error: snapshotError ?? connectError }));
      render();
      announce(t("foundation.bootstrap.announce.noSnapshot", { state: nextDefense.label }));
      armReconnect();
      return;
    }

    const options = { snapshotAvailable: true, snapshotSource };
    let nextDefense = snapshotError || connectError
      ? defensiveStateForError(snapshotError ?? connectError, options)
      : defensiveStateForConnection(connection?.state, options);
    if (snapshotSource === "cache" && nextDefense.id === "live") {
      nextDefense = defensiveState("stale", options);
    }
    setDefense(nextDefense);
    setVerifiedLiveContext(snapshotSource === "service" && nextDefense.id === "live"
      ? normalizeContext(operatorView)
      : null);
    setState({ ...withDefensiveState(createShellState(operatorView, route), nextDefense), modelSection });
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
