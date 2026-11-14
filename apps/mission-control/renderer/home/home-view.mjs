function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function metric(value, { percent = false, integer = false } = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return "UNAVAILABLE";
  if (typeof value === "string") return value;
  if (percent) return `${(value * 100).toFixed(1)}%`;
  if (integer) return Math.round(value).toLocaleString();
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 3 });
}

function card(title, rows, state) {
  return `<section class="home-metric-card" data-state="${esc(state)}">
    <header><h2>${esc(title)}</h2><span>${esc(state)}</span></header>
    <dl>${rows.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl>
  </section>`;
}

function renderStartup(model) {
  const startup = model.startup;
  const running = startup.running === true;
  const title = startup.state === "GENERATION_ZERO_READY"
    ? `Generation ${startup.generation} is accepted and ready`
    : running
      ? "Trainer is running. Waiting for the first accepted learning event."
      : "Accepted learner is idle. No domain learning evidence exists yet.";
  const detail = startup.state === "GENERATION_ZERO_READY"
    ? "Mission Control is connected to the real learner. Training has not started, so learning, curriculum, and resource cards have no evidence to report yet."
    : running
      ? "The control plane reports an active trainer. This view will populate when the first accepted learning records become available."
      : "The learner is valid and inspectable. Start or resume training when you are ready; empty evidence is not treated as a telemetry failure.";
  return `<section class="home-startup" data-state="${esc(startup.state)}">
    <span class="eyebrow">Live learner · setup state</span>
    <h2>${esc(title)}</h2>
    <p>${esc(detail)}</p>
    <dl>
      <div><dt>Accepted generation</dt><dd>${esc(startup.generation)}</dd></div>
      <div><dt>Optimizer step</dt><dd>${esc(startup.optimizerStep)}</dd></div>
      <div><dt>Trainer</dt><dd>${running ? "RUNNING" : startup.running === false ? "STOPPED" : "UNKNOWN"}</dd></div>
      <div><dt>Stage</dt><dd>${esc(startup.stage ?? "UNKNOWN")}</dd></div>
      <div><dt>Learning telemetry</dt><dd>${running ? "WAITING FOR FIRST ACCEPTED EVENT" : "NO TRAINING EVENTS YET"}</dd></div>
    </dl>
    <p class="home-startup-next"><strong>Next:</strong> use Operate or the documented CLI resume command to start training. Mission Control will replace this setup state with observed learner telemetry as accepted records arrive.</p>
  </section>`;
}

