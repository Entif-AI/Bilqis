import {
  actionSpec,
  authorizationPhrase,
  buildPreviewRequest,
  buildSubmitRequest,
  contextConflicts,
  initialOperateState,
  operateStageAvailable,
  parseParameters,
  terminalReceipt,
} from "./operate-model.mjs";
import { bindOperateInteractions, renderOperateMarkup } from "./operate-view.mjs";
import { operateT } from "./operate-messages.mjs";
import { t } from "../foundation/i18n.mjs";
import { focusToken, restoreFocus } from "../foundation/accessibility.mjs";

function sameContext(left, right) {
  return Boolean(left && right) && left.runId === right.runId &&
    left.generation === right.generation && left.generationManifest === right.generationManifest &&
    left.factoryRelease === right.factoryRelease && left.semanticRelease === right.semanticRelease &&
    left.topologyId === right.topologyId && left.mode === right.mode;
}

function publicError(error) {
  const code = typeof error?.code === "string" ? error.code
    : typeof error?.message === "string" && error.message.startsWith("GUI17_") ? error.message.split(":", 1)[0]
    : "GUI17_COMMAND_ERROR";
  const messageKey = code === "GUI17_PARAMETERS_JSON_INVALID" ? "operate.error.parametersJson"
    : code === "GUI17_PARAMETERS_OBJECT_REQUIRED" ? "operate.error.parametersObject"
    : code === "GUI17_PARAMETER_UNSUPPORTED" ? "operate.error.parameterUnsupported"
    : code === "GUI17_PARAMETER_SCALAR_REQUIRED" ? "operate.error.parameterScalar"
    : "operate.error.generic";
  return Object.freeze({
    code,
    message: operateT(messageKey),
  });
}

