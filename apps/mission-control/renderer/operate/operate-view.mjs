import {
  OPERATE_ACTIONS,
  actionSpec,
  authorizationPhrase,
  terminalReceipt,
} from "./operate-model.mjs";
import { operateT as t } from "./operate-messages.mjs";
import { controlClass } from "../foundation/primitives.mjs";
import { assertUniqueTestIds, testIdAttribute } from "../foundation/test-hooks.mjs";

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[char]));
}

function short(value) {
  if (value === null || value === undefined) return t("operate.value.unavailable");
  const text = String(value);
  return /^[0-9a-f]{64}$/.test(text) ? `${text.slice(0, 9)}…${text.slice(-9)}` : text;
}

function stateBadge(state, testId = "state") {
  const literal = state ?? t("operate.value.unknown");
  const token = String(literal).toLowerCase().replaceAll("_", "-").replaceAll(" ", "-");
  return `<span class="operate-state" data-operate-state="${esc(token)}" ${testIdAttribute("operate", testId)}>${esc(literal)}</span>`;
}

function stageHeader(stepKey, eyebrowKey, title, state = null, hook = "stage") {
  return `<header class="operate-stage-header" ${testIdAttribute("operate", hook, "heading")}>
    <span class="operate-step" aria-hidden="true">${esc(t(stepKey))}</span>
    <div><span class="eyebrow">${esc(t(eyebrowKey))}</span><h3>${esc(title)}</h3></div>
    ${state ? stateBadge(state, `${hook}-state`) : ""}
  </header>`;
}

function actionCatalog(state) {
  return `<section class="operate-catalog" aria-labelledby="operate-catalog-title" ${testIdAttribute("operate", "catalog")}>
    <header><h3 id="operate-catalog-title">${esc(t("operate.catalog.title"))}</h3><p>${esc(t("operate.catalog.summary"))}</p></header>
    <div class="operate-action-list" role="list">
      ${OPERATE_ACTIONS.map((item) => {
        const posture = !item.supported ? "unavailable" : item.mutation ? "authorization" : "read-only";
        return `<button type="button" class="${controlClass(item.mutation ? "mutate" : "secondary")} operate-action"
          data-operate-action="${esc(item.id)}" data-posture="${posture}" aria-pressed="${state.action === item.id}"
          ${testIdAttribute("operate", "action", item.id)} ${item.supported ? "" : "disabled"}>
          <span class="operate-action-copy"><strong>${esc(t(`operate.action.${item.id}.label`))}</strong><small>${esc(t(`operate.action.${item.id}.description`))}</small></span>
          <span class="operate-action-posture">${esc(t(`operate.posture.${posture === "authorization" ? "authorization" : posture === "read-only" ? "readOnly" : "unavailable"}`))}</span>
        </button>`;
      }).join("")}
    </div>
  </section>`;
}

function parameterError(state) {
  if (state.phase !== "ERROR" || !String(state.error?.code ?? "").startsWith("GUI17_PARAMETER")) return "";
  return `<div class="operate-inline-error" role="alert" ${testIdAttribute("operate", "request", "validation")}><strong>${esc(state.error.code)}</strong><span>${esc(state.error.message)}</span></div>`;
}

function parameterPanel(state, commandAvailable = true) {
  const spec = actionSpec(state.action);
  const dryRun = spec?.dryRun
    ? `<label class="operate-check"><input type="checkbox" data-operate-dry-run ${testIdAttribute("operate", "request", "dry-run")} ${state.dryRun ? "checked" : ""} /> ${esc(t("operate.request.dryRun"))}</label>`
    : "";
  const title = spec ? t(`operate.action.${spec.id}.label`) : t("operate.catalog.title");
  return `<section class="operate-stage operate-request" ${testIdAttribute("operate", "request")}>
    ${stageHeader("operate.request.step", "operate.request.eyebrow", title, state.phase, "request")}
    <p class="operate-stage-summary">${esc(spec ? t(`operate.action.${spec.id}.description`) : "")}</p>
    ${dryRun}
    <label class="operate-json">${esc(t("operate.request.parameters"))}
      <textarea data-operate-parameters ${testIdAttribute("operate", "request", "parameters")} rows="6" spellcheck="false">${esc(state.parametersText)}</textarea>
    </label>
    ${parameterError(state)}
    <p class="operate-hint">${esc(t("operate.request.hint"))}</p>
    <button type="button" class="${controlClass("primary")}" data-operate-preview ${testIdAttribute("operate", "request", "preview")} ${spec?.supported && commandAvailable ? "" : "disabled"}>${esc(t("operate.request.preview"))}</button>
  </section>`;
}

