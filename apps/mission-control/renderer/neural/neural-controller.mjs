import { t } from "../foundation/i18n.mjs";
import { loadNeuralRuntime } from "./neural-live.mjs";
import { productionNeuralMarkup } from "./neural-production-view.mjs";

function contextKey(context) {
  return context ? [context.runId, context.mode, context.generation].join(":") : "none";
}

export function createProductionNeuralController(api) {
  let key = null;
  let host = null;
  let context = null;
  let inspect = null;
  let model = null;
  let epoch = 0;

  function render() {
    if (!host) return;
    host.hidden = false;
    host.innerHTML = productionNeuralMarkup(model, context);
    host.querySelector("[data-neural-production-inspect]")?.addEventListener("click", () => {
      const snapshot = model?.snapshot;
      if (!snapshot || !inspect) return;
      inspect({
        kind: "neural",
        id: snapshot.recordId,
        label: snapshot.recordId,
        relations: [],
        details: {
          [t("model.neural.optimizerStep")]: snapshot.optimizerStep,
          [t("model.neural.production.coverage")]: snapshot.coverage,
          [t("model.neural.production.authority")]: snapshot.authority,
        },
      });
    });
  }

  async function activate(nextContext, { target, onInspect } = {}) {
    host = target;
    inspect = onInspect;
    context = nextContext;
    const nextKey = contextKey(nextContext);
    if (nextKey === key) { render(); return; }
    key = nextKey;
    const runEpoch = ++epoch;
    model = Object.freeze({ state: "LOADING", coverage: "UNKNOWN", snapshot: null });
    render();
    try {
      model = await loadNeuralRuntime(api, context);
    } catch (_error) {
      model = Object.freeze({ state: "UNAVAILABLE", coverage: "UNKNOWN", snapshot: null });
    }
    if (runEpoch === epoch) render();
  }

  function deactivate() {
    epoch += 1; key = null; host = null; context = null; inspect = null; model = null;
  }

  return Object.freeze({ activate, deactivate, state: () => model });
}
