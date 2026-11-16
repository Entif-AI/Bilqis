import { loadTeacherSnapshot } from "./teacher-live.mjs";
import { productionTeacherMarkup } from "./teacher-production-view.mjs";
import { bindTeacherTabs, TEACHER_TABS } from "./teacher-tabs.mjs";
import { t } from "../foundation/i18n.mjs";

function contextKey(context, launchMode) {
  if (!context) return `${launchMode}:none`;
  return [launchMode, context.runId, context.mode, context.generation].join(":");
}

export function createTeacherController(api, { fixtureSupport = null } = {}) {
  let key = null;
  let host = null;
  let inspect = null;
  let context = null;
  let launchMode = "production";
  let model = null;
  let activeTab = "roster";
  let epoch = 0;

  function inspectProduction(snapshot) {
    if (!snapshot || !inspect) return;
    inspect({
      kind: "strategy",
      id: snapshot.strategyId,
      label: snapshot.strategyId,
      relations: [],
      details: {
        [t("teacher.inspector.teacherIdentity")]: snapshot.teacherIdentity,
        [t("teacher.inspector.teacherEpoch")]: snapshot.teacherEpoch,
        [t("teacher.inspector.attempts")]: snapshot.attempts ?? t("teacher.value.unavailable"),
        [t("teacher.inspector.accepted")]: snapshot.accepted ?? t("teacher.value.unavailable"),
        [t("teacher.inspector.rejected")]: snapshot.rejected ?? t("teacher.value.unavailable"),
      },
    });
  }

  function renderProduction() {
    if (!host) return;
    host.hidden = false;
    host.innerHTML = productionTeacherMarkup(model, { activeTab });
    bindTeacherTabs(host, (tab) => {
      if (!TEACHER_TABS.includes(tab) || tab === activeTab) return;
      activeTab = tab;
      renderProduction();
      host.querySelector(`[data-teacher-tab="${tab}"]`)?.focus({ preventScroll: true });
    });
    host.querySelector("[data-production-strategy-inspect]")?.addEventListener("click", () => {
      inspectProduction(model?.snapshot ?? null);
    });
  }

  function renderFixture(selectedId = null) {
    if (!host || !fixtureSupport?.renderTeacherView) return;
    host.hidden = false;
    fixtureSupport.renderTeacherView(host, (id, strategy, relations) => inspect?.({
      kind: "strategy",
      id,
      label: strategy?.label ?? id,
      relations,
      details: {
        [t("teacher.inspector.role")]: strategy?.role ?? "UNKNOWN",
        [t("teacher.inspector.attempts")]: strategy?.attempts ?? "UNKNOWN",
        [t("teacher.inspector.retained")]: strategy?.retained ?? "UNKNOWN",
        [t("teacher.inspector.noGain")]: strategy?.noGain ?? "UNKNOWN",
        [t("teacher.inspector.interference")]: strategy?.interference ?? "UNKNOWN",
        [t("teacher.inspector.comparisonPosture")]: t("teacher.inspector.descriptiveOnly"),
        [t("teacher.inspector.policyMutation")]: t("teacher.inspector.none"),
      },
    }), selectedId);
  }

  async function load(runEpoch) {
    try {
      model = await loadTeacherSnapshot(api, context);
    } catch (_error) {
      model = Object.freeze({ state: "UNAVAILABLE", coverage: "UNKNOWN", snapshot: null });
    }
    if (runEpoch !== epoch) return;
    renderProduction();
  }

  async function activate(nextContext, { target, onInspect, selected = null, mode = "production" } = {}) {
    const nextMode = mode === "fixtures" ? "fixtures" : "production";
    const nextKey = contextKey(nextContext, nextMode);
    host = target;
    inspect = onInspect;
    context = nextContext;
    launchMode = nextMode;
    if (nextKey === key) {
      if (launchMode === "fixtures") renderFixture(selected?.kind === "strategy" ? selected.id : null);
      else renderProduction();
      return;
    }
    key = nextKey;
    const runEpoch = ++epoch;
    if (launchMode === "fixtures") {
      model = null;
      renderFixture(selected?.kind === "strategy" ? selected.id : null);
      return;
    }
    model = Object.freeze({ state: "LOADING", coverage: "UNKNOWN", snapshot: null });
    renderProduction();
    await load(runEpoch);
  }

  function deactivate() {
    epoch += 1;
    key = null;
    host = null;
    inspect = null;
    context = null;
    model = null;
  }

  return Object.freeze({ activate, deactivate, state: () => ({ model, activeTab, launchMode }) });
}