function targetFact(label, value, hook) {
  return `<div class="operate-fact" ${testIdAttribute("operate", "preflight", "fact", hook)}><dt>${esc(label)}</dt><dd title="${esc(value)}">${esc(short(value))}</dd></div>`;
}

function previewPanel(state) {
  const preview = state.preview;
  if (!preview) return `<section class="operate-stage operate-preflight is-pending" ${testIdAttribute("operate", "preflight")}>
    ${stageHeader("operate.preflight.step", "operate.preflight.eyebrow", t("operate.preflight.emptyTitle"), null, "preflight")}
    <p class="operate-stage-summary">${esc(t("operate.preflight.empty"))}</p>
  </section>`;
  const target = preview.target ?? {};
  const profile = preview.preflight?.resource_profile ?? {};
  const mutating = preview.consequence?.mutation === "MUTATING";
  const conflicts = state.conflicts ?? [];
  const consequenceKey = mutating ? "mutating" : "readOnly";
  const conflictKey = (label) => ({
    run: "run",
    generation: "generation",
    "generation manifest": "generationManifest",
    topology: "topology",
    "Factory release": "factoryRelease",
    "semantic release": "semanticRelease",
  }[label] ?? null);
  return `<section class="operate-stage operate-preflight" data-command-consequence="${mutating ? "mutating" : "read-only"}" ${testIdAttribute("operate", "preflight")}>
    ${stageHeader("operate.preflight.step", "operate.preflight.eyebrow", t("operate.preflight.title"), preview.mode ?? t("operate.value.unknown"), "preflight")}
    <div class="operate-consequence" data-posture="${mutating ? "mutating" : "read-only"}" ${testIdAttribute("operate", "preflight", "consequence")}>
      <strong>${esc(t(`operate.preflight.${consequenceKey}`))}</strong><span>${esc(t(`operate.preflight.${consequenceKey}Detail`))}</span>
    </div>
    <dl class="operate-facts" ${testIdAttribute("operate", "preflight", "facts")}>
      ${targetFact(t("operate.fact.targetRef"), preview.target_ref, "target-ref")}
      ${targetFact(t("operate.fact.run"), target.run_id, "run")}
      ${targetFact(t("operate.fact.generation"), target.generation, "generation")}
      ${targetFact(t("operate.fact.generationManifest"), target.generation_manifest_sha256, "manifest")}
      ${targetFact(t("operate.fact.topology"), target.topology_sha256, "topology")}
      ${targetFact(t("operate.fact.factory"), target.factory_release_sha256, "factory")}
      ${targetFact(t("operate.fact.semantic"), target.semantic_release_sha256, "semantic")}
      ${targetFact(t("operate.fact.source"), target.source_identity, "source")}
      ${targetFact(t("operate.fact.admission"), preview.preflight?.admission_policy, "admission")}
      ${targetFact(t("operate.fact.postcondition"), preview.expected_postcondition, "postcondition")}
    </dl>
    ${Object.keys(profile).length ? `<details class="ui-disclosure operate-resource-profile" ${testIdAttribute("operate", "preflight", "resources")}><summary>${esc(t("operate.preflight.resources"))}</summary><dl class="operate-resource-grid">${Object.entries(profile).map(([key, value]) => targetFact(key.replaceAll("_", " "), value, `resource-${key.replaceAll("_", "-")}`)).join("")}</dl></details>` : ""}
    ${conflicts.length ? `<div class="operate-blocker" role="alert" ${testIdAttribute("operate", "preflight", "stale")}><strong>${esc(t("operate.stale.title"))}</strong><ul>${conflicts.map((item) => { const key = conflictKey(item.label); const label = key ? t(`operate.stale.${key}`) : item.label; return `<li>${esc(t("operate.stale.item", { label, expected: short(item.expected), actual: short(item.actual) }))}</li>`; }).join("")}</ul><span>${esc(t("operate.stale.recovery"))}</span></div>` : ""}
  </section>`;
}