export function renderHomeMarkup(model, { historical = false } = {}) {
  if (model.startup) return renderStartup(model);
  const learning = model.learning;
  const curriculum = model.curriculum;
  const runtime = model.runtime;
  const system = model.system;
  const badge = model.provenance === "FIXTURE"
    ? historical ? "FIXTURE · HISTORICAL" : "FIXTURE EVIDENCE"
    : historical ? "HISTORICAL" : "LIVE QUERY";
  const learningCard = card("Learning", [
    ["Latest school score", metric(learning.latestSchoolScore, { percent: true })],
    ["Best school score", metric(learning.bestSchoolScore, { percent: true })],
    ["Whole-school growth", metric(learning.wholeSchoolGrowth, { percent: true })],
    ["G/RTN", metric(learning.gRtn)],
    ["P(RET)", metric(learning.pRet, { percent: true })],
    ["Retained optimizer steps", metric(learning.retainedOptimizerSteps, { integer: true })],
  ], model.state.capability ?? "UNKNOWN");
  const curriculumCard = card("Curriculum", [
    ["Qualified capabilities", metric(curriculum.qualifiedCapabilities, { integer: true })],
    ["Observed debt", metric(curriculum.observedDebt, { integer: true })],
    ["Active concepts", metric(curriculum.activeConcepts, { integer: true })],
    ["Ready", metric(curriculum.ready, { integer: true })],
    ["Held", metric(curriculum.held, { integer: true })],
    ["Implementation-uncovered", metric(curriculum.uncovered, { integer: true })],
  ], model.state.school ?? "UNKNOWN");
  const runtimeCard = card("Runtime", [
    ["Elapsed", metric(runtime.elapsed)], ["Visits", metric(runtime.visits, { integer: true })],
    ["Visit rate", metric(runtime.visitRate)], ["Retained candidates", metric(runtime.retainedCandidates, { integer: true })],
    ["Rejected candidates", metric(runtime.rejectedCandidates, { integer: true })],
    ["Accepted steps / hour", metric(runtime.acceptedStepsHour, { integer: true })],
  ], model.state.run ?? "UNKNOWN");
  const systemCard = card("System", [
    ["Unified memory pressure", metric(system.memoryPressure, { percent: true })],
    ["Peak memory", metric(system.peakMemory)], ["Disk reserve", metric(system.diskReserve)],
    ["Correction / requal debt", metric(system.correctionDebt, { integer: true })],
    ["Hard warnings", metric(system.hardWarnings, { integer: true })],
  ], model.state.resource ?? "UNKNOWN");

  return `<div class="home-dashboard" data-learning="${esc(model.learningStatus)}">
    <section class="home-verdict" aria-label="Three second learner health summary">
      <div><span class="eyebrow">${esc(badge)}</span><h2>${esc(model.learningStatus.replaceAll("_", " "))}</h2>
        <p>${model.learningStatus === "IMPROVING" ? "Fresh retained improvement is evidenced." : model.learningStatus === "THROUGHPUT_ONLY" ? "Throughput is present, but no fresh retained improvement is evidenced." : "No fresh retained improvement is currently evidenced."}</p></div>
      <div class="home-questions" aria-label="Five core operator questions">
        <span>RUNNING <strong>${runtime.running === true ? "YES" : runtime.running === false ? "NO" : "UNAVAILABLE"}</strong></span>
        <span>LEARNING <strong>${esc(model.learningStatus)}</strong></span>
        <span>WORK <strong>${esc(model.currentWork.capabilityId ?? "UNAVAILABLE")}</strong></span>
        <span>REGRESSION <strong>${model.pulse.some((event) => event.kind === "regress") ? "OBSERVED" : "NONE OBSERVED"}</strong></span>
        <span>INVALIDITY <strong>${model.attention.length ? `${model.attention.length} REVIEW` : "NONE OBSERVED"}</strong></span>
      </div>
    </section>
    <div class="home-health-strip">${learningCard}${curriculumCard}${runtimeCard}${systemCard}</div>
    <div class="home-lower-grid">
      <section class="home-panel home-pulse"><header><div><span class="eyebrow">Chronological evidence</span><h2>Learning Pulse</h2></div><span>${model.pulse.length} events</span></header>
        <div class="pulse-list">${model.pulse.map((event, index) => `<button type="button" data-home-target-kind="${esc(event.target?.kind ?? "evidence")}" data-home-target-id="${esc(event.target?.id ?? `pulse:${index}`)}"><span class="pulse-kind">${esc(event.kind)}</span><strong>${esc(event.label)}</strong><small>${esc(event.detail)}</small></button>`).join("") || `<p class="home-empty">No evidenced learning events.</p>`}</div>
      </section>
      <div class="home-middle-stack">
        <section class="home-panel home-current"><header><div><span class="eyebrow">Active transaction</span><h2>Current Work</h2></div><span>${esc(model.currentWork.capabilityId ? "OBSERVED" : "UNAVAILABLE")}</span></header>
          <dl>${[["Target capability",model.currentWork.capabilityId],["Strategy",model.currentWork.strategy],["Intent",model.currentWork.candidateIntent],["Source family",model.currentWork.sourceFamily],["Target assessment",model.currentWork.targetAssessment],["Protected assessment",model.currentWork.protectedAssessment]].map(([label,value])=>`<div><dt>${esc(label)}</dt><dd>${esc(value ?? "UNAVAILABLE")}</dd></div>`).join("")}</dl>
        </section>
        <section class="home-panel home-school"><header><div><span class="eyebrow">Compact capability overview</span><h2>School Map</h2></div><span>${model.schoolRows.length} rows</span></header>
          <div class="home-school-table-wrap"><table><thead><tr><th>Capability</th><th>Now</th><th>Best</th><th>Δ</th><th>Debt</th><th>Retention</th><th>Status</th></tr></thead><tbody>${model.schoolRows.map((row) => `<tr><th><button type="button" data-home-target-kind="capability" data-home-target-id="${esc(row.id)}">${esc(row.id)}</button></th><td>${esc(metric(row.now))}/${esc(metric(row.total))}</td><td>${esc(metric(row.best))}</td><td>${esc(metric(row.delta))}</td><td>${esc(metric(row.debt))}</td><td>${esc(metric(row.pRet,{percent:true}))}</td><td>${esc(row.status ?? "UNKNOWN")}</td></tr>`).join("")}</tbody></table></div>
        </section>
      </div>
      <section class="home-panel home-attention"><header><div><span class="eyebrow">Actionable only</span><h2>Attention Required</h2></div><span>${model.attention.length}</span></header>
        <div class="attention-list">${model.attention.map((item) => `<button type="button" data-home-target-kind="${esc(item.target?.kind ?? item.kind)}" data-home-target-id="${esc(item.target?.id ?? item.id)}"><span>${esc(item.kind)}</span><strong>${esc(item.label)}</strong><small>${esc(item.detail)}</small></button>`).join("") || `<p class="home-quiet">No actionable concerns in the available evidence.</p>`}</div>
      </section>
    </div>
  </div>`;
}

export function bindHomeInteractions(host, onInspect) {
  host.querySelectorAll("[data-home-target-id]").forEach((button) => {
    button.addEventListener("click", () => onInspect({
      kind: button.dataset.homeTargetKind,
      id: button.dataset.homeTargetId,
    }));
  });
}