export function createOperateController(api) {
  let host = null;
  let context = null;
  let defense = null;
  let state = initialOperateState();
  let onInspect = null;
  let onAnnounce = null;
  let unsubscribe = null;
  let active = false;
  let activeTrainingOperationId = null;

  function setState(next, { focusStage = null } = {}) {
    const activeElement = typeof document !== "undefined" ? document.activeElement : null;
    const token = activeElement && typeof host?.contains === "function" && host.contains(activeElement)
      ? focusToken(activeElement)
      : null;
    state = Object.freeze(next);
    render();
    if (focusStage) {
      queueMicrotask(() => host?.querySelector(`[data-operate-stage="${focusStage}"]`)?.focus?.());
    } else if (token && typeof document !== "undefined") {
      queueMicrotask(() => restoreFocus(document, token, "#domain-view"));
    }
  }

  function render() {
    if (!host || !active) return;
    host.hidden = false;
    host.innerHTML = renderOperateMarkup(state, defense);
    bindOperateInteractions(host, {
      onAction: selectAction,
      onStage: selectStage,
      onDryRun: (value) => setState({ ...state, activeStage: "request", dryRun: value, preview: null, inspection: null, conflicts: [], authorization: "", phase: "IDLE", error: null }),
      onParameters: (value) => { state = Object.freeze({ ...state, activeStage: "request", parametersText: value, preview: null, inspection: null, conflicts: [], authorization: "", phase: "IDLE", error: null }); },
      onAuthorization: (value) => {
        state = Object.freeze({ ...state, authorization: value });
        const submit = host?.querySelector("[data-operate-submit]");
        if (submit && state.preview?.consequence?.mutation === "MUTATING") {
          submit.disabled = state.authorization !== authorizationPhrase(state.preview) ||
            state.conflicts.length > 0 || state.phase === "SUBMITTING";
        }
      },
      onPreview: preview,
      onSubmit: submit,
      onReconcile: reconcile,
      onOpenReceipt: openReceipt,
      onOpenPostcondition: openPostcondition,
    });
  }

  function selectStage(stage) {
    if (!operateStageAvailable(state, stage)) return;
    setState({ ...state, activeStage: stage }, { focusStage: stage });
  }

  function selectAction(action) {
    const spec = actionSpec(action);
    if (!spec?.supported) return;
    const parametersText = action === "stop" && activeTrainingOperationId
      ? JSON.stringify({ operation_id: activeTrainingOperationId }, null, 2)
      : "{}";
    setState({
      ...initialOperateState(), action,
      dryRun: spec.dryRun && spec.mutation,
      parametersText,
    });
  }

  async function preview() {
    if (!defense?.mutationAllowed || state.phase === "PREVIEWING" || state.phase === "SUBMITTING") return;
    let parameters;
    try {
      parameters = parseParameters(state.parametersText);
    } catch (error) {
      setState({ ...state, activeStage: "request", error: publicError(error), phase: "ERROR" });
      return;
    }
    setState({ ...state, activeStage: "preflight", phase: "PREVIEWING", preview: null, inspection: null, conflicts: [], authorization: "", error: null }, { focusStage: "preflight" });
    try {
      const request = buildPreviewRequest({ action: state.action, dryRun: state.dryRun, parameters, context });
      const reviewed = await api.requestDryRun(request);
      const conflicts = contextConflicts(context, reviewed);
      setState({
        ...state, activeStage: "preflight", preview: reviewed, conflicts, authorization: "",
        phase: conflicts.length ? "STALE_CONTEXT" : "REVIEW", error: null,
      });
      onAnnounce?.(operateT(conflicts.length ? "operate.announce.stale" : "operate.announce.ready"));
    } catch (error) {
      setState({ ...state, activeStage: "preflight", phase: "ERROR", error: publicError(error) });
    }
  }

  async function submit() {
    if (!defense?.mutationAllowed || !state.preview || state.conflicts.length || state.phase === "SUBMITTING") return;
    if (state.preview.consequence?.mutation === "MUTATING" &&
        state.authorization !== authorizationPhrase(state.preview)) return;
    const request = buildSubmitRequest(state.preview);
    if (["create", "owner-launch", "resume"].includes(state.action)) {
      activeTrainingOperationId = state.preview.operation_id;
    }
    setState({ ...state, activeStage: "outcome", phase: "SUBMITTING", error: null }, { focusStage: "outcome" });
    try {
      const receipt = await api.requestCommand(request);
      let inspection;
      try {
        inspection = await api.fetchReceipt(receipt.operation_id);
      } catch (_error) {
        inspection = null;
      }
      if (inspection) {
        if (["create", "owner-launch", "resume"].includes(state.action) &&
            terminalReceipt(inspection.receipt?.state)) {
          activeTrainingOperationId = null;
        }
        setState({ ...state, inspection, phase: terminalReceipt(inspection.receipt?.state) ? "TERMINAL" : "PENDING", error: null });
      } else {
        setState({ ...state, phase: "LOST_ACK", error: null });
      }
      onAnnounce?.(operateT("operate.announce.command", { state: String(receipt.state).toLowerCase() }));
    } catch (_error) {
      setState({ ...state, phase: "LOST_ACK", inspection: null, error: null });
      onAnnounce?.(operateT("operate.announce.lost"));
    }
  }

  async function reconcile() {
    const operationId = state.inspection?.operation_id ?? state.preview?.operation_id;
    if (!operationId) return;
    setState({ ...state, activeStage: "outcome", phase: "RECONCILING", error: null }, { focusStage: "outcome" });
    try {
      const inspection = await api.fetchReceipt(operationId);
      if (["create", "owner-launch", "resume"].includes(state.action) &&
          terminalReceipt(inspection.receipt?.state)) {
        activeTrainingOperationId = null;
      }
      setState({ ...state, inspection, phase: terminalReceipt(inspection.receipt?.state) ? "TERMINAL" : "PENDING", error: null });
      onAnnounce?.(operateT("operate.announce.readback", { state: inspection.receipt?.state ?? operateT("operate.value.unknown") }));
    } catch (_error) {
      setState({ ...state, phase: "OUTCOME_UNKNOWN", inspection: null, error: null });
      onAnnounce?.(operateT("operate.announce.unknown"));
    }
  }

  function openReceipt() {
    const receipt = state.inspection?.receipt;
    if (!receipt) return;
    onInspect?.({
      kind: "operation", id: receipt.meta.record_id,
      details: {
        [operateT("operate.inspector.operation")]: receipt.operation_id,
        [operateT("operate.inspector.state")]: receipt.state,
        [operateT("operate.inspector.target")]: receipt.target_ref,
        [operateT("operate.inspector.postcondition")]: receipt.postcondition_ref ?? operateT("operate.value.unavailable"),
        [operateT("operate.inspector.error")]: receipt.error_ref ?? operateT("operate.value.none"),
      },
    });
  }

  function openPostcondition() {
    const inspection = state.inspection;
    if (!inspection?.postcondition) return;
    onInspect?.({
      kind: "operation",
      id: inspection.receipt?.postcondition_ref ?? `${inspection.operation_id}:postcondition`,
      details: Object.fromEntries(Object.entries(inspection.postcondition).map(([key, value]) => [key, typeof value === "object" ? JSON.stringify(value) : value])),
    });
  }

  async function subscribe() {
    if (typeof api.subscribeEvents !== "function") return;
    try {
      unsubscribe = api.subscribeEvents((event) => {
        const operationId = state.inspection?.operation_id ?? state.preview?.operation_id;
        if (event?.event_family !== "operator.action.state" || !operationId ||
            !String(event.payload_record_id ?? "").includes(operationId)) return;
        void reconcile();
      });
    } catch (_error) {
      unsubscribe = null;
    }
  }

  async function activate(nextContext, options = {}) {
    const changed = !sameContext(context, nextContext);
    context = nextContext;
    defense = options.defense;
    host = options.target;
    onInspect = options.onInspect;
    onAnnounce = options.onAnnounce;
    active = true;
    if (typeof document !== "undefined") {
      document.querySelector("#view-summary").textContent = t("shell.destination.operate.purpose");
    }
    if (changed) state = initialOperateState();
    render();
    if (!unsubscribe && defense?.mutationAllowed) await subscribe();
  }

  async function deactivate() {
    active = false;
    host = null;
    const stop = unsubscribe;
    unsubscribe = null;
    if (typeof stop === "function") await stop();
  }

  function currentState() { return state; }

  return Object.freeze({ activate, deactivate, currentState, preview, submit, reconcile });
}