function authorizePanel(state) {
  const preview = state.preview;
  if (!preview) return "";
  const mutating = preview.consequence?.mutation === "MUTATING";
  const phrase = authorizationPhrase(preview);
  const blocked = (state.conflicts?.length ?? 0) > 0 || state.phase === "SUBMITTING";
  const authorized = !mutating || state.authorization === phrase;
  const submitKey = preview.request?.dry_run ? "submitDryRun" : mutating ? "submitMutating" : "submitReadOnly";
  return `<section class="operate-stage operate-authorization" data-posture="${mutating ? "mutating" : "read-only"}" ${testIdAttribute("operate", "authorization")}>
    ${stageHeader("operate.authorization.step", "operate.authorization.eyebrow", t("operate.authorization.title"), t(mutating ? "operate.authorization.mutationState" : "operate.authorization.readOnlyState"), "authorization")}
    <p class="operate-stage-summary">${esc(t("operate.authorization.detail"))}</p>
    <div class="operate-target-binding" ${testIdAttribute("operate", "authorization", "target")}><small>${esc(t("operate.fact.targetRef"))}</small><code>${esc(preview.target_ref)}</code></div>
    ${mutating ? `<label class="operate-authorize-label">${esc(t("operate.authorization.type", { phrase }))}<input type="text" data-operate-authorization ${testIdAttribute("operate", "authorization", "phrase")} autocomplete="off" value="${esc(state.authorization)}" /></label>` : ""}
    ${blocked ? `<p class="operate-disabled-reason" ${testIdAttribute("operate", "authorization", "blocked")}>${esc(t("operate.authorization.blocked"))}</p>` : ""}
    <button type="button" class="${controlClass(mutating ? "mutate" : "primary")}" data-operate-submit ${testIdAttribute("operate", "authorization", "submit")} ${blocked || !authorized ? "disabled" : ""}>${esc(t(`operate.authorization.${submitKey}`))}</button>
  </section>`;
}

function lifecycleStrip(terminal) {
  const stages = ["reviewed", "preflighted", "authorized", "accepted", "readback", terminal ? "terminal" : "pending"];
  return `<ol class="operate-lifecycle" aria-label="${esc(t("operate.lifecycle.label"))}" ${testIdAttribute("operate", "receipt", "lifecycle")}>${stages.map((stage) => `<li>${esc(t(`operate.lifecycle.${stage}`))}</li>`).join("")}</ol>`;
}

function lifecyclePanel(state) {
  const inspection = state.inspection;
  if (!inspection && state.phase !== "LOST_ACK" && state.phase !== "OUTCOME_UNKNOWN") {
    return `<section class="operate-stage operate-receipt is-pending" ${testIdAttribute("operate", "receipt")}>
      ${stageHeader("operate.receipt.step", "operate.receipt.eyebrow", t("operate.receipt.emptyTitle"), null, "receipt")}
      <p class="operate-stage-summary">${esc(t("operate.receipt.empty"))}</p>
    </section>`;
  }
  if (!inspection) {
    const operationId = state.preview?.operation_id ?? t("operate.value.unknown");
    return `<section class="operate-stage operate-receipt operate-unknown" ${testIdAttribute("operate", "receipt")}>
      ${stageHeader("operate.receipt.step", "operate.receipt.eyebrow", t("operate.receipt.lostTitle"), "OUTCOME_UNKNOWN", "receipt")}
      <p>${esc(t("operate.receipt.lost", { operationId }))}</p><p>${esc(t("operate.receipt.noBlindRetry"))}</p>
      <button type="button" class="${controlClass("secondary")}" data-operate-reconcile ${testIdAttribute("operate", "receipt", "reconcile")}>${esc(t("operate.receipt.reconcile"))}</button>
    </section>`;
  }
  const receipt = inspection.receipt;
  const terminal = terminalReceipt(receipt?.state);
  const stdoutTail = inspection.logs?.stdout_tail;
  const stderrTail = inspection.logs?.stderr_tail;
  return `<section class="operate-stage operate-receipt" ${testIdAttribute("operate", "receipt")}>
    ${stageHeader("operate.receipt.step", "operate.receipt.eyebrow", inspection.operation_id, receipt?.state, "receipt")}
    ${lifecycleStrip(terminal)}
    <dl class="operate-facts">
      ${targetFact(t("operate.receipt.record"), receipt?.meta?.record_id, "receipt-record")}
      ${targetFact(t("operate.receipt.target"), receipt?.target_ref, "receipt-target")}
      ${targetFact(t("operate.receipt.postcondition"), receipt?.postcondition_ref, "receipt-postcondition")}
      ${targetFact(t("operate.receipt.error"), receipt?.error_ref, "receipt-error")}
    </dl>
    <div class="operate-receipt-actions">
      <button type="button" class="${controlClass("inspect")}" data-operate-open-receipt ${testIdAttribute("operate", "receipt", "open")}>${esc(t("operate.receipt.open"))}</button>
      ${inspection.postcondition ? `<button type="button" class="${controlClass("inspect")}" data-operate-open-postcondition ${testIdAttribute("operate", "receipt", "postcondition")}>${esc(t("operate.receipt.openPostcondition"))}</button>` : ""}
      ${!terminal || receipt?.state === "OUTCOME_UNKNOWN" ? `<button type="button" class="${controlClass("secondary")}" data-operate-reconcile ${testIdAttribute("operate", "receipt", "reconcile")}>${esc(t("operate.receipt.reconcile"))}</button>` : ""}
    </div>
    ${(stdoutTail || stderrTail) ? `<details class="ui-disclosure operate-command-logs" ${testIdAttribute("operate", "receipt", "logs")}><summary>${esc(t("operate.receipt.logs"))}</summary>${stderrTail ? `<h4>${esc(t("operate.receipt.stderr"))}</h4><pre>${esc(stderrTail)}</pre>` : ""}${stdoutTail ? `<h4>${esc(t("operate.receipt.stdout"))}</h4><pre>${esc(stdoutTail)}</pre>` : ""}</details>` : ""}
    <details class="ui-disclosure" ${testIdAttribute("operate", "receipt", "literal")}><summary>${esc(t("operate.receipt.literal"))}</summary><pre>${esc(JSON.stringify(inspection, null, 2))}</pre></details>
  </section>`;
}

