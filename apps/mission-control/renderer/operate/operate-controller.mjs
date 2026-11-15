import {
  actionSpec,
  authorizationPhrase,
  buildPreviewRequest,
  buildSubmitRequest,
  contextConflicts,
  initialOperateState,
  parseParameters,
  terminalReceipt,
} from "./operate-model.mjs";
import { bindOperateInteractions, renderOperateMarkup } from "./operate-view.mjs";
import { t } from "../foundation/i18n.mjs";

function sameContext(left, right) {
  return Boolean(left && right) && left.runId === right.runId &&
    left.generation === right.generation && left.generationManifest === right.generationManifest &&
    left.factoryRelease === right.factoryRelease && left.semanticRelease === right.semanticRelease &&
    left.topologyId === right.topologyId && left.mode === right.mode;
}

function publicError(error) {
  return Object.freeze({
    code: typeof error?.code === "string" ? error.code : "GUI17_COMMAND_ERROR",
    message: typeof error?.message === "string" ? error.message : "Command boundary rejected the request.",
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

  function setState(next) {
    state = Object.freeze(next);
    render();
  }

  function render() {
    if (!host || !active) return;
    host.hidden = false;
    host.innerHTML = renderOperateMarkup(state, defense);
    bindOperateInteractions(host, {
      onAction: selectAction,
      onDryRun: (value) => setState({ ...state, dryRun: value, preview: null, inspection: null, conflicts: [], authorization: "", phase: "IDLE", error: null }),
      onParameters: (value) => { state = Object.freeze({ ...state, parametersText: value, preview: null, inspection: null, conflicts: [], authorization: "", phase: "IDLE", error: null }); },
      onAuthorization: (value) => setState({ ...state, authorization: value }),
      onPreview: preview,
      onSubmit: submit,
      onReconcile: reconcile,
      onOpenReceipt: openReceipt,
      onOpenPostcondition: openPostcondition,
    });
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
      setState({ ...state, error: publicError(error), phase: "ERROR" });
      return;
    }
    setState({ ...state, phase: "PREVIEWING", preview: null, inspection: null, conflicts: [], authorization: "", error: null });
    try {
      const request = buildPreviewRequest({ action: state.action, dryRun: state.dryRun, parameters, context });
      const reviewed = await api.requestDryRun(request);
      const conflicts = contextConflicts(context, reviewed);
      setState({
        ...state, preview: reviewed, conflicts, authorization: "",
        phase: conflicts.length ? "STALE_CONTEXT" : "REVIEW", error: null,
      });
      onAnnounce?.(conflicts.length ? "Preflight found stale context. Authorization blocked." : "Preflight complete. Review exact target and consequence.");
    } catch (error) {
      setState({ ...state, phase: "ERROR", error: publicError(error) });
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
    setState({ ...state, phase: "SUBMITTING", error: null });
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
      onAnnounce?.(`Command ${receipt.state.toLowerCase()}. Operation identity retained.`);
    } catch (_error) {
      setState({ ...state, phase: "LOST_ACK", inspection: null, error: null });
      onAnnounce?.("Command acknowledgement unavailable. No retry will be attempted; reconcile by operation identity.");
    }
  }

  async function reconcile() {
    const operationId = state.inspection?.operation_id ?? state.preview?.operation_id;
    if (!operationId) return;
    setState({ ...state, phase: "RECONCILING", error: null });
    try {
      const inspection = await api.fetchReceipt(operationId);
      setState({ ...state, inspection, phase: terminalReceipt(inspection.receipt?.state) ? "TERMINAL" : "PENDING", error: null });
      onAnnounce?.(`Operation readback: ${inspection.receipt?.state ?? "UNKNOWN"}.`);
    } catch (_error) {
      setState({ ...state, phase: "OUTCOME_UNKNOWN", inspection: null, error: null });
      onAnnounce?.("Operation is not yet reconcilable. No retry was issued.");
    }
  }

  function openReceipt() {
    const receipt = state.inspection?.receipt;
    if (!receipt) return;
    onInspect?.({
      kind: "operation", id: receipt.meta.record_id,
      details: {
        [t("shell.inspector.detail.operation")]: receipt.operation_id,
        [t("shell.inspector.detail.state")]: receipt.state,
        [t("shell.inspector.detail.target")]: receipt.target_ref,
        [t("shell.inspector.detail.postcondition")]: receipt.postcondition_ref ?? t("shell.inspector.value.unavailable"),
        [t("shell.inspector.detail.error")]: receipt.error_ref ?? t("shell.inspector.value.none"),
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
      document.querySelector("#domain-context-boundary").hidden = true;
      document.querySelector("#visual-catalog").hidden = true;
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