export function renderOperateMarkup(state, defense) {
  const unavailable = !defense?.mutationAllowed;
  const globalError = state.error && !(state.phase === "ERROR" && String(state.error.code ?? "").startsWith("GUI17_PARAMETER"));
  const markup = `<div class="operate-view" data-operate-phase="${esc(state.phase)}" ${testIdAttribute("operate", "view")}>
    <header class="operate-heading" ${testIdAttribute("operate", "heading")}><div><span class="eyebrow">${esc(t("operate.eyebrow"))}</span><h2>${esc(t("operate.title"))}</h2><p>${esc(t("operate.summary"))}</p></div><div class="operate-zone" ${testIdAttribute("operate", "boundary")}><strong>${esc(t("operate.boundary.label"))}</strong><span>${esc(t("operate.boundary.live"))}</span><small>${esc(t("operate.boundary.detail"))}</small></div></header>
    ${unavailable ? `<div class="operate-blocker operate-global" role="alert" ${testIdAttribute("operate", "unavailable")}><strong>${esc(t("operate.unavailable.title"))}</strong><p>${esc(defense?.detail ?? t("operate.unavailable.fallback"))}</p></div>` : ""}
    ${globalError ? `<div class="operate-error operate-global" role="alert" ${testIdAttribute("operate", "error")}><strong>${esc(state.error.code ?? t("operate.error.genericCode"))}</strong><p>${esc(state.error.message ?? t("operate.error.generic"))}</p></div>` : ""}
    ${actionCatalog(state)}
    <div class="operate-sequence" ${testIdAttribute("operate", "sequence")}>
      ${parameterPanel(state, !unavailable)}${previewPanel(state)}${authorizePanel(state)}${lifecyclePanel(state)}
    </div>
  </div>`;
  assertUniqueTestIds(markup);
  return markup;
}

export function bindOperateInteractions(host, handlers) {
  host.querySelectorAll("[data-operate-action]").forEach((button) => button.addEventListener("click", () => handlers.onAction?.(button.dataset.operateAction)));
  host.querySelector("[data-operate-dry-run]")?.addEventListener("change", (event) => handlers.onDryRun?.(event.currentTarget.checked));
  host.querySelector("[data-operate-parameters]")?.addEventListener("input", (event) => handlers.onParameters?.(event.currentTarget.value));
  host.querySelector("[data-operate-authorization]")?.addEventListener("input", (event) => handlers.onAuthorization?.(event.currentTarget.value));
  host.querySelector("[data-operate-preview]")?.addEventListener("click", () => handlers.onPreview?.());
  host.querySelector("[data-operate-submit]")?.addEventListener("click", () => handlers.onSubmit?.());
  host.querySelectorAll("[data-operate-reconcile]").forEach((button) => button.addEventListener("click", () => handlers.onReconcile?.()));
  host.querySelector("[data-operate-open-receipt]")?.addEventListener("click", () => handlers.onOpenReceipt?.());
  host.querySelector("[data-operate-open-postcondition]")?.addEventListener("click", () => handlers.onOpenPostcondition?.());
}
